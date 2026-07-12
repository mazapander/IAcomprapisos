from datetime import date
from decimal import Decimal

from app.ingestion.base import SourceRecord
from app.ingestion.sources.bde_euribor import (
    BDEEuriborIngestion,
    _parse_decimal,
    _parse_period,
    parse_bde_euribor_csv,
)


def test_parses_spanish_months_and_iso_periods() -> None:
    assert _parse_period("ene-2025") == date(2025, 1, 1)
    assert _parse_period("2025-02") == date(2025, 2, 1)
    assert _parse_period("03/2025") == date(2025, 3, 1)


def test_parses_spanish_decimal_percentages() -> None:
    assert _parse_decimal("2,798") == Decimal("2.798")
    assert _parse_decimal("-0,505 %") == Decimal("-0.505")


def test_parses_semicolon_bde_csv() -> None:
    content = """Periodo;Míbor;Euríbor a un año\nene-2025;2,100;2,525\nfeb-2025;2,050;2,407\n"""

    result = parse_bde_euribor_csv(content)

    assert result[0][0] == date(2025, 1, 1)
    assert result[0][1] == Decimal("2.525")
    assert result[1][0] == date(2025, 2, 1)
    assert result[1][1] == Decimal("2.407")


def test_transforms_bde_raw_record() -> None:
    record = SourceRecord(
        dataset="bde_be1901_reference_rates",
        external_id="euribor_12m:2025-01-01",
        period=date(2025, 1, 1),
        geography_code="ES",
        payload={
            "value": "2.525",
            "download_url": "https://example.test/be1901.csv",
            "header": ["Periodo", "Euríbor a un año"],
        },
    )

    result = BDEEuriborIngestion().transform([record])

    assert len(result) == 1
    assert result[0].indicator_code == "euribor_12m_pct"
    assert result[0].geography_code == "ES"
    assert result[0].frequency == "monthly"
    assert result[0].value == Decimal("2.525")
    assert result[0].unit == "percent"
