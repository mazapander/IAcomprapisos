from datetime import datetime
from typing import Any

from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord
from app.ingestion.sources.mivau_tabular import decimal_value, download_rows, geography, period_value, pick


class MIVAURentIngestion(BaseIngestion):
    source = "mivau_rent"

    async def extract(self, parameters: dict[str, Any]) -> list[SourceRecord]:
        url = parameters.get("url")
        if not url:
            raise ValueError("mivau_rent requires parameters.url pointing to the official SERPAVI CSV/XLSX release")
        rows, metadata = await download_rows(url, parameters.get("sheet_name"))
        level = parameters.get("geographic_level", "municipality")
        records: list[SourceRecord] = []
        for index, row in enumerate(rows):
            period_raw = pick(row, ["año", "ano", "periodo"])
            rent_raw = pick(row, ["renta mensual mediana", "alquiler mensual mediano", "renta mediana", "alquiler mediano"])
            rent_m2_raw = pick(row, ["renta mediana por m2", "alquiler mediano por m2", "euros m2", "€/m2"])
            geo_name = pick(row, ["municipio", "provincia", "comunidad autonoma", "distrito", "seccion censal"])
            geo_code = pick(row, ["codigo municipio", "codigo ine", "codigo provincia", "codigo seccion"])
            if period_raw is None or geo_name is None or (rent_raw is None and rent_m2_raw is None):
                continue
            period = period_value(period_raw, "annual")
            records.append(SourceRecord(dataset="serpavi_rent_reference", external_id=f"{index}:{period}", period=period, geography_code=geography(geo_name, level, geo_code), observed_at=datetime.fromisoformat(metadata["retrieved_at"]), payload={"provider":"MIVAU_SERPAVI","row":row,**metadata}))
        return records

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        result: list[IndicatorValue] = []
        for record in records:
            row = record.payload["row"]
            common = {"download_url":record.payload.get("download_url"),"raw_row":row}
            rent = pick(row, ["renta mensual mediana", "alquiler mensual mediano", "renta mediana", "alquiler mediano"])
            rent_m2 = pick(row, ["renta mediana por m2", "alquiler mediano por m2", "euros m2", "€/m2"])
            if rent is not None:
                result.append(IndicatorValue(indicator_code="rent_monthly_median_eur", geography_code=record.geography_code or "ES", period=record.period, frequency="annual", value=decimal_value(rent), unit="eur_month", metadata=common))
            if rent_m2 is not None:
                result.append(IndicatorValue(indicator_code="rent_price_median_eur_m2", geography_code=record.geography_code or "ES", period=record.period, frequency="annual", value=decimal_value(rent_m2), unit="eur_m2_month", metadata=common))
        return result
