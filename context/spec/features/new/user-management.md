# Feature: User Management

**Status:** planned (in `new/`)

## Goal

Accounts so each user has an isolated context: their own chat history, AI memory, and vocabulary. A user never sees another user's data.

## Scope (v1)

- Register with email, password, display name, and target `learning_language` (native language is always English in v1).
- Login returning a JWT access token; authenticated requests carry `Authorization: Bearer <token>`.
- View and update own profile (`display_name`, `learning_language`).
- On registration, provision per-user defaults:
  - Default vocabulary group named **"Group 1"** (`is_default = true`).
  - Empty memory context (summary = null, no facts).

## Data (conceptual)

- `user`: `id`, `email` (unique), `password_hash`, `display_name`, `learning_language`, `created_at`.
- All other entities (messages, memory, groups, words) carry a `user_id` foreign key. Every query is scoped by `user_id`.

## Security

- Passwords hashed (bcrypt/argon2). JWT signed with `JWT_SECRET`, TTL from config.
- Authorization middleware resolves `user_id` from the token and injects it; handlers must scope all data access to it.

## API

See `api/auth.md`.

## Out of scope (v1)

Password reset, email verification, refresh tokens, OAuth/social login, roles/admin. Architecture should not preclude adding these.

## Traceability

- API: `api/auth.md`
- Design: `design/web.md` (account menu, profile)
- Related: [[chat-with-ai]], [[memory-management]], [[vocabulary]] all scope to `user_id`.
