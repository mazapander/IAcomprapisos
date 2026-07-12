"""initial schemas and tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS raw")
    op.execute("CREATE SCHEMA IF NOT EXISTS analytics")
    op.execute("CREATE SCHEMA IF NOT EXISTS control")
    op.create_table("ingestion_runs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("source", sa.String(80), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("requested_by", sa.String(80)), sa.Column("parameters", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("rows_received", sa.Integer(), nullable=False, server_default="0"), sa.Column("rows_written", sa.Integer(), nullable=False, server_default="0"), sa.Column("error", sa.Text()), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("finished_at", sa.DateTime(timezone=True)), schema="control")
    op.create_index("ix_ingestion_runs_source_started", "ingestion_runs", ["source", "started_at"], schema="control")
    op.create_table("source_records", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("source", sa.String(80), nullable=False), sa.Column("dataset", sa.String(120), nullable=False), sa.Column("external_id", sa.String(255)), sa.Column("period", sa.Date()), sa.Column("geography_code", sa.String(20)), sa.Column("payload", postgresql.JSONB(), nullable=False), sa.Column("payload_hash", sa.String(64), nullable=False), sa.Column("observed_at", sa.DateTime(timezone=True)), sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("source", "dataset", "payload_hash", name="uq_raw_source_dataset_hash"), schema="raw")
    op.create_index("ix_raw_source_period_geo", "source_records", ["source", "period", "geography_code"], schema="raw")
    op.create_table("geographies", sa.Column("code", sa.String(20), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("level", sa.String(20), nullable=False), sa.Column("parent_code", sa.String(20)), schema="analytics")
    op.create_table("indicator_observations", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("indicator_code", sa.String(100), nullable=False), sa.Column("geography_code", sa.String(20), nullable=False), sa.Column("period", sa.Date(), nullable=False), sa.Column("frequency", sa.String(20), nullable=False), sa.Column("value", sa.Numeric(20, 6), nullable=False), sa.Column("unit", sa.String(40), nullable=False), sa.Column("source", sa.String(80), nullable=False), sa.Column("source_run_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)), sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), sa.UniqueConstraint("indicator_code", "geography_code", "period", "source", name="uq_indicator_geo_period_source"), schema="analytics")
    op.create_index("ix_indicator_lookup", "indicator_observations", ["indicator_code", "geography_code", "period"], schema="analytics")


def downgrade() -> None:
    op.drop_schema("analytics", cascade=True)
    op.drop_schema("raw", cascade=True)
    op.drop_schema("control", cascade=True)
