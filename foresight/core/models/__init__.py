"""Foresight core entity models.

Re-exports every public model so consumers can do
``from foresight.core.models import Brand, Order``.

The models are split across files by domain area (tenant, brand, product,
inventory, order, forecast, ingestion) to keep each file scannable. The
re-exports here give callers a flat namespace.

Layering: this module belongs to ``foresight.core`` and must remain
free of imports from ``foresight.api``, ``foresight.worker``, or
``foresight.agents`` (enforced by import-linter).
"""

from __future__ import annotations

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin
from foresight.core.models.brand import Brand
from foresight.core.models.forecast import Forecast, ForecastPoint
from foresight.core.models.ingestion import IngestionJob, IngestionJobStatus
from foresight.core.models.inventory import InventorySnapshot
from foresight.core.models.order import Order, OrderLineItem, OrderStatus
from foresight.core.models.product import Product, Variant
from foresight.core.models.tenant import Tenant

__all__ = [
    "Base",
    "Brand",
    "Forecast",
    "ForecastPoint",
    "IngestionJob",
    "IngestionJobStatus",
    "InventorySnapshot",
    "Order",
    "OrderLineItem",
    "OrderStatus",
    "Product",
    "Tenant",
    "TenantScopedMixin",
    "TimestampMixin",
    "Variant",
]
