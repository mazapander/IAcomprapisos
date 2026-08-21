from decimal import Decimal

from fastapi.testclient import TestClient

from app.analytics.mortgage_decision import MortgageScenario, review_mortgage
from app.main import app


def test_balanced_mortgage_scenario() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(200000),
            savings_eur=Decimal(76000),
            annual_net_household_income_eur=Decimal(48000),
            mortgage_amount_eur=Decimal(150000),
            annual_apr_pct=Decimal("2.9"),
            term_years=25,
            monthly_living_costs_eur=Decimal(1200),
            market_apr_pct=Decimal(3),
            euribor_pct=Decimal("2.1"),
        )
    )
    assert result["status"] == "balanced"
    assert result["calculations"]["ltv_pct"] == Decimal("75.00")
    assert result["calculations"]["remaining_savings_eur"] == Decimal("6000.00")
    assert result["calculations"]["mortgage_spread_pp"] == Decimal("0.80")
    assert result["calculations"]["apr_vs_market_pp"] == Decimal("-0.10")


def test_risky_scenario_explains_cash_effort_and_ltv() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(250000),
            savings_eur=Decimal(20000),
            annual_net_household_income_eur=Decimal(30000),
            mortgage_amount_eur=Decimal(240000),
            annual_apr_pct=Decimal(5),
            term_years=30,
            existing_monthly_debt_eur=Decimal(300),
            monthly_living_costs_eur=Decimal(1200),
        )
    )
    codes = {alert["code"] for alert in result["alerts"]}
    assert result["status"] == "high_risk"
    assert {"insufficient_cash", "high_effort", "rate_stress", "high_ltv"} <= codes


def test_mortgage_review_api() -> None:
    response = TestClient(app).post(
        "/api/v1/mortgages/review",
        json={
            "property_price_eur": 200000,
            "savings_eur": 76000,
            "annual_net_household_income_eur": 48000,
            "mortgage_amount_eur": 150000,
            "annual_apr_pct": 2.9,
            "term_years": 25,
            "monthly_living_costs_eur": 1200,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "balanced"
