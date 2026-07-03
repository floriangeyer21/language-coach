# Feature: Vocabulary

**Status:** planned (in `new/`)

## Goal

Let a user build and review a personal vocabulary of words in their learning language, organized into groups, reviewable as flashcards.

## Concepts

- **Word:** a pair of `term` (learning language, e.g. German "Apfel") and `translation` (user's language = English, e.g. "apple").
- **Group:** a named collection of words. Each user has exactly one **default group** ("Group 1", created at registration, cannot be deleted).

## Scope (v1)

### Adding words
- User adds a word manually (term + optional translation). If translation omitted, server may auto-translate via OpenAI (best effort).
- User selects the group to add to. **Default is the last group the user added a word to** for that session/UI; if none, the default group ("Group 1").
- Words can also be added **by the AI chat** via the `add_vocabulary_word` tool (see [[chat-with-ai]]) — e.g. "add these words to my Travel group".

### Managing
- Create, rename, delete groups. Deleting a non-default group moves its words to the default group (never orphan words). Default group cannot be deleted.
- Edit a word (term, translation) and move it between groups.
- Delete a word.
- View stored words, filterable by group, with word counts per group.

### Reviewing (flashcards)
- User selects a group and reviews **all words in that group in random order**.
- Flashcard: front = English (`translation`), back = learning-language (`term`); flip to reveal, advance to next.
- No spaced-repetition / scoring in v1 — simple flip-and-advance. Randomization happens server-side per review request.

## Data (conceptual)

- `group`: `id`, `user_id`, `name`, `is_default`, `created_at`. Unique `(user_id, name)`.
- `word`: `id`, `user_id`, `group_id`, `term`, `translation`, `created_at`.

## API

See `api/vocabulary.md`.

## Design

Vocabulary screen + review/flashcard mode in `design/web.md`.

## Out of scope (v1)

Spaced repetition (SM-2), review history/stats, import/export, audio pronunciation, sharing groups between users. SRS may be layered on later without breaking the group model.

## Traceability

- API: `api/vocabulary.md`
- Design: `design/web.md`
- Related: [[chat-with-ai]] (AI adds words), [[user-management]] (default group provisioning)
