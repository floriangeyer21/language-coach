"""Vocabulary domain logic. Used by both the vocabulary router and the chat AI tool."""
from __future__ import annotations

from typing import Optional

from config import get_settings
from storage.base import StorageBackend

from .openai_client import get_client


async def auto_translate(term: str, learning_language: str) -> str:
    """Best-effort translation of a learning-language term into English."""
    try:
        client = get_client()
        resp = await client.chat.completions.create(
            model=get_settings().openai_memory_model,
            messages=[
                {"role": "system", "content": (
                    f"Translate the given {learning_language} word or phrase into English. "
                    "Reply with ONLY the English translation, no punctuation or extra words."
                )},
                {"role": "user", "content": term},
            ],
            temperature=0,
            max_tokens=30,
        )
        return (resp.choices[0].message.content or "").strip() or term
    except Exception:
        return term


async def add_word(
    store: StorageBackend,
    user: dict,
    term: str,
    translation: Optional[str] = None,
    group_id: Optional[int] = None,
    group_name: Optional[str] = None,
) -> dict:
    """Add a word to the user's vocabulary.

    Resolution order for the target group: explicit group_id -> group_name ->
    default group. Missing translation is auto-translated (best effort).
    """
    user_id = user["id"]

    if group_id is not None:
        group = await store.get_group(user_id, group_id)
        if group is None:
            group = await store.get_default_group(user_id)
    elif group_name:
        group = await store.get_group_by_name(user_id, group_name)
        if group is None:
            group = await store.create_group(user_id, group_name)
    else:
        group = await store.get_default_group(user_id)

    if not translation:
        translation = await auto_translate(term, user["learning_language"])

    return await store.create_word(user_id, term=term, translation=translation, group_id=group["id"])
