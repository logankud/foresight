"""Smoke tests for the GitHub Actions CI workflow.

Guards the workflow *contract* — that `ci.yml` exists, parses as YAML,
declares the expected jobs, and triggers on the expected events. Catches
the most common regressions: workflow file renamed, job removed, trigger
silently narrowed.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_JOBS = {"quality", "tests", "web-install"}


def _load_workflow() -> dict:
    return yaml.safe_load(CI_WORKFLOW.read_text())


def test_ci_workflow_exists() -> None:
    assert CI_WORKFLOW.exists(), f"Expected workflow at {CI_WORKFLOW}."


def test_ci_workflow_parses() -> None:
    config = _load_workflow()
    assert config, "Workflow must be a non-empty YAML mapping."
    assert config.get("name") == "ci", "Workflow `name:` must be 'ci'."


def test_ci_declares_required_jobs() -> None:
    config = _load_workflow()
    jobs = set(config.get("jobs", {}).keys())
    missing = REQUIRED_JOBS - jobs
    assert not missing, (
        f"CI workflow is missing required job(s): {missing!r}. "
        "If a job was intentionally retired, update REQUIRED_JOBS."
    )


def test_ci_triggers_on_pull_request_and_push() -> None:
    """The workflow must run on every PR and on pushes to `develop` / `main`.
    PyYAML parses bare `on:` as the Python boolean `True`, so accept either."""
    config = _load_workflow()
    triggers = config.get("on") or config.get(True)
    assert triggers is not None, "Workflow must declare `on:` triggers."

    assert "pull_request" in triggers, "Workflow must run on every pull request."

    push = triggers.get("push")
    assert push, "Workflow must run on push events."
    branches = push.get("branches", [])
    for required_branch in ("develop", "main"):
        assert required_branch in branches, (
            f"Workflow must run on push to `{required_branch}` (got: {branches!r})."
        )


def test_ci_has_concurrency_cancellation() -> None:
    """A new push to the same ref should cancel any in-flight CI run; without
    this, PR pushes pile up and burn Actions minutes."""
    config = _load_workflow()
    concurrency = config.get("concurrency")
    assert concurrency, "Workflow must declare a `concurrency:` block."
    assert concurrency.get("cancel-in-progress") is True, (
        "concurrency.cancel-in-progress must be true to cancel superseded runs."
    )
