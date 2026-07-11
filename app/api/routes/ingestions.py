from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_session
from app.ingestion.registry import available_sources
from app.ingestion.service import execute_ingestion, list_runs
from app.schemas.ingestion import IngestionRequest, IngestionRunResponse
router = APIRouter()

async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

@router.get("/sources")
async def sources() -> dict[str, list[str]]:
    return {"sources": available_sources()}

@router.post("/{source}", response_model=IngestionRunResponse, dependencies=[Depends(verify_api_key)])
async def trigger(source: str, payload: IngestionRequest, session: AsyncSession = Depends(get_session)):
    if source not in available_sources():
        raise HTTPException(status_code=404, detail="Unknown source")
    return await execute_ingestion(session, source, payload.requested_by, payload.parameters)

@router.get("/runs", response_model=list[IngestionRunResponse])
async def runs(limit: int = Query(100, ge=1, le=500), session: AsyncSession = Depends(get_session)):
    return await list_runs(session, limit)
