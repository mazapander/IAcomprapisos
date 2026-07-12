from datetime import datetime
from typing import Any

from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord
from app.ingestion.sources.mivau_tabular import download_rows, geography, period_value, pick, decimal_value


class MIVAUAppraisalIngestion(BaseIngestion):
    source = "mivau_appraisal"

    async def extract(self, parameters: dict[str, Any]) -> list[SourceRecord]:
        url = parameters.get("url")
        if not url:
            raise ValueError("mivau_appraisal requires parameters.url pointing to the official CSV/XLSX release")
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
            value_raw = pick(record.payload["row"], ["valor tasado", "euros por metro cuadrado", "€/m2", "eur/m2"])
            result.append(IndicatorValue(indicator_code="appraisal_price_eur_m2", geography_code=record.geography_code or "ES", period=record.period, frequency="quarterly", value=decimal_value(value_raw), unit="eur_m2", metadata={"download_url":record.payload.get("download_url"),"raw_row":record.payload["row"]}))
        return result
