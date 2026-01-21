import os
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.logging_config import (
    clear_session_context,
    configure_logging,
    set_session_context,
)
from app.db.init_db import init_db

# WebSocket route imports
from app.routes.websocket import market_feed, trading_updates
from app.services.market_streaming import personal_market_streaming

# Configure logging
configure_logging(
    log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO"
)
logger = structlog.get_logger()


def create_application() -> FastAPI:
    application = FastAPI(
        title="Elson Personal Trading Platform",
        description=("AI-driven personal trading and portfolio management platform"),
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    )

    # Logging context middleware
    @application.middleware("http")
    async def logging_context_middleware(request: Request, call_next):
        # Set session context for logging
        session_id = str(uuid.uuid4())
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        user_id = getattr(request.state, "user_id", None)

        set_session_context(
            session_id=session_id, user_id=user_id, request_id=request_id
        )

        try:
            response = await call_next(request)
            return response
        finally:
            clear_session_context()

    # Security middleware
    application.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    application.include_router(api_router, prefix="/api/v1")

    # Include WebSocket routers
    application.include_router(market_feed.router, tags=["websocket"])
    application.include_router(trading_updates.router, tags=["websocket"])

    return application


app = create_application()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Elson Trading Platform")
    await init_db()

    # Start the market streaming service
    try:
        await personal_market_streaming.start_streaming()
        logger.info("Market streaming service started successfully")
    except Exception as e:
        logger.error(f"Failed to start market streaming service: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Elson Trading Platform")

    # Stop the market streaming service
    try:
        await personal_market_streaming.stop_streaming()
        logger.info("Market streaming service stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping market streaming service: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Cloud Run.

    Returns database status and whether using fallback database.
    """
    from app.db.base import is_database_healthy, is_using_fallback_database

    db_healthy = is_database_healthy()
    using_fallback = is_using_fallback_database()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": "elson-trading-platform",
        "database": {
            "connected": db_healthy,
            "fallback_mode": using_fallback,
        },
    }


@app.get("/")
async def root():
    return {"message": "Elson Personal Trading Platform API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True if settings.ENVIRONMENT == "development" else False,
    )
