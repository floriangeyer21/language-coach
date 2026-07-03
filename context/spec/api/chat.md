# API — AI Chat

Drives / driven by `features/new/chat-with-ai.md` and `features/new/memory-management.md`.

## Model

- A user has one ongoing **conversation** with the AI coach in v1 (single thread). Messages belong to that conversation.
- `message`: `{ "id", "role": "user" | "assistant", "content", "created_at" }`.

## GET /chat/messages

Returns conversation history (paginated, newest-last within page).
Response `200`: `{ "items": [ <message>... ], "total": <int> }`.

## POST /chat/messages

Send a user message, get the assistant reply. This is the core loop.

Request: `{ "content": "Wie sagt man 'apple'?" }`

Behavior (see memory spec for detail):
1. Persist the user message.
2. Build the prompt = system prompt + long-term facts + running summary + last 10 messages + new message.
3. Call OpenAI (`OPENAI_CHAT_MODEL`). The model may invoke a tool to add vocabulary words (see below).
4. Persist and return the assistant message.
5. **Async, after responding:** update running summary and extract facts (`OPENAI_MEMORY_MODEL`). Does not block the response.

Response `201`:
```json
{ "message": { "id", "role": "assistant", "content", "created_at" },
  "actions": [ { "type": "vocabulary_added", "word_id": 5, "term": "Apfel", "group_id": 1 } ] }
```
- `actions` reports side effects the AI performed this turn (e.g. words it added to vocabulary), so the web UI can surface them.

### Streaming variant (recommended)

`POST /chat/messages?stream=true` returns Server-Sent Events: incremental `token` events, then a final `done` event carrying the same `message` + `actions` payload. Non-streaming remains the default.

## AI Tools (function calling)

The chat model is given tools so it can act on the user's data. v1 tool:

- **`add_vocabulary_word`** — args `{ term, translation?, group_name? }`. Adds a word to the user's vocabulary (default group if `group_name` omitted). Backed by the vocabulary service; result surfaces in `actions`. See `features/new/vocabulary.md`.

## DELETE /chat/messages

Clears the conversation history for the user. Does **not** erase long-term memory (facts/summary) unless `?reset_memory=true` is passed. Response `204`.
