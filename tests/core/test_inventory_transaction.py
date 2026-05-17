"""Tests for InventoryTransaction (E2.S6).

Covers signed quantities, kind enum, occurred_at vs created_at,
generic source_type / source_id provenance, and cascade behavior.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from foresight.core.models import (
    Brand,
    InventoryItem,
    InventoryItemKind,
    InventoryTransaction,
    InventoryTransactionKind,
    Tenant,
    UnitOfMeasure,
)
from sqlalchemy.orm import Session


def _now() -> datetime:
    return datetime.now(UTC)


def _bootstrap_item(
    session: Session,
    kind: InventoryItemKind = InventoryItemKind.FINISHED_GOOD,
    sku: str = "ITEM-1",
) -> InventoryItem:
    tenant = Tenant(name=f"Tenant-{sku}")
    session.add(tenant)
    session.flush()
    brand = Brand(tenant_id=tenant.id, name="Acme", slug=f"slug-{sku.lower()}")
    session.add(brand)
    session.flush()
    item = InventoryItem(
        tenant_id=tenant.id,
        brand_id=brand.id,
        kind=kind,
        sku=sku,
        name=sku,
        unit_of_measure=UnitOfMeasure.PIECES,
    )
    session.add(item)
    session.flush()
    return item


# ---------- Basic shape ----------


def test_transaction_signed_positive_for_receipt(db_session: Session) -> None:
    item = _bootstrap_item(db_session, InventoryItemKind.RAW_MATERIAL, "RAW-1")
    tx = InventoryTransaction(
        tenant_id=item.tenant_id,
        item_id=item.id,
        kind=InventoryTransactionKind.RECEIPT,
        quantity=Decimal("50.0000"),
        occurred_at=_now(),
        reason="Initial supplier receipt",
    )
    db_session.add(tx)
    db_session.flush()
    db_session.expire_all()

    refreshed = db_session.get(InventoryTransaction, tx.id)
    assert refreshed is not None
    assert refreshed.kind is InventoryTransactionKind.RECEIPT
    assert refreshed.quantity == Decimal("50.0000")


def test_transaction_signed_negative_for_consumption(db_session: Session) -> None:
    """Consumption events record negative quantities so stock-sum math
    works without per-kind sign flipping."""
    item = _bootstrap_item(db_session, InventoryItemKind.RAW_MATERIAL, "RAW-2")
    tx = InventoryTransaction(
        tenant_id=item.tenant_id,
        item_id=item.id,
        kind=InventoryTransactionKind.CONSUMPTION,
        quantity=Decimal("-12.5000"),
        occurred_at=_now(),
    )
    db_session.add(tx)
    db_session.flush()

    refreshed = db_session.get(InventoryTransaction, tx.id)
    assert refreshed is not None
    assert refreshed.quantity == Decimal("-12.5000")


def test_occurred_at_distinct_from_created_at(db_session: Session) -> None:
    """occurred_at represents when the real-world event happened;
    created_at is when we recorded it. Backfills set occurred_at to a
    past timestamp; the two MUST be allowed to differ."""
    item = _bootstrap_item(db_session, InventoryItemKind.FINISHED_GOOD, "FG-1")
    historical = _now() - timedelta(days=45)
    tx = InventoryTransaction(
        tenant_id=item.tenant_id,
        item_id=item.id,
        kind=InventoryTransactionKind.SALE,
        quantity=Decimal("-1"),
        occurred_at=historical,
    )
    db_session.add(tx)
    db_session.flush()

    refreshed = db_session.get(InventoryTransaction, tx.id)
    assert refreshed is not None
    # The two timestamps must not be the same field.
    assert refreshed.occurred_at == historical
    # created_at is "now-ish"; just verify it's > occurred_at (we
    # backdated occurred_at by 45 days).
    assert refreshed.created_at > refreshed.occurred_at


# ---------- Generic provenance ----------


def test_source_type_and_id_carry_vendor_provenance(db_session: Session) -> None:
    """Vendor-specific events live in source_type/source_id, NOT in the
    kind enum — that's the protocol-driven design point."""
    item = _bootstrap_item(db_session, InventoryItemKind.FINISHED_GOOD, "FG-2")
    source_id = uuid4()
    tx = InventoryTransaction(
        tenant_id=item.tenant_id,
        item_id=item.id,
        kind=InventoryTransactionKind.SALE,
        quantity=Decimal("-3"),
        occurred_at=_now(),
        source_type="shipbob_pick",
        source_id=source_id,
    )
    db_session.add(tx)
    db_session.flush()

    refreshed = db_session.get(InventoryTransaction, tx.id)
    assert refreshed is not None
    assert refreshed.source_type == "shipbob_pick"
    assert refreshed.source_id == source_id


def test_transaction_relationship_back_to_item(db_session: Session) -> None:
    item = _bootstrap_item(db_session, InventoryItemKind.RAW_MATERIAL, "RAW-3")
    db_session.add_all(
        [
            InventoryTransaction(
                tenant_id=item.tenant_id,
                item_id=item.id,
                kind=InventoryTransactionKind.RECEIPT,
                quantity=Decimal("10"),
                occurred_at=_now() - timedelta(days=2),
            ),
            InventoryTransaction(
                tenant_id=item.tenant_id,
                item_id=item.id,
                kind=InventoryTransactionKind.ADJUSTMENT,
                quantity=Decimal("-1"),
                occurred_at=_now(),
                reason="cycle count",
            ),
        ]
    )
    db_session.flush()
    db_session.expire_all()

    refreshed = db_session.get(InventoryItem, item.id)
    assert refreshed is not None
    assert len(refreshed.transactions) == 2
    quantities = {tx.quantity for tx in refreshed.transactions}
    assert quantities == {Decimal("10.0000"), Decimal("-1.0000")}


def test_transaction_id_is_uuid7(db_session: Session) -> None:
    item = _bootstrap_item(db_session, InventoryItemKind.FINISHED_GOOD, "FG-3")
    tx = InventoryTransaction(
        tenant_id=item.tenant_id,
        item_id=item.id,
        kind=InventoryTransactionKind.PRODUCTION,
        quantity=Decimal("5"),
        occurred_at=_now(),
    )
    db_session.add(tx)
    db_session.flush()

    assert isinstance(tx.id, UUID)
    assert tx.id.version == 7


# ---------- Cascade ----------


def test_deleting_item_cascades_transactions(db_session: Session) -> None:
    """Transactions are tightly coupled to their item — deleting the
    item should remove its history (this is rare; the audit log is
    typically immutable, but tenant deletion / GDPR teardown depends
    on this)."""
    item = _bootstrap_item(db_session, InventoryItemKind.FINISHED_GOOD, "FG-4")
    tx = InventoryTransaction(
        tenant_id=item.tenant_id,
        item_id=item.id,
        kind=InventoryTransactionKind.RECEIPT,
        quantity=Decimal("100"),
        occurred_at=_now(),
    )
    db_session.add(tx)
    db_session.flush()
    tx_id = tx.id

    db_session.delete(item)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(InventoryTransaction, tx_id) is None
