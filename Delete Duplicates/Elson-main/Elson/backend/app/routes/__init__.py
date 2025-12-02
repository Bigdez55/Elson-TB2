from fastapi import APIRouter
from . import user, portfolio, trade

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(portfolio.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(trade.router, prefix="/trades", tags=["trades"])
