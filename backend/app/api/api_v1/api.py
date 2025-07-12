from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    ai_trading,
    auth,
    enhanced_market_data,
    market_data,
    portfolio,
    trading,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    portfolio.router, prefix="/portfolio", tags=["portfolio"]
)
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
api_router.include_router(
    market_data.router, prefix="/market", tags=["market-data"]
)
api_router.include_router(
    enhanced_market_data.router,
    prefix="/market-enhanced",
    tags=["enhanced-market-data"],
)
api_router.include_router(ai_trading.router, prefix="/ai", tags=["ai-trading"])
