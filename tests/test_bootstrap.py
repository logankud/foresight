"""Smoke tests for the project bootstrap configuration.

These tests don't exercise application logic — they verify that the
foundational pyproject.toml hasn't drifted away from agreed E1.S1 / E1.S2
decisions (project name, Python floor, dependency groups, license).
Catching those regressions at PR time is far cheaper than diagnosing them
weeks later.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())


def test_project_name_is_foresight() -> None:
    config = _load_pyproject()
    assert config["project"]["name"] == "foresight"


def test_python_floor_is_311_or_higher() -> None:
    requires = _load_pyproject()["project"]["requires-python"]
    accepted_floors = (">=3.11", ">=3.12", ">=3.13", "~=3.11", "~=3.12", "~=3.13")
    assert any(marker in requires for marker in accepted_floors), (
        f"requires-python must declare Python >= 3.11 (got: {requires!r})"
    )


def test_dependency_groups_present() -> None:
    groups = _load_pyproject().get("dependency-groups", {})
    for required in ("dev", "test", "lint"):
        assert required in groups, f"missing dependency group: {required!r}"


def test_dev_group_includes_test_and_lint() -> None:
    dev = _load_pyproject()["dependency-groups"]["dev"]
    includes = {
        item["include-group"] for item in dev if isinstance(item, dict) and "include-group" in item
    }
    assert {"test", "lint"}.issubset(includes), (
        "dev group must include both test and lint groups via "
        "{include-group = ...}; otherwise `uv sync --group dev` won't pull "
        "the lint/test tools."
    )


def test_license_declared_proprietary() -> None:
    license_field = _load_pyproject()["project"]["license"]
    text = license_field.get("text", "") if isinstance(license_field, dict) else license_field
    assert "Proprietary" in text or "All Rights Reserved" in text, (
        "License field must reflect the chosen proprietary license."
    )
