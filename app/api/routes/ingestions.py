from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import IngestionRun
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


@router.post(
    "/{source}",
    response_model=IngestionRunResponse,
    dependencies=[Depends(verify_api_key)],
)
async def trigger(
    source: str,
    payload: IngestionRequest,
    session: AsyncSession = Depends(get_session),
):
    if source not in available_sources():
        raise HTTPException(status_code=404, detail="Unknown source")

    # n8n may retry when a long HTTP connection is aborted. Refuse a second live run
    # for the same source so retries cannot multiply expensive database work.
    active_since = datetime.now(UTC) - timedelta(minutes=30)
    active_run = await session.scalar(
        select(IngestionRun)
        .where(
            IngestionRun.source == source,
            IngestionRun.status == "running",
            IngestionRun.started_at >= active_since,
        )
        .order_by(IngestionRun.started_at.desc())
        .limit(1)
    )
    if active_run is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "An ingestion for this source is already running",
                "run_id": str(active_run.id),
                "source": source,
                "started_at": active_run.started_at.isoformat(),
            },
        )

    return await execute_ingestion(
        session,
        source,
        payload.requested_by,
        payload.parameters,
    )


@router.get("/runs", response_model=list[IngestionRunResponse])
async def runs(
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    return await list_runs(session, limit)
