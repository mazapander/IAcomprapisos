from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord

class MIVAURentIngestion(BaseIngestion):
    source = "mivau_rent"
    async def extract(self, parameters: dict) -> list[SourceRecord]:
        # TODO: admitir fichero anual SERPAVI o URL oficial versionada.
        return []
    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        return []
