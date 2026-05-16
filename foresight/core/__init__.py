"""``foresight.core`` — shared data models, storage abstractions, settings.

Owns the cross-cutting Python concerns consumed by every other subpackage:

- SQLAlchemy models (E2.S1)
- Database session factory + storage abstractions (E2.S3)
- Settings / config loading (E2 onward)
- Domain primitives and exceptions

This subpackage MUST be import-side-effect free: module loading must not
perform network calls, file system writes, or environment-dependent init.

Re-exports the public model surface so callers can do
``from foresight.core import Brand, Order``.
"""

from __future__ import annotations

from foresight.core.models import (
    Base,
    Brand,
    Forecast,
    ForecastPoint,
    IngestionJob,
    IngestionJobStatus,
    InventorySnapshot,
    Order,
    OrderLineItem,
    OrderStatus,
    Product,
    Tenant,
    TenantScopedMixin,
    TimestampMixin,
    Variant,
)

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
