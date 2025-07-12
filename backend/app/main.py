import os

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.db.init_db import init_db

logger = structlog.get_logger()


def create_application() -> FastAPI:
    application = FastAPI(
        title="Elson Personal Trading Platform",
        description="AI-driven personal trading and portfolio management platform",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    )

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

    return application


app = create_application()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Elson Trading Platform")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Elson Trading Platform")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "elson-trading-platform"}


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
