from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import IndicatorObservation
from app.db.session import get_session
router = APIRouter()

@router.get("/indicators")
async def indicators(indicator_code: str | None = None, geography_code: str | None = None, date_from: date | None = Query(None), date_to: date | None = Query(None), limit: int = Query(500, ge=1, le=5000), session: AsyncSession = Depends(get_session)):
    stmt = select(IndicatorObservation)
    if indicator_code: stmt = stmt.where(IndicatorObservation.indicator_code == indicator_code)
    if geography_code: stmt = stmt.where(IndicatorObservation.geography_code == geography_code)
    if date_from: stmt = stmt.where(IndicatorObservation.period >= date_from)
    if date_to: stmt = stmt.where(IndicatorObservation.period <= date_to)
    rows = (await session.scalars(stmt.order_by(IndicatorObservation.period.desc()).limit(limit))).all()
    return [{"indicator_code": r.indicator_code, "geography_code": r.geography_code, "period": r.period, "frequency": r.frequency, "value": r.value, "unit": r.unit, "source": r.source} for r in rows]
