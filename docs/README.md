# `docs/`

Project documentation that doesn't belong in `README.md`, `CONTRIBUTING.md`, or `PLAN.md`.

| Subdir | Contents |
|---|---|
| `journeys/` *(future)* | End-to-end user-journey docs (E10) — Onboard, Daily Check-in, Reorder Triggered. |
| `api/` *(future)* | API conventions and schema reference (E3). |

## Where decisions are documented

Foresight does **not** maintain a formal ADR (Architecture Decision Record) system. The planned ADR setup in `PLAN.md` E1.S6 was reviewed and deferred indefinitely — at the project's current size, decision rationale is already captured across:

- `PLAN.md` — Architectural Decisions table plus "Why:" annotations on every acceptance criterion.
- `CONTRIBUTING.md` — workflow, prerequisites, layering rules, CI overview.
- `foresight/__init__.py` docstring — layering rules between subpackages.
- Commit messages — every squash commit on `develop` carries a markdown body with Summary / Changes / Why.
- PR descriptions — the PR template requires a "Why" justification.

Adding per-decision ADR files would mostly duplicate this content while creating drift risk. We'll re-evaluate introducing ADRs once any of the following are true:

- A second contributor joins the project.
- The project hits a 12-month mark.
- `PLAN.md` grows past ~3000 lines, making decision discovery painful.

See `PLAN.md` story E1.S6 for the full deferral rationale.
