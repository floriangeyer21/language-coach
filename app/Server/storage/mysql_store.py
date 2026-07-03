"""MySQL storage backend (SQLAlchemy Core + aiomysql).

Implements StorageBackend with the same dict return shapes as the file backend.
See context/spec/data/mysql.md.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import create_async_engine

from .base import StorageBackend
from .schema import facts, memory, messages, metadata, users, vocab_groups, words


def _now() -> datetime:
    # Store naive UTC; formatted back to ISO(+00:00) on read for cross-backend parity.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _row(mapping) -> dict[str, Any]:
    """Convert a result row mapping to a plain dict, ISO-formatting datetimes."""
    out: dict[str, Any] = {}
    for k, v in dict(mapping).items():
        out[k] = _iso(v) if isinstance(v, datetime) else v
    return out


class MySQLStorage(StorageBackend):
    def __init__(self, database_url: str):
        # Note: pool_pre_ping is incompatible with the aiomysql adapter
        # (ping() signature mismatch in SQLAlchemy's pymysql dialect), so we rely
        # on pool_recycle to retire stale connections instead.
        self._engine = create_async_engine(
            database_url, pool_recycle=3600, future=True,
        )

    async def init(self) -> None:
        """Idempotently create tables on startup."""
        async with self._engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    # ---- users ----
    async def create_user(self, email, password_hash, display_name, learning_language):
        async with self._engine.begin() as conn:
            now = _now()
            res = await conn.execute(insert(users).values(
                email=email, password_hash=password_hash, display_name=display_name,
                learning_language=learning_language, created_at=now,
            ))
            uid = res.inserted_primary_key[0]
            await conn.execute(insert(memory).values(user_id=uid, summary=None, summary_updated_at=None))
            row = (await conn.execute(select(users).where(users.c.id == uid))).mappings().first()
            return _row(row)

    async def get_user_by_email(self, email):
        async with self._engine.begin() as conn:
            row = (await conn.execute(select(users).where(users.c.email == email))).mappings().first()
            return _row(row) if row else None

    async def get_user_by_id(self, user_id):
        async with self._engine.begin() as conn:
            row = (await conn.execute(select(users).where(users.c.id == user_id))).mappings().first()
            return _row(row) if row else None

    async def update_user(self, user_id, **fields):
        vals = {k: v for k, v in fields.items() if v is not None}
        async with self._engine.begin() as conn:
            if vals:
                await conn.execute(update(users).where(users.c.id == user_id).values(**vals))
            row = (await conn.execute(select(users).where(users.c.id == user_id))).mappings().first()
            return _row(row)

    # ---- messages ----
    async def add_message(self, user_id, role, content):
        async with self._engine.begin() as conn:
            now = _now()
            res = await conn.execute(insert(messages).values(
                user_id=user_id, role=role, content=content, created_at=now,
            ))
            mid = res.inserted_primary_key[0]
            row = (await conn.execute(select(messages).where(messages.c.id == mid))).mappings().first()
            return _row(row)

    async def list_messages(self, user_id, limit, offset):
        async with self._engine.begin() as conn:
            total = (await conn.execute(
                select(func.count()).select_from(messages).where(messages.c.user_id == user_id)
            )).scalar_one()
            rows = (await conn.execute(
                select(messages).where(messages.c.user_id == user_id)
                .order_by(messages.c.id.asc()).limit(limit).offset(offset)
            )).mappings().all()
            return [_row(r) for r in rows], total

    async def last_messages(self, user_id, n):
        async with self._engine.begin() as conn:
            rows = (await conn.execute(
                select(messages).where(messages.c.user_id == user_id)
                .order_by(messages.c.id.desc()).limit(n)
            )).mappings().all()
            return [_row(r) for r in reversed(rows)]

    async def clear_messages(self, user_id):
        async with self._engine.begin() as conn:
            await conn.execute(delete(messages).where(messages.c.user_id == user_id))

    # ---- memory ----
    async def _memory_dict(self, conn, user_id) -> dict[str, Any]:
        mem = (await conn.execute(select(memory).where(memory.c.user_id == user_id))).mappings().first()
        fact_rows = (await conn.execute(
            select(facts).where(facts.c.user_id == user_id).order_by(facts.c.id.asc())
        )).mappings().all()
        summary = mem["summary"] if mem else None
        updated = _iso(mem["summary_updated_at"]) if mem else None
        return {"summary": summary, "summary_updated_at": updated, "facts": [_row(f) for f in fact_rows]}

    async def get_memory(self, user_id):
        async with self._engine.begin() as conn:
            return await self._memory_dict(conn, user_id)

    async def set_summary(self, user_id, summary):
        async with self._engine.begin() as conn:
            await conn.execute(
                update(memory).where(memory.c.user_id == user_id)
                .values(summary=summary, summary_updated_at=_now())
            )
            return await self._memory_dict(conn, user_id)

    async def add_fact(self, user_id, text):
        async with self._engine.begin() as conn:
            res = await conn.execute(insert(facts).values(user_id=user_id, text=text, created_at=_now()))
            fid = res.inserted_primary_key[0]
            row = (await conn.execute(select(facts).where(facts.c.id == fid))).mappings().first()
            return _row(row)

    async def list_facts(self, user_id):
        async with self._engine.begin() as conn:
            rows = (await conn.execute(
                select(facts).where(facts.c.user_id == user_id).order_by(facts.c.id.asc())
            )).mappings().all()
            return [_row(r) for r in rows]

    async def delete_fact(self, user_id, fact_id):
        async with self._engine.begin() as conn:
            res = await conn.execute(
                delete(facts).where(facts.c.id == fact_id, facts.c.user_id == user_id)
            )
            return res.rowcount > 0

    async def wipe_memory(self, user_id):
        async with self._engine.begin() as conn:
            await conn.execute(
                update(memory).where(memory.c.user_id == user_id)
                .values(summary=None, summary_updated_at=None)
            )
            await conn.execute(delete(facts).where(facts.c.user_id == user_id))

    # ---- groups ----
    async def _count_words(self, conn, user_id, group_id) -> int:
        return (await conn.execute(
            select(func.count()).select_from(words)
            .where(words.c.user_id == user_id, words.c.group_id == group_id)
        )).scalar_one()

    async def create_group(self, user_id, name, is_default=False):
        async with self._engine.begin() as conn:
            res = await conn.execute(insert(vocab_groups).values(
                user_id=user_id, name=name, is_default=is_default, created_at=_now(),
            ))
            gid = res.inserted_primary_key[0]
            row = (await conn.execute(select(vocab_groups).where(vocab_groups.c.id == gid))).mappings().first()
            out = _row(row)
            out["word_count"] = 0
            return out

    async def list_groups(self, user_id):
        async with self._engine.begin() as conn:
            rows = (await conn.execute(
                select(vocab_groups).where(vocab_groups.c.user_id == user_id)
                .order_by(vocab_groups.c.is_default.desc(), vocab_groups.c.id.asc())
            )).mappings().all()
            # word counts in one grouped query
            counts = dict((await conn.execute(
                select(words.c.group_id, func.count()).where(words.c.user_id == user_id)
                .group_by(words.c.group_id)
            )).all())
            out = []
            for r in rows:
                g = _row(r)
                g["word_count"] = counts.get(r["id"], 0)
                out.append(g)
            return out

    async def get_group(self, user_id, group_id):
        async with self._engine.begin() as conn:
            row = (await conn.execute(
                select(vocab_groups).where(vocab_groups.c.id == group_id, vocab_groups.c.user_id == user_id)
            )).mappings().first()
            if not row:
                return None
            g = _row(row)
            g["word_count"] = await self._count_words(conn, user_id, group_id)
            return g

    async def get_group_by_name(self, user_id, name):
        async with self._engine.begin() as conn:
            row = (await conn.execute(
                select(vocab_groups).where(vocab_groups.c.user_id == user_id, vocab_groups.c.name == name)
            )).mappings().first()
            if not row:
                return None
            g = _row(row)
            g["word_count"] = await self._count_words(conn, user_id, row["id"])
            return g

    async def get_default_group(self, user_id):
        async with self._engine.begin() as conn:
            row = (await conn.execute(
                select(vocab_groups).where(vocab_groups.c.user_id == user_id, vocab_groups.c.is_default.is_(True))
            )).mappings().first()
            if not row:
                return None
            g = _row(row)
            g["word_count"] = await self._count_words(conn, user_id, row["id"])
            return g

    async def update_group(self, user_id, group_id, name):
        async with self._engine.begin() as conn:
            await conn.execute(
                update(vocab_groups).where(vocab_groups.c.id == group_id, vocab_groups.c.user_id == user_id)
                .values(name=name)
            )
            row = (await conn.execute(select(vocab_groups).where(vocab_groups.c.id == group_id))).mappings().first()
            g = _row(row)
            g["word_count"] = await self._count_words(conn, user_id, group_id)
            return g

    async def delete_group(self, user_id, group_id):
        async with self._engine.begin() as conn:
            await conn.execute(
                delete(vocab_groups).where(vocab_groups.c.id == group_id, vocab_groups.c.user_id == user_id)
            )

    # ---- words ----
    async def create_word(self, user_id, term, translation, group_id):
        async with self._engine.begin() as conn:
            res = await conn.execute(insert(words).values(
                user_id=user_id, term=term, translation=translation, group_id=group_id, created_at=_now(),
            ))
            wid = res.inserted_primary_key[0]
            row = (await conn.execute(select(words).where(words.c.id == wid))).mappings().first()
            return _row(row)

    async def list_words(self, user_id, group_id, limit, offset):
        async with self._engine.begin() as conn:
            cond = [words.c.user_id == user_id]
            if group_id is not None:
                cond.append(words.c.group_id == group_id)
            total = (await conn.execute(select(func.count()).select_from(words).where(*cond))).scalar_one()
            rows = (await conn.execute(
                select(words).where(*cond).order_by(words.c.id.asc()).limit(limit).offset(offset)
            )).mappings().all()
            return [_row(r) for r in rows], total

    async def get_word(self, user_id, word_id):
        async with self._engine.begin() as conn:
            row = (await conn.execute(
                select(words).where(words.c.id == word_id, words.c.user_id == user_id)
            )).mappings().first()
            return _row(row) if row else None

    async def update_word(self, user_id, word_id, **fields):
        vals = {k: v for k, v in fields.items() if v is not None}
        async with self._engine.begin() as conn:
            if vals:
                await conn.execute(
                    update(words).where(words.c.id == word_id, words.c.user_id == user_id).values(**vals)
                )
            row = (await conn.execute(select(words).where(words.c.id == word_id))).mappings().first()
            return _row(row)

    async def delete_word(self, user_id, word_id):
        async with self._engine.begin() as conn:
            res = await conn.execute(
                delete(words).where(words.c.id == word_id, words.c.user_id == user_id)
            )
            return res.rowcount > 0

    async def move_words_to_group(self, user_id, from_group_id, to_group_id):
        async with self._engine.begin() as conn:
            await conn.execute(
                update(words).where(words.c.user_id == user_id, words.c.group_id == from_group_id)
                .values(group_id=to_group_id)
            )
