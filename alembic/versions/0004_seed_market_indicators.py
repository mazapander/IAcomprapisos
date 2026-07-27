"""seed market indicators

Revision ID: 0004_seed_market_indicators
Revises: 0003_seed_euribor_indicator
"""

from alembic import op

revision = "0004_seed_market_indicators"
down_revision = "0003_seed_euribor_indicator"
branch_labels = None
depends_on = None

ROWS = [
    ("house_price_index", "Indice de precios de vivienda", "index_2025_100", "quarterly", "last_available", "national_ccaa", "ine_house_prices", "ine_table_79563"),
    ("house_price_index_new", "Indice de precios de vivienda nueva", "index_2025_100", "quarterly", "last_available", "national_ccaa", "ine_house_prices", "ine_table_79563"),
    ("house_price_index_used", "Indice de precios de vivienda usada", "index_2025_100", "quarterly", "last_available", "national_ccaa", "ine_house_prices", "ine_table_79563"),
    ("mortgages_housing_total", "Hipotecas sobre viviendas", "mortgages", "monthly", "sum", "national_province", "ine_mortgages", "ine_table_3200"),
    ("mortgages_housing_amount_thousand_eur", "Importe de hipotecas sobre viviendas", "thousand_eur", "monthly", "sum", "national_province", "ine_mortgages", "ine_table_3200"),
    ("appraisal_price_eur_m2", "Valor tasado de vivienda", "eur_m2", "quarterly", "last_available", "national_ccaa_province", "mivau_appraisal", "mivau_appraisal_value"),
    ("rent_monthly_median_eur", "Renta mensual mediana", "eur_month", "annual", "last_available", "multi_level", "mivau_rent", "serpavi_rent_reference"),
    ("rent_price_median_eur_m2", "Renta mediana por metro cuadrado", "eur_m2_month", "annual", "last_available", "multi_level", "mivau_rent", "serpavi_rent_reference"),
]


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO analytics.indicators
            (code, name, description, unit, native_frequency, aggregation_method, geographic_level, source, dataset)
        VALUES
            ('house_price_index', 'Indice de precios de vivienda', 'Indice de precios de vivienda', 'index_2025_100', 'quarterly', 'last_available', 'national_ccaa', 'ine_house_prices', 'ine_table_79563'),
            ('house_price_index_new', 'Indice de precios de vivienda nueva', 'Indice de precios de vivienda nueva', 'index_2025_100', 'quarterly', 'last_available', 'national_ccaa', 'ine_house_prices', 'ine_table_79563'),
            ('house_price_index_used', 'Indice de precios de vivienda usada', 'Indice de precios de vivienda usada', 'index_2025_100', 'quarterly', 'last_available', 'national_ccaa', 'ine_house_prices', 'ine_table_79563'),
            ('mortgages_housing_total', 'Hipotecas sobre viviendas', 'Hipotecas sobre viviendas', 'mortgages', 'monthly', 'sum', 'national_province', 'ine_mortgages', 'ine_table_3200'),
            ('mortgages_housing_amount_thousand_eur', 'Importe de hipotecas sobre viviendas', 'Importe de hipotecas sobre viviendas', 'thousand_eur', 'monthly', 'sum', 'national_province', 'ine_mortgages', 'ine_table_3200'),
            ('appraisal_price_eur_m2', 'Valor tasado de vivienda', 'Valor tasado de vivienda', 'eur_m2', 'quarterly', 'last_available', 'national_ccaa_province', 'mivau_appraisal', 'mivau_appraisal_value'),
            ('rent_monthly_median_eur', 'Renta mensual mediana', 'Renta mensual mediana', 'eur_month', 'annual', 'last_available', 'multi_level', 'mivau_rent', 'serpavi_rent_reference'),
            ('rent_price_median_eur_m2', 'Renta mediana por metro cuadrado', 'Renta mediana por metro cuadrado', 'eur_m2_month', 'annual', 'last_available', 'multi_level', 'mivau_rent', 'serpavi_rent_reference')
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    codes = ",".join(f"'{row[0]}'" for row in ROWS)
    op.execute(f"DELETE FROM analytics.indicators WHERE code IN ({codes})")
