import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings
from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord
from app.ingestion.sources.bde_euribor import (
    _fold,
    _parse_decimal,
    _parse_period,
    _read_rows,
)

logger = logging.getLogger(__name__)

BDE_MORTGAGE_RATES_PAGE = (
    "https://www.bde.es/webbe/es/estadisticas/temas/instituciones-financieras.html"
)
BDE_MORTGAGE_APRC_CSV = (
    "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1906.csv"
)
BDE_MORTGAGE_VOLUME_CSV = (
    "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1912.csv"
)

_METADATA_KEYS = {
    "alias de la serie": "series_alias",
    "numero secuencial": "sequential_number",
    "nombre de la serie/codigo de la serie": "series_name_code",
    "descripcion de la serie": "series_description",
    "descripcion de las unidades": "unit_description",
    "frecuencia": "frequency_description",
}


def parse_bde_table_series(
    content: str,
    series_index: int,
) -> list[tuple[date, Decimal, dict[str, Any]]]:
    """Parse one Banco de España series from a multi-series CSV table.

    ``series_index`` is zero-based among the numeric series and excludes the date
    column. Banco de España table CSVs contain metadata rows first and monthly
    observations afterwards; keeping the selected series metadata makes the mapping
    auditable if the upstream table evolves.
    """
    if series_index < 0:
        raise ValueError("series_index must be non-negative")

    rows = _read_rows(content)
    value_column = series_index + 1
    metadata: dict[str, Any] = {"series_index": series_index}
    observations: list[tuple[date, Decimal, dict[str, Any]]] = []

    for row in rows:
        if not row:
            continue

        label = _fold(row[0])
        for source_label, metadata_key in _METADATA_KEYS.items():
            if label == source_label and value_column < len(row):
                metadata[metadata_key] = row[value_column]
                break

        if value_column >= len(row):
            continue

        try:
            period = _parse_period(row[0])
            value = _parse_decimal(row[value_column])
        except ValueError:
            continue

        observations.append((period, value, dict(metadata)))

    if not observations:
        raise ValueError(
            f"No Banco de España observations parsed for series_index={series_index}"
        )
    return observations


async def _fetch_csv(client: httpx.AsyncClient, url: str) -> tuple[str, httpx.Response]:
    response = await client.get(url)
    response.raise_for_status()
    encoding = response.encoding or "utf-8"
    content = response.content.decode(encoding, errors="replace").lstrip("\ufeff")
    return content, response


class BDEMortgageMarketIngestion(BaseIngestion):
    """Mortgage rates and volumes actually agreed in new monthly business.

    Under the monetary and financial institutions (MIR) methodology, new business
    includes renegotiations of existing contracts. That caveat is persisted in each
    raw/analytics record so the public product does not present the series as purely
    first-time mortgage originations.
    """

    source = "bde_mortgage_market"

    async def extract(self, parameters: dict[str, Any]) -> list[SourceRecord]:
        aprc_url = parameters.get("aprc_url", BDE_MORTGAGE_APRC_CSV)
        volume_url = parameters.get("volume_url", BDE_MORTGAGE_VOLUME_CSV)

        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            aprc_content, aprc_response = await _fetch_csv(client, aprc_url)
            volume_content, volume_response = await _fetch_csv(client, volume_url)

        # Table 19.6: housing is the first numeric series.
        aprc_observations = parse_bde_table_series(aprc_content, series_index=0)
        # Table 19.12: housing total is the second numeric series, after overdrafts/
        # revolving-credit facilities.
        volume_observations = parse_bde_table_series(volume_content, series_index=1)

        retrieved_at = datetime.now(UTC)
        date_from = (
            date.fromisoformat(parameters["date_from"])
            if parameters.get("date_from")
            else None
        )
        date_to = (
            date.fromisoformat(parameters["date_to"])
            if parameters.get("date_to")
            else None
        )

        records: list[SourceRecord] = []
        specs = (
            (
                aprc_observations,
                aprc_response,
                "bde_be1906_mortgage_aprc",
                "mortgage_new_business_aprc_pct",
                "percent",
            ),
            (
                volume_observations,
                volume_response,
                "bde_be1912_mortgage_volume",
                "mortgage_new_business_volume_million_eur",
                "million_eur",
            ),
        )

        for observations, response, dataset, indicator_code, unit in specs:
            for period, value, series_metadata in observations:
                if date_from and period < date_from:
                    continue
                if date_to and period > date_to:
                    continue

                records.append(
                    SourceRecord(
                        dataset=dataset,
                        external_id=f"{indicator_code}:{period.isoformat()}",
                        period=period,
                        geography_code="ES",
                        observed_at=retrieved_at,
                        payload={
                            "provider": "Banco de España",
                            "source_page": BDE_MORTGAGE_RATES_PAGE,
                            "download_url": str(response.url),
                            "content_type": response.headers.get("content-type"),
                            "http_status": response.status_code,
                            "indicator_code": indicator_code,
                            "period": period.isoformat(),
                            "value": str(value),
                            "unit": unit,
                            "frequency": "monthly",
                            "new_business_definition": "MIR",
                            "includes_renegotiations": True,
                            "retrieved_at": retrieved_at.isoformat(),
                            "series_metadata": series_metadata,
                        },
                    )
                )

        logger.info(
            "Banco de España mortgage market parsed aprc=%d volume=%d records=%d",
            len(aprc_observations),
            len(volume_observations),
            len(records),
        )
        return records

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        result: list[IndicatorValue] = []
        for record in records:
            if not record.period or not record.geography_code:
                continue
            indicator_code = record.payload.get("indicator_code")
            unit = record.payload.get("unit")
            if not indicator_code or not unit:
                continue

            result.append(
                IndicatorValue(
                    indicator_code=str(indicator_code),
                    geography_code=record.geography_code,
                    period=record.period,
                    frequency="monthly",
                    value=Decimal(str(record.payload["value"])),
                    unit=str(unit),
                    metadata={
                        "dataset": record.dataset,
                        "download_url": record.payload.get("download_url"),
                        "series_metadata": record.payload.get("series_metadata"),
                        "new_business_definition": "MIR",
                        "includes_renegotiations": True,
                    },
                )
            )
        return result
