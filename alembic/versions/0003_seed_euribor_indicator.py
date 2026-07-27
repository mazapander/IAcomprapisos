"""seed Euribor indicator definition

Revision ID: 0003_seed_euribor_indicator
Revises: 0002_source_traceability
"""

from alembic import op

revision = "0003_seed_euribor_indicator"
down_revision = "0002_source_traceability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO analytics.indicators
            (code, name, description, unit, native_frequency, aggregation_method, geographic_level, source, dataset)
        VALUES
            ('euribor_12m_pct', 'Euribor a 12 meses', 'Media mensual oficial del Euribor a un ano publicada por el Banco de Espana', 'percent', 'monthly', 'last_available', 'national', 'bde_euribor', 'bde_be1901_reference_rates')
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM analytics.indicators WHERE code = 'euribor_12m_pct'")
