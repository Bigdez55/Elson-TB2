from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, market_data, portfolio, trading

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
api_router.include_router(market_data.router, prefix="/market", tags=["market-data"])
