"""File-based storage backend for development.

Persists all data as a single JSON document guarded by an asyncio lock.
Implements the same StorageBackend interface as the (future) MySQL backend,
so switching backends requires no feature-code changes.
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

from .base import StorageBackend


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FileStorage(StorageBackend):
    def __init__(self, path: str):
        self._dir = path
        self._file = os.path.join(path, "db.json")
        self._lock = asyncio.Lock()
        os.makedirs(path, exist_ok=True)
        self._db = self._load()

    # ---- persistence ----
    def _load(self) -> dict[str, Any]:
        if os.path.exists(self._file):
            with open(self._file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "counters": {"user": 0, "message": 0, "fact": 0, "group": 0, "word": 0},
            "users": {},      # id -> user
            "messages": {},   # user_id -> [msg]
            "memory": {},     # user_id -> {summary, summary_updated_at, facts:[]}
            "groups": {},     # user_id -> [group]
            "words": {},      # user_id -> [word]
        }

    def _flush(self) -> None:
        tmp = self._file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._db, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._file)

    def _next_id(self, kind: str) -> int:
        self._db["counters"][kind] += 1
        return self._db["counters"][kind]

    # ---- users ----
    async def create_user(self, email, password_hash, display_name, learning_language):
        async with self._lock:
            uid = self._next_id("user")
            user = {
                "id": uid, "email": email, "password_hash": password_hash,
                "display_name": display_name, "learning_language": learning_language,
                "created_at": _now(),
            }
            self._db["users"][str(uid)] = user
            self._db["messages"][str(uid)] = []
            self._db["memory"][str(uid)] = {"summary": None, "summary_updated_at": None, "facts": []}
            self._db["groups"][str(uid)] = []
            self._db["words"][str(uid)] = []
            self._flush()
            return dict(user)

    async def get_user_by_email(self, email):
        for u in self._db["users"].values():
            if u["email"].lower() == email.lower():
                return dict(u)
        return None

    async def get_user_by_id(self, user_id):
        u = self._db["users"].get(str(user_id))
        return dict(u) if u else None

    async def update_user(self, user_id, **fields):
        async with self._lock:
            u = self._db["users"][str(user_id)]
            for k, v in fields.items():
                if v is not None:
                    u[k] = v
            self._flush()
            return dict(u)

    # ---- messages ----
    async def add_message(self, user_id, role, content):
        async with self._lock:
            mid = self._next_id("message")
            msg = {"id": mid, "role": role, "content": content, "created_at": _now()}
            self._db["messages"][str(user_id)].append(msg)
            self._flush()
            return dict(msg)

    async def list_messages(self, user_id, limit, offset):
        msgs = self._db["messages"].get(str(user_id), [])
        total = len(msgs)
        return [dict(m) for m in msgs[offset:offset + limit]], total

    async def last_messages(self, user_id, n):
        msgs = self._db["messages"].get(str(user_id), [])
        return [dict(m) for m in msgs[-n:]]

    async def clear_messages(self, user_id):
        async with self._lock:
            self._db["messages"][str(user_id)] = []
            self._flush()

    # ---- memory ----
    async def get_memory(self, user_id):
        return dict(self._db["memory"][str(user_id)])

    async def set_summary(self, user_id, summary):
        async with self._lock:
            mem = self._db["memory"][str(user_id)]
            mem["summary"] = summary
            mem["summary_updated_at"] = _now()
            self._flush()
            return dict(mem)

    async def add_fact(self, user_id, text):
        async with self._lock:
            fid = self._next_id("fact")
            fact = {"id": fid, "text": text, "created_at": _now()}
            self._db["memory"][str(user_id)]["facts"].append(fact)
            self._flush()
            return dict(fact)

    async def list_facts(self, user_id):
        return [dict(f) for f in self._db["memory"][str(user_id)]["facts"]]

    async def delete_fact(self, user_id, fact_id):
        async with self._lock:
            facts = self._db["memory"][str(user_id)]["facts"]
            for i, f in enumerate(facts):
                if f["id"] == fact_id:
                    facts.pop(i)
                    self._flush()
                    return True
            return False

    async def wipe_memory(self, user_id):
        async with self._lock:
            self._db["memory"][str(user_id)] = {"summary": None, "summary_updated_at": None, "facts": []}
            self._flush()

    # ---- groups ----
    async def create_group(self, user_id, name, is_default=False):
        async with self._lock:
            gid = self._next_id("group")
            group = {"id": gid, "name": name, "is_default": is_default, "created_at": _now()}
            self._db["groups"][str(user_id)].append(group)
            self._flush()
            return dict(group)

    def _word_count(self, user_id: int, group_id: int) -> int:
        return sum(1 for w in self._db["words"].get(str(user_id), []) if w["group_id"] == group_id)

    async def list_groups(self, user_id):
        groups = self._db["groups"].get(str(user_id), [])
        out = []
        for g in groups:
            g2 = dict(g)
            g2["word_count"] = self._word_count(user_id, g["id"])
            out.append(g2)
        # default group first, then by id
        out.sort(key=lambda g: (not g["is_default"], g["id"]))
        return out

    async def get_group(self, user_id, group_id):
        for g in self._db["groups"].get(str(user_id), []):
            if g["id"] == group_id:
                g2 = dict(g)
                g2["word_count"] = self._word_count(user_id, group_id)
                return g2
        return None

    async def get_group_by_name(self, user_id, name):
        for g in self._db["groups"].get(str(user_id), []):
            if g["name"].lower() == name.lower():
                g2 = dict(g)
                g2["word_count"] = self._word_count(user_id, g["id"])
                return g2
        return None

    async def get_default_group(self, user_id):
        for g in self._db["groups"].get(str(user_id), []):
            if g["is_default"]:
                g2 = dict(g)
                g2["word_count"] = self._word_count(user_id, g["id"])
                return g2
        # should not happen; provisioned at registration
        return None

    async def update_group(self, user_id, group_id, name):
        async with self._lock:
            for g in self._db["groups"][str(user_id)]:
                if g["id"] == group_id:
                    g["name"] = name
                    self._flush()
                    g2 = dict(g)
                    g2["word_count"] = self._word_count(user_id, group_id)
                    return g2
            raise KeyError(group_id)

    async def delete_group(self, user_id, group_id):
        async with self._lock:
            groups = self._db["groups"][str(user_id)]
            self._db["groups"][str(user_id)] = [g for g in groups if g["id"] != group_id]
            self._flush()

    # ---- words ----
    async def create_word(self, user_id, term, translation, group_id):
        async with self._lock:
            wid = self._next_id("word")
            word = {"id": wid, "term": term, "translation": translation,
                    "group_id": group_id, "created_at": _now()}
            self._db["words"][str(user_id)].append(word)
            self._flush()
            return dict(word)

    async def list_words(self, user_id, group_id, limit, offset):
        words = self._db["words"].get(str(user_id), [])
        if group_id is not None:
            words = [w for w in words if w["group_id"] == group_id]
        total = len(words)
        return [dict(w) for w in words[offset:offset + limit]], total

    async def get_word(self, user_id, word_id):
        for w in self._db["words"].get(str(user_id), []):
            if w["id"] == word_id:
                return dict(w)
        return None

    async def update_word(self, user_id, word_id, **fields):
        async with self._lock:
            for w in self._db["words"][str(user_id)]:
                if w["id"] == word_id:
                    for k, v in fields.items():
                        if v is not None:
                            w[k] = v
                    self._flush()
                    return dict(w)
            raise KeyError(word_id)

    async def delete_word(self, user_id, word_id):
        async with self._lock:
            words = self._db["words"][str(user_id)]
            new = [w for w in words if w["id"] != word_id]
            found = len(new) != len(words)
            self._db["words"][str(user_id)] = new
            if found:
                self._flush()
            return found

    async def move_words_to_group(self, user_id, from_group_id, to_group_id):
        async with self._lock:
            for w in self._db["words"][str(user_id)]:
                if w["group_id"] == from_group_id:
                    w["group_id"] = to_group_id
            self._flush()
