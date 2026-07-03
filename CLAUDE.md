# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Spec-Driven Development

This is a **spec-driven project**. Before writing or modifying any code:

1. Check `context/spec/` for an existing spec that covers the area.
2. If no spec exists, create or update one first, then implement.
3. Implementation should trace back to a spec section — if you can't point to one, the spec is incomplete.

The `context/spec/overview.md` is the entry point. It contains the project vision, core concepts, and an index of all spec files.

## Change Log

`context/CHANGELOG.md` is a running, high-level record of what has been done to
the project (planning, features, infra, tooling). Consult it to quickly get up
to speed on project history, and append a short one-line entry whenever you
complete a meaningful step (newest entries at the top).

## Feature Spec Lifecycle

Features live in `context/spec/features/` and follow a two-stage flow:

1. **Planning** — create a spec file under `context/spec/features/new/`. The file should describe the feature before any code is written.
2. **Done** — once the feature is fully implemented, move the spec file to `context/spec/features/existing/`.

Never write code for a feature that doesn't have a spec in `new/`. Never leave a shipped feature's spec in `new/`.

## Code Location

**All application code lives under `app/`.** The repo root holds only specs (`context/`), docs, and top-level config. Never place source code outside `app/`.

```
app/
  server/    # Python backend — FastAPI
  web/       # JS frontend — Next.js (React)
```

## Tech Stack

- **Server:** Python + FastAPI (async, OpenAPI-typed).
- **Web:** Next.js (React).
- **AI provider:** OpenAI.
- **Memory/DB:** MySQL in production; a local file-based store is acceptable for early development behind the same interface.
- **Auth:** email + password, JWT access tokens.

## Configuration & Secrets

All environment variables (OpenAI token, DB connection, JWT secret, etc.) are declared in a single dedicated config file inside `app/` — see `context/spec/config.md`. Never hardcode secrets; read them from this config layer.

## Project Structure

```
context/
  spec/
    overview.md              # Vision, core concepts, spec index
    api/                     # Server API specification
    design/                  # Web design specification (dark theme)
    config.md                # Environment variables & config layout
    features/
      new/                   # Specs for planned / in-progress features
      existing/              # Specs for fully implemented features
app/                         # All application code (see Code Location)
```
