# Web Design Spec

Visual and interaction spec for `app/web` (Next.js). v1 covers web only. **Dark theme.**

## Principles

- Dark-first, single theme in v1 (no light mode toggle yet). Calm, focused, reading-heavy (chat + flashcards).
- Content-centered layout, generous whitespace, no visual clutter competing with the conversation.
- Accessible: text contrast ≥ WCAG AA on the dark background; keyboard-navigable; visible focus rings.

## Color Tokens

Defined as CSS variables; components reference tokens, never raw hex.

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0F1115` | App background |
| `--surface` | `#171A21` | Cards, panels, message bubbles (assistant) |
| `--surface-2` | `#1F232C` | Raised/hover surfaces |
| `--border` | `#2A2F3A` | Dividers, card borders |
| `--text` | `#E6E8EB` | Primary text |
| `--text-muted` | `#9AA1AC` | Secondary text, timestamps |
| `--primary` | `#6C8CFF` | Primary actions, links, user message bubble |
| `--primary-hover` | `#586FE0` | Hover state |
| `--success` | `#4ADE80` | "Word added" confirmations |
| `--danger` | `#F87171` | Destructive actions, errors |

## Typography

- System/UI sans stack (e.g. Inter). Base 16px, line-height 1.6 for body.
- Scale: `h1` 28, `h2` 22, `h3` 18, body 16, small 13.
- Learning-language text may render slightly larger/emphasized in flashcards.

## Layout

- **App shell:** left sidebar nav (persistent on desktop, collapsible drawer on mobile) + main content area.
- Sidebar items: **Chat**, **Vocabulary**, **Memory**, and account menu (profile, logout) pinned at the bottom.
- Max content width ~ 820px for reading views; flashcard view centered.
- Responsive: single-column below 768px; sidebar becomes a top bar + drawer.

## Screens

### Chat
- Scrollable message list: assistant bubbles on `--surface` (left-aligned), user bubbles on `--primary` (right-aligned).
- Sticky composer at bottom: multiline input + send. Enter sends, Shift+Enter newlines.
- Streaming: assistant tokens appear incrementally with a typing indicator.
- When the AI adds a vocabulary word (`actions`), show an inline toast/chip: "Added *Apfel* to Group 1" in `--success`.

### Vocabulary
- Group selector (tabs or dropdown) listing groups with word counts; default group first.
- Word list: term / translation columns, add-word button, per-word edit/delete, move-to-group control.
- **Review mode:** launched per group. Full-screen centered flashcard:
  - Front shows the English prompt; tap/click/Space flips to reveal the learning-language term (CSS flip animation).
  - Next advances to a randomly ordered next card; progress indicator (e.g. "3 / 12").
  - Exit returns to the group list.

### Memory
- Read/edit view of the AI's memory: editable summary textarea (save button) and a list of facts with add/delete.
- "Reset memory" as a guarded destructive action (confirm dialog, `--danger`).

## Components (shared)

Buttons (primary/secondary/danger), text inputs, textarea, cards, toasts, confirm dialog, loading skeletons, empty states. All themed via the tokens above.

## Out of scope (v1)

Light mode, theming customization, animations beyond the flashcard flip and streaming indicator, mobile-native app.
