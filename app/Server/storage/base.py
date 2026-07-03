"""Storage interface. Feature code depends only on this, never on a concrete backend.

Selected via STORAGE_BACKEND (file in dev, mysql in prod) — see context/spec/config.md.
Entities are plain dicts; every method is scoped by user_id where applicable.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class StorageBackend(ABC):
    # ---- users ----
    @abstractmethod
    async def create_user(self, email: str, password_hash: str, display_name: str,
                          learning_language: str) -> dict[str, Any]: ...

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def update_user(self, user_id: int, **fields: Any) -> dict[str, Any]: ...

    # ---- messages ----
    @abstractmethod
    async def add_message(self, user_id: int, role: str, content: str) -> dict[str, Any]: ...

    @abstractmethod
    async def list_messages(self, user_id: int, limit: int, offset: int) -> tuple[list[dict], int]: ...

    @abstractmethod
    async def last_messages(self, user_id: int, n: int) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def clear_messages(self, user_id: int) -> None: ...

    # ---- memory ----
    @abstractmethod
    async def get_memory(self, user_id: int) -> dict[str, Any]: ...

    @abstractmethod
    async def set_summary(self, user_id: int, summary: str) -> dict[str, Any]: ...

    @abstractmethod
    async def add_fact(self, user_id: int, text: str) -> dict[str, Any]: ...

    @abstractmethod
    async def list_facts(self, user_id: int) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def delete_fact(self, user_id: int, fact_id: int) -> bool: ...

    @abstractmethod
    async def wipe_memory(self, user_id: int) -> None: ...

    # ---- vocabulary groups ----
    @abstractmethod
    async def create_group(self, user_id: int, name: str, is_default: bool = False) -> dict[str, Any]: ...

    @abstractmethod
    async def list_groups(self, user_id: int) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_group(self, user_id: int, group_id: int) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def get_group_by_name(self, user_id: int, name: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def get_default_group(self, user_id: int) -> dict[str, Any]: ...

    @abstractmethod
    async def update_group(self, user_id: int, group_id: int, name: str) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_group(self, user_id: int, group_id: int) -> None: ...

    # ---- vocabulary words ----
    @abstractmethod
    async def create_word(self, user_id: int, term: str, translation: str,
                          group_id: int) -> dict[str, Any]: ...

    @abstractmethod
    async def list_words(self, user_id: int, group_id: Optional[int],
                         limit: int, offset: int) -> tuple[list[dict], int]: ...

    @abstractmethod
    async def get_word(self, user_id: int, word_id: int) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def update_word(self, user_id: int, word_id: int, **fields: Any) -> dict[str, Any]: ...

    @abstractmethod
    async def delete_word(self, user_id: int, word_id: int) -> bool: ...

    @abstractmethod
    async def move_words_to_group(self, user_id: int, from_group_id: int, to_group_id: int) -> None: ...
