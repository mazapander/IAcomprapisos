import logging
import re
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import settings
from app.ingestion.base import SourceRecord

logger = logging.getLogger(__name__)

CCAA_CODES = {"nacional":"ES","andalucia":"CCAA:01","aragon":"CCAA:02","asturias":"CCAA:03","balears":"CCAA:04","canarias":"CCAA:05","cantabria":"CCAA:06","castilla y leon":"CCAA:07","castilla - la mancha":"CCAA:08","cataluna":"CCAA:09","comunitat valenciana":"CCAA:10","extremadura":"CCAA:11","galicia":"CCAA:12","madrid":"CCAA:13","murcia":"CCAA:14","navarra":"CCAA:15","pais vasco":"CCAA:16","rioja":"CCAA:17","ceuta":"CCAA:18","melilla":"CCAA:19"}
PROVINCE_CODES = {"alava":"01","araba/alava":"01","albacete":"02","alicante/alacant":"03","almeria":"04","avila":"05","badajoz":"06","balears, illes":"07","barcelona":"08","burgos":"09","caceres":"10","cadiz":"11","castellon/castello":"12","ciudad real":"13","cordoba":"14","coruna, a":"15","cuenca":"16","girona":"17","granada":"18","guadalajara":"19","gipuzkoa":"20","huelva":"21","huesca":"22","jaen":"23","leon":"24","lleida":"25","rioja, la":"26","lugo":"27","madrid":"28","malaga":"29","murcia":"30","navarra":"31","ourense":"32","asturias":"33","palencia":"34","palmas, las":"35","pontevedra":"36","salamanca":"37","santa cruz de tenerife":"38","cantabria":"39","segovia":"40","sevilla":"41","soria":"42","tarragona":"43","teruel":"44","toledo":"45","valencia/valencia":"46","valladolid":"47","bizkaia":"48","zamora":"49","zaragoza":"50","ceuta":"51","melilla":"52"}


def fold(value: str) -> str:
    return re.sub(r"\s+", " ", value.translate(str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")).strip()).lower()


def geography_code(name: str) -> str | None:
    value = fold(name)
    if "total nacional" in value or value.startswith("nacional"):
        return "ES"
    for label, code in PROVINCE_CODES.items():
        if re.search(rf"(^|[;|.])\s*(?:{code}\s+)?{re.escape(label)}\s*($|[;|.])", value):
            return f"PROV:{code}"
    for label, code in CCAA_CODES.items():
        if label in value:
            return code
    return None


def _parse_ine_timestamp(value: Any) -> date | None:
    """Parse the INE ``Fecha`` field.

    The INE Tempus API returns ``Fecha`` either as a Unix epoch number (seconds
    or milliseconds) or as an ISO 8601 string such as
    ``"2026-04-01T00:00:00.000+02:00"``. Returns the first day of the
    corresponding month, or ``None`` if the value cannot be interpreted as a
    date.
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


def parse_period(obs: dict[str, Any], frequency: str) -> date:
    label = str(obs.get("T3_Periodo") or obs.get("Periodo") or obs.get("period") or "")
    if frequency == "quarterly":
        match = re.search(r"(\d{4})T([1-4])", label)
        if match:
            return date(int(match.group(1)), (int(match.group(2)) - 1) * 3 + 1, 1)
    match = re.search(r"(\d{4})M(\d{1,2})", label)
    if match:
        return date(int(match.group(1)), int(match.group(2)), 1)
    year = obs.get("Anyo")
    period = obs.get("FK_Periodo")
    if year and period:
        return date(int(year), ((int(period) - 1) * 3 + 1) if frequency == "quarterly" else int(period), 1)
    timestamp = obs.get("Fecha")
    if timestamp is not None:
        parsed_date = _parse_ine_timestamp(timestamp)
        if parsed_date is not None:
            return parsed_date
    raise ValueError(f"Cannot parse INE period: {obs}")


def parse_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        raise ValueError("Missing value")
    if isinstance(value, str):
        value = value.replace(".", "").replace(",", ".")
    return Decimal(str(value))


async def extract_ine_table(
    table_id: str,
    source: str,
    parameters: dict[str, Any],
    frequency: str,
) -> list[SourceRecord]:
    url = f"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{table_id}"
    logger.info("Fetching INE table table_id=%s tip=%s", table_id, parameters.get("tip", "AM"))
    async with httpx.AsyncClient(
        timeout=settings.http_timeout_seconds,
        follow_redirects=True,
    ) as client:
        response = await client.get(url, params={"tip": parameters.get("tip", "AM")})
        response.raise_for_status()
        payload = response.json()
    logger.info("INE table table_id=%s series=%d", table_id, len(payload) if isinstance(payload, list) else 0)
    retrieved_at = datetime.now(UTC)
    records: list[SourceRecord] = []
    skipped_unsupported = 0
    for series in payload:
        name = str(series.get("Nombre") or "")
        code = str(series.get("COD") or "")
        geo = geography_code(name)
        for obs in series.get("Data") or []:
            try:
                period = parse_period(obs, frequency)
            except ValueError as exc:
                skipped_unsupported += 1
                logger.warning(
                    "Skipping INE observation without parseable period source=%s series=%s error=%s observation=%s",
                    source,
                    code,
                    exc,
                    obs,
                )
                continue
            if parameters.get("date_from") and period < date.fromisoformat(parameters["date_from"]):
                continue
            if parameters.get("date_to") and period > date.fromisoformat(parameters["date_to"]):
                continue
            records.append(
                SourceRecord(
                    dataset=f"ine_table_{table_id}",
                    external_id=f"{code}:{period}",
                    period=period,
                    geography_code=geo,
                    observed_at=retrieved_at,
                    payload={
                        "provider": "INE",
                        "table_id": table_id,
                        "api_url": str(response.url),
                        "series_code": code,
                        "series_name": name,
                        "series_metadata": {k: v for k, v in series.items() if k != "Data"},
                        "observation": obs,
                        "retrieved_at": retrieved_at.isoformat(),
                    },
                )
            )
    if skipped_unsupported:
        logger.info("INE table table_id=%s skipped_unparseable=%d records=%d", table_id, skipped_unsupported, len(records))
    return records
