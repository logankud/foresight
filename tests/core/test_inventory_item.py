"""Tests for the InventoryItem entity (E2.S6).

Covers UUIDv7 PKs, enum columns, brand-scoped SKU uniqueness, the
Variant ↔ InventoryItem link, and cascade behavior.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from foresight.core.models import (
    Brand,
    InventoryItem,
    InventoryItemKind,
    Product,
    Tenant,
    UnitOfMeasure,
    Variant,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _now() -> datetime:
    return datetime.now(UTC)


def _make_tenant(session: Session, name: str = "Acme Coffee Co.") -> Tenant:
    tenant = Tenant(name=name)
    session.add(tenant)
    session.flush()
    return tenant


def _make_brand(session: Session, tenant: Tenant, slug: str = "acme-coffee") -> Brand:
    brand = Brand(tenant_id=tenant.id, name="Acme Coffee", slug=slug)
    session.add(brand)
    session.flush()
    return brand


def _make_inventory_item(
    session: Session,
    brand: Brand,
    *,
    sku: str = "ITEM-001",
    kind: InventoryItemKind = InventoryItemKind.FINISHED_GOOD,
    uom: UnitOfMeasure = UnitOfMeasure.PIECES,
    name: str = "Test Item",
) -> InventoryItem:
    item = InventoryItem(
        tenant_id=brand.tenant_id,
        brand_id=brand.id,
        kind=kind,
        sku=sku,
        name=name,
        unit_of_measure=uom,
    )
    session.add(item)
    session.flush()
    return item


# ---------- Basic shape ----------


def test_inventory_item_gets_uuid7_pk(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    item = _make_inventory_item(db_session, brand)
    assert isinstance(item.id, UUID)
    assert item.id.version == 7


def test_finished_good_with_optional_metadata(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    item = InventoryItem(
        tenant_id=tenant.id,
        brand_id=brand.id,
        kind=InventoryItemKind.FINISHED_GOOD,
        sku="ESPRESSO-250G",
        name="Espresso Beans 250g",
        unit_of_measure=UnitOfMeasure.PIECES,
        barcode="0123456789012",
        notes="Hero SKU",
    )
    db_session.add(item)
    db_session.flush()

    refreshed = db_session.get(InventoryItem, item.id)
    assert refreshed is not None
    assert refreshed.barcode == "0123456789012"
    assert refreshed.notes == "Hero SKU"
    assert refreshed.kind is InventoryItemKind.FINISHED_GOOD
    assert refreshed.unit_of_measure is UnitOfMeasure.PIECES


def test_raw_material_with_supplier_metadata(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    item = InventoryItem(
        tenant_id=tenant.id,
        brand_id=brand.id,
        kind=InventoryItemKind.RAW_MATERIAL,
        sku="GREEN-COFFEE-ETHIOPIA",
        name="Ethiopian green coffee",
        unit_of_measure=UnitOfMeasure.POUNDS,
        supplier_name="Origin Coffee Importers",
    )
    db_session.add(item)
    db_session.flush()

    refreshed = db_session.get(InventoryItem, item.id)
    assert refreshed is not None
    assert refreshed.kind is InventoryItemKind.RAW_MATERIAL
    assert refreshed.unit_of_measure is UnitOfMeasure.POUNDS
    assert refreshed.supplier_name == "Origin Coffee Importers"


# ---------- Uniqueness ----------


def test_inventory_item_sku_unique_within_brand(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    _make_inventory_item(db_session, brand, sku="DUP-SKU")
    with pytest.raises(IntegrityError):
        _make_inventory_item(db_session, brand, sku="DUP-SKU")
        db_session.flush()


def test_inventory_item_sku_reusable_across_brands(db_session: Session) -> None:
    """SKU namespace is brand-scoped — two brands legitimately may use
    the same SKU string for their own catalog items."""
    tenant = _make_tenant(db_session)
    b1 = _make_brand(db_session, tenant, slug="brand-one")
    b2 = _make_brand(db_session, tenant, slug="brand-two")
    _make_inventory_item(db_session, b1, sku="SHARED-SKU")
    _make_inventory_item(db_session, b2, sku="SHARED-SKU")
    db_session.flush()  # no error


def test_finished_good_and_raw_material_share_sku_namespace(db_session: Session) -> None:
    """Sharing SKU between a finished good and a raw material in the
    same brand is intentionally rejected — operators would never want
    that, and the schema prevents the foot-gun."""
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    _make_inventory_item(db_session, brand, sku="COLLIDE", kind=InventoryItemKind.FINISHED_GOOD)
    with pytest.raises(IntegrityError):
        _make_inventory_item(db_session, brand, sku="COLLIDE", kind=InventoryItemKind.RAW_MATERIAL)
        db_session.flush()


# ---------- Variant linkage ----------


def test_variant_links_to_inventory_item(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    item = _make_inventory_item(
        db_session, brand, sku="ESPRESSO-250G", kind=InventoryItemKind.FINISHED_GOOD
    )

    product = Product(tenant_id=tenant.id, brand_id=brand.id, title="Espresso Beans 250g")
    db_session.add(product)
    db_session.flush()

    variant = Variant(
        tenant_id=tenant.id,
        brand_id=brand.id,
        product_id=product.id,
        sku="ESPRESSO-250G-WHOLE",
        title="Whole bean",
        inventory_item_id=item.id,
    )
    db_session.add(variant)
    db_session.flush()
    db_session.expire_all()

    refreshed_item = db_session.get(InventoryItem, item.id)
    assert refreshed_item is not None
    assert len(refreshed_item.variants) == 1
    assert refreshed_item.variants[0].sku == "ESPRESSO-250G-WHOLE"

    refreshed_variant = db_session.get(Variant, variant.id)
    assert refreshed_variant is not None
    assert refreshed_variant.inventory_item is not None
    assert refreshed_variant.inventory_item.id == item.id


def test_deleting_inventory_item_set_nulls_variant_link(db_session: Session) -> None:
    """Variants outlive InventoryItem deletion (historical orders may
    still reference the Variant). Schema sets the FK to NULL on delete."""
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    item = _make_inventory_item(db_session, brand, sku="LINKED")

    product = Product(tenant_id=tenant.id, brand_id=brand.id, title="P")
    db_session.add(product)
    db_session.flush()
    variant = Variant(
        tenant_id=tenant.id,
        brand_id=brand.id,
        product_id=product.id,
        sku="LINKED-V1",
        title="V",
        inventory_item_id=item.id,
    )
    db_session.add(variant)
    db_session.flush()
    variant_id = variant.id

    db_session.delete(item)
    db_session.flush()
    db_session.expire_all()

    refreshed = db_session.get(Variant, variant_id)
    assert refreshed is not None  # variant survives
    assert refreshed.inventory_item_id is None  # link nulled


def test_deleting_brand_cascades_inventory_items(db_session: Session) -> None:
    tenant = _make_tenant(db_session)
    brand = _make_brand(db_session, tenant)
    item = _make_inventory_item(db_session, brand, sku="CASCADE-ME")
    item_id = item.id

    db_session.delete(brand)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(InventoryItem, item_id) is None
