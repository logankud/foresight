"""Smoke + relationship tests for the E2.S1 entity models.

These tests run against a real Postgres (see ``tests/conftest.py``) so
SQLAlchemy 2.x mapping semantics, ``Numeric``, ``Enum``, ``JSONB``, and
``UUID`` columns all exercise their production code paths.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from foresight.core.models import (
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
    Variant,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ---------- Helpers ----------


def _now() -> datetime:
    return datetime.now(UTC)


def _make_tenant(session: Session, name: str = "Acme Coffee Co.") -> Tenant:
    tenant = Tenant(name=name)
    session.add(tenant)
    session.flush()
    return tenant


def _make_brand(session: Session, tenant: Tenant, slug: str = "acme-coffee") -> Brand:
    brand = Brand(
        tenant_id=tenant.id,
        name="Acme Coffee",
        slug=slug,
    )
    session.add(brand)
    session.flush()
    return brand


def _make_product_with_variant(
    session: Session, brand: Brand, sku: str = "SKU-ESPRESSO-250G"
) -> tuple[Product, Variant]:
    product = Product(
        tenant_id=brand.tenant_id,
        brand_id=brand.id,
        external_ref="gid://shopify/Product/100",
        title="Espresso Beans 250g",
    )
    session.add(product)
    session.flush()
    variant = Variant(
        tenant_id=brand.tenant_id,
        brand_id=brand.id,
        product_id=product.id,
        external_ref="gid://shopify/ProductVariant/200",
        sku=sku,
        title="Whole bean",
    )
    session.add(variant)
    session.flush()
    return product, variant


# ---------- Basic instantiation + UUIDv7 PKs ----------


def test_tenant_can_be_inserted_and_gets_uuid_pk(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    assert isinstance(tenant.id, UUID)
    assert tenant.id.version == 7


def test_tenant_name_is_unique(db_session: Session) -> None:
    _make_tenant(db_session, "Duplicate")
    with pytest.raises(IntegrityError):
        _make_tenant(db_session, "Duplicate")
        db_session.flush()


def test_tenant_brand_relationship(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    _make_brand(db_session, tenant)
    db_session.flush()

    refreshed = db_session.get(Tenant, tenant.id)
    assert refreshed is not None
    assert len(refreshed.brands) == 1
    assert refreshed.brands[0].slug == "acme-coffee"


def test_brand_slug_unique_within_tenant(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    _make_brand(db_session, tenant, "acme-coffee")
    with pytest.raises(IntegrityError):
        _make_brand(db_session, tenant, "acme-coffee")
        db_session.flush()


def test_brand_slug_reusable_across_tenants(db_session: Session) -> None:
    """Different tenants may legitimately reuse a slug (e.g., the same
    handle for parallel test stores) — uniqueness is scoped per-tenant."""
    t1 = _make_tenant(db_session, "Tenant 1")
    t2 = _make_tenant(db_session, "Tenant 2")
    _make_brand(db_session, t1, "same-slug")
    _make_brand(db_session, t2, "same-slug")
    db_session.flush()  # no error


# ---------- Product + Variant ----------


def test_product_variant_relationship(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    product, variant = _make_product_with_variant(db_session, brand)

    refreshed = db_session.get(Product, product.id)
    assert refreshed is not None
    assert len(refreshed.variants) == 1
    assert refreshed.variants[0].sku == "SKU-ESPRESSO-250G"
    assert refreshed.brand.id == brand.id


def test_variant_sku_unique_within_brand(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    _, _ = _make_product_with_variant(db_session, brand, sku="DUP")
    with pytest.raises(IntegrityError):
        _make_product_with_variant(db_session, brand, sku="DUP")
        db_session.flush()


# ---------- Inventory ----------


def test_inventory_snapshot_attaches_to_variant(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    _, variant = _make_product_with_variant(db_session, brand)

    snap = InventorySnapshot(
        tenant_id=tenant.id,
        variant_id=variant.id,
        external_location_ref="loc-1",
        quantity=120,
        observed_at=_now(),
    )
    db_session.add(snap)
    db_session.flush()

    refreshed = db_session.get(Variant, variant.id)
    assert refreshed is not None
    assert len(refreshed.inventory_snapshots) == 1
    assert refreshed.inventory_snapshots[0].quantity == 120


# ---------- Orders + Line Items ----------


def test_order_with_line_items(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    _, variant = _make_product_with_variant(db_session, brand)

    order = Order(
        tenant_id=tenant.id,
        brand_id=brand.id,
        external_ref="gid://shopify/Order/9001",
        name="#1042",
        status=OrderStatus.PAID,
        currency="USD",
        total_price=Decimal("42.00"),
        subtotal_price=Decimal("38.00"),
        placed_at=_now(),
    )
    db_session.add(order)
    db_session.flush()

    line = OrderLineItem(
        tenant_id=tenant.id,
        order_id=order.id,
        variant_id=variant.id,
        quantity=2,
        unit_price=Decimal("19.00"),
        total_discount=Decimal("0.00"),
    )
    db_session.add(line)
    db_session.flush()

    refreshed = db_session.get(Order, order.id)
    assert refreshed is not None
    assert refreshed.status is OrderStatus.PAID
    assert len(refreshed.line_items) == 1
    assert refreshed.line_items[0].variant.sku == "SKU-ESPRESSO-250G"


def test_order_external_ref_globally_unique(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)

    order_kwargs: dict = dict(
        tenant_id=tenant.id,
        brand_id=brand.id,
        external_ref="gid://shopify/Order/9001",
        name="#1042",
        status=OrderStatus.PAID,
        currency="USD",
        total_price=Decimal("42.00"),
        placed_at=_now(),
    )
    db_session.add(Order(**order_kwargs))
    db_session.flush()

    with pytest.raises(IntegrityError):
        db_session.add(Order(**order_kwargs))
        db_session.flush()


# ---------- Forecast + ForecastPoint ----------


def test_forecast_records_model_provenance(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    _, variant = _make_product_with_variant(db_session, brand)

    inputs_as_of = _now() - timedelta(days=1)
    run_at = _now()
    forecast = Forecast(
        tenant_id=tenant.id,
        brand_id=brand.id,
        model_name="days_of_cover",
        model_version="0.1.0",
        inputs_as_of=inputs_as_of,
        run_at=run_at,
    )
    db_session.add(forecast)
    db_session.flush()

    point = ForecastPoint(
        tenant_id=tenant.id,
        forecast_id=forecast.id,
        variant_id=variant.id,
        current_inventory=100,
        velocity_per_day=Decimal("4.5000"),
        days_of_cover=Decimal("22.22"),
        days_of_cover_lo=Decimal("18.00"),
        days_of_cover_hi=Decimal("26.50"),
    )
    db_session.add(point)
    db_session.flush()

    refreshed = db_session.get(Forecast, forecast.id)
    assert refreshed is not None
    assert refreshed.model_name == "days_of_cover"
    assert refreshed.model_version == "0.1.0"
    assert len(refreshed.points) == 1
    assert refreshed.points[0].variant.sku == "SKU-ESPRESSO-250G"


def test_zero_velocity_forecast_point_reports_null_days_of_cover(
    db_session: Session,
) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    _, variant = _make_product_with_variant(db_session, brand)

    forecast = Forecast(
        tenant_id=tenant.id,
        brand_id=brand.id,
        model_name="days_of_cover",
        model_version="0.1.0",
        inputs_as_of=_now(),
        run_at=_now(),
    )
    db_session.add(forecast)
    db_session.flush()

    point = ForecastPoint(
        tenant_id=tenant.id,
        forecast_id=forecast.id,
        variant_id=variant.id,
        current_inventory=42,
        velocity_per_day=None,
        days_of_cover=None,
        reason="zero velocity in 30-day window",
    )
    db_session.add(point)
    db_session.flush()

    refreshed = db_session.get(ForecastPoint, point.id)
    assert refreshed is not None
    assert refreshed.days_of_cover is None
    assert refreshed.reason == "zero velocity in 30-day window"


# ---------- IngestionJob ----------


def test_ingestion_job_status_lifecycle(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)

    job = IngestionJob(
        tenant_id=tenant.id,
        brand_id=brand.id,
        job_type="shipbob_backfill_orders",
        status=IngestionJobStatus.PENDING,
        rows_per_table={},
    )
    db_session.add(job)
    db_session.flush()

    job.status = IngestionJobStatus.RUNNING
    job.started_at = _now()
    db_session.flush()

    job.status = IngestionJobStatus.SUCCEEDED
    job.ended_at = _now()
    job.rows_per_table = {"orders": 1042, "order_line_items": 3120}
    db_session.flush()

    refreshed = db_session.get(IngestionJob, job.id)
    assert refreshed is not None
    assert refreshed.status is IngestionJobStatus.SUCCEEDED
    assert refreshed.rows_per_table["orders"] == 1042


# ---------- Tenant cascade ----------


def test_deleting_tenant_cascades_to_brand_data(db_session: Session) -> None:
    """All tenant_id FKs use ON DELETE CASCADE so removing a tenant
    tears down its rows. This is the GDPR-friendly behavior.

    The DB-side cascade fires when the tenant DELETE statement executes,
    but SQLAlchemy's identity map still holds the now-orphaned child
    rows. ``expire_all()`` forces SQLAlchemy to re-read on next access,
    which is how we observe the cascade.
    """
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    product, variant = _make_product_with_variant(db_session, brand)
    tenant_id, brand_id, product_id, variant_id = (
        tenant.id,
        brand.id,
        product.id,
        variant.id,
    )

    db_session.delete(tenant)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(Tenant, tenant_id) is None
    assert db_session.get(Brand, brand_id) is None
    assert db_session.get(Product, product_id) is None
    assert db_session.get(Variant, variant_id) is None
