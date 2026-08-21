from datetime import date
from decimal import Decimal

from app.analytics.derived import (
    MarketAssumptions,
    ObservationPoint,
    annual_change_pct,
    build_market_summary,
    mortgage_payment,
    percentile_rank,
    price_to_rent_years,
)


def point(code: str, period: date, value: str, unit: str, geo: str = "PROV:24") -> ObservationPoint:
    return ObservationPoint(code, geo, period, Decimal(value), unit, "test")


def test_financial_primitives() -> None:
    assert annual_change_pct(Decimal("108.4"), Decimal(100)) == Decimal("8.400")
    assert mortgage_payment(Decimal(100000), Decimal(0), 25) == Decimal(
        "333.3333333333333333333333333"
    )
    assert price_to_rent_years(Decimal(1800), Decimal(10)) == Decimal(15)
    assert percentile_rank(Decimal(3), [Decimal(1), Decimal(3), Decimal(5)]) == Decimal(
        "66.66666666666666666666666667"
    )


def test_market_summary_builds_card_and_product_analytics() -> None:
    rows = [
        point("appraisal_price_eur_m2", date(2024, 1, 1), "1700", "eur_m2"),
        point("appraisal_price_eur_m2", date(2025, 1, 1), "1850", "eur_m2"),
        point("income_net_mean_household_eur", date(2024, 1, 1), "31000", "eur_year"),
        point("income_net_mean_household_eur", date(2025, 1, 1), "32400", "eur_year"),
        point("income_share_salary_pct", date(2025, 1, 1), "61", "percent"),
        point("mortgages_housing_total", date(2024, 6, 1), "100", "mortgages"),
        point("mortgages_housing_total", date(2025, 6, 1), "108.4", "mortgages"),
        point(
            "mortgage_new_business_volume_million_eur",
            date(2025, 6, 1),
            "1234.5",
            "million_eur",
            "ES",
        ),
        point("rent_price_median_eur_m2", date(2024, 1, 1), "9.5", "eur_m2_month"),
        point("mortgage_new_business_aprc_pct", date(2025, 6, 1), "2.94", "percent", "ES"),
        point("euribor_12m_pct", date(2025, 6, 1), "2.10", "percent", "ES"),
    ]

    result = build_market_summary(rows, "PROV:24", MarketAssumptions())

    assert result["market_card"]["price_eur_m2"]["value"] == Decimal("1850.00")
    assert result["market_card"]["mortgages_yoy_pct"]["value"] == Decimal("8.40")
    assert result["market_card"]["new_financing_volume_eur"]["value"] == Decimal("1234500000.00")
    assert result["derived"]["mortgage_spread_pp"]["value"] == Decimal("0.84")
    assert result["derived"]["price_to_income_years"]["value"] == Decimal("5.14")
    assert result["derived"]["price_to_rent_years"]["value"] == Decimal("16.23")
    assert result["coverage"]["available_fields"] == 8


def test_effort_uses_disclosed_euribor_fallback_when_apr_is_missing() -> None:
    rows = [
        point("appraisal_price_eur_m2", date(2025, 1, 1), "1850", "eur_m2"),
        point("income_net_mean_household_eur", date(2025, 1, 1), "32400", "eur_year"),
        point("euribor_12m_pct", date(2025, 1, 1), "2.1", "percent", "ES"),
    ]
    result = build_market_summary(rows, "PROV:24", MarketAssumptions())
    assert result["market_card"]["estimated_purchase_effort_pct"]["value"] is not None
    assert result["assumptions"]["effort_rate_basis"] == "euribor_plus_assumed_spread"
    assert result["derived"]["mortgage_spread_pp"]["value"] is None
