# API — Auth & Users

Drives / driven by `features/new/user-management.md`.

## POST /auth/register  (public)

Create an account. On success also provisions the user's default vocabulary group ("Group 1") and empty memory context.

Request:
```json
{ "email": "a@b.com", "password": "plaintext", "display_name": "Vlad", "learning_language": "German" }
```
- `learning_language` is the target language the user is learning. UI/native language is always English in v1.

Response `201`:
```json
{ "user": { "id": 1, "email": "a@b.com", "display_name": "Vlad", "learning_language": "German", "created_at": "..." },
  "access_token": "jwt...", "token_type": "bearer" }
```
Errors: `409 email_taken`, `400 weak_password`.

## POST /auth/login  (public)

Request: `{ "email": "...", "password": "..." }`
Response `200`: same shape as register (`user` + `access_token`).
Errors: `401 invalid_credentials`.

## GET /users/me

Response `200`: the `user` object (as above).

## PATCH /users/me

Update mutable profile fields.
Request (all optional): `{ "display_name": "...", "learning_language": "..." }`
Response `200`: updated `user`.

## Password Handling

- Passwords hashed with bcrypt/argon2; never stored or returned in plaintext.
- JWT payload: `{ sub: <user_id>, exp }`, signed with `JWT_SECRET`. TTL from `ACCESS_TOKEN_TTL_MIN`.
- v1 is single access token (no refresh token). Refresh flow is a future extension.
