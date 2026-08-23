from decimal import Decimal

from fastapi.testclient import TestClient

from app.analytics.mortgage_decision import (
    MortgageScenario,
    PurchaseBudgetScenario,
    calculate_purchase_budget,
    review_mortgage,
)
from app.analytics.derived import mortgage_payment
from app.main import app


def test_balanced_mortgage_scenario() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(200000),
            savings_eur=Decimal(76000),
            annual_net_household_income_eur=Decimal(48000),
            mortgage_amount_eur=Decimal(150000),
            annual_nominal_rate_pct=Decimal("2.75"),
            annual_apr_pct=Decimal("2.9"),
            rate_type="variable",
            term_years=25,
            monthly_living_costs_eur=Decimal(1200),
            market_apr_pct=Decimal(3),
            euribor_pct=Decimal("2.1"),
        )
    )
    assert result["status"] == "balanced"
    assert result["calculations"]["ltv_pct"] == Decimal("75.00")
    assert result["calculations"]["remaining_savings_eur"] == Decimal("6000.00")
    assert result["calculations"]["mortgage_spread_pp"] == Decimal("0.65")
    assert result["calculations"]["apr_vs_market_pp"] == Decimal("-0.10")


def test_risky_scenario_explains_cash_effort_and_ltv() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(250000),
            savings_eur=Decimal(20000),
            annual_net_household_income_eur=Decimal(30000),
            mortgage_amount_eur=Decimal(240000),
            annual_nominal_rate_pct=Decimal(5),
            rate_type="variable",
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
            "annual_nominal_rate_pct": 2.75,
            "annual_apr_pct": 2.9,
            "term_years": 25,
            "monthly_living_costs_eur": 1200,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "balanced"


def test_fixed_rate_is_not_stressed_and_does_not_claim_euribor_spread() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(200000),
            savings_eur=Decimal(80000),
            annual_net_household_income_eur=Decimal(48000),
            mortgage_amount_eur=Decimal(150000),
            annual_nominal_rate_pct=Decimal(3),
            term_years=25,
            rate_type="fixed",
            euribor_pct=Decimal(2),
        )
    )
    assert result["calculations"]["stressed_monthly_payment_eur"] == result["calculations"]["monthly_payment_eur"]
    assert result["calculations"]["mortgage_spread_pp"] is None


def test_french_payment_uses_tin_and_matches_independent_reference_case() -> None:
    # 100,000 EUR, 3% annual nominal rate, 300 monthly instalments.
    assert mortgage_payment(Decimal(100000), Decimal(3), 25).quantize(Decimal("0.01")) == Decimal(
        "474.21"
    )


def test_apr_is_not_used_to_calculate_interest() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(100000),
            savings_eur=Decimal(30000),
            annual_net_household_income_eur=Decimal(30000),
            mortgage_amount_eur=Decimal(80000),
            annual_nominal_rate_pct=Decimal(0),
            annual_apr_pct=Decimal(2),
            term_years=20,
        )
    )
    assert result["calculations"]["monthly_payment_eur"] == Decimal("333.33")
    assert result["calculations"]["total_interest_eur"] == Decimal("0.00")


def test_mixed_mortgage_models_both_phases_and_rate_stress() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(250000),
            savings_eur=Decimal(80000),
            annual_net_household_income_eur=Decimal(48000),
            mortgage_amount_eur=Decimal(200000),
            annual_nominal_rate_pct=Decimal("2.1"),
            term_years=30,
            rate_type="mixed",
            mixed_fixed_years=5,
            variable_spread_pct=Decimal("0.7"),
            euribor_pct=Decimal("2.0"),
            monthly_living_costs_eur=Decimal(1400),
        )
    )
    calculations = result["calculations"]
    assert calculations["monthly_payment_eur"] == Decimal("749.28")
    assert calculations["post_fixed_monthly_payment_eur"] == Decimal("801.74")
    assert calculations["stressed_monthly_payment_eur"] > calculations["post_fixed_monthly_payment_eur"]
    assert calculations["mortgage_spread_pp"] == Decimal("0.70")
    assert result["assumptions"]["mixed_fixed_years"] == 5


def test_mixed_mortgage_api_requires_phase_terms() -> None:
    response = TestClient(app).post(
        "/api/v1/mortgages/review",
        json={
            "property_price_eur": 250000,
            "savings_eur": 80000,
            "annual_net_household_income_eur": 48000,
            "mortgage_amount_eur": 200000,
            "annual_nominal_rate_pct": 2.1,
            "term_years": 30,
            "rate_type": "mixed",
        },
    )
    assert response.status_code == 422


def test_purchase_budget_is_limited_by_available_savings() -> None:
    result = calculate_purchase_budget(
        PurchaseBudgetScenario(
            annual_net_household_income_eur=Decimal(48000),
            savings_eur=Decimal(70000),
            annual_nominal_rate_pct=Decimal(3),
            term_years=25,
            monthly_living_costs_eur=Decimal(1500),
        )
    )
    assert result["limiting_factor"] == "available_savings"
    assert result["calculations"]["max_purchase_price_eur"] == Decimal("203333.33")
    assert result["calculations"]["reserved_savings_eur"] == Decimal("9000.00")


def test_purchase_budget_api_returns_explainable_limits() -> None:
    response = TestClient(app).post(
        "/api/v1/mortgages/budget",
        json={
            "annual_net_household_income_eur": 48000,
            "savings_eur": 70000,
            "annual_nominal_rate_pct": 3,
            "term_years": 25,
            "monthly_living_costs_eur": 1500,
        },
    )
    assert response.status_code == 200
    assert response.json()["limiting_factor"] in {"monthly_capacity", "available_savings"}


def test_offer_cost_keeps_interest_fees_and_linked_products_separate() -> None:
    result = review_mortgage(
        MortgageScenario(
            property_price_eur=Decimal(200000),
            savings_eur=Decimal(70000),
            annual_net_household_income_eur=Decimal(48000),
            mortgage_amount_eur=Decimal(150000),
            annual_nominal_rate_pct=Decimal(3),
            term_years=20,
            upfront_fees_eur=Decimal(750),
            monthly_linked_costs_eur=Decimal(25),
        )
    )
    calculations = result["calculations"]
    assert calculations["linked_costs_total_eur"] == Decimal("6000.00")
    assert calculations["estimated_total_cost_eur"] == (
        calculations["total_interest_eur"] + Decimal("6750.00")
    )
