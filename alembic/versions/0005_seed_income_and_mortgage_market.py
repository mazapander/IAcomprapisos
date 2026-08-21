"""seed income and mortgage market indicators

Revision ID: 0005_seed_income_mortgage_market
Revises: 0004_seed_market_indicators
"""

from alembic import op

revision = "0005_seed_income_mortgage_market"
down_revision = "0004_seed_market_indicators"
branch_labels = None
depends_on = None

CODES = [
    "income_net_mean_person_eur",
    "income_net_mean_household_eur",
    "income_mean_equivalised_eur",
    "income_median_equivalised_eur",
    "income_gross_mean_person_eur",
    "income_gross_mean_household_eur",
    "income_share_salary_pct",
    "income_share_pensions_pct",
    "income_share_unemployment_benefits_pct",
    "income_share_other_benefits_pct",
    "income_share_other_income_pct",
    "mortgage_new_business_aprc_pct",
    "mortgage_new_business_volume_million_eur",
]


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO analytics.indicators
            (code, name, description, unit, native_frequency, aggregation_method,
             geographic_level, source, dataset)
        VALUES
            ('income_net_mean_person_eur', 'Renta neta media por persona',
             'Renta neta media anual por persona del Atlas de Distribucion de Renta de los Hogares',
             'eur_year', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53689'),
            ('income_net_mean_household_eur', 'Renta neta media por hogar',
             'Renta neta media anual por hogar del Atlas de Distribucion de Renta de los Hogares',
             'eur_year', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53689'),
            ('income_mean_equivalised_eur', 'Renta media por unidad de consumo',
             'Renta media anual por unidad de consumo del Atlas de Distribucion de Renta de los Hogares',
             'eur_year', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53689'),
            ('income_median_equivalised_eur', 'Renta mediana por unidad de consumo',
             'Renta mediana anual por unidad de consumo del Atlas de Distribucion de Renta de los Hogares',
             'eur_year', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53689'),
            ('income_gross_mean_person_eur', 'Renta bruta media por persona',
             'Renta bruta media anual por persona del Atlas de Distribucion de Renta de los Hogares',
             'eur_year', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53689'),
            ('income_gross_mean_household_eur', 'Renta bruta media por hogar',
             'Renta bruta media anual por hogar del Atlas de Distribucion de Renta de los Hogares',
             'eur_year', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53689'),
            ('income_share_salary_pct', 'Peso de salarios en la renta',
             'Porcentaje de la renta procedente de salarios',
             'percent', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53687'),
            ('income_share_pensions_pct', 'Peso de pensiones en la renta',
             'Porcentaje de la renta procedente de pensiones',
             'percent', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53687'),
            ('income_share_unemployment_benefits_pct', 'Peso de prestaciones por desempleo en la renta',
             'Porcentaje de la renta procedente de prestaciones por desempleo',
             'percent', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53687'),
            ('income_share_other_benefits_pct', 'Peso de otras prestaciones en la renta',
             'Porcentaje de la renta procedente de otras prestaciones',
             'percent', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53687'),
            ('income_share_other_income_pct', 'Peso de otros ingresos en la renta',
             'Porcentaje de la renta procedente de otros ingresos',
             'percent', 'annual', 'last_available', 'national_ccaa_province',
             'ine_household_income', 'ine_table_53687'),
            ('mortgage_new_business_aprc_pct', 'TAE media de nuevas hipotecas',
             'TAE media de nuevas operaciones de credito a la vivienda. La definicion MIR incluye renegociaciones.',
             'percent', 'monthly', 'last_available', 'national',
             'bde_mortgage_market', 'bde_be1906_mortgage_aprc'),
            ('mortgage_new_business_volume_million_eur', 'Importe de nuevas hipotecas',
             'Importe mensual de nuevas operaciones de credito a la vivienda, en millones de euros. La definicion MIR incluye renegociaciones.',
             'million_eur', 'monthly', 'sum', 'national',
             'bde_mortgage_market', 'bde_be1912_mortgage_volume')
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    codes = ",".join(f"'{code}'" for code in CODES)
    op.execute(f"DELETE FROM analytics.indicators WHERE code IN ({codes})")
