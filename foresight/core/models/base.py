"""SQLAlchemy declarative base + common mixins.

Every Foresight entity inherits ``Base`` and (typically) the
``TimestampMixin`` and ``TenantScopedMixin``. Conventions enforced here:

- Primary keys are UUIDv7 (sortable by creation time).
- Every row carries a ``created_at`` / ``updated_at`` pair.
- Every domain row (everything except ``Tenant`` itself) carries a
  ``tenant_id`` FK to ``tenants.id`` with an index, and the FK has
  ``ON DELETE CASCADE`` so deleting a tenant tears down its data.

The tenant boundary is **declared** here; **enforcement** (the
session-level filter) lands in E2.S3.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from uuid_utils import uuid7

if TYPE_CHECKING:  # pragma: no cover
    pass


def _uuid7() -> UUID:
    """Generate a UUIDv7.

    ``uuid_utils.uuid7()`` returns its own UUID type; we coerce to the
    stdlib ``uuid.UUID`` so SQLAlchemy's PG ``UUID`` mapping serializes
    it consistently.
    """
    return UUID(str(uuid7()))


def _utcnow() -> datetime:
    """Timezone-aware "now" for default columns."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base for every Foresight model.

    Kept minimal; column conventions live in the mixins below.
    """


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns.

    Both use ``DateTime(timezone=True)`` to avoid the timezone-naive
    landmines that have plagued every codebase that learned the hard way.
    ``updated_at`` auto-updates on every flush of the parent row.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )


class TenantScopedMixin:
    """Adds a ``tenant_id`` FK that points at ``tenants.id``.

    Use ``declared_attr`` so the column is created on each subclass with
    a correctly-pointing FK. ``ON DELETE CASCADE`` so deleting a tenant
    tears down its data (GDPR-friendly).

    Subclasses should also declare an index on ``tenant_id`` (and often
    composite indexes including it) for query performance — the
    enforcement layer in E2.S3 will always filter on ``tenant_id``.
    """

    @declared_attr
    @classmethod
    def tenant_id(cls) -> Mapped[UUID]:
        return mapped_column(
            PG_UUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


def uuid_pk() -> Mapped[UUID]:
    """Convenience for declaring a UUIDv7 primary key on a model.

    Usage::

        class Tenant(Base):
            id: Mapped[UUID] = uuid_pk()
    """
    return mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=_uuid7,
    )
