"""Tiered AI memory. See context/spec/features/new/memory-management.md.

Tiers:
  1. short-term  -> last 10 messages (from chat history, not stored separately)
  2. mid-term    -> running summary (incrementally revised)
  3. long-term   -> deduplicated facts
"""
from __future__ import annotations

import json

from config import get_settings
from storage.base import StorageBackend

from .openai_client import get_client

SHORT_TERM_N = 10


async def build_context_blocks(store: StorageBackend, user_id: int) -> tuple[str, list[dict]]:
    """Return (memory_preamble, recent_messages) to prepend to a chat request."""
    memory = await store.get_memory(user_id)
    facts = memory.get("facts", [])
    summary = memory.get("summary")

    parts = []
    if facts:
        parts.append("Known facts about the user:\n" + "\n".join(f"- {f['text']}" for f in facts))
    if summary:
        parts.append("Conversation summary so far:\n" + summary)
    preamble = "\n\n".join(parts)

    recent = await store.last_messages(user_id, SHORT_TERM_N)
    recent_msgs = [{"role": m["role"], "content": m["content"]} for m in recent]
    return preamble, recent_msgs


async def update_memory_after_turn(store: StorageBackend, user_id: int) -> None:
    """Async post-turn job: revise the running summary and extract new facts.

    Best-effort and eventually consistent — failures are swallowed so they never
    affect the user-visible chat.
    """
    try:
        memory = await store.get_memory(user_id)
        existing_summary = memory.get("summary") or "(none yet)"
        existing_facts = [f["text"] for f in memory.get("facts", [])]

        recent = await store.last_messages(user_id, SHORT_TERM_N)
        transcript = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

        client = get_client()
        resp = await client.chat.completions.create(
            model=get_settings().openai_memory_model,
            messages=[
                {"role": "system", "content": (
                    "You maintain long-term memory for a language-learning coach app. "
                    "Given the current summary, the list of known facts, and the recent "
                    "conversation, produce an updated summary and any NEW durable facts "
                    "about the user (their level, goals, native/target language, "
                    "preferences, struggles). Do NOT repeat facts already known. "
                    "Respond as strict JSON: "
                    '{"summary": "<revised summary>", "new_facts": ["fact", ...]}'
                )},
                {"role": "user", "content": (
                    f"Current summary:\n{existing_summary}\n\n"
                    f"Known facts:\n" + ("\n".join(f"- {f}" for f in existing_facts) or "(none)") +
                    f"\n\nRecent conversation:\n{transcript}"
                )},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content or "{}")

        new_summary = (data.get("summary") or "").strip()
        if new_summary:
            await store.set_summary(user_id, new_summary)

        existing_lower = {f.lower() for f in existing_facts}
        for fact in data.get("new_facts", []) or []:
            fact = (fact or "").strip()
            if fact and fact.lower() not in existing_lower:
                await store.add_fact(user_id, fact)
                existing_lower.add(fact.lower())
    except Exception:
        # Memory is best-effort; log in a real deployment.
        pass
