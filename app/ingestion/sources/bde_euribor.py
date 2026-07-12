from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord

class BDEEuriborIngestion(BaseIngestion):
    source = "bde_euribor"
    async def extract(self, parameters: dict) -> list[SourceRecord]:
        # TODO: descargar y parsear la serie oficial del Banco de España.
        return []
    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        return []
