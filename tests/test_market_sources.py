from datetime import date
from decimal import Decimal

from app.ingestion.base import SourceRecord
from app.ingestion.sources.ine_house_prices import INEHousePricesIngestion
from app.ingestion.sources.ine_mortgages import INEMortgagesIngestion
from app.ingestion.sources.mivau_appraisal import MIVAUAppraisalIngestion
from app.ingestion.sources.mivau_rent import MIVAURentIngestion
from app.ingestion.sources.mivau_tabular import decimal_value, geography, period_value


def test_quarter_and_geography_helpers() -> None:
    assert period_value("2025 T3", "quarterly") == date(2025, 7, 1)
    assert period_value("2024", "annual") == date(2024, 1, 1)
    assert geography("Bizkaia", "province", "48") == "PROV:48"
    assert geography("Bilbao", "municipality", "48020") == "MUN:48020"
    assert decimal_value("1.234,50") == Decimal("1234.50")


def test_house_price_index_transformation() -> None:
    record = SourceRecord(dataset="ine_table_79563", period=date(2026, 1, 1), geography_code="CCAA:16", payload={"series_code":"x","series_name":"16 País Vasco; Vivienda segunda mano; Índice","observation":{"Valor":"125,500"}})
    item = INEHousePricesIngestion().transform([record])[0]
    assert item.indicator_code == "house_price_index_used"
    assert item.frequency == "quarterly"
    assert item.value == Decimal("125.500")


def test_mortgage_transformation() -> None:
    record = SourceRecord(dataset="ine_table_3200", period=date(2026, 4, 1), geography_code="PROV:24", payload={"series_code":"x","series_name":"24 León; Viviendas; Número de hipotecas","observation":{"Valor":321}})
    item = INEMortgagesIngestion().transform([record])[0]
    assert item.indicator_code == "mortgages_housing_total"
    assert item.value == Decimal("321")


def test_appraisal_transformation() -> None:
    record = SourceRecord(dataset="mivau_appraisal_value", period=date(2025, 4, 1), geography_code="PROV:24", payload={"row":{"valor tasado euros por metro cuadrado":"1.850,25"},"download_url":"https://example.test/value.xlsx"})
    item = MIVAUAppraisalIngestion().transform([record])[0]
    assert item.indicator_code == "appraisal_price_eur_m2"
    assert item.value == Decimal("1850.25")


def test_serpavi_transformation_keeps_annual_frequency() -> None:
    record = SourceRecord(dataset="serpavi_rent_reference", period=date(2023, 1, 1), geography_code="MUN:48020", payload={"row":{"renta mensual mediana":850,"renta mediana por m2":"12,5"},"download_url":"https://example.test/serpavi.xlsx"})
    result = MIVAURentIngestion().transform([record])
    assert {item.indicator_code for item in result} == {"rent_monthly_median_eur", "rent_price_median_eur_m2"}
    assert all(item.frequency == "annual" for item in result)
