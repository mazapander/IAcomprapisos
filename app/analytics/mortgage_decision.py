from dataclasses import dataclass
from decimal import Decimal

from app.analytics.derived import mortgage_payment, rounded


@dataclass(frozen=True)
class MortgageScenario:
    property_price_eur: Decimal
    savings_eur: Decimal
    annual_net_household_income_eur: Decimal
    mortgage_amount_eur: Decimal
    annual_nominal_rate_pct: Decimal
    term_years: int
    rate_type: str = "fixed"
    annual_apr_pct: Decimal | None = None
    mixed_fixed_years: int | None = None
    variable_spread_pct: Decimal | None = None
    upfront_fees_eur: Decimal = Decimal(0)
    monthly_linked_costs_eur: Decimal = Decimal(0)
    existing_monthly_debt_eur: Decimal = Decimal(0)
    monthly_living_costs_eur: Decimal = Decimal(0)
    purchase_cost_pct: Decimal = Decimal(10)
    stress_rate_increase_pp: Decimal = Decimal(2)
    market_apr_pct: Decimal | None = None
    euribor_pct: Decimal | None = None


@dataclass(frozen=True)
class PurchaseBudgetScenario:
    annual_net_household_income_eur: Decimal
    savings_eur: Decimal
    annual_nominal_rate_pct: Decimal
    term_years: int = 25
    existing_monthly_debt_eur: Decimal = Decimal(0)
    monthly_living_costs_eur: Decimal = Decimal(0)
    purchase_cost_pct: Decimal = Decimal(10)
    max_effort_pct: Decimal = Decimal(35)
    max_ltv_pct: Decimal = Decimal(80)
    reserve_months: int = 6


def _ratio_pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    return numerator / denominator * 100 if denominator > 0 else None


def _principal_from_payment(
    monthly_payment_eur: Decimal,
    annual_rate_pct: Decimal,
    term_years: int,
) -> Decimal:
    months = term_years * 12
    monthly_rate = annual_rate_pct / Decimal(1200)
    if monthly_rate == 0:
        return monthly_payment_eur * months
    factor = (Decimal(1) + monthly_rate) ** months
    return monthly_payment_eur * (factor - 1) / (monthly_rate * factor)


def _remaining_principal(
    principal_eur: Decimal,
    annual_rate_pct: Decimal,
    total_years: int,
    paid_months: int,
) -> Decimal:
    payment = mortgage_payment(principal_eur, annual_rate_pct, total_years)
    if payment is None:
        raise ValueError("The mortgage scenario cannot produce a monthly payment")
    monthly_rate = annual_rate_pct / Decimal(1200)
    if monthly_rate == 0:
        return principal_eur - payment * paid_months
    factor = (Decimal(1) + monthly_rate) ** paid_months
    return principal_eur * factor - payment * (factor - 1) / monthly_rate


def calculate_purchase_budget(scenario: PurchaseBudgetScenario) -> dict:
    """Estimate a prudent maximum purchase price without persisting personal inputs."""
    monthly_income = scenario.annual_net_household_income_eur / 12
    max_payment = monthly_income * scenario.max_effort_pct / 100 - scenario.existing_monthly_debt_eur
    reserve_eur = (
        scenario.monthly_living_costs_eur + scenario.existing_monthly_debt_eur
    ) * scenario.reserve_months
    usable_savings = max(Decimal(0), scenario.savings_eur - reserve_eur)

    if max_payment <= 0:
        max_loan = Decimal(0)
    else:
        max_loan = _principal_from_payment(
            max_payment,
            scenario.annual_nominal_rate_pct,
            scenario.term_years,
        )

    ltv_ratio = scenario.max_ltv_pct / 100
    purchase_cost_ratio = scenario.purchase_cost_pct / 100
    income_limited_price = max_loan / ltv_ratio
    cash_share = Decimal(1) - ltv_ratio + purchase_cost_ratio
    savings_limited_price = usable_savings / cash_share if cash_share > 0 else Decimal(0)
    max_purchase_price = max(Decimal(0), min(income_limited_price, savings_limited_price))
    limiting_factor = (
        "monthly_capacity" if income_limited_price <= savings_limited_price else "available_savings"
    )
    mortgage_amount = max_purchase_price * ltv_ratio
    estimated_payment = mortgage_payment(
        mortgage_amount,
        scenario.annual_nominal_rate_pct,
        scenario.term_years,
    ) or Decimal(0)
    cash_required = max_purchase_price * cash_share

    alerts: list[dict[str, str]] = []
    if max_payment <= 0:
        alerts.append(
            {
                "level": "critical",
                "code": "no_monthly_capacity",
                "message": "Las deudas actuales consumen el límite de esfuerzo elegido.",
            }
        )
    if usable_savings <= 0:
        alerts.append(
            {
                "level": "warning",
                "code": "savings_reserved",
                "message": "El ahorro disponible quedaría reservado como colchón de seguridad.",
            }
        )

    return {
        "status": "limited" if alerts else "estimated",
        "limiting_factor": limiting_factor,
        "alerts": alerts,
        "calculations": {
            "max_purchase_price_eur": rounded(max_purchase_price),
            "recommended_mortgage_eur": rounded(mortgage_amount),
            "estimated_monthly_payment_eur": rounded(estimated_payment),
            "cash_required_eur": rounded(cash_required),
            "reserved_savings_eur": rounded(reserve_eur),
            "remaining_savings_eur": rounded(scenario.savings_eur - cash_required),
            "max_monthly_payment_eur": rounded(max(Decimal(0), max_payment)),
        },
        "assumptions": {
            "max_effort_pct": scenario.max_effort_pct,
            "max_ltv_pct": scenario.max_ltv_pct,
            "purchase_cost_pct": scenario.purchase_cost_pct,
            "reserve_months": scenario.reserve_months,
            "amortization_method": "french_monthly",
        },
        "disclaimer": (
            "Presupuesto orientativo, no una aprobación bancaria. Impuestos, bonificaciones, "
            "tasación y criterios de riesgo pueden cambiar el importe financiable."
        ),
    }


def review_mortgage(scenario: MortgageScenario) -> dict:
    monthly_payment = mortgage_payment(
        scenario.mortgage_amount_eur,
        scenario.annual_nominal_rate_pct,
        scenario.term_years,
    )
    post_fixed_payment: Decimal | None = None
    if scenario.rate_type == "mixed":
        if (
            scenario.mixed_fixed_years is None
            or scenario.variable_spread_pct is None
            or scenario.euribor_pct is None
            or scenario.mixed_fixed_years >= scenario.term_years
        ):
            raise ValueError("The mixed mortgage scenario is incomplete")
        fixed_months = scenario.mixed_fixed_years * 12
        remaining_principal = _remaining_principal(
            scenario.mortgage_amount_eur,
            scenario.annual_nominal_rate_pct,
            scenario.term_years,
            fixed_months,
        )
        variable_rate = scenario.euribor_pct + scenario.variable_spread_pct
        post_fixed_payment = mortgage_payment(
            remaining_principal,
            variable_rate,
            scenario.term_years - scenario.mixed_fixed_years,
        )
        stressed_payment = mortgage_payment(
            remaining_principal,
            variable_rate + scenario.stress_rate_increase_pp,
            scenario.term_years - scenario.mixed_fixed_years,
        )
    else:
        stressed_rate = (
            scenario.annual_nominal_rate_pct + scenario.stress_rate_increase_pp
            if scenario.rate_type == "variable"
            else scenario.annual_nominal_rate_pct
        )
        stressed_payment = mortgage_payment(
            scenario.mortgage_amount_eur,
            stressed_rate,
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
    if scenario.rate_type == "mixed" and post_fixed_payment is not None:
        fixed_months = scenario.mixed_fixed_years * 12
        total_repayment = (
            monthly_payment * fixed_months
            + post_fixed_payment * (scenario.term_years * 12 - fixed_months)
        )
    else:
        total_repayment = monthly_payment * scenario.term_years * 12
    total_interest = total_repayment - scenario.mortgage_amount_eur
    linked_costs_total = scenario.monthly_linked_costs_eur * scenario.term_years * 12
    estimated_total_cost = total_interest + scenario.upfront_fees_eur + linked_costs_total

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
    if scenario.rate_type in {"variable", "mixed"} and stressed_effort is not None and stressed_effort > 40:
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
            "post_fixed_monthly_payment_eur": rounded(post_fixed_payment),
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
            "total_interest_eur": rounded(total_interest),
            "upfront_fees_eur": rounded(scenario.upfront_fees_eur),
            "linked_costs_total_eur": rounded(linked_costs_total),
            "estimated_total_cost_eur": rounded(estimated_total_cost),
            "mortgage_spread_pp": rounded(
                scenario.variable_spread_pct
                if scenario.rate_type == "mixed"
                else (
                    scenario.annual_nominal_rate_pct - scenario.euribor_pct
                    if scenario.rate_type == "variable" and scenario.euribor_pct is not None
                    else None
                )
            ),
            "apr_vs_market_pp": rounded(
                scenario.annual_apr_pct - scenario.market_apr_pct
                if scenario.annual_apr_pct is not None and scenario.market_apr_pct is not None
                else None
            ),
        },
        "assumptions": {
            "amortization_method": "french_monthly",
            "rate_type": scenario.rate_type,
            "mixed_fixed_years": scenario.mixed_fixed_years,
            "variable_spread_pct": scenario.variable_spread_pct,
            "stress_rate_increase_pp": scenario.stress_rate_increase_pp,
            "interest_total_excludes_fees": True,
            "estimated_total_cost_includes_declared_fees_and_linked_products": True,
        },
        "disclaimer": (
            "Orientación educativa basada en los datos aportados; no sustituye la FEIN, "
            "el asesoramiento financiero ni la evaluación de solvencia de la entidad."
        ),
    }
