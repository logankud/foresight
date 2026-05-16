"""Forecast and ForecastPoint — predictions persisted with provenance.

Each ``Forecast`` is a single run of the forecasting pipeline (E5) for
one brand at a specific point in time. It tracks ``model_name`` /
``model_version`` / ``inputs_as_of`` so we can audit *why* a particular
recommendation was made even months later.

Each ``ForecastPoint`` is the per-variant output of that run.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.brand import Brand
    from foresight.core.models.product import Variant


class Forecast(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "forecasts"
    __table_args__ = (
        Index("ix_forecasts_brand_run_at", "brand_id", "run_at"),
        # Useful for "show me the latest forecast for this brand" queries.
        Index("ix_forecasts_tenant_run_at", "tenant_id", "run_at"),
    )

    id: Mapped[UUID] = uuid_pk()
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Provenance — these three fields are the audit story.
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    inputs_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # When the actual run happened (may differ slightly from inputs_as_of
    # for backtests / replays).
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Optional reference to an S3 artifact (parquet) holding the full
    # input + output snapshot. Set by E5.S3.
    artifact_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifact_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Relationships
    brand: Mapped[Brand] = relationship(back_populates="forecasts")
    points: Mapped[list[ForecastPoint]] = relationship(
        back_populates="forecast",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"Forecast(id={self.id!r}, brand_id={self.brand_id!r}, "
            f"model={self.model_name}@{self.model_version}, run_at={self.run_at!r})"
        )


class ForecastPoint(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "forecast_points"
    __table_args__ = (
        # A given forecast run produces one point per variant.
        UniqueConstraint("forecast_id", "variant_id", name="uq_forecast_points_forecast_variant"),
        Index("ix_forecast_points_variant_id", "variant_id"),
    )

    id: Mapped[UUID] = uuid_pk()
    forecast_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("forecasts.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("variants.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Core prediction surface. Nullable because zero-velocity SKUs
    # honestly report `days_of_cover = NULL` rather than infinity.
    current_inventory: Mapped[int] = mapped_column(Integer, nullable=False)
    velocity_per_day: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    days_of_cover: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Confidence band (lo / hi) for days_of_cover.
    days_of_cover_lo: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    days_of_cover_hi: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Reason field — used when days_of_cover is NULL to explain why
    # (e.g., "zero velocity in window", "no inventory data").
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    forecast: Mapped[Forecast] = relationship(back_populates="points")
    variant: Mapped[Variant] = relationship(back_populates="forecast_points")

    def __repr__(self) -> str:
        return f"ForecastPoint(variant_id={self.variant_id!r}, days_of_cover={self.days_of_cover})"
