from fastapi import APIRouter

from app.analytics.mortgage_decision import MortgageScenario, review_mortgage
from app.schemas.mortgage import MortgageReviewRequest

router = APIRouter()


@router.post("/review")
async def mortgage_review(payload: MortgageReviewRequest):
    """Review affordability, liquidity and rate risk for one mortgage scenario."""
    return review_mortgage(MortgageScenario(**payload.model_dump()))
