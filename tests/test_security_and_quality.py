from datetime import date
from decimal import Decimal

import pytest

from app.ingestion.base import IndicatorValue
from app.core.config import Settings
from app.ingestion.quality import validate_indicator_batch
from app.ingestion.security import validate_source_url


def indicator(**changes) -> IndicatorValue:
    values = {
        "indicator_code": "mortgages_housing_total",
        "geography_code": "PROV:24",
        "period": date(2026, 6, 1),
        "frequency": "monthly",
        "value": Decimal(100),
        "unit": "mortgages",
    }
    values.update(changes)
    return IndicatorValue(**values)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.bde.es/data.csv",
        "https://127.0.0.1/private",
        "https://169.254.169.254/latest/meta-data",
        "https://evil.example/data.csv",
        "https://user:password@www.bde.es/data.csv",
    ],
)
def test_source_url_validation_blocks_ssrf_vectors(url: str) -> None:
    with pytest.raises(ValueError):
        validate_source_url(url)


def test_source_url_validation_accepts_official_subdomains() -> None:
    assert validate_source_url("https://servicios.ine.es/data.json")
    assert validate_source_url("https://www.bde.es/data.csv")


def test_production_settings_require_secure_cookies_and_https() -> None:
    with pytest.raises(ValueError, match="ANALYTICS_COOKIE_SECURE"):
        Settings(app_env="production", api_key="a-real-secret", analytics_cookie_secure=False)
    with pytest.raises(ValueError, match="PUBLIC_BASE_URL"):
        Settings(
            app_env="production",
            api_key="a-real-secret",
            analytics_cookie_secure=True,
            public_base_url="http://example.test",
        )


def test_indicator_quality_rejects_conflicting_duplicates() -> None:
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        validate_indicator_batch([indicator(), indicator(value=Decimal(101))])


def test_indicator_quality_rejects_invalid_ranges_and_geography() -> None:
    with pytest.raises(ValueError, match="Invalid geography"):
        validate_indicator_batch([indicator(geography_code="24")])
    with pytest.raises(ValueError, match="Negative value"):
        validate_indicator_batch([indicator(value=Decimal(-1))])
    with pytest.raises(ValueError, match="Income share"):
        validate_indicator_batch(
            [
                indicator(
                    indicator_code="income_share_salary_pct",
                    value=Decimal(101),
                    unit="percent",
                )
            ]
        )
