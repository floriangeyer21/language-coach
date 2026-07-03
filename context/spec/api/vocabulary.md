# API — Vocabulary

Drives / driven by `features/new/vocabulary.md`.

## Model

- `group`: `{ "id", "name", "is_default": bool, "word_count", "created_at" }`. Each user has exactly one default group (created at registration, name "Group 1").
- `word`: `{ "id", "term", "translation", "group_id", "created_at" }`.
  - `term` = word in the **learning language** (e.g. German "Apfel").
  - `translation` = word in the user's language (English, e.g. "apple").

## Groups

### GET /vocabulary/groups
`200`: `{ "items": [ <group>... ], "total" }`.

### POST /vocabulary/groups
Request: `{ "name": "Food" }` → `201`: the group. Error `409 group_name_taken`.

### PATCH /vocabulary/groups/{id}
Request: `{ "name": "..." }` → `200`. The default group cannot be renamed to collide; default flag is immutable.

### DELETE /vocabulary/groups/{id}
`204`. Cannot delete the default group (`400 cannot_delete_default`). Words in a deleted group move to the default group (do not orphan words).

## Words

### GET /vocabulary/words
Query: `?group_id=` (optional filter), plus pagination. `200`: `{ "items": [ <word>... ], "total" }`.

### POST /vocabulary/words
Request: `{ "term": "Apfel", "translation": "apple", "group_id": null }`
- If `group_id` omitted/null → added to the user's default group.
- `translation` optional; if omitted the server may auto-translate via OpenAI (best effort).
`201`: the word. Same endpoint is used by the chat AI tool `add_vocabulary_word`.

### PATCH /vocabulary/words/{id}
Request (optional fields): `{ "term", "translation", "group_id" }` → `200`. Moving between groups = change `group_id`.

### DELETE /vocabulary/words/{id}
`204`.

## Review (Flashcards)

### GET /vocabulary/groups/{id}/review
Returns all words in the group in **random order** for a flashcard session.
`200`: `{ "group": <group>, "cards": [ { "id", "front", "back" }... ] }`
- `front` = `translation` (user's language, English) — the prompt side.
- `back` = `term` (learning language) — the answer side.
- No spaced-repetition state in v1; the client flips cards and advances. Ordering is randomized server-side per request.
