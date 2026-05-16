"""Shared pytest fixtures for Foresight tests.

The DB fixtures here implement the **compose Postgres + transactional
rollback** strategy locked in during E2.S1 planning:

1. ``db_engine`` (session-scoped): connects to the Postgres reachable via
   the compose stack (or the URL in ``$DATABASE_URL`` if overridden).
   Creates a dedicated ``foresight_test`` database, runs
   ``Base.metadata.create_all()`` once, and tears down at session end.
   Until E2.S4 migrations land, schema is created directly from the
   SQLAlchemy models.

2. ``db_session`` (function-scoped): opens a connection + transaction,
   binds a Session to it, and **rolls back the outer transaction** when
   the test exits. Each test sees a fresh-looking DB without any
   between-test cleanup code.

Tests that don't touch the DB don't request these fixtures and pay no
cost.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from urllib.parse import urlparse, urlunparse

import pytest
from foresight.core.models import Base
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

# Test DB name is intentionally distinct from the production-style `foresight`
# DB so a stray `pytest` against a populated compose DB doesn't wipe data.
TEST_DB_NAME = "foresight_test"


def _server_url() -> str:
    """Return a connection URL pointing at the Postgres *server* (not a
    specific database), so we can `CREATE DATABASE foresight_test`.
    """
    base = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://foresight:foresight-dev@localhost:5432/foresight",
    )
    parsed = urlparse(base)
    # Replace the path (database name) with the maintenance DB `postgres`.
    return urlunparse(parsed._replace(path="/postgres"))


def _test_db_url() -> str:
    parsed = urlparse(_server_url())
    return urlunparse(parsed._replace(path=f"/{TEST_DB_NAME}"))


def _drop_then_create_test_db() -> None:
    """Drop + create the `foresight_test` database with autocommit.

    Done via psycopg directly (autocommit-required) rather than
    SQLAlchemy's connection which defaults to a transaction.
    """
    server_url = _server_url()
    server_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with server_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    server_engine.dispose()


def _drop_test_db() -> None:
    server_engine = create_engine(_server_url(), isolation_level="AUTOCOMMIT")
    with server_engine.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)'))
    server_engine.dispose()


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    """Session-scoped engine bound to the freshly-created test DB."""
    _drop_then_create_test_db()
    engine = create_engine(_test_db_url(), pool_pre_ping=True)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()
        _drop_test_db()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """Function-scoped Session that auto-rolls-back at test end.

    Uses the SAVEPOINT-rollback pattern so commits inside the test still
    appear to work (they nest inside the outer transaction).
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    # If the test code commits, immediately reopen a nested SAVEPOINT so
    # subsequent statements still benefit from rollback.
    nested = connection.begin_nested()

    @pytest.hookimpl  # type: ignore[misc]
    def _restart_savepoint(_session: Session, _transaction: object) -> None:
        nonlocal nested
        if not nested.is_active:  # pragma: no cover - defensive
            nested = connection.begin_nested()

    from sqlalchemy import event

    event.listen(session, "after_transaction_end", _restart_savepoint)

    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", _restart_savepoint)
        session.close()
        transaction.rollback()
        connection.close()
