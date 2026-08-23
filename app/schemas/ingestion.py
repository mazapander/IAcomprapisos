from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    requested_by: str = "n8n"
    parameters: dict[str, Any] = Field(default_factory=dict)


class IngestionRunResponse(BaseModel):
    id: UUID
    source: str
    status: str
    rows_received: int
    rows_written: int
    rows_inserted: int
    rows_updated: int
    rows_unchanged: int
    latest_period: date | None
    error: str | None
    started_at: datetime
    finished_at: datetime | None
    model_config = {"from_attributes": True}
