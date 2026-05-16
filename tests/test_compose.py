"""Smoke tests for the local Docker Compose stack.

Guards the compose *contract* — file exists, parses, declares the
expected service, and the service has a healthcheck. Catches the
common regressions (file renamed, healthcheck stripped, image bumped
to a major version unintentionally) without requiring Docker to be
running.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = REPO_ROOT / "infra" / "compose" / "docker-compose.yml"


def _load_compose() -> dict:
    return yaml.safe_load(COMPOSE_FILE.read_text())


def test_compose_file_exists() -> None:
    assert COMPOSE_FILE.exists(), f"Expected compose file at {COMPOSE_FILE}."


def test_compose_declares_db_service() -> None:
    services = _load_compose().get("services", {})
    assert "db" in services, (
        f"Compose file must declare a `db` service (Postgres). Got services: {sorted(services)!r}."
    )


def test_db_image_is_pinned_to_postgres_16_alpine() -> None:
    """Catches accidental major-version bumps. Postgres major versions
    occasionally introduce backward-incompatible defaults; pinning at
    16-alpine until we deliberately upgrade is the right floor."""
    db = _load_compose()["services"]["db"]
    image = db.get("image", "")
    assert image.startswith("postgres:16"), (
        f"db.image must pin to a postgres:16 variant (got: {image!r})."
    )


def test_db_has_healthcheck() -> None:
    """Without a healthcheck, `make up` returns before Postgres can
    accept connections — every subsequent migrate/seed/test command
    races against an unready DB."""
    db = _load_compose()["services"]["db"]
    healthcheck = db.get("healthcheck")
    assert healthcheck, "db service must declare a healthcheck."
    assert "pg_isready" in str(healthcheck.get("test", "")), (
        "healthcheck must use `pg_isready` (the canonical Postgres readiness check)."
    )


def test_db_port_is_localhost_only() -> None:
    """Binding to 0.0.0.0 exposes the dev DB to the entire local network
    (and any malicious actor on the same WiFi). Localhost-only is the
    deliberate safe default."""
    db = _load_compose()["services"]["db"]
    ports = db.get("ports", [])
    assert any("127.0.0.1:5432" in str(p) for p in ports), (
        f"db.ports must bind to 127.0.0.1 only (got: {ports!r})."
    )


def test_db_has_persistent_volume() -> None:
    """Without a named volume, every `compose down` wipes data — dev DBs
    get re-seeded constantly. Persistent volume + explicit `down -v` reset
    is the documented contract."""
    db = _load_compose()["services"]["db"]
    volumes = db.get("volumes", [])
    assert any("foresight_db_data" in str(v) for v in volumes), (
        f"db service must mount the `foresight_db_data` named volume (got: {volumes!r})."
    )
