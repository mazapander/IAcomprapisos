from datetime import datetime
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
    error: str | None
    started_at: datetime
    finished_at: datetime | None
    model_config = {"from_attributes": True}
