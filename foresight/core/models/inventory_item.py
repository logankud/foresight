"""InventoryItem — the unified physical-good abstraction.

A single entity covering both **finished goods** (sold via storefronts;
auto-populated from integrations like ShipBob, Shopify, Amazon) and
**raw materials** (manually tracked production inputs).

Mirrors ShipBob's *Inventory Item* concept: one InventoryItem is the
physical good that holds real-time stock, and many ``Variant`` rows
(per-channel listings) can map to it. Raw materials have no Variant.

**Real-time stock** = sum of ``InventoryTransaction.quantity`` rows for
this item. The transactions table is the immutable event log; this
table holds the catalog metadata.

Recipes (which raw materials make which finished goods) live in
``BillOfMaterials`` (E2.S7).
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.brand import Brand
    from foresight.core.models.inventory_transaction import InventoryTransaction
    from foresight.core.models.product import Variant


class UnitOfMeasure(enum.StrEnum):
    """The four units we support for inventory quantities.

    Stored as the canonical short string (``g``, ``lb``, ``oz``, ``pc``).
    If a future need arises for ``kg`` / ``ml`` / etc., we add a new
    enum value and ship a migration — that's the right friction
    (an enum extension is reviewable; a freeform text field isn't).
    """

    GRAMS = "g"
    POUNDS = "lb"
    OUNCES = "oz"
    PIECES = "pc"


class InventoryItemKind(enum.StrEnum):
    """Distinguishes finished goods from production inputs.

    Drives downstream behavior: finished goods can have Variants
    (channel listings); raw materials never do. BOMs reference raw
    materials as components and finished goods as the produced output.
    """

    FINISHED_GOOD = "finished_good"
    RAW_MATERIAL = "raw_material"


class InventoryItem(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "inventory_items"
    __table_args__ = (
        # SKU is the canonical handle within a brand; both finished
        # goods and raw materials share the same namespace so we catch
        # accidental collisions (e.g., naming a raw material the same
        # as a finished good).
        UniqueConstraint("brand_id", "sku", name="uq_inventory_items_brand_sku"),
        Index("ix_inventory_items_brand_kind", "brand_id", "kind"),
    )

    id: Mapped[UUID] = uuid_pk()
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[InventoryItemKind] = mapped_column(
        Enum(InventoryItemKind, name="inventory_item_kind_enum"),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    unit_of_measure: Mapped[UnitOfMeasure] = mapped_column(
        Enum(UnitOfMeasure, name="unit_of_measure_enum"),
        nullable=False,
    )
    # ShipBob convention — barcode aids receiving / inbound.
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Raw-material metadata. Free-form because the vast majority of
    # tracking is human-readable (supplier names, lot codes, etc.).
    supplier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    brand: Mapped[Brand] = relationship(back_populates="inventory_items")
    variants: Mapped[list[Variant]] = relationship(
        back_populates="inventory_item",
        # Variants outlive an InventoryItem deletion: SET NULL on Variant.
        passive_deletes=True,
    )
    transactions: Mapped[list[InventoryTransaction]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"InventoryItem(id={self.id!r}, sku={self.sku!r}, kind={self.kind.value})"
