"""InventorySnapshot — Shopify/ShipBob-sourced finished-goods stock cache.

**Scope:** this entity caches **finished-goods inventory levels reported
by an external vendor** (Shopify, ShipBob, etc.) at a specific point in
time. It exists so we can reconstruct historical finished-goods stock
without depending on the vendor's API limits.

**For the broader unified inventory model — including raw materials and
production events — see ``InventoryItem`` and ``InventoryTransaction``
(land with E2.S6).** ``BillOfMaterials`` (E2.S7) links finished goods
to the raw materials that produce them.

The vendor that emitted any given row lives on the ``Integration`` row
(E2.S8); ``external_location_ref`` carries the vendor's own location id
(Shopify location id, ShipBob warehouse id, etc.).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.product import Variant


class InventorySnapshot(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "inventory_snapshots"
    __table_args__ = (
        Index("ix_inventory_variant_observed", "variant_id", "observed_at"),
        Index("ix_inventory_tenant_observed", "tenant_id", "observed_at"),
    )

    id: Mapped[UUID] = uuid_pk()
    variant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Vendor's location identifier (Shopify location id, ShipBob
    # warehouse id, etc.) — kept as a string to survive vendor format
    # changes. The vendor itself lives on the Integration row (E2.S8).
    external_location_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # The "as-of" instant for this stock level. NOT created_at, which is
    # when we recorded it — observed_at is when the vendor says the
    # level was true (may differ in case of webhook backfill).
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    variant: Mapped[Variant] = relationship(back_populates="inventory_snapshots")

    def __repr__(self) -> str:
        return (
            f"InventorySnapshot(variant_id={self.variant_id!r}, "
            f"qty={self.quantity}, observed_at={self.observed_at!r})"
        )
