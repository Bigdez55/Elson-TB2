from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    advanced_trading,
    ai_portfolio,
    ai_trading,
    auth,
    enhanced_market_data,
    market_data,
    monitoring,
    portfolio,
    risk_management,
    trading,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
api_router.include_router(market_data.router, prefix="/market", tags=["market-data"])
api_router.include_router(
    enhanced_market_data.router,
    prefix="/market-enhanced",
    tags=["enhanced-market-data"],
)
api_router.include_router(ai_trading.router, prefix="/ai", tags=["ai-trading"])
api_router.include_router(ai_portfolio.router, prefix="/ai-portfolio", tags=["ai-portfolio"])
api_router.include_router(risk_management.router, prefix="/risk", tags=["risk-management"])
api_router.include_router(advanced_trading.router, prefix="/advanced", tags=["advanced-trading"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
