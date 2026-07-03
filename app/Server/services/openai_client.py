"""Thin wrapper around the OpenAI async client. Only place that talks to OpenAI."""
from functools import lru_cache

from openai import AsyncOpenAI

from config import get_settings


@lru_cache
def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key)
