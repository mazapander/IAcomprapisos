import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import xlrd

from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord
from app.ingestion.security import validate_source_url
from app.ingestion.sources.ine_common import CCAA_CODES, PROVINCE_CODES, fold
from app.ingestion.sources.mivau_tabular import decimal_value, download_rows, geography, period_value, pick

MIVAU_APPRAISAL_SERIES_URL = "https://apps.fomento.gob.es/boletinonline2/sedal/35101000.XLS"
MIVAU_CCAA_ALIASES = {
    "asturias (principado de )": "03",
    "balears (illes)": "04",
    "castilla-la mancha": "08",
    "comunidad valenciana": "10",
    "madrid (comunidad de)": "13",
    "murcia (region de)": "14",
    "navarra (comunidad foral de)": "15",
    "rioja (la)": "17",
}
MIVAU_PROVINCE_ALIASES = {
    "coruna (a)": "15",
    "palmas (las)": "35",
    "balears (illes)": "07",
}


def mivau_geography(name: str) -> str | None:
    label = fold(name)
    if label in {"total nacional", "nacional", "espana"}:
        return "ES"
    ccaa_code = MIVAU_CCAA_ALIASES.get(label) or CCAA_CODES.get(label)
    if ccaa_code:
        return f"CCAA:{ccaa_code.split(':')[-1]}"
    province_code = MIVAU_PROVINCE_ALIASES.get(label) or PROVINCE_CODES.get(label)
    return f"PROV:{province_code}" if province_code else None


def _mivau_period_columns(sheet: Any) -> dict[int, date]:
    for row_index in range(min(20, sheet.nrows)):
        row = sheet.row_values(row_index)
        if not any("ano" in fold(value) for value in row):
            continue
        quarter_row = sheet.row_values(min(row_index + 2, sheet.nrows - 1))
        current_year: int | None = None
        columns: dict[int, date] = {}
        for column, value in enumerate(row):
            match = re.search(r"(19|20)\d{2}", str(value))
            if match:
                current_year = int(match.group(0))
            quarter_match = re.search(r"([1-4])", str(quarter_row[column]))
            if current_year and quarter_match:
                columns[column] = date(current_year, (int(quarter_match.group(1)) - 1) * 3 + 1, 1)
        if columns:
            return columns
    raise ValueError("MIVAU appraisal workbook does not contain quarterly period headers")


def parse_mivau_appraisal_workbook(content: bytes) -> list[tuple[str, date, Decimal]]:
    """Parse the official MIVAU historical XLS into national, CCAA and province observations."""
    workbook = xlrd.open_workbook(file_contents=content)
    observations: list[tuple[str, date, Decimal]] = []
    for sheet in workbook.sheets():
        columns = _mivau_period_columns(sheet)
        for row_index in range(sheet.nrows):
            row = sheet.row_values(row_index)
            if len(row) < 2:
                continue
            geography_code = mivau_geography(str(row[1]))
            if not geography_code:
                continue
            for column, period in columns.items():
                if column >= len(row) or row[column] in {None, "", "n.r."}:
                    continue
                try:
                    value = decimal_value(row[column])
                except (InvalidOperation, ValueError):
                    continue
                observations.append((geography_code, period, value))
    return observations


class MIVAUAppraisalIngestion(BaseIngestion):
    source = "mivau_appraisal"

    async def extract(self, parameters: dict[str, Any]) -> list[SourceRecord]:
        url = parameters.get("url") or MIVAU_APPRAISAL_SERIES_URL
        validate_source_url(url)
        if url.lower().endswith(".xls"):
            import httpx

            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            retrieved_at = datetime.now(UTC)
            return [
                SourceRecord(
                    dataset="mivau_appraisal_value",
                    external_id=f"{geography_code}:{period.isoformat()}",
                    period=period,
                    geography_code=geography_code,
                    observed_at=retrieved_at,
                    payload={
                        "provider": "MIVAU",
                        "value": str(value),
                        "download_url": str(response.url),
                        "retrieved_at": retrieved_at.isoformat(),
                    },
                )
                for geography_code, period, value in parse_mivau_appraisal_workbook(response.content)
            ]
        rows, metadata = await download_rows(url, parameters.get("sheet_name"))
        records: list[SourceRecord] = []
        for index, row in enumerate(rows):
            period_raw = pick(row, ["periodo", "trimestre", "año", "ano"])
            value_raw = pick(row, ["valor tasado", "euros por metro cuadrado", "€/m2", "eur/m2"])
            geo_name = pick(row, ["provincia", "comunidad autonoma", "territorio", "ambito"])
            geo_code = pick(row, ["codigo provincia", "codigo comunidad", "codigo ine"])
            if period_raw is None or value_raw is None or geo_name is None:
                continue
            level = parameters.get("geographic_level", "province")
            period = period_value(period_raw, "quarterly")
            records.append(SourceRecord(dataset="mivau_appraisal_value", external_id=f"{index}:{period}", period=period, geography_code=geography(geo_name, level, geo_code), observed_at=datetime.fromisoformat(metadata["retrieved_at"]), payload={"provider":"MIVAU","row":row,**metadata}))
        return records

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        result: list[IndicatorValue] = []
        for record in records:
            value_raw = record.payload.get("value") or pick(
                record.payload["row"], ["valor tasado", "euros por metro cuadrado", "€/m2", "eur/m2"]
            )
            result.append(IndicatorValue(indicator_code="appraisal_price_eur_m2", geography_code=record.geography_code or "ES", period=record.period, frequency="quarterly", value=decimal_value(value_raw), unit="eur_m2", metadata={"download_url":record.payload.get("download_url"),"raw_row":record.payload.get("row")}))
        return result
