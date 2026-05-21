"""Brand — a sellable identity under a tenant.

One tenant may have multiple brands (e.g., a holding company running
several DTC brands). A brand is a pure identity entity here — the
storefront connections (Shopify, Amazon) and OMS connections (ShipBob)
live in the ``Integration`` table that lands with E2.S8.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.forecast import Forecast
    from foresight.core.models.ingestion import IngestionJob
    from foresight.core.models.inventory_item import InventoryItem
    from foresight.core.models.order import Order
    from foresight.core.models.product import Product
    from foresight.core.models.tenant import Tenant


class Brand(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "brands"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_brand_tenant_slug"),
        Index("ix_brands_tenant_id_name", "tenant_id", "name"),
    )

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # URL-safe handle for the brand, unique within a tenant. Used in API
    # paths, UI breadcrumbs, and anywhere a stable short identifier is
    # convenient. Storefront-specific handles (Shopify shop subdomain,
    # Amazon seller id, ShipBob account id) live on `Integration` rows,
    # not here.
    slug: Mapped[str] = mapped_column(String(120), nullable=False)

    # Relationships
    tenant: Mapped[Tenant] = relationship(back_populates="brands")
    products: Mapped[list[Product]] = relationship(
        back_populates="brand", cascade="all, delete-orphan", passive_deletes=True
    )
    orders: Mapped[list[Order]] = relationship(
        back_populates="brand", cascade="all, delete-orphan", passive_deletes=True
    )
    forecasts: Mapped[list[Forecast]] = relationship(
        back_populates="brand", cascade="all, delete-orphan", passive_deletes=True
    )
    ingestion_jobs: Mapped[list[IngestionJob]] = relationship(
        back_populates="brand", cascade="all, delete-orphan", passive_deletes=True
    )
    inventory_items: Mapped[list[InventoryItem]] = relationship(
        back_populates="brand", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"Brand(id={self.id!r}, slug={self.slug!r})"
