from dataclasses import asdict, dataclass
from decimal import Decimal

from app.analytics.derived import mortgage_payment, rounded


@dataclass(frozen=True)
class MortgageScenario:
    property_price_eur: Decimal
    savings_eur: Decimal
    annual_net_household_income_eur: Decimal
    mortgage_amount_eur: Decimal
    annual_apr_pct: Decimal
    term_years: int
    existing_monthly_debt_eur: Decimal = Decimal(0)
    monthly_living_costs_eur: Decimal = Decimal(0)
    purchase_cost_pct: Decimal = Decimal(10)
    stress_rate_increase_pp: Decimal = Decimal(2)
    market_apr_pct: Decimal | None = None
    euribor_pct: Decimal | None = None


def _ratio_pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    return numerator / denominator * 100 if denominator > 0 else None


def review_mortgage(scenario: MortgageScenario) -> dict:
    monthly_payment = mortgage_payment(
        scenario.mortgage_amount_eur,
        scenario.annual_apr_pct,
        scenario.term_years,
    )
    stressed_payment = mortgage_payment(
        scenario.mortgage_amount_eur,
        scenario.annual_apr_pct + scenario.stress_rate_increase_pp,
        scenario.term_years,
    )
    if monthly_payment is None or stressed_payment is None:
        raise ValueError("The mortgage scenario cannot produce a monthly payment")

    monthly_income = scenario.annual_net_household_income_eur / 12
    purchase_costs = scenario.property_price_eur * scenario.purchase_cost_pct / 100
    cash_required = scenario.property_price_eur + purchase_costs - scenario.mortgage_amount_eur
    remaining_savings = scenario.savings_eur - cash_required
    effort = _ratio_pct(
        monthly_payment + scenario.existing_monthly_debt_eur,
        monthly_income,
    )
    stressed_effort = _ratio_pct(
        stressed_payment + scenario.existing_monthly_debt_eur,
        monthly_income,
    )
    committed_income = _ratio_pct(
        monthly_payment + scenario.existing_monthly_debt_eur + scenario.monthly_living_costs_eur,
        monthly_income,
    )
    ltv = _ratio_pct(scenario.mortgage_amount_eur, scenario.property_price_eur)
    emergency_months = (
        remaining_savings / scenario.monthly_living_costs_eur
        if remaining_savings > 0 and scenario.monthly_living_costs_eur > 0
        else Decimal(0)
    )
    total_repayment = monthly_payment * scenario.term_years * 12

    alerts: list[dict[str, str]] = []
    if remaining_savings < 0:
        alerts.append(
            {
                "level": "critical",
                "code": "insufficient_cash",
                "message": "El ahorro disponible no cubre entrada y gastos estimados.",
            }
        )
    if effort is not None and effort > 35:
        alerts.append(
            {
                "level": "critical" if effort > 40 else "warning",
                "code": "high_effort",
                "message": "La cuota y las deudas superan el 35 % de la renta neta mensual.",
            }
        )
    if stressed_effort is not None and stressed_effort > 40:
        alerts.append(
            {
                "level": "critical" if stressed_effort > 45 else "warning",
                "code": "rate_stress",
                "message": "Una subida de tipos dejaría el esfuerzo por encima del 40 %.",
            }
        )
    if ltv is not None and ltv > 80:
        alerts.append(
            {
                "level": "critical" if ltv > 90 else "warning",
                "code": "high_ltv",
                "message": "La financiación supera el 80 % del precio de compra.",
            }
        )
    if remaining_savings >= 0 and scenario.monthly_living_costs_eur > 0 and emergency_months < 3:
        alerts.append(
            {
                "level": "warning",
                "code": "low_buffer",
                "message": "Tras la compra quedarían menos de tres meses de gastos como colchón.",
            }
        )

    critical = any(alert["level"] == "critical" for alert in alerts)
    status = "high_risk" if critical else ("review" if alerts else "balanced")
    return {
        "status": status,
        "alerts": alerts,
        "calculations": {
            "monthly_payment_eur": rounded(monthly_payment),
            "stressed_monthly_payment_eur": rounded(stressed_payment),
            "effort_pct": rounded(effort),
            "stressed_effort_pct": rounded(stressed_effort),
            "committed_income_pct": rounded(committed_income),
            "ltv_pct": rounded(ltv),
            "purchase_costs_eur": rounded(purchase_costs),
            "cash_required_eur": rounded(cash_required),
            "remaining_savings_eur": rounded(remaining_savings),
            "emergency_buffer_months": rounded(emergency_months),
            "total_repayment_eur": rounded(total_repayment),
            "total_interest_eur": rounded(total_repayment - scenario.mortgage_amount_eur),
            "mortgage_spread_pp": rounded(
                scenario.annual_apr_pct - scenario.euribor_pct
                if scenario.euribor_pct is not None
                else None
            ),
            "apr_vs_market_pp": rounded(
                scenario.annual_apr_pct - scenario.market_apr_pct
                if scenario.market_apr_pct is not None
                else None
            ),
        },
        "scenario": asdict(scenario),
        "disclaimer": (
            "Orientación educativa basada en los datos aportados; no sustituye la FEIN, "
            "el asesoramiento financiero ni la evaluación de solvencia de la entidad."
        ),
    }
