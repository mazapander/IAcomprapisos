from datetime import date
from decimal import Decimal

import httpx
import pytest

from app.ingestion.base import SourceRecord
from app.ingestion.registry import available_sources
from app.ingestion.sources.bde_mortgage_market import (
    BDEMortgageMarketIngestion,
    parse_bde_table_series,
    validate_bde_series_identity,
)
from app.ingestion.sources.ine_common import fetch_ine_payload, parse_period
from app.ingestion.sources.ine_income import INEHouseholdIncomeIngestion
from app.ingestion.sources.mivau_appraisal import mivau_geography


def test_annual_ine_period_is_normalized_to_first_day_of_year() -> None:
    assert parse_period({"T3_Periodo": "2023"}, "annual") == date(2023, 1, 1)
    assert parse_period({"Anyo": 2022, "FK_Periodo": 1}, "annual") == date(
        2022, 1, 1
    )


def test_mivau_appraisal_names_are_canonicalised_for_national_ccaa_and_province() -> None:
    assert mivau_geography("TOTAL NACIONAL") == "ES"
    assert mivau_geography("Asturias (Principado de )") == "CCAA:03"
    assert mivau_geography("Madrid (Comunidad de)") == "CCAA:13"
    assert mivau_geography("Coruña (A)") == "PROV:15"
    assert mivau_geography("Palmas (Las)") == "PROV:35"


@pytest.mark.asyncio
async def test_ine_redirect_is_retried_on_verified_https_destination() -> None:
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.path.endswith("/53689"):
            return httpx.Response(
                301,
                headers={"location": "/wstempus/js/ES/DATOS_TABLA/53689/"},
            )
        return httpx.Response(200, json=[{"COD": "income"}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        payload, resolved_url = await fetch_ine_payload(
            client,
            "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/53689",
            {"tip": "AM"},
        )

    assert payload == [{"COD": "income"}]
    assert resolved_url.endswith("/53689/")
    assert requests == [
        "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/53689?tip=AM",
        "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/53689/",
    ]


@pytest.mark.asyncio
async def test_ine_payload_retries_a_transient_protocol_disconnect() -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.RemoteProtocolError("server disconnected")
        return httpx.Response(200, json=[{"COD": "income"}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        payload, _ = await fetch_ine_payload(
            client,
            "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/53689",
            {"tip": "AM"},
        )

    assert payload == [{"COD": "income"}]
    assert attempts == 2


def test_ine_redirect_rejects_an_untrusted_host() -> None:
    from app.ingestion.sources.ine_common import _secure_ine_redirect

    with pytest.raises(ValueError, match="not allowlisted"):
        _secure_ine_redirect("https://servicios.ine.es/source", "https://example.test/data")


def test_household_income_transformation() -> None:
    records = [
        SourceRecord(
            dataset="ine_table_53689",
            period=date(2023, 1, 1),
            geography_code="PROV:24",
            payload={
                "table_id": "53689",
                "series_code": "income-household",
                "series_name": "24 León; Renta neta media por hogar",
                "observation": {"Valor": "38.326"},
            },
        ),
        SourceRecord(
            dataset="ine_table_53687",
            period=date(2023, 1, 1),
            geography_code="PROV:24",
            payload={
                "table_id": "53687",
                "series_code": "income-salary",
                "series_name": "24 León; Salario",
                "observation": {"Valor": "61,7"},
            },
        ),
    ]

    result = INEHouseholdIncomeIngestion().transform(records)
    by_code = {item.indicator_code: item for item in result}

    assert by_code["income_net_mean_household_eur"].value == Decimal("38326")
    assert by_code["income_net_mean_household_eur"].unit == "eur_year"
    assert by_code["income_share_salary_pct"].value == Decimal("61.7")
    assert by_code["income_share_salary_pct"].unit == "percent"
    assert all(item.frequency == "annual" for item in result)


def test_bde_multi_series_parser_selects_mortgage_columns() -> None:
    aprc_csv = """ALIAS DE LA SERIE;Vivienda;Consumo
FRECUENCIA;MENSUAL;MENSUAL
MAY 2026;2,92;7,10
JUN 2026;2,94;7,20
"""
    volume_csv = """ALIAS DE LA SERIE;Descubiertos;Vivienda total
FRECUENCIA;MENSUAL;MENSUAL
MAY 2026;1000;6857
JUN 2026;1200;8088
"""

    aprc = parse_bde_table_series(aprc_csv, series_index=0)
    volume = parse_bde_table_series(volume_csv, series_index=1)

    assert aprc[-1][0] == date(2026, 6, 1)
    assert aprc[-1][1] == Decimal("2.94")
    assert aprc[-1][2]["series_alias"] == "Vivienda"
    assert volume[-1][0] == date(2026, 6, 1)
    assert volume[-1][1] == Decimal("8088")
    assert volume[-1][2]["series_alias"] == "Vivienda total"


def test_bde_series_identity_fails_closed_if_upstream_columns_change() -> None:
    observations = [(date(2026, 6, 1), Decimal("2.94"), {"series_alias": "BE_19_6.2"})]

    try:
        validate_bde_series_identity(observations, "mortgage_new_business_aprc_pct")
    except ValueError as exc:
        assert "expected BE_19_6.1" in str(exc)
    else:
        raise AssertionError("A changed Banco de España series must be rejected")


def test_bde_mortgage_market_transformation_preserves_mir_caveat() -> None:
    records = [
        SourceRecord(
            dataset="bde_be1906_mortgage_aprc",
            period=date(2026, 6, 1),
            geography_code="ES",
            payload={
                "indicator_code": "mortgage_new_business_aprc_pct",
                "value": "2.94",
                "unit": "percent",
                "download_url": "https://example.test/be1906.csv",
                "series_metadata": {"series_alias": "Vivienda"},
            },
        ),
        SourceRecord(
            dataset="bde_be1912_mortgage_volume",
            period=date(2026, 6, 1),
            geography_code="ES",
            payload={
                "indicator_code": "mortgage_new_business_volume_million_eur",
                "value": "8088",
                "unit": "million_eur",
                "download_url": "https://example.test/be1912.csv",
                "series_metadata": {"series_alias": "Vivienda total"},
            },
        ),
        SourceRecord(
            dataset="bde_be1904_mortgage_tedr_total",
            period=date(2026, 6, 1),
            geography_code="ES",
            payload={
                "indicator_code": "mortgage_new_business_tedr_pct",
                "value": "2.89",
                "unit": "percent",
                "download_url": "https://example.test/be1904.csv",
                "series_metadata": {"series_alias": "Vivienda tipo medio ponderado"},
            },
        ),
    ]

    result = BDEMortgageMarketIngestion().transform(records)
    by_code = {item.indicator_code: item for item in result}

    assert by_code["mortgage_new_business_aprc_pct"].value == Decimal("2.94")
    assert by_code["mortgage_new_business_volume_million_eur"].value == Decimal(
        "8088"
    )
    assert by_code["mortgage_new_business_tedr_pct"].value == Decimal("2.89")
    assert all(item.metadata["includes_renegotiations"] is True for item in result)


def test_new_sources_are_registered() -> None:
    sources = available_sources()
    assert "ine_household_income" in sources
    assert "bde_mortgage_market" in sources
