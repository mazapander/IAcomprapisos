from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.derived import ObservationPoint
from app.analytics.national_observatory import (
    OBSERVATORY_INDICATOR_CODES,
    build_national_observatory,
)
from app.db.models import IndicatorObservation
from app.db.session import get_session
from app.schemas.observatory import NationalObservatoryResponse

router = APIRouter()


@router.get("/national", response_model=NationalObservatoryResponse)
async def national_observatory(
    session: Annotated[AsyncSession, Depends(get_session)],
    years: Annotated[int, Query(ge=3, le=20)] = 10,
) -> dict:
    """Return the national price, mortgage and rate dashboard."""
    cutoff = date(datetime.now(UTC).year - years, 1, 1)
    rows = (
        await session.scalars(
            select(IndicatorObservation)
            .where(
                IndicatorObservation.geography_code == "ES",
                IndicatorObservation.indicator_code.in_(OBSERVATORY_INDICATOR_CODES),
                IndicatorObservation.period >= cutoff,
            )
            .order_by(IndicatorObservation.period.asc())
        )
    ).all()
    result = build_national_observatory(
        [
            ObservationPoint(
                indicator_code=row.indicator_code,
                geography_code=row.geography_code,
                period=row.period,
                value=row.value,
                unit=row.unit,
                source=row.source,
            )
            for row in rows
        ]
    )
    result["generated_at"] = datetime.now(UTC)
    return result
