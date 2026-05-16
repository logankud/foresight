"""Order and OrderLineItem — sales transaction primitives.

An Order is a Shopify order; OrderLineItem rows are the per-variant
breakdown. Money columns use ``Numeric(12, 2)`` to preserve precision
(no floats). Currency is stored on the parent Order; line items
inherit it for SQL convenience but the parent is authoritative.
"""

from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.brand import Brand
    from foresight.core.models.product import Variant


class OrderStatus(enum.StrEnum):
    """Coarse status — matches Shopify's ``financial_status`` + ``fulfillment_status``
    collapsed into a single ladder for forecasting purposes. Detailed status
    bits are preserved as raw columns when E4.S3 backfill lands."""

    PENDING = "pending"
    PAID = "paid"
    FULFILLED = "fulfilled"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Order(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        # Vendor's order identifier is globally unique — catches
        # duplicate ingestion regardless of which adapter emitted it.
        UniqueConstraint("external_ref", name="uq_orders_external_ref"),
        Index("ix_orders_brand_placed_at", "brand_id", "placed_at"),
        Index("ix_orders_tenant_placed_at", "tenant_id", "placed_at"),
    )

    id: Mapped[UUID] = uuid_pk()
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Vendor's order identifier (Shopify GID, ShipBob order id, Amazon
    # order id, etc.). Nullable for manually-created test orders.
    external_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Shopify's customer-facing order name, e.g. "#1042".
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 4217
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    brand: Mapped[Brand] = relationship(back_populates="orders")
    line_items: Mapped[list[OrderLineItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Order(id={self.id!r}, name={self.name!r}, status={self.status.value})"


class OrderLineItem(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "order_line_items"
    __table_args__ = (
        Index("ix_order_line_items_order_id", "order_id"),
        Index("ix_order_line_items_variant_id", "variant_id"),
    )

    id: Mapped[UUID] = uuid_pk()
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Variant FK is intentionally RESTRICT (not CASCADE) — deleting a
    # variant must not silently nuke historical sales. Shopify itself
    # treats variants as archive-able, not deletable.
    variant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("variants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_discount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # Relationships
    order: Mapped[Order] = relationship(back_populates="line_items")
    variant: Mapped[Variant] = relationship(back_populates="order_lines")

    def __repr__(self) -> str:
        return (
            f"OrderLineItem(order_id={self.order_id!r}, "
            f"variant_id={self.variant_id!r}, qty={self.quantity})"
        )
