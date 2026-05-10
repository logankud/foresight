"""``foresight.worker`` — background-jobs service.

Scheduled + on-demand jobs: Shopify ingestion (E4), forecast pipeline runs
(E5), retry / scheduling infrastructure.

May import from ``foresight.core`` and ``foresight.agents``.
MUST NOT import from ``foresight.api``; cross-service calls go over HTTP
(using the service-key auth defined in E3.S2).
"""

from __future__ import annotations
