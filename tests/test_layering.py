"""Smoke test for the import-linter layering contracts.

`uv run lint-imports` evaluates the contracts defined under
``[tool.importlinter]`` in ``pyproject.toml`` against the current import
graph. This test runs it as a subprocess and asserts exit 0 — which
means every contract is "kept" (no layering violations) AND the
contracts themselves are well-formed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_layering_contracts_kept() -> None:
    result = subprocess.run(
        ["uv", "run", "lint-imports"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"lint-imports failed — at least one layering contract was broken or "
        f"the configuration is invalid.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "broken" not in result.stdout.lower() or "0 broken" in result.stdout, (
        f"lint-imports reported broken contracts:\n{result.stdout}"
    )
