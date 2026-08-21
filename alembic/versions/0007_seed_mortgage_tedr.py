"""seed mortgage TEDR indicators

Revision ID: 0007_seed_mortgage_tedr
Revises: 0006_product_analytics
"""

from alembic import op

revision = "0007_seed_mortgage_tedr"
down_revision = "0006_product_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO analytics.indicators
            (code, name, description, unit, native_frequency, aggregation_method,
             geographic_level, source, dataset)
        VALUES
            ('mortgage_new_business_tedr_pct',
             'TEDR media de nuevas operaciones de vivienda',
             'Tipo efectivo definicion restringida medio ponderado de nuevas operaciones de credito a la vivienda; excluye gastos conexos',
             'percent', 'monthly', 'last_available', 'national',
             'bde_mortgage_market', 'bde_be1904_mortgage_tedr_total'),
            ('mortgage_new_business_tedr_up_to_1y_pct',
             'TEDR de vivienda con fijacion inicial hasta un ano',
             'TEDR de nuevas operaciones de vivienda con periodo inicial de fijacion del tipo hasta un ano; proxy para hipotecas variables',
             'percent', 'monthly', 'last_available', 'national',
             'bde_mortgage_market', 'bde_be1904_mortgage_tedr_up_to_1y')
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM analytics.indicators
        WHERE code IN (
            'mortgage_new_business_tedr_pct',
            'mortgage_new_business_tedr_up_to_1y_pct'
        )
        """
    )
