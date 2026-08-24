from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.analytics.derived import ObservationPoint, annual_change_pct, rounded


@dataclass(frozen=True)
class ObservatorySeriesSpec:
    code: str
    label: str
    group: str
    description: str
    indicator_code: str


OBSERVATORY_SERIES: tuple[ObservatorySeriesSpec, ...] = (
    ObservatorySeriesSpec(
        code="house_price_index",
        label="Precio de la vivienda",
        group="prices",
        description="Índice oficial de precios de compraventa de vivienda.",
        indicator_code="house_price_index",
    ),
    ObservatorySeriesSpec(
        code="appraisal_price_eur_m2",
        label="Valor tasado medio",
        group="prices",
        description="Valor tasado medio por metro cuadrado.",
        indicator_code="appraisal_price_eur_m2",
    ),
    ObservatorySeriesSpec(
        code="mortgages_housing_total",
        label="Hipotecas constituidas",
        group="mortgages",
        description="Número mensual de hipotecas constituidas sobre viviendas.",
        indicator_code="mortgages_housing_total",
    ),
    ObservatorySeriesSpec(
        code="average_mortgage_amount_eur",
        label="Importe medio por hipoteca",
        group="mortgages",
        description="Importe total dividido entre el número de hipotecas del mismo periodo.",
        indicator_code="average_mortgage_amount_eur",
    ),
    ObservatorySeriesSpec(
        code="mortgage_new_business_volume_million_eur",
        label="Nueva financiación",
        group="mortgages",
        description="Volumen mensual de nuevo negocio hipotecario, incluidas renegociaciones.",
        indicator_code="mortgage_new_business_volume_million_eur",
    ),
    ObservatorySeriesSpec(
        code="euribor_12m_pct",
        label="Euríbor a 12 meses",
        group="rates",
        description="Referencia mensual utilizada habitualmente en hipotecas variables.",
        indicator_code="euribor_12m_pct",
    ),
    ObservatorySeriesSpec(
        code="mortgage_new_business_tedr_pct",
        label="Tipo efectivo nuevas hipotecas",
        group="rates",
        description="TEDR medio de las nuevas operaciones hipotecarias para vivienda.",
        indicator_code="mortgage_new_business_tedr_pct",
    ),
    ObservatorySeriesSpec(
        code="mortgage_new_business_aprc_pct",
        label="TAE nuevas hipotecas",
        group="rates",
        description="Coste anual equivalente medio de las nuevas operaciones hipotecarias.",
        indicator_code="mortgage_new_business_aprc_pct",
    ),
)

OBSERVATORY_INDICATOR_CODES = {
    spec.indicator_code
    for spec in OBSERVATORY_SERIES
    if spec.indicator_code != "average_mortgage_amount_eur"
} | {"mortgages_housing_amount_thousand_eur"}

GROUP_METADATA = {
    "prices": {
        "label": "Precios",
        "description": "Cuánto cuesta la vivienda y cómo cambia su valoración.",
    },
    "mortgages": {
        "label": "Hipotecas",
        "description": "Cuántas operaciones se firman y qué volumen se financia.",
    },
    "rates": {
        "label": "Tipos y tasas",
        "description": "Referencias y coste efectivo del crédito hipotecario.",
    },
}


def _deduplicated_series(
    observations: list[ObservationPoint], indicator_code: str
) -> list[ObservationPoint]:
    by_period = {
        row.period: row
        for row in observations
        if row.geography_code == "ES" and row.indicator_code == indicator_code
    }
    return [by_period[period] for period in sorted(by_period)]


def _average_mortgage_amount(observations: list[ObservationPoint]) -> list[ObservationPoint]:
    counts = {
        row.period: row
        for row in _deduplicated_series(observations, "mortgages_housing_total")
    }
    amounts = _deduplicated_series(observations, "mortgages_housing_amount_thousand_eur")
    result: list[ObservationPoint] = []
    for amount in amounts:
        count = counts.get(amount.period)
        if count is None or count.value <= 0:
            continue
        result.append(
            ObservationPoint(
                indicator_code="average_mortgage_amount_eur",
                geography_code="ES",
                period=amount.period,
                value=amount.value * Decimal(1000) / count.value,
                unit="eur",
                source=amount.source,
            )
        )
    return result


def _year_ago(series: list[ObservationPoint]) -> ObservationPoint | None:
    if not series:
        return None
    latest = series[-1]
    target = date(latest.period.year - 1, latest.period.month, 1)
    return next((row for row in reversed(series[:-1]) if row.period == target), None)


def _change(current: ObservationPoint, previous: ObservationPoint | None) -> dict:
    if previous is None:
        return {"value": None, "unit": None}
    if current.unit == "percent":
        return {"value": rounded(current.value - previous.value), "unit": "percentage_points"}
    return {"value": rounded(annual_change_pct(current.value, previous.value)), "unit": "percent"}


def _direction(current: ObservationPoint, previous: ObservationPoint | None) -> str | None:
    if previous is None:
        return None
    if current.value > previous.value:
        return "up"
    if current.value < previous.value:
        return "down"
    return "flat"


def _serialize_series(spec: ObservatorySeriesSpec, series: list[ObservationPoint]) -> dict:
    latest = series[-1] if series else None
    previous = series[-2] if len(series) > 1 else None
    year_ago = _year_ago(series)
    return {
        "code": spec.code,
        "label": spec.label,
        "description": spec.description,
        "available": latest is not None,
        "latest": (
            {
                "value": rounded(latest.value),
                "unit": latest.unit,
                "period": latest.period,
                "source": latest.source,
            }
            if latest
            else None
        ),
        "change_previous": _change(latest, previous) if latest else {"value": None, "unit": None},
        "change_year_on_year": (
            _change(latest, year_ago) if latest else {"value": None, "unit": None}
        ),
        "direction": _direction(latest, previous) if latest else None,
        "points": [
            {"period": row.period, "value": rounded(row.value)} for row in series
        ],
    }


def build_national_observatory(
    observations: list[ObservationPoint], max_points: int = 120
) -> dict:
    """Build the public national dashboard from traceable stored observations."""
    average_amount = _average_mortgage_amount(observations)
    groups = {
        code: {**metadata, "series": []}
        for code, metadata in GROUP_METADATA.items()
    }
    latest_periods: list[date] = []
    available = 0

    for spec in OBSERVATORY_SERIES:
        series = (
            average_amount
            if spec.indicator_code == "average_mortgage_amount_eur"
            else _deduplicated_series(observations, spec.indicator_code)
        )[-max_points:]
        serialized = _serialize_series(spec, series)
        groups[spec.group]["series"].append(serialized)
        if series:
            available += 1
            latest_periods.append(series[-1].period)

    return {
        "geography_code": "ES",
        "groups": groups,
        "coverage": {
            "available_series": available,
            "total_series": len(OBSERVATORY_SERIES),
            "latest_period": max(latest_periods) if latest_periods else None,
        },
        "methodology": {
            "change_for_rates": "percentage_points",
            "change_for_amounts": "percent",
            "average_mortgage_amount": (
                "importe total de hipotecas sobre viviendas / número de hipotecas "
                "del mismo periodo"
            ),
            "notice": (
                "Cada serie conserva su fuente y último periodo disponible. "
                "La ausencia de datos se muestra y no se sustituye por estimaciones."
            ),
        },
    }
