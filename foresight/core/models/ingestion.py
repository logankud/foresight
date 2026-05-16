"""IngestionJob — the run history for Shopify ingestion + retries.

One row per backfill or webhook-batch attempt. Used by:
- Operators to inspect failures (E4.S5 ops endpoints).
- The worker to resume from ``last_cursor`` instead of restarting.
- The agent to answer "is my data fresh?" questions.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from foresight.core.models.base import Base, TenantScopedMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from foresight.core.models.brand import Brand


class IngestionJobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IngestionJob(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        Index("ix_ingestion_jobs_brand_status", "brand_id", "status"),
        Index("ix_ingestion_jobs_tenant_started_at", "tenant_id", "started_at"),
    )

    id: Mapped[UUID] = uuid_pk()
    brand_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Coarse-grained "what kind of job is this" — backfill, webhook batch, etc.
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[IngestionJobStatus] = mapped_column(
        Enum(IngestionJobStatus, name="ingestion_job_status_enum"),
        nullable=False,
        default=IngestionJobStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Per-entity row counts so ops can answer "did we get all the orders?"
    rows_per_table: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False, default=dict)
    # Last cursor for resumability. Shape is job-type specific.
    last_cursor: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Sanitized error message for failed jobs (full trace stays in logs).
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    brand: Mapped[Brand] = relationship(back_populates="ingestion_jobs")

    def __repr__(self) -> str:
        return (
            f"IngestionJob(id={self.id!r}, job_type={self.job_type!r}, "
            f"status={self.status.value}, attempt={self.attempt})"
        )
