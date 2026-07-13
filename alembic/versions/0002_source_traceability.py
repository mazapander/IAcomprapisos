"""source traceability and indicator catalog

Revision ID: 0002_source_traceability
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_source_traceability"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("source_records", sa.Column("source_version", sa.String(length=80), nullable=True), schema="raw")
    op.add_column("source_records", sa.Column("dataset_version", sa.String(length=80), nullable=True), schema="raw")
    op.add_column("source_records", sa.Column("source_url", sa.Text(), nullable=True), schema="raw")
    op.add_column("source_records", sa.Column("content_type", sa.String(length=120), nullable=True), schema="raw")
    op.add_column("source_records", sa.Column("http_status", sa.Integer(), nullable=True), schema="raw")
    op.add_column("source_records", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True), schema="raw")
    op.add_column("source_records", sa.Column("available_at", sa.DateTime(timezone=True), nullable=True), schema="raw")
    op.add_column("indicator_observations", sa.Column("available_at", sa.DateTime(timezone=True), nullable=True), schema="analytics")

    op.create_table(
        "indicators",
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("native_frequency", sa.String(length=20), nullable=False),
        sa.Column("aggregation_method", sa.String(length=40), nullable=False),
        sa.Column("geographic_level", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("dataset", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.PrimaryKeyConstraint("code"),
        schema="analytics",
    )

    indicators = sa.table(
        "indicators",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("unit", sa.String),
        sa.column("native_frequency", sa.String),
        sa.column("aggregation_method", sa.String),
        sa.column("geographic_level", sa.String),
        sa.column("source", sa.String),
        sa.column("dataset", sa.String),
        schema="analytics",
    )
    op.bulk_insert(
        indicators,
        [
            {"code": "housing_sales_total", "name": "Compraventas de vivienda", "description": "Número total de compraventas de viviendas", "unit": "transactions", "native_frequency": "monthly", "aggregation_method": "sum", "geographic_level": "national_ccaa_province", "source": "ine_transmissions", "dataset": "ine_table_6150"},
            {"code": "housing_sales_new", "name": "Compraventas de vivienda nueva", "description": "Número de compraventas de viviendas nuevas", "unit": "transactions", "native_frequency": "monthly", "aggregation_method": "sum", "geographic_level": "national_ccaa_province", "source": "ine_transmissions", "dataset": "ine_table_6150"},
            {"code": "housing_sales_used", "name": "Compraventas de vivienda usada", "description": "Número de compraventas de viviendas usadas", "unit": "transactions", "native_frequency": "monthly", "aggregation_method": "sum", "geographic_level": "national_ccaa_province", "source": "ine_transmissions", "dataset": "ine_table_6150"},
            {"code": "housing_sales_free_market", "name": "Compraventas de vivienda libre", "description": "Número de compraventas de viviendas libres", "unit": "transactions", "native_frequency": "monthly", "aggregation_method": "sum", "geographic_level": "national_ccaa_province", "source": "ine_transmissions", "dataset": "ine_table_6150"},
            {"code": "housing_sales_protected", "name": "Compraventas de vivienda protegida", "description": "Número de compraventas de viviendas protegidas", "unit": "transactions", "native_frequency": "monthly", "aggregation_method": "sum", "geographic_level": "national_ccaa_province", "source": "ine_transmissions", "dataset": "ine_table_6150"},
        ],
    )


def downgrade() -> None:
    op.drop_table("indicators", schema="analytics")
    op.drop_column("indicator_observations", "available_at", schema="analytics")
    op.drop_column("source_records", "available_at", schema="raw")
    op.drop_column("source_records", "published_at", schema="raw")
    op.drop_column("source_records", "http_status", schema="raw")
    op.drop_column("source_records", "content_type", schema="raw")
    op.drop_column("source_records", "source_url", schema="raw")
    op.drop_column("source_records", "dataset_version", schema="raw")
    op.drop_column("source_records", "source_version", schema="raw")
