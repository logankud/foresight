"""Smoke tests for the top-level Makefile.

These guard the Makefile *contract* — what targets exist, that they're
discoverable via `make help`, and that the working ones still run.
Catches the most common regression classes: target deleted, target
renamed, target added without a help annotation.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = REPO_ROOT / "Makefile"


def _run_make(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", *args],
        cwd=REPO_ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


# Targets the contract guarantees, split by category.
WORKING_TARGETS = {
    "help",
    "install",
    "install-py",
    "install-web",
    "test",
    "fmt",
    "lint",
    "ci",
    "web-dev",
    "web-build",
    "web-lint",
    "clean",
}

STUB_TARGETS = {
    "up",
    "down",
    "migrate",
    "seed",
}

ALL_TARGETS = WORKING_TARGETS | STUB_TARGETS


def test_makefile_exists() -> None:
    assert MAKEFILE.exists(), "Top-level Makefile must exist."


def test_help_is_default_target() -> None:
    """Running `make` with no arguments should print the help output."""
    result = _run_make()
    assert "Foresight — make targets" in result.stdout


def test_help_lists_all_targets() -> None:
    """Every documented target must show up in `make help` so contributors
    don't have to grep the Makefile to find commands."""
    result = _run_make("help")
    missing = [t for t in ALL_TARGETS if t not in result.stdout]
    assert not missing, (
        f"Targets missing from `make help`: {missing!r}. Ensure each "
        "`.PHONY: <name>` is followed by `<name>: ... ## description`."
    )


def test_every_phony_target_has_help_annotation() -> None:
    """Static check: every target declared in `.PHONY:` lines must have a
    `## comment` somewhere in the file, otherwise it won't show up in help."""
    text = MAKEFILE.read_text()
    phony_targets: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^\.PHONY:\s*(.+)$", line)
        if match:
            phony_targets.update(match.group(1).split())

    annotated_targets = set(re.findall(r"^([a-zA-Z0-9_-]+):.*?##", text, flags=re.MULTILINE))
    missing = phony_targets - annotated_targets
    assert not missing, f"`.PHONY` targets missing `## description` annotations: {missing!r}"


def test_stub_targets_exit_zero_with_pointer() -> None:
    """Stub targets (for future stories) must exit 0 and tell the contributor
    where to look. Failing here means a stub regressed to either a hard error
    or a silent no-op."""
    for target in STUB_TARGETS:
        result = _run_make(target)
        assert result.returncode == 0, f"`make {target}` must exit 0, got {result.returncode}."
        assert (
            "stub" in result.stdout.lower()
        ), f"`make {target}` must announce itself as a stub, got: {result.stdout!r}"
        assert (
            "PLAN.md" in result.stdout
        ), f"`make {target}` must point at PLAN.md so contributors find context."


def test_lint_exits_zero_on_clean_tree() -> None:
    """`make lint` must pass on the tree as committed — i.e., the lint
    contract is reachable from a fresh clone without manual fixes."""
    result = _run_make("lint", check=False)
    assert (
        result.returncode == 0
    ), f"`make lint` failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
