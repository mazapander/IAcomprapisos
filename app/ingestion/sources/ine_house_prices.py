from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord
from app.ingestion.sources.ine_common import extract_ine_table, fold, parse_decimal

TABLE_ID = "79563"


class INEHousePricesIngestion(BaseIngestion):
    source = "ine_house_prices"

    async def extract(self, parameters: dict) -> list[SourceRecord]:
        return await extract_ine_table(TABLE_ID, self.source, parameters, "quarterly")

    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        result: list[IndicatorValue] = []
        for record in records:
            name = fold(str(record.payload.get("series_name", "")))
            if not record.geography_code or not record.period or "indice" not in name:
                continue
            if "variacion" in name:
                continue
            indicator = "house_price_index"
            if "vivienda nueva" in name:
                indicator = "house_price_index_new"
            elif "segunda mano" in name:
                indicator = "house_price_index_used"
            observation = record.payload["observation"]
            value = parse_decimal(observation.get("Valor"))
            result.append(IndicatorValue(indicator_code=indicator, geography_code=record.geography_code, period=record.period, frequency="quarterly", value=value, unit="index_2025_100", metadata={"table_id":TABLE_ID,"series_code":record.payload.get("series_code"),"series_name":record.payload.get("series_name")}))
        return result
