import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        Index("ix_ingestion_runs_source_started", "source", "started_at"),
        {"schema": "control"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20))
    requested_by: Mapped[str | None] = mapped_column(String(80))
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    rows_received: Mapped[int] = mapped_column(Integer, default=0)
    rows_written: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RawSourceRecord(Base):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("source", "dataset", "payload_hash", name="uq_raw_source_dataset_hash"),
        Index("ix_raw_source_period_geo", "source", "period", "geography_code"),
        {"schema": "raw"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    source: Mapped[str] = mapped_column(String(80))
    dataset: Mapped[str] = mapped_column(String(120))
    source_version: Mapped[str | None] = mapped_column(String(80))
    dataset_version: Mapped[str | None] = mapped_column(String(80))
    external_id: Mapped[str | None] = mapped_column(String(255))
    period: Mapped[date | None] = mapped_column(Date)
    geography_code: Mapped[str | None] = mapped_column(String(20))
    source_url: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str | None] = mapped_column(String(120))
    http_status: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB)
    payload_hash: Mapped[str] = mapped_column(String(64))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IndicatorDefinition(Base):
    __tablename__ = "indicators"
    __table_args__ = ({"schema": "analytics"},)

    code: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(40))
    native_frequency: Mapped[str] = mapped_column(String(20))
    aggregation_method: Mapped[str] = mapped_column(String(40))
    geographic_level: Mapped[str] = mapped_column(String(30))
    source: Mapped[str] = mapped_column(String(80))
    dataset: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class IndicatorObservation(Base):
    __tablename__ = "indicator_observations"
    __table_args__ = (
        UniqueConstraint(
            "indicator_code",
            "geography_code",
            "period",
            "source",
            name="uq_indicator_geo_period_source",
        ),
        Index("ix_indicator_lookup", "indicator_code", "geography_code", "period"),
        {"schema": "analytics"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(100))
    geography_code: Mapped[str] = mapped_column(String(20))
    period: Mapped[date] = mapped_column(Date)
    frequency: Mapped[str] = mapped_column(String(20))
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    unit: Mapped[str] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(80))
    source_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
