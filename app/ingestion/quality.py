import re
from decimal import Decimal

from app.ingestion.base import IndicatorValue

GEOGRAPHY_PATTERN = re.compile(r"^(ES|CCAA:\d{2}|PROV:\d{2}|MUN:\d{5}|NAME:.+)$")
NON_NEGATIVE_UNITS = {
    "eur",
    "eur_m2",
    "eur_month",
    "eur_m2_month",
    "eur_year",
    "million_eur",
    "thousand_eur",
    "mortgages",
    "transactions",
    "index_2025_100",
}


def validate_indicator_batch(items: list[IndicatorValue]) -> None:
    """Fail an ingestion before writing internally inconsistent observations."""
    seen: dict[tuple[str, str, object], tuple[Decimal, str]] = {}
    for item in items:
        if not GEOGRAPHY_PATTERN.fullmatch(item.geography_code):
            raise ValueError(f"Invalid geography code: {item.geography_code}")
        if not item.value.is_finite():
            raise ValueError(f"Non-finite value for {item.indicator_code}")
        if item.unit in NON_NEGATIVE_UNITS and item.value < 0:
            raise ValueError(f"Negative value for non-negative indicator {item.indicator_code}")
        if item.indicator_code.startswith("income_share_") and not 0 <= item.value <= 100:
            raise ValueError(f"Income share outside [0, 100]: {item.indicator_code}")
        if item.unit == "percent" and not Decimal("-20") <= item.value <= Decimal("200"):
            raise ValueError(f"Percentage outside safety bounds: {item.indicator_code}")

        key = (item.indicator_code, item.geography_code, item.period)
        signature = (item.value, item.unit)
        previous = seen.get(key)
        if previous is not None and previous != signature:
            raise ValueError(f"Conflicting duplicate observation in one batch: {key}")
        seen[key] = signature
