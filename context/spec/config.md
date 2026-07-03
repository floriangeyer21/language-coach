# Configuration & Secrets Spec

All configuration is centralized so secrets never leak into code and environments can be swapped without code changes.

## Location

- **Server:** `app/server/config.py` — a single module that loads and validates all environment variables (recommended: a Pydantic `Settings` class via `pydantic-settings`). Nothing else in the server reads `os.environ` directly.
- **Environment files:** `app/server/.env` (gitignored, real secrets) and `app/server/.env.example` (committed, placeholder values documenting every variable).
- **Web:** Next.js reads `NEXT_PUBLIC_*` vars from `app/web/.env.local`; only the API base URL is public.

## Server Environment Variables

| Variable | Purpose | Example / Default |
|----------|---------|-------------------|
| `OPENAI_API_KEY` | OpenAI auth token (provided later) | `sk-...` |
| `OPENAI_CHAT_MODEL` | Model for chat replies | `gpt-4o` |
| `OPENAI_MEMORY_MODEL` | Model for summary/fact extraction | `gpt-4o-mini` |
| `DATABASE_URL` | MySQL DSN in production | `mysql+aiomysql://user:pass@host/db` |
| `STORAGE_BACKEND` | `mysql` or `file` | `file` (dev), `mysql` (prod) |
| `FILE_STORAGE_PATH` | Dir for file backend | `./.data` |
| `JWT_SECRET` | Signing key for access tokens | `<random>` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_TTL_MIN` | Access token lifetime (minutes) | `60` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |

## Web Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Server base URL | `http://localhost:8000` |

## Rules

- Every variable that exists in `.env` must be documented in `.env.example`.
- The config module fails fast on startup if a required variable is missing.
- Storage backend is selected via `STORAGE_BACKEND` behind a common interface (see `features/new/memory-management.md`), so switching file → MySQL requires no feature-code changes.
