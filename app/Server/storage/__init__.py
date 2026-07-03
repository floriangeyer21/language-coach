"""Storage factory — selects backend from config."""
from functools import lru_cache

from config import get_settings

from .base import StorageBackend
from .file_store import FileStorage


@lru_cache
def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.storage_backend == "file":
        return FileStorage(settings.file_storage_path)
    if settings.storage_backend == "mysql":
        # Imported lazily so the file backend has no SQLAlchemy/aiomysql dependency.
        from .mysql_store import MySQLStorage
        return MySQLStorage(settings.database_url)
    raise ValueError(f"Unknown STORAGE_BACKEND: {settings.storage_backend}")
