from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import redis
from starlette.middleware.sessions import SessionMiddleware
from prometheus_client import make_asgi_app
import time
import gc

from .core.config import settings
from .core.logging import setup_logging
from .core.centralized_logging import setup_centralized_logging, shutdown_logging
from .core.security import CSRFMiddleware, SecurityHeadersMiddleware, brute_force_protection
from .core.metrics import MetricsMiddleware, update_circuit_breaker_metrics
from .core.middleware import add_middleware, PerformanceHeadersMiddleware, ResponseCachingMiddleware, RateLimitMiddleware
from .core.caching import clear_all_cache
from .core.background import start_worker_thread, stop_worker_thread
from .db.database import engine, SessionLocal
from .routes.api_v1 import api_router
from .routes.websocket import market_feed
from .services.market_data import MarketDataService
from .services.market_data_streaming import get_streaming_service
from .services.neural_network import PredictionService
from ..trading_engine.engine.circuit_breaker import get_circuit_breaker

# Setup logging
setup_logging()
# Setup centralized logging with ELK stack
if settings.ELK_LOGGING_ENABLED:
    setup_centralized_logging()
logger = logging.getLogger(__name__)

# Create database tables
from .db.database import Base, init_db
# Create all tables
Base.metadata.create_all(bind=engine)
# Initialize database with any additional setup
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_time = time.time()
    logger.info("Starting up trading bot application...")
    
    # Initialize services
    market_service = MarketDataService(
        api_key=settings.SCHWAB_API_KEY,
        api_secret=settings.SCHWAB_SECRET
    )
    app.state.market_service = market_service
    
    prediction_service = PredictionService(market_service)
    app.state.prediction_service = prediction_service
    
    # Initialize market data streaming service
    streaming_service = get_streaming_service()
    app.state.streaming_service = streaming_service
    
    # Initialize circuit breaker
    circuit_breaker = get_circuit_breaker()
    app.state.circuit_breaker = circuit_breaker
    
    # Initialize background task processing
    start_worker_thread()
    logger.info("Background task processor initialized")
    
    # Clear cache on startup
    clear_all_cache()
    logger.info("Cache cleared during startup")
    
    # Schedule regular metrics updates and maintenance tasks
    @app.on_event("startup")
    async def startup_event():
        import asyncio
        
        async def update_metrics():
            while True:
                try:
                    # Update circuit breaker metrics
                    breakers = circuit_breaker.get_status()
                    breaker_counts = {}
                    for key, breaker in breakers.items():
                        breaker_type = breaker.get("type", "unknown")
                        if breaker_type not in breaker_counts:
                            breaker_counts[breaker_type] = 0
                        breaker_counts[breaker_type] += 1
                    
                    update_circuit_breaker_metrics(breaker_counts)
                    
                except Exception as e:
                    logger.error(f"Error updating metrics: {str(e)}")
                
                await asyncio.sleep(15)  # Update every 15 seconds
        
        async def run_garbage_collection():
            """Periodically run garbage collection to free memory."""
            while True:
                try:
                    # Only run when not in debug mode (not needed during development)
                    if not settings.DEBUG:
                        # Collect statistics before GC
                        objects_before = len(gc.get_objects())
                        memory_before = gc.get_count()
                        
                        # Run garbage collection
                        collected = gc.collect(2)  # Full collection
                        
                        # Log results
                        objects_after = len(gc.get_objects())
                        memory_after = gc.get_count()
                        logger.debug(f"GC: Collected {collected} objects. "
                                    f"Objects: {objects_before} → {objects_after}, "
                                    f"Memory: {memory_before} → {memory_after}")
                except Exception as e:
                    logger.error(f"Error in garbage collection: {e}")
                
                # Run every 10 minutes
                await asyncio.sleep(600)
        
        # Start background tasks
        asyncio.create_task(update_metrics())
        asyncio.create_task(run_garbage_collection())
    
    # Log startup time
    startup_time = time.time() - start_time
    logger.info(f"Application startup completed in {startup_time:.2f} seconds")
    
    yield
    
    # Shutdown
    logger.info("Shutting down trading bot application...")
    
    # Stop background task processing
    stop_worker_thread()
    logger.info("Background task processor stopped")
    
    # Close services
    await market_service.close()
    
    # Stop streaming service
    await streaming_service.stop()
    logger.info("Market data streaming service stopped")
    
    # Clear cache on shutdown
    clear_all_cache()
    logger.info("Cache cleared during shutdown")
    
    # Shutdown centralized logging
    if settings.ELK_LOGGING_ENABLED:
        shutdown_logging()
        logger.info("Centralized logging shut down")

app = FastAPI(
    title="Trading Bot API",
    description="API for automated trading system with ML predictions",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,  # Hide docs in production
    redoc_url="/api/redoc" if settings.DEBUG else None,  # Hide redoc in production
)

# Store startup time for uptime calculation
app.state.startup_time = time.time()

# Create metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Add Prometheus metrics middleware
app.add_middleware(MetricsMiddleware)

# Add security middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"] if settings.DEBUG else settings.ALLOWED_ORIGINS)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add performance optimization middleware
add_middleware(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket routes
app.include_router(market_feed.router)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Include additional health metrics
    from app.core.background import get_queue_status
    
    # Basic health status
    health_data = {
        "status": "healthy", 
        "version": settings.VERSION,
        "timestamp": int(time.time()),
        "uptime": int(time.time() - app.state.startup_time),
    }
    
    # Add background task status
    health_data["background_tasks"] = get_queue_status()
    
    # Add streaming service status
    streaming_service = get_streaming_service()
    health_data["streaming"] = {
        "active": streaming_service.stream_active,
        "connections": sum(streaming_service.connection_status.values()),
        "client_count": len(getattr(streaming_service.websocket_manager, "active_connections", [])),
        "subscription_count": len(getattr(streaming_service.websocket_manager, "subscriptions", {}))
    }
    
    # Add memory usage if not in debug mode
    if not settings.DEBUG:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        health_data["memory"] = {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024)
        }
    
    return health_data

@app.middleware("http")
async def check_brute_force_protection(request: Request, call_next):
    """Middleware to check for IP lockouts due to brute force attempts"""
    # Skip for non-login endpoints
    if not request.url.path.endswith("/login/access-token"):
        return await call_next(request)
        
    # Check if IP is locked out
    client_ip = request.client.host
    is_locked, remaining = brute_force_protection.is_locked_out(client_ip)
    
    if is_locked:
        logger.warning(f"Blocked login attempt from locked out IP: {client_ip}")
        return {"detail": f"Too many failed attempts. Try again in {remaining} seconds."}
        
    # Continue with the request
    response = await call_next(request)
    
    # Record the attempt result
    if request.method == "POST" and request.url.path.endswith("/login/access-token"):
        success = response.status_code == 200
        brute_force_protection.record_attempt(client_ip, success)
        
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)