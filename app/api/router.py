from fastapi import APIRouter
from app.api.routes import analytics, health, ingestions
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingestions.router, prefix="/ingestions", tags=["ingestions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
