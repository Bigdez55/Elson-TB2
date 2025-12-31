from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    advanced_trading,
    ai_portfolio,
    ai_routes,
    ai_trading,
    auth,
    auto_trading,
    biometric,
    education,
    enhanced_market_data,
    market_data,
    market_data_routes,
    market_routes,
    market_routes_enhanced,
    market_streaming,
    micro_invest,
    model_performance,
    monitoring,
    portfolio,
    portfolio_routes,
    risk_management,
    risk_routes,
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

# New routes from archive integration
api_router.include_router(
    ai_routes.router, prefix="/ai-recommendations", tags=["ai-recommendations"]
)
api_router.include_router(
    market_data_routes.router, prefix="/market-data", tags=["market-data-enhanced"]
)
api_router.include_router(
    market_routes.router, prefix="/markets", tags=["markets"]
)
api_router.include_router(
    market_routes_enhanced.router, prefix="/market-enhanced-v2", tags=["market-v2"]
)
api_router.include_router(
    micro_invest.router, prefix="/micro-invest", tags=["micro-investing"]
)
api_router.include_router(
    model_performance.router, prefix="/ml-models", tags=["ml-models"]
)
api_router.include_router(
    portfolio_routes.router, prefix="/portfolios", tags=["portfolio-management"]
)
api_router.include_router(
    risk_routes.router, prefix="/risk-profiles", tags=["risk-profiles"]
)
