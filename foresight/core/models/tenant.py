"""Tenant — the top-level account in Foresight's multi-tenant model.

A tenant typically maps to one operating company / customer. A tenant
may own multiple `Brand`s (e.g., a holding company running several DTC
brands under one account).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.brand import Brand


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    # Free-form plan identifier; concrete plan/billing model lives outside MVP.
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="trial")

    # Relationships
    brands: Mapped[list[Brand]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Tenant(id={self.id!r}, name={self.name!r})"
