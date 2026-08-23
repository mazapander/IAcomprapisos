from fastapi import APIRouter

from app.analytics.mortgage_decision import (
    MortgageScenario,
    PurchaseBudgetScenario,
    calculate_purchase_budget,
    review_mortgage,
)
from app.schemas.mortgage import MortgageBudgetRequest, MortgageReviewRequest

router = APIRouter()


@router.post("/review")
async def mortgage_review(payload: MortgageReviewRequest):
    """Review affordability, liquidity and rate risk for one mortgage scenario."""
    return review_mortgage(MortgageScenario(**payload.model_dump()))


@router.post("/budget")
async def mortgage_budget(payload: MortgageBudgetRequest):
    """Estimate a sustainable purchase budget from income, savings and chosen limits."""
    return calculate_purchase_budget(PurchaseBudgetScenario(**payload.model_dump()))
