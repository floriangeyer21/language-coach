# LanguageCoach — Project Specification

## Vision

An AI-powered language coaching application. Initially AI-only; the architecture should not preclude adding human coaches later.

## Core Concepts

- **Learner** — the end user practicing a language
- **Coach** — the entity providing feedback and exercises (AI model today, potentially human later)
- **Session** — a single practice interaction between a learner and a coach
- **Lesson** — structured content within a session (vocabulary, grammar, conversation, pronunciation, etc.)

## Tech Stack

- **Server:** Python + FastAPI, under `app/server/`.
- **Web:** Next.js (React), under `app/web/`. Dark-themed.
- **AI provider:** OpenAI.
- **Storage:** MySQL in production; file-based store in dev, behind one interface.
- **Auth:** email + password, JWT.
- All code lives under `app/`. All config/secrets in a single config layer (`config.md`).

## Goals (v1)

Three initial features:

1. **User management** — accounts, per-user isolated context.
2. **AI chat with memory** — contextual coaching conversation grounded in tiered memory.
3. **Vocabulary** — grouped words with flashcard review.

## Spec Index

| File | Description |
|------|-------------|
| `overview.md` | This file — project vision and concepts |
| `config.md` | Environment variables & config layout |
| `api/overview.md` | Server API conventions + domain index |
| `api/auth.md` | Auth & user endpoints |
| `api/chat.md` | AI chat endpoints + tools |
| `api/memory.md` | Memory inspection/management endpoints |
| `api/vocabulary.md` | Vocabulary & flashcard endpoints |
| `design/web.md` | Web design spec (dark theme) |
| `data/mysql.md` | MySQL production data source |
| `features/new/user-management.md` | Accounts & per-user isolation |
| `features/new/chat-with-ai.md` | Contextual AI chat |
| `features/new/memory-management.md` | Tiered AI memory |
| `features/new/vocabulary.md` | Vocabulary & flashcards |
| `features/existing/` | Specs for fully implemented features |

## Conventions

- Each feature or domain area gets its own spec file in this folder.
- Specs drive implementation — code should trace back to a spec section.
- When a spec changes, update it before changing code.
