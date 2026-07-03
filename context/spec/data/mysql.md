# Data Source: MySQL

Production storage backend. Implements the same `StorageBackend` interface
(`app/server/storage/base.py`) as the dev file backend, so switching is a config
change only (`STORAGE_BACKEND=mysql`) with no feature-code changes.
See `../config.md` and `../features/new/memory-management.md`.

## Driver & Access Layer

- **Driver:** `aiomysql` (async).
- **Access layer:** SQLAlchemy 2.0 **Core** (not ORM) with an async engine
  (`create_async_engine`). Tables are declared as `Table` objects on a shared
  `MetaData`; queries are built with the Core expression language (parameterized —
  no string interpolation).
- **Connection:** from `DATABASE_URL`, e.g. `mysql+aiomysql://user:pass@host:3306/languagecoach`.
- **Pooling:** engine default pool with `pool_recycle=3600` to retire stale
  connections. (`pool_pre_ping` is intentionally **not** used — it is incompatible
  with the aiomysql adapter's `ping()` signature under SQLAlchemy's pymysql
  dialect; `pool_recycle` covers the dropped-connection case.)
- **Charset:** database and all text columns use `utf8mb4` (learning-language text
  may be non-ASCII).

## Bootstrap / DDL

- On server startup, if `STORAGE_BACKEND=mysql`, the backend's `init()` runs
  `metadata.create_all` (idempotent — creates tables only if absent).
- No migration framework in v1; the schema below is authoritative. Schema changes
  are additive until a migration tool is introduced.

## Schema

All ids are `BIGINT AUTO_INCREMENT` primary keys unless noted. All `created_at` /
`summary_updated_at` are `DATETIME(6)` stored in UTC; the backend returns them as
ISO 8601 strings (`+00:00`) to match the file backend's output shape. Every
non-user table has a `user_id` FK with `ON DELETE CASCADE`, and is queried scoped
by `user_id`.

### `users`
| column | type | notes |
|--------|------|-------|
| id | BIGINT PK AI | |
| email | VARCHAR(255) | UNIQUE, indexed |
| password_hash | VARCHAR(255) | bcrypt/argon2 hash |
| display_name | VARCHAR(255) | |
| learning_language | VARCHAR(100) | |
| created_at | DATETIME(6) | |

### `messages`
| column | type | notes |
|--------|------|-------|
| id | BIGINT PK AI | |
| user_id | BIGINT | FK users.id, CASCADE |
| role | VARCHAR(16) | `user` \| `assistant` |
| content | TEXT | |
| created_at | DATETIME(6) | |

Index: `(user_id, id)` — history listing and "last N" are ordered by `id`.

### `memory`
One row per user (created with the user).
| column | type | notes |
|--------|------|-------|
| user_id | BIGINT PK | FK users.id, CASCADE |
| summary | TEXT NULL | running summary |
| summary_updated_at | DATETIME(6) NULL | |

### `facts`
| column | type | notes |
|--------|------|-------|
| id | BIGINT PK AI | |
| user_id | BIGINT | FK users.id, CASCADE |
| text | TEXT | fact content |
| created_at | DATETIME(6) | |

Index: `(user_id)`.

### `vocab_groups`
(`groups` is a MySQL reserved word — table named `vocab_groups`.)
| column | type | notes |
|--------|------|-------|
| id | BIGINT PK AI | |
| user_id | BIGINT | FK users.id, CASCADE |
| name | VARCHAR(255) | |
| is_default | BOOLEAN | exactly one true per user |
| created_at | DATETIME(6) | |

Constraint: `UNIQUE (user_id, name)`. Listing order: `is_default DESC, id ASC`.
`word_count` is derived via `COUNT` join on `words`, not stored.

### `words`
| column | type | notes |
|--------|------|-------|
| id | BIGINT PK AI | |
| user_id | BIGINT | FK users.id, CASCADE |
| group_id | BIGINT | FK vocab_groups.id |
| term | VARCHAR(512) | learning language |
| translation | VARCHAR(512) | English |
| created_at | DATETIME(6) | |

Indexes: `(user_id)`, `(group_id)`.

## Interface Mapping

Each `StorageBackend` method maps to parameterized Core statements:

- `create_user` → INSERT into `users` **and** INSERT the user's `memory` row
  (single logical unit). The default vocab group is created separately by the
  auth router (`create_group(..., is_default=True)`), matching the file backend.
- `last_messages(n)` → `SELECT ... WHERE user_id=? ORDER BY id DESC LIMIT n`,
  reversed in Python to chronological order.
- `list_*` → paginated `LIMIT/OFFSET` plus a `COUNT(*)` for `total`.
- `get_memory` → SELECT the `memory` row + SELECT its `facts`, assembled into
  `{summary, summary_updated_at, facts: [...]}`.
- `set_summary` → UPSERT the `memory` row, stamping `summary_updated_at`.
- `delete_group` → the router moves words to the default group first
  (`move_words_to_group`) then deletes; the default group is never deleted
  (enforced in the router, per `api/vocabulary.md`).
- `move_words_to_group` → `UPDATE words SET group_id=? WHERE user_id=? AND group_id=?`.

## Concurrency & Integrity

- Writes rely on MySQL row-level locking; each method runs in its own
  transaction (engine `begin()`), committed on success.
- Uniqueness (`users.email`, `(user_id, name)` on groups) is enforced by DB
  constraints in addition to the router's pre-checks.

## Return Shape Parity

Methods return the same plain `dict` shapes as the file backend (same keys,
`created_at` as ISO strings, group dicts include computed `word_count`). This is a
hard requirement — routers and services are backend-agnostic.
