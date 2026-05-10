"""``foresight.api`` — FastAPI service.

Public HTTP API consumed by the Next.js web app, the Slack adapter, and the
worker (callbacks for long-running jobs). Real content lands across E3.*
stories.

May import from ``foresight.core`` and ``foresight.agents``.
MUST NOT import from ``foresight.worker``; cross-service calls go over HTTP.
"""

from __future__ import annotations
