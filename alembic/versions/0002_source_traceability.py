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


def _has_column(schema: str, table: str, column: str) -> bool:
    columns = sa.inspect(op.get_bind()).get_columns(table, schema=schema)
    return any(row["name"] == column for row in columns)


def _has_table(schema: str, table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table, schema=schema)


def _add_column_if_missing(schema: str, table: str, column: sa.Column) -> None:
    if not _has_column(schema, table, column.name):
        op.add_column(table, column, schema=schema)


def upgrade() -> None:
    _add_column_if_missing("raw", "source_records", sa.Column("source_version", sa.String(length=80), nullable=True))
    _add_column_if_missing("raw", "source_records", sa.Column("dataset_version", sa.String(length=80), nullable=True))
    _add_column_if_missing("raw", "source_records", sa.Column("source_url", sa.Text(), nullable=True))
    _add_column_if_missing("raw", "source_records", sa.Column("content_type", sa.String(length=120), nullable=True))
    _add_column_if_missing("raw", "source_records", sa.Column("http_status", sa.Integer(), nullable=True))
    _add_column_if_missing("raw", "source_records", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("raw", "source_records", sa.Column("available_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("analytics", "indicator_observations", sa.Column("available_at", sa.DateTime(timezone=True), nullable=True))

    if not _has_table("analytics", "indicators"):
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
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.PrimaryKeyConstraint("code"),
            schema="analytics",
        )

    op.execute(
        """
        INSERT INTO analytics.indicators
            (code, name, description, unit, native_frequency, aggregation_method, geographic_level, source, dataset)
        VALUES
            ('housing_sales_total', 'Compraventas de vivienda', 'Numero total de compraventas de viviendas', 'transactions', 'monthly', 'sum', 'national_ccaa_province', 'ine_transmissions', 'ine_table_6150'),
            ('housing_sales_new', 'Compraventas de vivienda nueva', 'Numero de compraventas de viviendas nuevas', 'transactions', 'monthly', 'sum', 'national_ccaa_province', 'ine_transmissions', 'ine_table_6150'),
            ('housing_sales_used', 'Compraventas de vivienda usada', 'Numero de compraventas de viviendas usadas', 'transactions', 'monthly', 'sum', 'national_ccaa_province', 'ine_transmissions', 'ine_table_6150'),
            ('housing_sales_free_market', 'Compraventas de vivienda libre', 'Numero de compraventas de viviendas libres', 'transactions', 'monthly', 'sum', 'national_ccaa_province', 'ine_transmissions', 'ine_table_6150'),
            ('housing_sales_protected', 'Compraventas de vivienda protegida', 'Numero de compraventas de viviendas protegidas', 'transactions', 'monthly', 'sum', 'national_ccaa_province', 'ine_transmissions', 'ine_table_6150')
        ON CONFLICT (code) DO NOTHING
        """
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
