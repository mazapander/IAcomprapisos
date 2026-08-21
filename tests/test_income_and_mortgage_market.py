from datetime import date
from decimal import Decimal

from app.ingestion.base import SourceRecord
from app.ingestion.registry import available_sources
from app.ingestion.sources.bde_mortgage_market import (
    BDEMortgageMarketIngestion,
    parse_bde_table_series,
)
from app.ingestion.sources.ine_common import parse_period
from app.ingestion.sources.ine_income import INEHouseholdIncomeIngestion


def test_annual_ine_period_is_normalized_to_first_day_of_year() -> None:
    assert parse_period({"T3_Periodo": "2023"}, "annual") == date(2023, 1, 1)
    assert parse_period({"Anyo": 2022, "FK_Periodo": 1}, "annual") == date(
        2022, 1, 1
    )


def test_household_income_transformation() -> None:
    records = [
        SourceRecord(
            dataset="ine_table_53689",
            period=date(2023, 1, 1),
            geography_code="PROV:24",
            payload={
                "table_id": "53689",
                "series_code": "income-household",
                "series_name": "24 León; Renta neta media por hogar",
                "observation": {"Valor": "38.326"},
            },
        ),
        SourceRecord(
            dataset="ine_table_53687",
            period=date(2023, 1, 1),
            geography_code="PROV:24",
            payload={
                "table_id": "53687",
                "series_code": "income-salary",
                "series_name": "24 León; Salario",
                "observation": {"Valor": "61,7"},
            },
        ),
    ]

    result = INEHouseholdIncomeIngestion().transform(records)
    by_code = {item.indicator_code: item for item in result}

    assert by_code["income_net_mean_household_eur"].value == Decimal("38326")
    assert by_code["income_net_mean_household_eur"].unit == "eur_year"
    assert by_code["income_share_salary_pct"].value == Decimal("61.7")
    assert by_code["income_share_salary_pct"].unit == "percent"
    assert all(item.frequency == "annual" for item in result)


def test_bde_multi_series_parser_selects_mortgage_columns() -> None:
    aprc_csv = """ALIAS DE LA SERIE;Vivienda;Consumo
FRECUENCIA;MENSUAL;MENSUAL
MAY 2026;2,92;7,10
JUN 2026;2,94;7,20
"""
    volume_csv = """ALIAS DE LA SERIE;Descubiertos;Vivienda total
FRECUENCIA;MENSUAL;MENSUAL
MAY 2026;1000;6857
JUN 2026;1200;8088
"""

    aprc = parse_bde_table_series(aprc_csv, series_index=0)
    volume = parse_bde_table_series(volume_csv, series_index=1)

    assert aprc[-1][0] == date(2026, 6, 1)
    assert aprc[-1][1] == Decimal("2.94")
    assert aprc[-1][2]["series_alias"] == "Vivienda"
    assert volume[-1][0] == date(2026, 6, 1)
    assert volume[-1][1] == Decimal("8088")
    assert volume[-1][2]["series_alias"] == "Vivienda total"


def test_bde_mortgage_market_transformation_preserves_mir_caveat() -> None:
    records = [
        SourceRecord(
            dataset="bde_be1906_mortgage_aprc",
            period=date(2026, 6, 1),
            geography_code="ES",
            payload={
                "indicator_code": "mortgage_new_business_aprc_pct",
                "value": "2.94",
                "unit": "percent",
                "download_url": "https://example.test/be1906.csv",
                "series_metadata": {"series_alias": "Vivienda"},
            },
        ),
        SourceRecord(
            dataset="bde_be1912_mortgage_volume",
            period=date(2026, 6, 1),
            geography_code="ES",
            payload={
                "indicator_code": "mortgage_new_business_volume_million_eur",
                "value": "8088",
                "unit": "million_eur",
                "download_url": "https://example.test/be1912.csv",
                "series_metadata": {"series_alias": "Vivienda total"},
            },
        ),
    ]

    result = BDEMortgageMarketIngestion().transform(records)
    by_code = {item.indicator_code: item for item in result}

    assert by_code["mortgage_new_business_aprc_pct"].value == Decimal("2.94")
    assert by_code["mortgage_new_business_volume_million_eur"].value == Decimal(
        "8088"
    )
    assert all(item.metadata["includes_renegotiations"] is True for item in result)


def test_new_sources_are_registered() -> None:
    sources = available_sources()
    assert "ine_household_income" in sources
    assert "bde_mortgage_market" in sources
