import csv
import io
import logging
import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.core.config import settings
from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord

logger = logging.getLogger(__name__)

BDE_REFERENCE_RATES_PAGE = "https://www.bde.es/webbe/es/estadisticas/temas/tipos-interes.html"
BDE_REFERENCE_RATES_CSV = "https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/be1901.csv"

MONTHS = {
    "ene": 1, "enero": 1, "jan": 1,
    "feb": 2, "febrero": 2,
    "mar": 3, "marzo": 3,
    "abr": 4, "abril": 4, "apr": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "junio": 6,
    "jul": 7, "julio": 7,
    "ago": 8, "agosto": 8, "aug": 8,
    "sep": 9, "sept": 9, "septiembre": 9,
    "oct": 10, "octubre": 10,
    "nov": 11, "noviembre": 11,
    "dic": 12, "diciembre": 12, "dec": 12,
}


def _fold(value: str) -> str:
    translation = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return re.sub(r"\s+", " ", value.translate(translation).strip()).lower()


def _parse_period(value: str) -> date:
    normalized = _fold(value).replace(".", "").strip()
    for pattern in ("%Y-%m-%d", "%Y-%m", "%m/%Y", "%Y/%m", "%d/%m/%Y", "%Y%m"):
        try:
            parsed = datetime.strptime(normalized, pattern)
            return date(parsed.year, parsed.month, 1)
        except ValueError:
            pass

    match = re.search(r"(?P<month>[a-z]+)[-/ ](?P<year>\d{4})", normalized)
    if match and match.group("month") in MONTHS:
        return date(int(match.group("year")), MONTHS[match.group("month")], 1)

    match = re.search(r"(?P<year>\d{4})[-/ ](?P<month>[a-z]+)", normalized)
    if match and match.group("month") in MONTHS:
        return date(int(match.group("year")), MONTHS[match.group("month")], 1)

    raise ValueError(f"Unsupported Banco de España period: {value}")


def _parse_decimal(value: str) -> Decimal:
    normalized = value.strip().replace("%", "").replace(" ", "")
    if not normalized or normalized.lower() in {"-", "..", "...", "n.d.", "na"}:
        raise ValueError("Banco de España value is empty")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid Banco de España numeric value: {value}") from exc


def _read_rows(content: str) -> list[list[str]]:
    sample = content[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";"
    return [
        [cell.strip().strip('"') for cell in row]
        for row in csv.reader(io.StringIO(content), dialect)
        if any(cell.strip() for cell in row)
    ]


def _find_named_euribor_column(rows: list[list[str]]) -> tuple[int, int] | None:
    for row_index, row in enumerate(rows):
        for column_index, cell in enumerate(row):
            folded = _fold(cell)
            if "euribor" in folded and any(
                label in folded for label in ("un ano", "12 meses", "1 ano", "a 12 meses")
            ):
                return row_index, column_index
    return None


def _find_date_and_value_columns(rows: list[list[str]]) -> tuple[int, int, int]:
    """Fallback for BDE files whose header only exposes a series code.

    The be1901 download is already a dedicated series file, so the value column may be
    labelled with an internal code rather than the words 'Euribor 12 months'. We locate
    the first row containing a parseable date and a numeric value and infer its columns.
    """
    for row_index, row in enumerate(rows):
        date_column: int | None = None
        value_column: int | None = None
        for index, cell in enumerate(row):
            if date_column is None:
                try:
                    _parse_period(cell)
                    date_column = index
                    continue
                except ValueError:
                    pass
            try:
                _parse_decimal(cell)
                if index != date_column:
                    value_column = index
            except ValueError:
                continue
        if date_column is not None and value_column is not None:
            return row_index, date_column, value_column
    raise ValueError("No date/value observations could be located in the Banco de España CSV")


def parse_bde_euribor_csv(content: str) -> list[tuple[date, Decimal, dict[str, Any]]]:
    rows = _read_rows(content)
    named = _find_named_euribor_column(rows)

    if named is not None:
        header_index, value_column = named
        data_start = header_index + 1
        date_column_hint: int | None = None
    else:
        first_data_row, date_column_hint, value_column = _find_date_and_value_columns(rows)
        header_index = max(0, first_data_row - 1)
        data_start = first_data_row
        logger.info(
            "BDE Euribor parser using dedicated-series fallback date_column=%d value_column=%d",
            date_column_hint,
            value_column,
        )

    result: list[tuple[date, Decimal, dict[str, Any]]] = []
    for row in rows[data_start:]:
        if value_column >= len(row):
            continue

        period: date | None = None
        date_column = date_column_hint
        candidate_indexes = [date_column_hint] if date_column_hint is not None else range(min(4, len(row)))
        for index in candidate_indexes:
            if index is None or index >= len(row):
                continue
            try:
                period = _parse_period(row[index])
                date_column = index
                break
            except ValueError:
                continue
        if period is None:
            continue

        try:
            value = _parse_decimal(row[value_column])
        except ValueError:
            continue

        result.append(
            (
                period,
                value,
                {
                    "raw_row": row,
                    "header": rows[header_index] if rows else [],
                    "date_column": date_column,
                    "value_column": value_column,
                },
            )
        )

    if not result:
        raise ValueError("No monthly 12-month Euribor observations could be parsed")
    return result


class BDEEuriborIngestion(BaseIngestion):
    source = "bde_euribor"

    async def extract(self, parameters: dict[str, Any]) -> list[SourceRecord]:
        url = parameters.get("url", BDE_REFERENCE_RATES_CSV)
        logger.info("Fetching Banco de España Euribor url=%s", url)
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.content.decode(response.encoding or "utf-8", errors="replace").lstrip("\ufeff")

        retrieved_at = datetime.now(UTC)
        observations = parse_bde_euribor_csv(content)
        logger.info("Banco de España Euribor parsed observations=%d", len(observations))
        records: list[SourceRecord] = []
        for period, value, metadata in observations:
            date_from = parameters.get("date_from")
            date_to = parameters.get("date_to")
            if date_from and period < date.fromisoformat(date_from):
                continue
            if date_to and period > date.fromisoformat(date_to):
                continue
            records.append(
                SourceRecord(
                    dataset="bde_be1901_reference_rates",
                    external_id=f"euribor_12m:{period.isoformat()}",
                    period=period,
                    geography_code="ES",
                    observed_at=retrieved_at,
                    payload={
                        "provider": "Banco de España",
                        "source_page": BDE_REFERENCE_RATES_PAGE,
                        "download_url": str(response.url),
                        "content_type": response.headers.get("content-type"),
                        "http_status": response.status_code,
                        "period": period.isoformat(),
                        "value": str(value),
                        "unit": "percent",
                        "frequency": "monthly",
                        "retrieved_at": retrieved_at.isoformat(),
                        **metadata,
                    },
                )
            )
        return records

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        return [
            IndicatorValue(
                indicator_code="euribor_12m_pct",
                geography_code="ES",
                period=record.period,
                frequency="monthly",
                value=Decimal(str(record.payload["value"])),
                unit="percent",
                metadata={
                    "dataset": record.dataset,
                    "download_url": record.payload.get("download_url"),
                    "header": record.payload.get("header"),
                },
            )
            for record in records
            if record.period is not None
        ]
