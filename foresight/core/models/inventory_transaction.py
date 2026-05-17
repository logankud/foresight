"""InventoryTransaction — immutable event log of stock changes.

Each row records a single stock-affecting event: a receipt of raw
materials, production of finished goods, a sale, a manual count
correction, etc. Real-time stock for any ``InventoryItem`` is the sum
of its transactions' signed ``quantity`` values.

**Vendor specifics are not first-class enum values.** ShipBob picks,
restocks, etc. are recorded via the generic ``source_type`` /
``source_id`` columns (e.g., ``source_type="shipbob_pick"``). This
keeps the enum vendor-neutral and aligned with the protocol-driven
adapter design — adding a new vendor never requires adding a new
enum value or shipping a migration.
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.inventory_item import InventoryItem


class InventoryTransactionKind(enum.StrEnum):
    """The five generic stock-event kinds.

    Vendor-specific events are recorded via ``source_type`` /
    ``source_id`` rather than separate enum values — see the module
    docstring for the rationale.
    """

    RECEIPT = "receipt"  # raw materials received from a supplier
    CONSUMPTION = "consumption"  # raw materials consumed in production
    PRODUCTION = "production"  # finished goods produced
    SALE = "sale"  # finished goods sold (typically linked to Order)
    ADJUSTMENT = "adjustment"  # manual count correction / cycle count


class InventoryTransaction(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        Index("ix_inv_tx_item_occurred", "item_id", "occurred_at"),
        Index("ix_inv_tx_tenant_occurred", "tenant_id", "occurred_at"),
    )

    id: Mapped[UUID] = uuid_pk()
    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[InventoryTransactionKind] = mapped_column(
        Enum(InventoryTransactionKind, name="inventory_transaction_kind_enum"),
        nullable=False,
    )
    # Signed: positive = increase (receipt, production, positive adjustment);
    # negative = decrease (consumption, sale, negative adjustment).
    # Numeric(14, 4) supports fractional units (e.g., 12.5g) and large
    # quantities without float rounding.
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    # When the event happened (NOT when we recorded it — that's
    # ``created_at`` from TimestampMixin). Lets us backfill historical
    # data correctly.
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Free-form human note: "spilled bag" / "annual count adjustment"
    # / "ShipBob discrepancy reconciliation". Renders in the UI; not
    # parsed by code.
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Generic provenance: what business object caused this event?
    # E.g., source_type="order", source_id=<Order.id> for a SALE row.
    # source_type="shipbob_pick", source_id=<external ShipBob pick id>
    # for vendor-emitted events (stored as a UUID parsed from the
    # vendor's id, or NULL when the vendor uses string ids).
    source_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Relationships
    item: Mapped[InventoryItem] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return (
            f"InventoryTransaction(item_id={self.item_id!r}, "
            f"kind={self.kind.value}, qty={self.quantity}, "
            f"occurred_at={self.occurred_at!r})"
        )
