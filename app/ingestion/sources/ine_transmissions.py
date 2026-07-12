from app.ingestion.base import BaseIngestion, IndicatorValue, SourceRecord

class INETransmissionsIngestion(BaseIngestion):
    source = "ine_transmissions"
    async def extract(self, parameters: dict) -> list[SourceRecord]:
        # TODO: configurar table_id y mapear la respuesta oficial del INE.
        # Se mantiene aislado para que cambios del proveedor no afecten al dominio.
        return []
    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]:
        return []
