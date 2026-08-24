from fastapi import APIRouter

from app.api.routes import analytics, health, ingestions, markets, mortgages, observatory, product

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingestions.router, prefix="/ingestions", tags=["ingestions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(markets.router, prefix="/markets", tags=["markets"])
api_router.include_router(
    observatory.router,
    prefix="/markets/observatory",
    tags=["national-observatory"],
)
api_router.include_router(mortgages.router, prefix="/mortgages", tags=["mortgages"])
api_router.include_router(product.router, prefix="/product", tags=["product"])
