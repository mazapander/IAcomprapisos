from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.derived import (
    INDICATOR_ALIASES,
    MarketAssumptions,
    ObservationPoint,
    build_market_summary,
)
from app.db.models import IndicatorObservation
from app.db.session import get_session

router = APIRouter()


@router.get("/{geography_code}/summary")
async def market_summary(
    geography_code: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    home_size_m2: Annotated[Decimal, Query(gt=0, le=1000)] = Decimal(90),
    ltv_pct: Annotated[Decimal, Query(gt=0, le=100)] = Decimal(80),
    term_years: Annotated[int, Query(ge=1, le=50)] = 25,
    fallback_mortgage_spread_pp: Annotated[Decimal, Query(ge=0, le=10)] = Decimal(1),
):
    """Build a territorial product card and derived housing analytics.

    Territorial indicators prefer the requested geography and fall back to the
    national series only when the same indicator has no local observation. Each
    metric includes its effective geography so consumers can disclose that fallback.
    """
    indicator_codes = sorted({code for aliases in INDICATOR_ALIASES.values() for code in aliases})
    rows = (
        await session.scalars(
            select(IndicatorObservation)
            .where(
                IndicatorObservation.indicator_code.in_(indicator_codes),
                IndicatorObservation.geography_code.in_([geography_code, "ES"]),
            )
            .order_by(IndicatorObservation.period.asc())
        )
    ).all()
    observations = [
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
    result = build_market_summary(
        observations,
        geography_code,
        MarketAssumptions(
            home_size_m2=home_size_m2,
            ltv_pct=ltv_pct,
            term_years=term_years,
            fallback_mortgage_spread_pp=fallback_mortgage_spread_pp,
        ),
    )
    result["generated_at"] = datetime.now(UTC)
    return result
