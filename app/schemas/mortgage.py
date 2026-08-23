from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MortgageReviewRequest(BaseModel):
    property_price_eur: Decimal = Field(gt=0)
    savings_eur: Decimal = Field(ge=0)
    annual_net_household_income_eur: Decimal = Field(gt=0)
    mortgage_amount_eur: Decimal = Field(gt=0)
    rate_type: Literal["fixed", "variable", "mixed"] = "fixed"
    annual_nominal_rate_pct: Decimal = Field(ge=0, le=30)
    annual_apr_pct: Decimal | None = Field(default=None, ge=0, le=30)
    term_years: int = Field(ge=1, le=50)
    mixed_fixed_years: int | None = Field(default=None, ge=1, le=40)
    variable_spread_pct: Decimal | None = Field(default=None, ge=0, le=10)
    upfront_fees_eur: Decimal = Field(default=Decimal(0), ge=0)
    monthly_linked_costs_eur: Decimal = Field(default=Decimal(0), ge=0)
    existing_monthly_debt_eur: Decimal = Field(default=Decimal(0), ge=0)
    monthly_living_costs_eur: Decimal = Field(default=Decimal(0), ge=0)
    purchase_cost_pct: Decimal = Field(default=Decimal(10), ge=0, le=30)
    stress_rate_increase_pp: Decimal = Field(default=Decimal(2), ge=0, le=15)
    market_apr_pct: Decimal | None = Field(default=None, ge=0, le=30)
    euribor_pct: Decimal | None = Field(default=None, ge=-10, le=30)

    @model_validator(mode="after")
    def mixed_offer_is_complete(self):
        if self.rate_type != "mixed":
            return self
        missing = [
            label
            for label, value in (
                ("mixed_fixed_years", self.mixed_fixed_years),
                ("variable_spread_pct", self.variable_spread_pct),
                ("euribor_pct", self.euribor_pct),
            )
            if value is None
        ]
        if missing:
            raise ValueError(f"Mixed mortgages require: {', '.join(missing)}")
        if self.mixed_fixed_years >= self.term_years:
            raise ValueError("The mixed fixed period must be shorter than the mortgage term")
        return self


class MortgageBudgetRequest(BaseModel):
    annual_net_household_income_eur: Decimal = Field(gt=0)
    savings_eur: Decimal = Field(ge=0)
    annual_nominal_rate_pct: Decimal = Field(ge=0, le=30)
    term_years: int = Field(default=25, ge=1, le=50)
    existing_monthly_debt_eur: Decimal = Field(default=Decimal(0), ge=0)
    monthly_living_costs_eur: Decimal = Field(default=Decimal(0), ge=0)
    purchase_cost_pct: Decimal = Field(default=Decimal(10), ge=0, le=30)
    max_effort_pct: Decimal = Field(default=Decimal(35), gt=0, le=60)
    max_ltv_pct: Decimal = Field(default=Decimal(80), gt=0, le=100)
    reserve_months: int = Field(default=6, ge=0, le=36)
