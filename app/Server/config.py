"""Central configuration. Nothing else in the server reads os.environ directly.

See context/spec/config.md.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: str
    openai_chat_model: str = "gpt-4o"
    openai_memory_model: str = "gpt-4o-mini"

    # Storage
    storage_backend: str = "file"  # "file" | "mysql"
    file_storage_path: str = "./.data"
    database_url: str = ""

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 60

    # CORS
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    # Fails fast if a required variable (e.g. OPENAI_API_KEY, JWT_SECRET) is missing.
    return Settings()
