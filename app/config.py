from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    news_api_key: str | None = os.getenv("NEWS_API_KEY") or None
    news_api_endpoint: str = os.getenv(
        "NEWS_API_ENDPOINT", "https://newsapi.org/v2/everything"
    )
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    database_path: str = os.getenv("DATABASE_PATH", "data/newsagent.db")
    chroma_path: str = os.getenv("CHROMA_PATH", "data/chroma")
    articles_per_page: int = _int_env("ARTICLES_PER_PAGE", 10)
    news_fetch_limit: int = _int_env("NEWS_FETCH_LIMIT", 50)
    initial_fetch_on_startup: bool = _bool_env("INITIAL_FETCH_ON_STARTUP", True)
    initial_news_count: int = _int_env("INITIAL_NEWS_COUNT", _int_env("NEWS_FETCH_LIMIT", 50))


settings = Settings()
