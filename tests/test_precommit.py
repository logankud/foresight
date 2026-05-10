"""Smoke tests for the pre-commit configuration.

These guard the pre-commit *contract* — that the config is valid YAML,
that the expected hooks are declared, and that pre-commit itself
considers the config well-formed. Catches the most common regressions:
config deleted, hook removed without updating the contract, broken YAML.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PRECOMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"


# Hook IDs (across repos) that must exist for the layering / format / type
# gates to actually function.
REQUIRED_HOOK_IDS = {
    # Generic file hygiene
    "end-of-file-fixer",
    "trailing-whitespace",
    "check-yaml",
    "check-toml",
    "check-merge-conflict",
    "check-added-large-files",
    "detect-private-key",
    # Python: ruff format + lint
    "ruff",
    "ruff-format",
    # Local hooks (Python project)
    "mypy",
    "lint-imports",
}


def test_precommit_config_exists() -> None:
    assert PRECOMMIT_CONFIG.exists(), ".pre-commit-config.yaml must exist at repo root."


def test_precommit_config_is_valid() -> None:
    """`pre-commit validate-config` parses and structurally validates the
    config. A failure here means the file is broken in a way that no
    contributor's pre-commit invocation will succeed until it's fixed."""
    result = subprocess.run(
        ["uv", "run", "pre-commit", "validate-config", str(PRECOMMIT_CONFIG)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"pre-commit validate-config failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.parametrize("hook_id", sorted(REQUIRED_HOOK_IDS))
def test_required_hook_is_declared(hook_id: str) -> None:
    """Every required hook must be findable by its `id:` in the config."""
    text = PRECOMMIT_CONFIG.read_text()
    needle = f"id: {hook_id}"
    assert needle in text, (
        f"Pre-commit hook {hook_id!r} is missing from .pre-commit-config.yaml — "
        f"either restore it or update REQUIRED_HOOK_IDS if the hook was "
        "intentionally retired."
    )
