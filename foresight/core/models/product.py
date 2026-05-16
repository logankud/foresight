"""Product and Variant — the catalog primitives.

A ``Product`` is a vendor-side product (e.g., a Shopify product
"Espresso Beans 250g"); a ``Variant`` is a specific per-channel SKU
within that product. Inventory, forecasts, and order line items all
attach to Variants (SKU-level), not Products.

External-system identifiers (Shopify GID, Amazon ASIN, ShipBob product
id, etc.) are stored as ``external_ref`` strings — the vendor that
emitted them lives on the ``Integration`` row (E2.S8). For raw
materials (no channel), see ``InventoryItem`` (E2.S6).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.brand import Brand
    from foresight.core.models.forecast import ForecastPoint
    from foresight.core.models.inventory import InventorySnapshot
    from foresight.core.models.order import OrderLineItem


class Product(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        # Vendor's product identifier is globally unique when present.
        UniqueConstraint("external_ref", name="uq_products_external_ref"),
        Index("ix_products_brand_id", "brand_id"),
    )

    id: Mapped[UUID] = uuid_pk()
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Vendor's product identifier. Nullable for manually-created products
    # that don't originate from any external system. Examples of valid
    # values: a Shopify GID ("gid://shopify/Product/1234567890"), a
    # ShipBob channel-product id, etc. The vendor itself lives on the
    # Integration row (E2.S8).
    external_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    brand: Mapped[Brand] = relationship(back_populates="products")
    variants: Mapped[list[Variant]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Product(id={self.id!r}, title={self.title!r})"


class Variant(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "variants"
    __table_args__ = (
        # SKU is unique within a brand.
        UniqueConstraint("brand_id", "sku", name="uq_variants_brand_sku"),
        UniqueConstraint("external_ref", name="uq_variants_external_ref"),
        Index("ix_variants_product_id", "product_id"),
    )

    id: Mapped[UUID] = uuid_pk()
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Vendor's per-channel SKU identifier (Shopify GID, Amazon ASIN, etc.).
    # Nullable for manually-created variants.
    external_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sku: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    product: Mapped[Product] = relationship(back_populates="variants")
    inventory_snapshots: Mapped[list[InventorySnapshot]] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    order_lines: Mapped[list[OrderLineItem]] = relationship(back_populates="variant")
    forecast_points: Mapped[list[ForecastPoint]] = relationship(
        back_populates="variant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Variant(id={self.id!r}, sku={self.sku!r})"
