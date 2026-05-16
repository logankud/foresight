"""Foresight runtime settings.

Reads configuration from environment variables (or a `.env` file in local
dev) via `pydantic-settings`. Required variables fail fast at process
startup with a clear error message rather than mysteriously misbehaving
at first use.

Resolution order:
1. Process env (`os.environ`).
2. `.env` file at the repo root (local dev only — `.env` is gitignored).
3. Hard-coded defaults declared on the model below.

E9.S5 will extend this to read from AWS Secrets Manager when
``APP_ENV`` is ``dev`` or ``prod``; for now everything reads from env.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level Foresight settings.

    Subdivided into ``app_env``, ``database``, ``aws``, etc. as the
    surface grows. Today: app-env + database only.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- App env -----
    app_env: Literal["local", "dev", "prod", "test"] = Field(
        default="local",
        description="Runtime environment. Drives where secrets resolve from.",
    )

    # ----- Database -----
    database_url: str = Field(
        default="postgresql+psycopg://foresight:foresight-dev@localhost:5432/foresight",
        description="SQLAlchemy database URL. Defaults to the compose Postgres.",
    )

    # Pool sizing — sensible defaults for a single-tenant dev box. Tuned
    # per-env via AWS Secrets Manager in E9.S5.
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=5, ge=0, le=100)
    db_statement_timeout_ms: int = Field(
        default=30_000,
        description="Per-statement timeout in milliseconds.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance.

    ``lru_cache`` ensures the env is parsed once per process; subsequent
    callers get the same instance. To reset for tests, call
    ``get_settings.cache_clear()``.
    """
    return Settings()
