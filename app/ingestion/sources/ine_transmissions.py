import logging
import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.core.config import settings
from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord

logger = logging.getLogger(__name__)

INE_TABLE_ID = "6150"
INE_TABLE_URL = "https://www.ine.es/jaxiT3/Tabla.htm?t=6150"
INE_API_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/6150"

INDICATOR_BY_CATEGORY = {
    "viviendas: total": "housing_sales_total",
    "vivienda nueva": "housing_sales_new",
    "vivienda usada": "housing_sales_used",
    "vivienda libre": "housing_sales_free_market",
    "vivienda protegida": "housing_sales_protected",
}

CCAA_NAMES = {
    "andalucia": "01", "aragon": "02", "asturias, principado de": "03",
    "balears, illes": "04", "canarias": "05", "cantabria": "06",
    "castilla y leon": "07", "castilla - la mancha": "08", "cataluna": "09",
    "comunitat valenciana": "10", "extremadura": "11", "galicia": "12",
    "madrid, comunidad de": "13", "murcia, region de": "14",
    "navarra, comunidad foral de": "15", "pais vasco": "16", "rioja, la": "17",
    "ceuta": "18", "melilla": "19",
}

PROVINCE_CODES = {
    "alava": "01", "araba/alava": "01", "albacete": "02", "alicante/alacant": "03",
    "almeria": "04", "avila": "05", "badajoz": "06", "balears, illes": "07",
    "barcelona": "08", "burgos": "09", "caceres": "10", "cadiz": "11",
    "castellon/castello": "12", "ciudad real": "13", "cordoba": "14", "coruna, a": "15",
    "cuenca": "16", "girona": "17", "granada": "18", "guadalajara": "19",
    "gipuzkoa": "20", "huelva": "21", "huesca": "22", "jaen": "23",
    "leon": "24", "lleida": "25", "rioja, la": "26", "lugo": "27",
    "madrid": "28", "malaga": "29", "murcia": "30", "navarra": "31",
    "ourense": "32", "asturias": "33", "palencia": "34", "palmas, las": "35",
    "pontevedra": "36", "salamanca": "37", "santa cruz de tenerife": "38",
    "cantabria": "39", "segovia": "40", "sevilla": "41", "soria": "42",
    "tarragona": "43", "teruel": "44", "toledo": "45", "valencia/valencia": "46",
    "valladolid": "47", "bizkaia": "48", "zamora": "49", "zaragoza": "50",
    "ceuta": "51", "melilla": "52",
}


def _fold(value: str) -> str:
    translation = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return re.sub(r"\s+", " ", value.translate(translation).strip()).lower()


def _geography_code(series_name: str) -> str | None:
    folded = _fold(series_name)
    if "total nacional" in folded:
        return "ES"
    for province_name, code in PROVINCE_CODES.items():
        if re.search(rf"(^|[.;|])\s*(?:{code}\s+)?{re.escape(province_name)}\s*($|[.;|])", folded):
            return f"PROV:{code}"
    for ccaa_name, code in CCAA_NAMES.items():
        if re.search(rf"(^|[.;|])\s*(?:{code}\s+)?{re.escape(ccaa_name)}\s*($|[.;|])", folded):
            return f"CCAA:{code}"
    return None


def _category(series_name: str) -> str | None:
    folded = _fold(series_name)
    for label, indicator in INDICATOR_BY_CATEGORY.items():
        if label in folded:
            return indicator
    return None


def _parse_ine_timestamp(value: Any) -> date | None:
    """Parse the INE ``Fecha`` field.

    The INE Tempus API returns ``Fecha`` either as a Unix epoch number (seconds
    or milliseconds) or as an ISO 8601 string such as
    ``"2026-04-01T00:00:00.000+02:00"``. This helper accepts both shapes and
    returns the first day of the corresponding month, or ``None`` if the value
    cannot be interpreted as a date.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        epoch = float(value) / (1000.0 if value > 10_000_000_000 else 1.0)
        parsed = datetime.fromtimestamp(epoch, tz=UTC)
        return date(parsed.year, parsed.month, 1)
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            epoch = float(text)
        except ValueError:
            return None
        epoch = epoch / (1000.0 if epoch > 10_000_000_000 else 1.0)
        parsed = datetime.fromtimestamp(epoch, tz=UTC)
    return date(parsed.year, parsed.month, 1)


def _period_from_observation(observation: dict[str, Any]) -> date:
    year = observation.get("Anyo") or observation.get("year")
    period_label = str(
        observation.get("T3_Periodo")
        or observation.get("Periodo")
        or observation.get("period")
        or ""
    )
    match = re.search(r"(?P<year>\d{4})M(?P<month>\d{1,2})", period_label)
    if match:
        return date(int(match.group("year")), int(match.group("month")), 1)
    month = observation.get("FK_Periodo") or observation.get("month")
    if year and month:
        return date(int(year), int(month), 1)
    timestamp = observation.get("Fecha")
    if timestamp is not None:
        parsed_date = _parse_ine_timestamp(timestamp)
        if parsed_date is not None:
            return parsed_date
    raise ValueError(f"Unable to determine INE period from observation: {observation}")


def _decimal(value: Any) -> Decimal:
    if value is None or value == "":
        raise ValueError("INE observation has no value")
    normalized = str(value).replace(".", "").replace(",", ".") if isinstance(value, str) else value
    try:
        return Decimal(str(normalized))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid INE numeric value: {value}") from exc


class INETransmissionsIngestion(BaseIngestion):
    source = "ine_transmissions"

    async def extract(self, parameters: dict[str, Any]) -> list[SourceRecord]:
        query = {"tip": parameters.get("tip", "AM")}
        logger.info("Fetching INE transmissions tip=%s", query["tip"])
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(INE_API_URL, params=query)
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, list):
            raise ValueError("Unexpected INE response: expected a list of series")

        logger.info("INE transmissions payload received series=%d", len(payload))

        retrieved_at = datetime.now(UTC)
        records: list[SourceRecord] = []
        parsed_periods = 0
        skipped_unsupported = 0
        for series in payload:
            series_name = str(series.get("Nombre") or series.get("name") or "")
            series_code = str(series.get("COD") or series.get("code") or "")
            geography = _geography_code(series_name)
            for observation in series.get("Data") or series.get("data") or []:
                try:
                    period = _period_from_observation(observation)
                except ValueError as exc:
                    skipped_unsupported += 1
                    logger.warning(
                        "Skipping INE observation without parseable period series=%s error=%s observation=%s",
                        series_code,
                        exc,
                        observation,
                    )
                    continue
                parsed_periods += 1
                date_from = parameters.get("date_from")
                date_to = parameters.get("date_to")
                if date_from and period < date.fromisoformat(date_from):
                    continue
                if date_to and period > date.fromisoformat(date_to):
                    continue
                records.append(
                    SourceRecord(
                        dataset=f"ine_table_{INE_TABLE_ID}",
                        external_id=f"{series_code}:{period.isoformat()}",
                        period=period,
                        geography_code=geography,
                        observed_at=retrieved_at,
                        payload={
                            "provider": "INE",
                            "table_id": INE_TABLE_ID,
                            "table_url": INE_TABLE_URL,
                            "api_url": str(response.url),
                            "series_code": series_code,
                            "series_name": series_name,
                            "series_metadata": {
                                key: value
                                for key, value in series.items()
                                if key not in {"Data", "data"}
                            },
                            "observation": observation,
                            "retrieved_at": retrieved_at.isoformat(),
                        },
                    )
                )
        logger.info(
            "INE transmissions parsed periods=%d skipped=%d records=%d",
            parsed_periods,
            skipped_unsupported,
            len(records),
        )
        return records

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        indicators: list[IndicatorValue] = []
        for record in records:
            series_name = str(record.payload.get("series_name", ""))
            indicator_code = _category(series_name)
            if not indicator_code or not record.geography_code or not record.period:
                continue
            observation = record.payload["observation"]
            value = _decimal(
                observation.get("Valor")
                if "Valor" in observation
                else observation.get("value")
            )
            indicators.append(
                IndicatorValue(
                    indicator_code=indicator_code,
                    geography_code=record.geography_code,
                    period=record.period,
                    frequency="monthly",
                    value=value,
                    unit="transactions",
                    metadata={
                        "provider_table_id": INE_TABLE_ID,
                        "series_code": record.payload.get("series_code"),
                        "series_name": series_name,
                        "provisional": observation.get("Secreto") is False
                        and observation.get("FK_TipoDato") not in {None, 1},
                    },
                )
            )
        return indicators
