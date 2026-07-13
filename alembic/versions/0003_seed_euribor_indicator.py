"""seed Euribor indicator definition

Revision ID: 0003_seed_euribor_indicator
Revises: 0002_source_traceability
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_seed_euribor_indicator"
down_revision = "0002_source_traceability"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
            {
                "code": "euribor_12m_pct",
                "name": "Euríbor a 12 meses",
                "description": "Media mensual oficial del Euríbor a un año publicada por el Banco de España",
                "unit": "percent",
                "native_frequency": "monthly",
                "aggregation_method": "last_available",
                "geographic_level": "national",
                "source": "bde_euribor",
                "dataset": "bde_be1901_reference_rates",
            }
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM analytics.indicators WHERE code = 'euribor_12m_pct'")
