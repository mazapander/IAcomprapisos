from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class ObservatoryPoint(BaseModel):
    period: date
    value: Decimal


class ObservatoryLatest(BaseModel):
    value: Decimal
    unit: str
    period: date
    source: str


class ObservatoryChange(BaseModel):
    value: Decimal | None
    unit: str | None


class ObservatorySeries(BaseModel):
    code: str
    label: str
    description: str
    available: bool
    latest: ObservatoryLatest | None
    change_previous: ObservatoryChange
    change_year_on_year: ObservatoryChange
    direction: Literal["up", "down", "flat"] | None
    points: list[ObservatoryPoint]


class ObservatoryGroup(BaseModel):
    label: str
    description: str
    series: list[ObservatorySeries]


class ObservatoryGroups(BaseModel):
    prices: ObservatoryGroup
    mortgages: ObservatoryGroup
    rates: ObservatoryGroup


class ObservatoryCoverage(BaseModel):
    available_series: int
    total_series: int
    latest_period: date | None


class ObservatoryMethodology(BaseModel):
    change_for_rates: Literal["percentage_points"]
    change_for_amounts: Literal["percent"]
    average_mortgage_amount: str
    notice: str


class NationalObservatoryResponse(BaseModel):
    geography_code: Literal["ES"]
    generated_at: datetime
    groups: ObservatoryGroups
    coverage: ObservatoryCoverage
    methodology: ObservatoryMethodology
