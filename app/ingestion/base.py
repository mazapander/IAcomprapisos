from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

@dataclass(slots=True)
class SourceRecord:
    dataset: str
    payload: dict[str, Any]
    external_id: str | None = None
    period: date | None = None
    geography_code: str | None = None
    observed_at: datetime | None = None

@dataclass(slots=True)
class IndicatorValue:
    indicator_code: str
    geography_code: str
    period: date
    frequency: str
    value: Decimal
    unit: str
    published_at: datetime | None = None
    metadata: dict[str, Any] | None = None

class BaseIngestion(ABC):
    source: str
    @abstractmethod
    async def extract(self, parameters: dict[str, Any]) -> list[SourceRecord]: ...
    @abstractmethod
    def transform(self, records: list[SourceRecord]) -> list[IndicatorValue]: ...
