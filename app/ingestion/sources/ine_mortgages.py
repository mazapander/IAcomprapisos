from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord
from app.ingestion.sources.ine_common import extract_ine_table, fold, parse_decimal

TABLE_ID = "3200"


class INEMortgagesIngestion(BaseIngestion):
    source = "ine_mortgages"

    async def extract(self, parameters: dict) -> list[SourceRecord]:
        return await extract_ine_table(TABLE_ID, self.source, parameters, "monthly")

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        result: list[IndicatorValue] = []
        for record in records:
            name = fold(str(record.payload.get("series_name", "")))
            if not record.geography_code or not record.period or "viviendas" not in name:
                continue
            if "numero de hipotecas" in name:
                code, unit = "mortgages_housing_total", "mortgages"
            elif "importe de hipotecas" in name:
                code, unit = "mortgages_housing_amount_thousand_eur", "thousand_eur"
            else:
                continue
            value = parse_decimal(record.payload["observation"].get("Valor"))
            result.append(IndicatorValue(indicator_code=code, geography_code=record.geography_code, period=record.period, frequency="monthly", value=value, unit=unit, metadata={"table_id":TABLE_ID,"series_code":record.payload.get("series_code"),"series_name":record.payload.get("series_name")}))
        return result
