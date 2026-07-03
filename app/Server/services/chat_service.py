"""Chat turn orchestration: prompt assembly, OpenAI call, tool calling.

See context/spec/features/new/chat-with-ai.md and api/chat.md.
"""
from __future__ import annotations

import json

from config import get_settings
from storage.base import StorageBackend

from . import vocabulary_service
from .openai_client import get_client

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_vocabulary_word",
            "description": (
                "Save a word the user is learning to their personal vocabulary. "
                "Use when the user asks to add/save a word, or when it clearly helps "
                "their learning. The term is in the user's target learning language."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "The word/phrase in the learning language."},
                    "translation": {"type": "string", "description": "English translation (optional)."},
                    "group_name": {"type": "string", "description": "Target group name (optional; omit for default group)."},
                },
                "required": ["term"],
            },
        },
    }
]


def _system_prompt(user: dict) -> str:
    return (
        f"You are a patient, encouraging language coach. The user is a native English "
        f"speaker learning {user['learning_language']}. Teach in a concise, friendly way. "
        f"When you introduce useful vocabulary or the user asks to save a word, call the "
        f"add_vocabulary_word tool. Keep replies focused and not overly long."
    )


async def generate_reply(store: StorageBackend, user: dict, memory_preamble: str,
                         recent_messages: list[dict]) -> tuple[str, list[dict]]:
    """Return (assistant_text, actions). Handles up to one round of tool calls."""
    settings = get_settings()
    client = get_client()

    messages: list[dict] = [{"role": "system", "content": _system_prompt(user)}]
    if memory_preamble:
        messages.append({"role": "system", "content": memory_preamble})
    messages.extend(recent_messages)

    actions: list[dict] = []

    resp = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        tools=TOOLS,
        temperature=0.6,
    )
    choice = resp.choices[0].message

    if choice.tool_calls:
        messages.append({
            "role": "assistant",
            "content": choice.content or "",
            "tool_calls": [tc.model_dump() for tc in choice.tool_calls],
        })
        for tc in choice.tool_calls:
            if tc.function.name == "add_vocabulary_word":
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                word = await vocabulary_service.add_word(
                    store, user,
                    term=args.get("term", ""),
                    translation=args.get("translation"),
                    group_name=args.get("group_name"),
                )
                actions.append({
                    "type": "vocabulary_added",
                    "word_id": word["id"], "term": word["term"], "group_id": word["group_id"],
                })
                messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps({"ok": True, "word": word}),
                })
            else:
                messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps({"ok": False, "error": "unknown_tool"}),
                })

        followup = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=messages,
            temperature=0.6,
        )
        text = followup.choices[0].message.content or ""
    else:
        text = choice.content or ""

    return text, actions
