from app.ingestion.base import BaseIngestion
from app.ingestion.sources.bde_euribor import BDEEuriborIngestion
from app.ingestion.sources.ine_transmissions import INETransmissionsIngestion
from app.ingestion.sources.mivau_rent import MIVAURentIngestion

_REGISTRY: dict[str, BaseIngestion] = {item.source: item for item in [INETransmissionsIngestion(), BDEEuriborIngestion(), MIVAURentIngestion()]}

def get_ingestion(source: str) -> BaseIngestion:
    if source not in _REGISTRY:
        raise KeyError(source)
    return _REGISTRY[source]

def available_sources() -> list[str]:
    return sorted(_REGISTRY)
