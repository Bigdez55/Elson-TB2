from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    advanced_trading,
    ai_portfolio,
    ai_trading,
    auth,
    auto_trading,
    biometric,
    education,
    enhanced_market_data,
    market_data,
    market_streaming,
    monitoring,
    portfolio,
    risk_management,
    security,
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
api_router.include_router(
    market_streaming.router, prefix="/streaming", tags=["market-streaming"]
)
api_router.include_router(ai_trading.router, prefix="/ai", tags=["ai-trading"])
api_router.include_router(
    ai_portfolio.router, prefix="/ai-portfolio", tags=["ai-portfolio"]
)
api_router.include_router(
    risk_management.router, prefix="/risk", tags=["risk-management"]
)
api_router.include_router(
    advanced_trading.router, prefix="/advanced", tags=["advanced-trading"]
)
api_router.include_router(
    auto_trading.router, prefix="/auto-trading", tags=["auto-trading"]
)
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(security.router, prefix="/security", tags=["security"])
api_router.include_router(biometric.router, prefix="/biometric", tags=["biometric"])
api_router.include_router(education.router, prefix="/education", tags=["education"])
