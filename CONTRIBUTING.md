# Contributing to Foresight

Foresight follows a strict per-story workflow defined in [`CLAUDE.md`](./CLAUDE.md). This document is the human-facing companion: branching model, commit conventions, PR/UAT flow, and the one-time GitHub configuration that has to happen by hand.

> **Note**: Conventions documented here are intentionally minimal. Full conventions (ADRs, code review checklist, style guides) land with story **E1.S6 — ADR system + first ADRs**. See `PLAN.md`.

## Branching Model

| Branch | Purpose |
|---|---|
| `main` | **Default branch on GitHub.** Tracks tagged releases. `develop` is promoted into `main` only as part of a release cut. No day-to-day feature work targets `main` directly. |
| `develop` | **Integration branch.** All `feature/*` PRs target `develop`. Becomes a release candidate when promoted to `main`. |
| `feature/{story-id}-{slug}` | One branch per developer story (e.g., `feature/E1.S0-git-bootstrap`, `feature/E2.S1-core-entities`). Branched from `develop`, PR'd back to `develop`. |

Story IDs come from `PLAN.md` (`E#.S#` format) and remain stable across PRs, commits, and issues.

> ⚠️ **Always specify `--base develop` when opening a PR.** Because `main` is the GitHub default branch, `gh pr create` and the GitHub web "Compare & pull request" button will pre-fill `main` as the base. For story PRs this is wrong — branch protection on `main` will reject feature PRs anyway, but explicit `--base develop` avoids the round-trip:
> ```
> gh pr create --base develop --head feature/E#.S#-slug …
> ```

## Commit Conventions

- **One commit per feature branch.** Use squash merge to ensure the PR lands as a single commit on `develop`.
- **Markdown commit messages.** The squash commit body must include:
  - A short, conventional subject line (`type(story-id): summary`, e.g., `feat(E2.S1): add core entity models`).
  - A `## Summary` section explaining the change.
  - A `## Changes` section listing each touched file/area.
  - A `## Why` section when the rationale isn't self-evident.
- **No `--no-verify`, no `--amend` of pushed commits.** If a hook fails, fix the issue and create a new commit; never bypass the gate.
- **No force-pushing to `develop` or `main`.** Force-pushes are allowed only to your own `feature/*` branch before review.

Example commit subject line:
```
feat(E2.S1): add core entity models for Tenant, Brand, Product, Variant
```

## Pull Request / UAT Flow

Every story moves through these phases:

1. **Plan** — implementation plan written and accepted by the user before code is written.
2. **Implementation** — feature branch, single commit (or rebased to one before opening the PR).
3. **Validation** — `pytest` (or equivalent) runs locally; ≥80% test coverage on touched code or a documented exemption.
4. **UAT** — open a PR using the [PR template](./.github/PULL_REQUEST_TEMPLATE.md) with **Story ID, Summary, Implementation Steps, Validation Steps, Test Coverage, Reviewer Checklist** filled in. Wait for explicit user approval.
5. **Merge** — only after UAT approval, squash-merge the PR into `develop` and delete the feature branch.
6. **Documentation** — update `README.md` and/or `PLAN.md` to reflect the merged state.

## One-Time GitHub Setup (Manual)

These steps require admin access and cannot be safely automated:

### 1. Default branch
Keep `main` as the **default branch** (no change needed). `main` is the public face of the repo and tracks releases; feature PRs explicitly target `develop`. Branch protection (below) is what prevents accidental landings on `main`.

### 2. Branch protection rules on `develop`
**Settings → Branches → Branch protection rules → Add rule** with pattern `develop`:
- ☑ Require a pull request before merging
- ☑ Require approvals (1)
- ☑ Require status checks to pass before merging *(enable once CI lands in story E1.S5; for now leave unchecked)*
- ☑ Require branches to be up to date before merging
- ☑ Require linear history *(enforces squash/rebase merges, blocks merge commits)*
- ☐ Allow force pushes — leave **off**
- ☐ Allow deletions — leave **off**

### 3. Branch protection rules on `main` (stricter)
Same as `develop`, plus:
- ☑ Restrict who can push to matching branches *(release manager only — prevents accidental direct landings now and force-pushes post-MVP)*
- ☑ Require pull request reviews from CODEOWNERS *(once `CODEOWNERS` lands)*
- *Practical effect: only PRs from `develop` can land on `main`, and only as part of a release cut. Feature PRs that mistakenly target `main` will be blocked from merging.*

### 4. Default merge button behavior
**Settings → General → Pull Requests:**
- ☑ Allow squash merging *(default; the only allowed mode for `feature/*` → `develop`)*
- ☐ Allow merge commits — disable
- ☐ Allow rebase merging — disable
- ☑ Automatically delete head branches

## Local Development

After cloning, run **`make install`** followed by **`make hooks`** once. The first sets up the venv + node modules; the second installs the pre-commit hooks that gate every commit.

### Common commands

```bash
make help          # List every target with a one-line description
make install       # Install Python (uv) and Node (pnpm) deps
make hooks         # Install pre-commit hooks (run once after install)
make test          # Run pytest with coverage (gate: ≥80%)
make fmt           # Format Python code (ruff format)
make lint          # Lint + type-check + layering (ruff + mypy + import-linter)
make pre-commit    # Run every pre-commit hook on every file
make ci            # Meta: install + lint + test (mirrors what CI runs)
make web-dev       # Run the Next.js dev server
make clean         # Wipe caches, venvs, build artifacts
```

### Pre-commit hooks

`make hooks` installs `pre-commit` as a **uv tool** (placing it on `~/.local/bin`) and registers the git hook. The uv-tool install is intentional: uv's lazy project-venv management can prune the project venv between commands, which would otherwise leave the git hook unable to find `pre-commit`. As a uv tool, `pre-commit` lives in a stable location on PATH and isn't affected by `uv sync`.

Hooks run automatically on `git commit`. They enforce:

- Generic hygiene: end-of-file newline, trailing whitespace, no merge conflict markers, no committed secrets, no >500KB binaries.
- Python: ruff (lint + auto-fix + format), mypy (strict mode on `foresight/`), import-linter (layering rules between subpackages).
- TOML/YAML well-formedness.

Hooks are mostly auto-fixers — when one modifies a file, re-stage and re-commit. `--no-verify` is forbidden by `CONTRIBUTING.md`; investigate failures, don't bypass them.

### Layering rules (machine-enforced)

The subpackage layering rules in `foresight/__init__.py` are enforced by `import-linter` via the `[tool.importlinter]` section of `pyproject.toml`. Adding a layering violation will fail `make lint`, the `lint-imports` pre-commit hook, **and** `tests/test_layering.py`.

## Continuous Integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every PR and every push to `develop` / `main`. Three jobs run in parallel:

| Job | What it runs | Equivalent local command |
|---|---|---|
| `quality` | `pre-commit run --all-files` — ruff, mypy, import-linter, file hygiene | `make pre-commit` |
| `tests` | `pytest` with coverage (80% gate) | `make test` |
| `web-install` | `pnpm install --frozen-lockfile` for `web/` | `cd web && pnpm install --frozen-lockfile` |

The `quality` job intentionally reuses `.pre-commit-config.yaml` rather than re-listing tools — local hooks and CI run the **same** versions, with no drift. The 80% coverage gate is enforced inside `pyproject.toml` (`coverage.fail_under`), so it works identically in CI and locally.

If CI fails, run `make pre-commit` or `make test` locally to reproduce. CI uploads the pytest junit XML as an artifact on failure (retention 14 days).

Some targets are stubs awaiting future stories (e.g., `make up`, `make migrate`). They print a pointer to the story that will implement them and exit 0 — so the command shape stays stable from day one.

### Prerequisites

| Tool | Min version | Install |
|---|---|---|
| `uv` | 0.5+ | `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `pnpm` | 11+ | `brew install pnpm` |
| Node | 22 LTS | `brew install node@22` (keg-only is fine; the Makefile picks it up automatically) |
| Python | 3.12+ | uv will install it for you via `.python-version` |

## Reporting Issues

Issues should reference the relevant story ID from `PLAN.md` whenever applicable. For ad-hoc bugs not tied to a story, open the issue first and we'll decide whether to fold it into an existing story or carve out a new one.
