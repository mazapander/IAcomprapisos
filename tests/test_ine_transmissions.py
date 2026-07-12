from datetime import date
from decimal import Decimal

from app.ingestion.base import SourceRecord
from app.ingestion.sources.ine_transmissions import (
    INETransmissionsIngestion,
    _category,
    _decimal,
    _geography_code,
    _period_from_observation,
)


def test_maps_national_and_province_geographies() -> None:
    assert _geography_code("Total Nacional; Viviendas: Total") == "ES"
    assert _geography_code("48 Bizkaia; Vivienda usada") == "PROV:48"


def test_maps_ccaa_geography() -> None:
    assert _geography_code("16 País Vasco; Vivienda nueva") == "CCAA:16"


def test_maps_categories() -> None:
    assert _category("48 Bizkaia; Viviendas: Total") == "housing_sales_total"
    assert _category("48 Bizkaia; Vivienda usada") == "housing_sales_used"


def test_parses_monthly_period_variants() -> None:
    assert _period_from_observation({"T3_Periodo": "2026M04"}) == date(2026, 4, 1)
    assert _period_from_observation({"Anyo": 2025, "FK_Periodo": 12}) == date(2025, 12, 1)


def test_parses_ine_numeric_values() -> None:
    assert _decimal("1.234") == Decimal("1234")
    assert _decimal("1.234,50") == Decimal("1234.50")
    assert _decimal(125) == Decimal("125")


def test_transforms_raw_record_to_canonical_indicator() -> None:
    record = SourceRecord(
        dataset="ine_table_6150",
        external_id="TEST:2026-04-01",
        period=date(2026, 4, 1),
        geography_code="PROV:48",
        payload={
            "series_code": "TEST",
            "series_name": "48 Bizkaia; Vivienda usada",
            "observation": {"Valor": 321, "T3_Periodo": "2026M04"},
        },
    )

    result = INETransmissionsIngestion().transform([record])

    assert len(result) == 1
    assert result[0].indicator_code == "housing_sales_used"
    assert result[0].geography_code == "PROV:48"
    assert result[0].period == date(2026, 4, 1)
    assert result[0].frequency == "monthly"
    assert result[0].value == Decimal("321")
    assert result[0].unit == "transactions"
