from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

TWO_PLACES = Decimal("0.01")


def rounded(value: Decimal | None, places: Decimal = TWO_PLACES) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(places, rounding=ROUND_HALF_UP)


def annual_change_pct(current: Decimal, previous: Decimal) -> Decimal | None:
    if previous == 0:
        return None
    return (current / previous - 1) * 100


def mortgage_spread_pp(apr_pct: Decimal, euribor_pct: Decimal) -> Decimal:
    return apr_pct - euribor_pct


def mortgage_payment(
    principal_eur: Decimal,
    annual_rate_pct: Decimal,
    term_years: int,
) -> Decimal | None:
    if principal_eur <= 0 or term_years <= 0 or annual_rate_pct < 0:
        return None
    months = term_years * 12
    monthly_rate = annual_rate_pct / Decimal(1200)
    if monthly_rate == 0:
        return principal_eur / months
    factor = (Decimal(1) + monthly_rate) ** months
    return principal_eur * monthly_rate * factor / (factor - 1)


def mortgage_effort_pct(
    price_eur_m2: Decimal,
    annual_household_income_eur: Decimal,
    annual_rate_pct: Decimal,
    home_size_m2: Decimal,
    ltv_pct: Decimal,
    term_years: int,
) -> Decimal | None:
    if annual_household_income_eur <= 0 or home_size_m2 <= 0 or not 0 < ltv_pct <= 100:
        return None
    principal = price_eur_m2 * home_size_m2 * ltv_pct / 100
    payment = mortgage_payment(principal, annual_rate_pct, term_years)
    if payment is None:
        return None
    return payment / (annual_household_income_eur / 12) * 100


def price_to_income_years(
    price_eur_m2: Decimal,
    annual_household_income_eur: Decimal,
    home_size_m2: Decimal,
) -> Decimal | None:
    if annual_household_income_eur <= 0 or home_size_m2 <= 0:
        return None
    return price_eur_m2 * home_size_m2 / annual_household_income_eur


def price_to_rent_years(price_eur_m2: Decimal, monthly_rent_eur_m2: Decimal) -> Decimal | None:
    if monthly_rent_eur_m2 <= 0:
        return None
    return price_eur_m2 / (monthly_rent_eur_m2 * 12)


def income_adjusted_price_change_pct(
    current_price: Decimal,
    previous_price: Decimal,
    current_income: Decimal,
    previous_income: Decimal,
) -> Decimal | None:
    if previous_price <= 0 or current_income <= 0 or previous_income <= 0:
        return None
    current_ratio = current_price / current_income
    previous_ratio = previous_price / previous_income
    return annual_change_pct(current_ratio, previous_ratio)


def percentile_rank(current: Decimal, history: Iterable[Decimal]) -> Decimal | None:
    values = list(history)
    if not values:
        return None
    at_or_below = sum(1 for value in values if value <= current)
    return Decimal(at_or_below) / Decimal(len(values)) * 100


@dataclass(frozen=True)
class ObservationPoint:
    indicator_code: str
    geography_code: str
    period: date
    value: Decimal
    unit: str
    source: str


@dataclass(frozen=True)
class MarketAssumptions:
    home_size_m2: Decimal = Decimal(90)
    ltv_pct: Decimal = Decimal(80)
    term_years: int = 25
    fallback_mortgage_spread_pp: Decimal = Decimal(1)


INDICATOR_ALIASES: dict[str, tuple[str, ...]] = {
    "price": ("appraisal_price_eur_m2",),
    "income": (
        "income_net_mean_household_eur",
        "annual_household_net_income_eur",
        "household_net_income_annual_eur",
        "household_net_income_eur",
        "net_household_income_eur",
    ),
    "salary_share": (
        "income_share_salary_pct",
        "salary_income_weight_pct",
        "salary_income_share_pct",
        "household_salary_share_pct",
    ),
    "mortgages": ("mortgages_housing_total",),
    "financing": (
        "mortgage_new_business_volume_million_eur",
        "new_mortgage_financing_eur",
        "new_mortgage_volume_eur",
        "mortgages_housing_amount_thousand_eur",
    ),
    "mortgage_apr": (
        "mortgage_new_business_aprc_pct",
        "new_mortgage_apr_pct",
        "new_mortgage_tae_pct",
        "mortgage_new_business_apr_pct",
        "mortgage_interest_rate_pct",
    ),
    "mortgage_tedr": ("mortgage_new_business_tedr_pct",),
    "mortgage_tedr_variable": ("mortgage_new_business_tedr_up_to_1y_pct",),
    "euribor": ("euribor_12m_pct",),
    "rent_m2": ("rent_price_median_eur_m2", "rent_price_eur_m2"),
}


def _series(
    observations: Iterable[ObservationPoint],
    key: str,
    geography_code: str,
) -> list[ObservationPoint]:
    rows = list(observations)
    for indicator_code in INDICATOR_ALIASES[key]:
        local = [
            row
            for row in rows
            if row.indicator_code == indicator_code and row.geography_code == geography_code
        ]
        if local:
            return sorted(local, key=lambda row: row.period)
        national = [
            row
            for row in rows
            if row.indicator_code == indicator_code and row.geography_code == "ES"
        ]
        if national:
            return sorted(national, key=lambda row: row.period)
    return []


def _previous_year(series: list[ObservationPoint]) -> ObservationPoint | None:
    if len(series) < 2:
        return None
    latest = series[-1]
    target = date(latest.period.year - 1, latest.period.month, 1)
    return next((row for row in reversed(series[:-1]) if row.period == target), None)


def _latest_at_or_before(series: list[ObservationPoint], period: date) -> ObservationPoint | None:
    candidates = [row for row in series if row.period <= period]
    return candidates[-1] if candidates else None


def _metric(row: ObservationPoint | None, value: Decimal | None = None) -> dict:
    if row is None or (value is None and row.value is None):
        return {"value": None, "unit": None, "period": None, "source": None}
    return {
        "value": rounded(row.value if value is None else value),
        "unit": row.unit,
        "period": row.period,
        "source": row.source,
        "indicator_code": row.indicator_code,
        "geography_code": row.geography_code,
    }


def _derived_metric(value: Decimal | None, unit: str, inputs: list[str]) -> dict:
    return {"value": rounded(value), "unit": unit, "inputs": inputs}


def build_market_summary(
    observations: Iterable[ObservationPoint],
    geography_code: str,
    assumptions: MarketAssumptions,
) -> dict:
    rows = list(observations)
    series = {key: _series(rows, key, geography_code) for key in INDICATOR_ALIASES}
    latest = {key: values[-1] if values else None for key, values in series.items()}

    mortgages_previous = _previous_year(series["mortgages"])
    mortgages_yoy = (
        annual_change_pct(latest["mortgages"].value, mortgages_previous.value)
        if latest["mortgages"] and mortgages_previous
        else None
    )

    financing = latest["financing"]
    financing_value = financing.value if financing else None
    if financing:
        if financing.indicator_code == "mortgages_housing_amount_thousand_eur":
            financing_value *= 1000
        elif financing.indicator_code == "mortgage_new_business_volume_million_eur":
            financing_value *= 1_000_000

    apr = latest["mortgage_apr"]
    tedr = latest["mortgage_tedr"]
    variable_tedr = latest["mortgage_tedr_variable"]
    euribor = latest["euribor"]
    rate_for_effort = tedr.value if tedr else None
    rate_basis = "observed_tedr"
    if rate_for_effort is None and euribor:
        rate_for_effort = euribor.value + assumptions.fallback_mortgage_spread_pp
        rate_basis = "euribor_plus_assumed_spread"

    price = latest["price"]
    income = latest["income"]
    rent = latest["rent_m2"]
    effort = (
        mortgage_effort_pct(
            price.value,
            income.value,
            rate_for_effort,
            assumptions.home_size_m2,
            assumptions.ltv_pct,
            assumptions.term_years,
        )
        if price and income and rate_for_effort is not None
        else None
    )
    price_income = (
        price_to_income_years(price.value, income.value, assumptions.home_size_m2)
        if price and income
        else None
    )
    price_rent = price_to_rent_years(price.value, rent.value) if price and rent else None
    spread = (
        mortgage_spread_pp(variable_tedr.value, euribor.value)
        if variable_tedr and euribor
        else None
    )

    income_previous = _previous_year(series["income"])
    aligned_price = _latest_at_or_before(series["price"], income.period) if income else None
    price_previous = (
        _latest_at_or_before(series["price"], income_previous.period)
        if income_previous
        else None
    )
    adjusted_change = (
        income_adjusted_price_change_pct(
            aligned_price.value,
            price_previous.value,
            income.value,
            income_previous.value,
        )
        if aligned_price and price_previous and income and income_previous
        else None
    )

    price_income_history: list[Decimal] = []
    for price_point in series["price"]:
        income_point = _latest_at_or_before(series["income"], price_point.period)
        if income_point:
            value = price_to_income_years(
                price_point.value, income_point.value, assumptions.home_size_m2
            )
            if value is not None:
                price_income_history.append(value)

    price_rent_history: list[Decimal] = []
    for price_point in series["price"]:
        rent_point = _latest_at_or_before(series["rent_m2"], price_point.period)
        if rent_point:
            value = price_to_rent_years(price_point.value, rent_point.value)
            if value is not None:
                price_rent_history.append(value)

    product_fields = [
        price,
        income,
        latest["salary_share"],
        latest["mortgages"],
        apr,
        tedr,
        financing,
        euribor,
    ]
    available = sum(value is not None for value in product_fields) + int(effort is not None)
    missing = [key for key, value in latest.items() if key not in {"rent_m2"} and value is None]

    return {
        "geography_code": geography_code,
        "assumptions": {
            "home_size_m2": assumptions.home_size_m2,
            "ltv_pct": assumptions.ltv_pct,
            "term_years": assumptions.term_years,
            "fallback_mortgage_spread_pp": assumptions.fallback_mortgage_spread_pp,
            "effort_rate_basis": rate_basis if effort is not None else None,
        },
        "market_card": {
            "price_eur_m2": _metric(price),
            "annual_household_net_income_eur": _metric(income),
            "salary_income_weight_pct": _metric(latest["salary_share"]),
            "mortgages_yoy_pct": _derived_metric(
                mortgages_yoy,
                "percent",
                [latest["mortgages"].indicator_code] if latest["mortgages"] else [],
            ),
            "new_mortgage_apr_pct": _metric(apr),
            "new_mortgage_tedr_pct": _metric(tedr),
            "new_financing_volume_eur": _metric(financing, financing_value),
            "euribor_12m_pct": _metric(euribor),
            "estimated_purchase_effort_pct": _derived_metric(
                effort,
                "percent",
                [
                    code
                    for code in [
                        price.indicator_code if price else None,
                        income.indicator_code if income else None,
                        tedr.indicator_code
                        if tedr
                        else (euribor.indicator_code if euribor else None),
                    ]
                    if code
                ],
            ),
        },
        "derived": {
            "mortgage_spread_pp": _derived_metric(
                spread,
                "percentage_points",
                [
                    code
                    for code in [
                        variable_tedr.indicator_code if variable_tedr else None,
                        euribor.indicator_code if euribor else None,
                    ]
                    if code
                ],
            ),
            "price_to_income_years": _derived_metric(
                price_income,
                "years",
                [
                    code
                    for code in [
                        price.indicator_code if price else None,
                        income.indicator_code if income else None,
                    ]
                    if code
                ],
            ),
            "price_to_rent_years": _derived_metric(
                price_rent,
                "years",
                [
                    code
                    for code in [
                        price.indicator_code if price else None,
                        rent.indicator_code if rent else None,
                    ]
                    if code
                ],
            ),
            "income_adjusted_price_yoy_pct": _derived_metric(
                adjusted_change,
                "percent",
                [
                    code
                    for code in [
                        price.indicator_code if price else None,
                        income.indicator_code if income else None,
                    ]
                    if code
                ],
            ),
            "historical_percentiles": {
                "price": rounded(
                    percentile_rank(price.value, (row.value for row in series["price"]))
                )
                if price and len(series["price"]) >= 8
                else None,
                "price_to_income": rounded(percentile_rank(price_income, price_income_history))
                if price_income is not None and len(price_income_history) >= 8
                else None,
                "price_to_rent": rounded(percentile_rank(price_rent, price_rent_history))
                if price_rent is not None and len(price_rent_history) >= 8
                else None,
                "sample_sizes": {
                    "price": len(series["price"]),
                    "price_to_income": len(price_income_history),
                    "price_to_rent": len(price_rent_history),
                },
            },
        },
        "coverage": {
            "available_fields": available,
            "total_fields": 9,
            "ratio_pct": rounded(Decimal(available) / Decimal(9) * 100),
            "missing_inputs": missing,
        },
    }
