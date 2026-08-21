from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class MortgageReviewRequest(BaseModel):
    property_price_eur: Decimal = Field(gt=0)
    savings_eur: Decimal = Field(ge=0)
    annual_net_household_income_eur: Decimal = Field(gt=0)
    mortgage_amount_eur: Decimal = Field(gt=0)
    rate_type: Literal["fixed", "variable"] = "fixed"
    annual_nominal_rate_pct: Decimal = Field(ge=0, le=30)
    annual_apr_pct: Decimal | None = Field(default=None, ge=0, le=30)
    term_years: int = Field(ge=1, le=50)
    existing_monthly_debt_eur: Decimal = Field(default=Decimal(0), ge=0)
    monthly_living_costs_eur: Decimal = Field(default=Decimal(0), ge=0)
    purchase_cost_pct: Decimal = Field(default=Decimal(10), ge=0, le=30)
    stress_rate_increase_pp: Decimal = Field(default=Decimal(2), ge=0, le=15)
    market_apr_pct: Decimal | None = Field(default=None, ge=0, le=30)
    euribor_pct: Decimal | None = Field(default=None, ge=-10, le=30)
