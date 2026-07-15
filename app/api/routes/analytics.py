from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IndicatorDefinition, IndicatorObservation
from app.db.session import get_session

router = APIRouter()


def _observation_payload(row: IndicatorObservation) -> dict:
    return {
        "indicator_code": row.indicator_code,
        "geography_code": row.geography_code,
        "period": row.period,
        "frequency": row.frequency,
        "value": row.value,
        "unit": row.unit,
        "source": row.source,
        "published_at": row.published_at,
        "available_at": row.available_at,
        "metadata": row.extra_metadata or {},
    }


@router.get("/indicators")
async def indicators(
    indicator_code: str | None = None,
    geography_code: str | None = None,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
):
    """Backward-compatible flat observation endpoint."""
    stmt = select(IndicatorObservation)
    if indicator_code:
        stmt = stmt.where(IndicatorObservation.indicator_code == indicator_code)
    if geography_code:
        stmt = stmt.where(IndicatorObservation.geography_code == geography_code)
    if date_from:
        stmt = stmt.where(IndicatorObservation.period >= date_from)
    if date_to:
        stmt = stmt.where(IndicatorObservation.period <= date_to)
    rows = (
        await session.scalars(
            stmt.order_by(IndicatorObservation.period.desc()).limit(limit)
        )
    ).all()
    return [_observation_payload(row) for row in rows]


@router.get("/catalog")
async def catalog(
    source: str | None = None,
    active_only: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """Return the machine-readable indicator catalog and aggregation semantics."""
    stmt = select(IndicatorDefinition)
    if source:
        stmt = stmt.where(IndicatorDefinition.source == source)
    if active_only:
        stmt = stmt.where(IndicatorDefinition.active.is_(True))
    rows = (await session.scalars(stmt.order_by(IndicatorDefinition.code))).all()
    return {
        "generated_at": datetime.now(UTC),
        "count": len(rows),
        "data": [
            {
                "code": row.code,
                "name": row.name,
                "description": row.description,
                "unit": row.unit,
                "native_frequency": row.native_frequency,
                "aggregation_method": row.aggregation_method,
                "geographic_level": row.geographic_level,
                "source": row.source,
                "dataset": row.dataset,
                "active": row.active,
                "metadata": row.extra_metadata or {},
            }
            for row in rows
        ],
    }


@router.get("/observations")
async def observations(
    indicator_code: Annotated[list[str] | None, Query()] = None,
    geography_code: Annotated[list[str] | None, Query()] = None,
    source: Annotated[list[str] | None, Query()] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(5000, ge=1, le=50000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Return tidy/long-form data suitable for models, BI tools and n8n."""
    stmt = select(IndicatorObservation)
    if indicator_code:
        stmt = stmt.where(IndicatorObservation.indicator_code.in_(indicator_code))
    if geography_code:
        stmt = stmt.where(IndicatorObservation.geography_code.in_(geography_code))
    if source:
        stmt = stmt.where(IndicatorObservation.source.in_(source))
    if date_from:
        stmt = stmt.where(IndicatorObservation.period >= date_from)
    if date_to:
        stmt = stmt.where(IndicatorObservation.period <= date_to)

    ordering = (
        IndicatorObservation.period.asc()
        if order == "asc"
        else IndicatorObservation.period.desc()
    )
    rows = (
        await session.scalars(
            stmt.order_by(
                IndicatorObservation.indicator_code,
                IndicatorObservation.geography_code,
                ordering,
            )
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return {
        "generated_at": datetime.now(UTC),
        "count": len(rows),
        "offset": offset,
        "limit": limit,
        "data": [_observation_payload(row) for row in rows],
    }


@router.get("/series/{indicator_code}/{geography_code}")
async def series(
    indicator_code: str,
    geography_code: str,
    date_from: date | None = None,
    date_to: date | None = None,
    source: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Return one chronological series with its catalog definition."""
    stmt = select(IndicatorObservation).where(
        IndicatorObservation.indicator_code == indicator_code,
        IndicatorObservation.geography_code == geography_code,
    )
    if source:
        stmt = stmt.where(IndicatorObservation.source == source)
    if date_from:
        stmt = stmt.where(IndicatorObservation.period >= date_from)
    if date_to:
        stmt = stmt.where(IndicatorObservation.period <= date_to)
    rows = (
        await session.scalars(stmt.order_by(IndicatorObservation.period.asc()))
    ).all()
    definition = await session.get(IndicatorDefinition, indicator_code)
    return {
        "indicator": {
            "code": indicator_code,
            "name": definition.name if definition else indicator_code,
            "description": definition.description if definition else None,
            "unit": definition.unit if definition else (rows[0].unit if rows else None),
            "native_frequency": (
                definition.native_frequency if definition else (rows[0].frequency if rows else None)
            ),
            "aggregation_method": definition.aggregation_method if definition else None,
            "source": definition.source if definition else source,
        },
        "geography_code": geography_code,
        "first_period": rows[0].period if rows else None,
        "last_period": rows[-1].period if rows else None,
        "count": len(rows),
        "data": [
            {
                "period": row.period,
                "value": row.value,
                "published_at": row.published_at,
                "available_at": row.available_at,
            }
            for row in rows
        ],
    }


@router.get("/latest")
async def latest(
    indicator_code: Annotated[list[str] | None, Query()] = None,
    geography_code: Annotated[list[str] | None, Query()] = None,
    source: Annotated[list[str] | None, Query()] = None,
    session: AsyncSession = Depends(get_session),
):
    """Return the latest available observation for every selected series."""
    latest_periods = (
        select(
            IndicatorObservation.indicator_code.label("indicator_code"),
            IndicatorObservation.geography_code.label("geography_code"),
            IndicatorObservation.source.label("source"),
            func.max(IndicatorObservation.period).label("max_period"),
        )
        .group_by(
            IndicatorObservation.indicator_code,
            IndicatorObservation.geography_code,
            IndicatorObservation.source,
        )
        .subquery()
    )
    stmt = select(IndicatorObservation).join(
        latest_periods,
        and_(
            IndicatorObservation.indicator_code == latest_periods.c.indicator_code,
            IndicatorObservation.geography_code == latest_periods.c.geography_code,
            IndicatorObservation.source == latest_periods.c.source,
            IndicatorObservation.period == latest_periods.c.max_period,
        ),
    )
    if indicator_code:
        stmt = stmt.where(IndicatorObservation.indicator_code.in_(indicator_code))
    if geography_code:
        stmt = stmt.where(IndicatorObservation.geography_code.in_(geography_code))
    if source:
        stmt = stmt.where(IndicatorObservation.source.in_(source))
    rows = (
        await session.scalars(
            stmt.order_by(
                IndicatorObservation.indicator_code,
                IndicatorObservation.geography_code,
            )
        )
    ).all()
    return {
        "generated_at": datetime.now(UTC),
        "count": len(rows),
        "data": [_observation_payload(row) for row in rows],
    }
