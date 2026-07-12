"""seed market indicators

Revision ID: 0004_seed_market_indicators
Revises: 0003_seed_euribor_indicator
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_seed_market_indicators"
down_revision = "0003_seed_euribor_indicator"
branch_labels = None
depends_on = None

ROWS = [
("house_price_index","Índice de precios de vivienda","index_2025_100","quarterly","last_available","national_ccaa","ine_house_prices","ine_table_79563"),
("house_price_index_new","Índice de precios de vivienda nueva","index_2025_100","quarterly","last_available","national_ccaa","ine_house_prices","ine_table_79563"),
("house_price_index_used","Índice de precios de vivienda usada","index_2025_100","quarterly","last_available","national_ccaa","ine_house_prices","ine_table_79563"),
("mortgages_housing_total","Hipotecas sobre viviendas","mortgages","monthly","sum","national_province","ine_mortgages","ine_table_3200"),
("mortgages_housing_amount_thousand_eur","Importe de hipotecas sobre viviendas","thousand_eur","monthly","sum","national_province","ine_mortgages","ine_table_3200"),
("appraisal_price_eur_m2","Valor tasado de vivienda","eur_m2","quarterly","last_available","national_ccaa_province","mivau_appraisal","mivau_appraisal_value"),
("rent_monthly_median_eur","Renta mensual mediana","eur_month","annual","last_available","multi_level","mivau_rent","serpavi_rent_reference"),
("rent_price_median_eur_m2","Renta mediana por metro cuadrado","eur_m2_month","annual","last_available","multi_level","mivau_rent","serpavi_rent_reference"),
]

def upgrade() -> None:
    table = sa.table("indicators",sa.column("code",sa.String),sa.column("name",sa.String),sa.column("description",sa.Text),sa.column("unit",sa.String),sa.column("native_frequency",sa.String),sa.column("aggregation_method",sa.String),sa.column("geographic_level",sa.String),sa.column("source",sa.String),sa.column("dataset",sa.String),schema="analytics")
    op.bulk_insert(table,[{"code":c,"name":n,"description":n,"unit":u,"native_frequency":f,"aggregation_method":a,"geographic_level":g,"source":s,"dataset":d} for c,n,u,f,a,g,s,d in ROWS])

def downgrade() -> None:
    codes = ",".join(f"'{row[0]}'" for row in ROWS)
    op.execute(f"DELETE FROM analytics.indicators WHERE code IN ({codes})")
