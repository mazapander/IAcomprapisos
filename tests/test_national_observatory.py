from datetime import date
from decimal import Decimal

from app.analytics.derived import ObservationPoint
from app.analytics.national_observatory import build_national_observatory


def point(code: str, period: date, value: str, unit: str, source: str = "test"):
    return ObservationPoint(code, "ES", period, Decimal(value), unit, source)


def test_observatory_builds_price_mortgage_and_rate_series() -> None:
    observations = [
        point("house_price_index", date(2024, 6, 1), "100", "index_2025_100", "INE"),
        point("house_price_index", date(2025, 6, 1), "108", "index_2025_100", "INE"),
        point("mortgages_housing_total", date(2024, 6, 1), "100", "mortgages", "INE"),
        point("mortgages_housing_total", date(2025, 6, 1), "110", "mortgages", "INE"),
        point(
            "mortgages_housing_amount_thousand_eur",
            date(2025, 6, 1),
            "16500",
            "thousand_eur",
            "INE",
        ),
        point("euribor_12m_pct", date(2024, 6, 1), "3.65", "percent", "BdE"),
        point("euribor_12m_pct", date(2025, 6, 1), "2.10", "percent", "BdE"),
    ]

    result = build_national_observatory(observations)

    price = result["groups"]["prices"]["series"][0]
    assert price["latest"]["value"] == Decimal("108.00")
    assert price["change_year_on_year"] == {
        "value": Decimal("8.00"),
        "unit": "percent",
    }

    average = result["groups"]["mortgages"]["series"][1]
    assert average["latest"]["value"] == Decimal("150000.00")
    assert average["latest"]["unit"] == "eur"

    euribor = result["groups"]["rates"]["series"][0]
    assert euribor["change_year_on_year"] == {
        "value": Decimal("-1.55"),
        "unit": "percentage_points",
    }
    assert result["coverage"]["available_series"] == 4


def test_observatory_discloses_missing_series_instead_of_estimating() -> None:
    result = build_national_observatory([])

    assert result["coverage"]["available_series"] == 0
    assert result["coverage"]["total_series"] == 8
    assert all(
        not series["available"]
        for group in result["groups"].values()
        for series in group["series"]
    )
