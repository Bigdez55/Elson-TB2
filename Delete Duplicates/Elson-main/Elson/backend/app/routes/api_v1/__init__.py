from fastapi import APIRouter
from .trading import router as trading_router
from .users import router as users_router
from .portfolio import router as portfolio_router
from .family import router as family_router
from .ai import router as ai_router
from .risk import router as risk_router
from .education import router as education_router
from .subscription_routes import router as subscription_router
from .webhook_routes import router as webhook_router
from .market_data_routes import router as market_data_router
from .market_routes import router as market_router
from .model_performance import router as model_performance_router
from ..investment_routes import router as investment_router
from ..auth_routes import router as auth_router

# Create main v1 router
api_router = APIRouter()

# Include all route modules
api_router.include_router(trading_router, prefix="/trading", tags=["trading"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(family_router, prefix="/family", tags=["family"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(risk_router, prefix="/risk", tags=["risk"])
api_router.include_router(education_router, prefix="/education", tags=["education"])
api_router.include_router(investment_router, prefix="/investments", tags=["investments"])
api_router.include_router(subscription_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(market_data_router, prefix="/market-data", tags=["market-data"])
api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(model_performance_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(auth_router, tags=["auth"])

# This makes the routes accessible as:
# /api/v1/trading/...
# /api/v1/users/...
# /api/v1/portfolio/...
# /api/v1/family/...
# /api/v1/ai/...
# /api/v1/education/...