# Server API Spec

Defines the HTTP API exposed by `app/server` (FastAPI). This is the contract between web and server.

## Conventions

- Base path: `/api`. All examples below omit the `/api` prefix.
- Format: JSON request/response bodies; `Content-Type: application/json`.
- Auth: `Authorization: Bearer <access_token>` on all protected routes. Public routes: `POST /auth/register`, `POST /auth/login`.
- IDs: integers (auto-increment) or UUID strings — consistent across all entities. Timestamps: ISO 8601 UTC.
- Errors: consistent envelope
  ```json
  { "error": { "code": "invalid_credentials", "message": "Email or password is incorrect." } }
  ```
- Status codes: `200` OK, `201` Created, `400` validation, `401` unauthenticated, `403` forbidden, `404` not found, `409` conflict, `422` FastAPI body validation, `500` server.
- Every response body scoped to the authenticated user; a user can never read or mutate another user's data.
- Pagination: list endpoints accept `?limit=` (default 50, max 200) and `?offset=`; responses include `{ "items": [...], "total": <int> }`.

## Domains

| Domain | Prefix | Spec |
|--------|--------|------|
| Auth & users | `/auth`, `/users` | `auth.md` |
| AI chat | `/chat` | `chat.md` |
| Memory | `/memory` | `memory.md` |
| Vocabulary | `/vocabulary` | `vocabulary.md` |

Each domain spec lists endpoints, request/response shapes, and links to the driving feature spec in `features/`.
