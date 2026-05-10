"""Foresight — data-first, AI-native operations platform for DTC / e-com brands.

This is the single top-level Python package for the project. Subpackages:

- ``foresight.core``    — shared data models, db, storage, settings (E2)
- ``foresight.agents``  — AgentClient protocol, tool registry (E6)
- ``foresight.api``     — FastAPI service (E3)
- ``foresight.worker``  — background-jobs runner (E4, E5)

Layering rules:

- ``foresight.core`` may not import from ``foresight.api``, ``foresight.worker``,
  or ``foresight.agents``.
- ``foresight.api`` and ``foresight.worker`` must not import from each other;
  cross-service communication goes over HTTP.
- ``foresight.agents`` may import from ``foresight.core`` only.

These rules are documented in CONTRIBUTING.md and will be machine-enforced when
``import-linter`` lands in E1.S4 (pre-commit).
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
