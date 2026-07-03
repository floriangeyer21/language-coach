# Feature: AI Memory Management

**Status:** planned (in `new/`)

## Goal

Give the AI coach durable, per-user memory so conversations are contextual and continuous, while keeping per-request token cost bounded. Three tiers of memory.

## Memory Tiers

1. **Short-term — last 10 messages.**
   - The most recent 10 messages (user + assistant) of the user's conversation, sent verbatim on every chat request.
   - Derived directly from chat history; not stored separately.

2. **Mid-term — running summary.**
   - A single evolving natural-language summary of the whole conversation with this user (their level, goals, recurring topics, style preferences).
   - Stored per user, updated over time (not regenerated from scratch each turn — incrementally revised).
   - Sent on every chat request alongside short-term messages.

3. **Long-term — facts.**
   - Discrete, durable facts about the user (e.g. "Native English speaker", "Learning German for work", "Struggles with dative case").
   - Stored as a list per user. Sent on every chat request.
   - Deduplicated: the extractor must avoid adding facts already present.

## Prompt Assembly (per chat turn)

Order sent to `OPENAI_CHAT_MODEL`:
```
[system prompt: role = language coach, user's learning_language]
[long-term facts]
[running summary]
[last 10 messages]
[new user message]
```

## Update Flow (async, after each turn)

Chosen strategy: **async after each turn** — does not block the chat reply.

After the assistant reply is returned to the user:
1. A background job calls `OPENAI_MEMORY_MODEL` with the latest exchange + current summary.
2. It produces: (a) a revised running summary, (b) any new facts to append (deduplicated against existing).
3. Persist the updated summary (with `summary_updated_at`) and new facts.
4. Failures are logged and retried/skipped without affecting the user-visible chat; memory is best-effort, eventually consistent.

## User Control

Users can review and correct memory: overwrite the summary, add/delete facts, or wipe all long-term memory. See `api/memory.md`.

## Storage Interface

Memory persistence goes through the common storage abstraction (`STORAGE_BACKEND` = `file` in dev, `mysql` in prod) so backends are swappable without changing this feature's logic. See `config.md`.

## Data (conceptual)

- `memory`: `user_id`, `summary` (nullable text), `summary_updated_at`.
- `fact`: `id`, `user_id`, `text`, `created_at`.

## API

See `api/memory.md` and `api/chat.md`.

## Traceability

- API: `api/memory.md`, `api/chat.md`
- Design: `design/web.md` (Memory screen)
- Related: [[chat-with-ai]], [[user-management]]
