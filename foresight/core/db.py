"""SQLAlchemy engine + session factory.

This module is intentionally minimal — just enough infrastructure for
E2.S1 model tests to run. The full storage abstraction (with BlobStore,
context-managed session helpers, and tenant-scoped query injection)
lands in E2.S3.

For tests, use the ``db_session`` fixture in ``tests/conftest.py``
(landing with E2.S1 tests). It wraps each test in a transaction and
rolls back at the end.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from foresight.core.settings import get_settings

# Lazy-initialized engine. Created on first call to `get_engine()` so
# importing this module doesn't trigger a DB connection.
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return the process-singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            connect_args={"options": f"-c statement_timeout={settings.db_statement_timeout_ms}"},
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the process-singleton sessionmaker.

    Sessions are bound to the engine returned by ``get_engine()``.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            class_=Session,
        )
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager that yields a Session and commits on exit (or
    rolls back on exception).

    Intended for production code paths; tests should use the
    transactional-rollback fixture in ``tests/conftest.py``.
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_for_tests() -> None:
    """Reset the cached engine + session factory.

    Useful in test fixtures that need to recreate the engine against a
    different URL (e.g., per-session testcontainers). Production code
    should never call this.
    """
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
