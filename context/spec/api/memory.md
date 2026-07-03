# API — Memory

Drives / driven by `features/new/memory-management.md`. Lets the user inspect and manage what the AI remembers about them.

## GET /memory

Response `200`:
```json
{ "summary": "User is a beginner in German, prefers grammar-focused explanations...",
  "summary_updated_at": "...",
  "facts": [ { "id": 3, "text": "Native English speaker learning German", "created_at": "..." } ] }
```

## PUT /memory/summary

Manually overwrite the running summary (user correction).
Request: `{ "summary": "..." }` → Response `200`: updated memory object.

## POST /memory/facts

Add a long-term fact manually.
Request: `{ "text": "Works as a software engineer" }` → Response `201`: the fact.

## DELETE /memory/facts/{id}

Remove a fact. Response `204`.

## DELETE /memory

Wipe all long-term memory (summary + facts) for the user. Does not delete chat history. Response `204`.

## Notes

- Short-term memory (last 10 messages) is derived from chat history, not stored separately — no endpoint.
- Summary and facts are updated automatically by the async post-turn job; these endpoints are for user-facing review and correction.
