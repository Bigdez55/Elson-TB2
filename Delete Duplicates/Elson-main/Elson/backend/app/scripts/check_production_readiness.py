#!/usr/bin/env python
"""
Production Readiness Check

This script performs a comprehensive analysis of the Elson Wealth App 
to determine if it's ready for production deployment.
"""

import os
import sys
import logging
import argparse
import requests
import socket
import time
import json
from typing import Dict, List, Any, Tuple, Set, Optional
import importlib.util

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("production-readiness")

def check_environment_variables() -> Tuple[List[str], List[str]]:
    """
    Check if all required environment variables are set for production.
    
    Returns:
        Tuple of (missing_variables, insecure_variables)
    """
    # Import settings to check environment variables
    from app.core.config import settings
    
    # Required environment variables for production
    required_vars = [
        "SECRET_KEY",
        "DATABASE_URL",
        "ALLOWED_ORIGINS",
        "ALPHA_VANTAGE_API_KEY",
        "FINNHUB_API_KEY",
        "FMP_API_KEY",
    ]
    
    # Check if we're using the default broker and add its required keys
    if settings.DEFAULT_BROKER == "schwab":
        required_vars.extend(["SCHWAB_API_KEY", "SCHWAB_SECRET"])
    
    # Add Stripe keys if in production
    if settings.ENVIRONMENT == "production":
        required_vars.extend(["STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET"])
    
    # Check for missing variables
    missing_vars = []
    for var in required_vars:
        value = getattr(settings, var, None)
        if value is None or value == "":
            missing_vars.append(var)
    
    # Check for insecure variables
    insecure_vars = []
    
    # Check SECRET_KEY
    if len(settings.SECRET_KEY) < 32:
        insecure_vars.append("SECRET_KEY (too short)")
    
    if settings.SECRET_KEY == "testsecretkey123456789testsecretkey123456789":
        insecure_vars.append("SECRET_KEY (using test key)")
    
    # Check test API keys
    test_keys = {
        "ALPHA_VANTAGE_API_KEY": "A8M59L08MN0B61O7",
        "FINNHUB_API_KEY": "cv4i511r01qn2gaaafk0cv4i511r01qn2gaaafkg",
        "FMP_API_KEY": "TXEInHh2qwGikT5fOwmqPQOjIntkYkVI"
    }
    
    for key_name, test_value in test_keys.items():
        if getattr(settings, key_name, None) == test_value:
            insecure_vars.append(f"{key_name} (using test key)")
    
    # Check for SQLite in production
    if settings.ENVIRONMENT == "production" and "sqlite" in settings.DATABASE_URL:
        insecure_vars.append("DATABASE_URL (using SQLite in production)")
    
    # Check for debug mode in production
    if settings.ENVIRONMENT == "production" and settings.DEBUG:
        insecure_vars.append("DEBUG (enabled in production)")
        
    return missing_vars, insecure_vars

def check_database_connection() -> Tuple[bool, str]:
    """
    Check if the database connection is working.
    
    Returns:
        (success, message)
    """
    try:
        from app.db.database import engine
        from sqlalchemy import text
        
        # Try to connect to the database
        with engine.connect() as connection:
            # Execute a simple query
            result = connection.execute(text("SELECT 1")).fetchone()
            
            if result and result[0] == 1:
                return True, "Database connection successful"
            else:
                return False, "Database connection failed - query returned unexpected result"
    
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

def check_redis_connection() -> Tuple[bool, str, Optional[Dict]]:
    """
    Check if the Redis connection is working.
    
    Returns:
        (success, message, info)
    """
    try:
        from app.db.database import get_redis_connection
        from app.core.config import settings
        
        # Try to connect to Redis
        redis_conn = get_redis_connection()
        
        # In development mode, Redis might not be available but that's ok
        if redis_conn is None:
            if settings.ENVIRONMENT in ["development", "test"]:
                return True, "Redis not available in development mode (optional)", None
            else:
                return False, "Redis connection failed: Redis connection returned None", None
        
        # Try a simple operation
        redis_conn.set("production_check", "1")
        result = redis_conn.get("production_check")
        redis_conn.delete("production_check")
        
        if result == b"1":
            # Get some info about Redis
            info = redis_conn.info()
            return True, "Redis connection successful", {
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_days": round(int(info.get("uptime_in_seconds", 0)) / 86400, 2)
            }
        else:
            return False, "Redis connection failed - operation returned unexpected result", None
    
    except Exception as e:
        from app.core.config import settings
        if settings.ENVIRONMENT in ["development", "test"]:
            return True, f"Redis not available in development mode (optional): {str(e)}", None
        else:
            return False, f"Redis connection failed: {str(e)}", None

def check_api_health(url: str = "http://localhost:8000/health") -> Tuple[bool, str, Optional[Dict]]:
    """
    Check if the API health endpoint is responding.
    
    Returns:
        (success, message, health_data)
    """
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            return True, "API health check successful", health_data
        else:
            return False, f"API health check failed with status code {response.status_code}", None
    
    except requests.exceptions.RequestException as e:
        return False, f"API health check failed: {str(e)}", None

def check_websocket_availability(host: str = "localhost", port: int = 8000, path: str = "/ws") -> Tuple[bool, str]:
    """
    Check if the WebSocket server is listening.
    
    Returns:
        (success, message)
    """
    try:
        # Just check if the socket is open - we don't actually connect with WebSocket protocol
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True, f"Port {port} is open for WebSocket connections"
        else:
            return False, f"Port {port} is closed or not accessible"
    
    except Exception as e:
        return False, f"WebSocket check failed: {str(e)}"

def check_database_migrations() -> Tuple[bool, str, Optional[Dict]]:
    """
    Check if all database migrations have been applied.
    
    Returns:
        (success, message, migration_data)
    """
    try:
        # Check if alembic is installed
        if importlib.util.find_spec("alembic") is None:
            return False, "Alembic is not installed", None
        
        # Import alembic config and functions
        import alembic.config
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        
        # Get alembic config
        config = alembic.config.Config("alembic.ini")
        script = ScriptDirectory.from_config(config)
        
        # Get the current database revision
        from app.db.database import engine
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
        
        # Get the latest available revision
        head_rev = script.get_current_head()
        
        if current_rev == head_rev:
            return True, "Database is up to date with the latest migration", {
                "current_revision": current_rev,
                "latest_revision": head_rev,
                "status": "up_to_date"
            }
        else:
            return False, "Database is not up to date with the latest migration", {
                "current_revision": current_rev,
                "latest_revision": head_rev,
                "status": "needs_upgrade"
            }
    
    except Exception as e:
        return False, f"Migration check failed: {str(e)}", None

def perform_model_validation() -> Tuple[bool, List[str]]:
    """
    Validate that all models load and initialize correctly.
    
    Returns:
        (success, errors)
    """
    errors = []
    
    try:
        # Import all models
        from app.models import user, portfolio, trade, account, notification, education, subscription
        
        # List of all model files to check
        model_modules = [user, portfolio, trade, account, notification, education, subscription]
        
        for module in model_modules:
            # Get all classes in the module that might be models
            for name in dir(module):
                if name.startswith('_'):
                    continue
                
                try:
                    # Try to access the class
                    cls = getattr(module, name)
                    # Check if it's a SQLAlchemy model class
                    from app.models.base import Base
                    if isinstance(cls, type) and issubclass(cls, Base) and cls != Base:
                        # It's a model class, check if it has expected attributes
                        if not hasattr(cls, '__tablename__'):
                            errors.append(f"Model {module.__name__}.{name} missing __tablename__")
                except Exception as e:
                    errors.append(f"Error validating model {module.__name__}.{name}: {str(e)}")
        
        return len(errors) == 0, errors
    
    except Exception as e:
        errors.append(f"Model validation failed: {str(e)}")
        return False, errors

def check_api_integration() -> Dict[str, Any]:
    """
    Check if API integration points are configured correctly.
    
    Returns:
        Results dictionary
    """
    results = {}
    
    # Check Schwab integration
    try:
        from app.core.config import settings
        from app.services.broker.schwab import SchwabBroker
        
        if settings.SCHWAB_API_KEY and settings.SCHWAB_SECRET:
            # Just create an instance to check initialization
            broker = SchwabBroker(api_key=settings.SCHWAB_API_KEY, secret=settings.SCHWAB_SECRET)
            results["schwab"] = {
                "status": "configured",
                "api_key_set": bool(settings.SCHWAB_API_KEY),
                "secret_set": bool(settings.SCHWAB_SECRET)
            }
        else:
            results["schwab"] = {
                "status": "not_configured",
                "api_key_set": bool(settings.SCHWAB_API_KEY),
                "secret_set": bool(settings.SCHWAB_SECRET)
            }
    except Exception as e:
        results["schwab"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Alpaca integration
    try:
        from app.core.config import settings
        from app.services.broker.alpaca import AlpacaBroker
        
        if settings.ALPACA_API_KEY_ID and settings.ALPACA_API_SECRET:
            # Just create an instance to check initialization
            broker = AlpacaBroker(api_key=settings.ALPACA_API_KEY_ID, secret=settings.ALPACA_API_SECRET)
            results["alpaca"] = {
                "status": "configured",
                "api_key_set": bool(settings.ALPACA_API_KEY_ID),
                "secret_set": bool(settings.ALPACA_API_SECRET)
            }
        else:
            results["alpaca"] = {
                "status": "not_configured",
                "api_key_set": bool(settings.ALPACA_API_KEY_ID),
                "secret_set": bool(settings.ALPACA_API_SECRET)
            }
    except Exception as e:
        results["alpaca"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check market data API providers
    for provider in ["alpha_vantage", "finnhub", "fmp", "polygon", "coinbase"]:
        try:
            # Import the API factory
            from app.services.external_api.factory import get_api_client
            
            # Try to get a client for this provider
            client = get_api_client(provider)
            
            if client:
                results[provider] = {
                    "status": "available",
                    "class": client.__class__.__name__
                }
            else:
                results[provider] = {
                    "status": "not_available"
                }
        except Exception as e:
            results[provider] = {
                "status": "error",
                "error": str(e)
            }
    
    # Check Stripe configuration
    try:
        from app.core.config import settings
        
        if settings.STRIPE_API_KEY and settings.STRIPE_WEBHOOK_SECRET:
            results["stripe"] = {
                "status": "configured",
                "api_key_set": bool(settings.STRIPE_API_KEY),
                "webhook_secret_set": bool(settings.STRIPE_WEBHOOK_SECRET)
            }
        else:
            results["stripe"] = {
                "status": "not_configured",
                "api_key_set": bool(settings.STRIPE_API_KEY),
                "webhook_secret_set": bool(settings.STRIPE_WEBHOOK_SECRET)
            }
    except Exception as e:
        results["stripe"] = {
            "status": "error",
            "error": str(e)
        }
    
    return results

def main():
    """Main function to run all production readiness checks."""
    parser = argparse.ArgumentParser(description="Check production readiness for Elson Wealth App")
    parser.add_argument("--env-file", help="Path to .env file to load")
    parser.add_argument("--health-url", default="http://localhost:8000/health", help="URL for API health check")
    parser.add_argument("--websocket-host", default="localhost", help="Host for WebSocket check")
    parser.add_argument("--websocket-port", type=int, default=8000, help="Port for WebSocket check")
    parser.add_argument("--output", help="Output file for JSON report")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    # Load specified env file if provided
    if args.env_file:
        if os.path.exists(args.env_file):
            logger.info(f"Loading environment from: {args.env_file}")
            os.environ["ENV_FILE"] = args.env_file
        else:
            logger.error(f"Environment file not found: {args.env_file}")
            sys.exit(1)
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Start time for performance measurement
    start_time = time.time()
    
    # Initialize results dictionary
    results = {
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Check environment variables
    logger.info("Checking environment variables...")
    missing_vars, insecure_vars = check_environment_variables()
    results["checks"]["environment_variables"] = {
        "missing_variables": missing_vars,
        "insecure_variables": insecure_vars,
        "status": "pass" if not missing_vars and not insecure_vars else "fail"
    }
    
    # Check database connection
    logger.info("Checking database connection...")
    db_success, db_message = check_database_connection()
    results["checks"]["database_connection"] = {
        "status": "pass" if db_success else "fail",
        "message": db_message
    }
    
    # Check Redis connection
    logger.info("Checking Redis connection...")
    redis_success, redis_message, redis_info = check_redis_connection()
    results["checks"]["redis_connection"] = {
        "status": "pass" if redis_success else "fail",
        "message": redis_message
    }
    if redis_info:
        results["checks"]["redis_connection"]["info"] = redis_info
    
    # Check database migrations
    logger.info("Checking database migrations...")
    migration_success, migration_message, migration_data = check_database_migrations()
    results["checks"]["database_migrations"] = {
        "status": "pass" if migration_success else "fail",
        "message": migration_message
    }
    if migration_data:
        results["checks"]["database_migrations"]["data"] = migration_data
    
    # Check model validation
    logger.info("Validating models...")
    model_success, model_errors = perform_model_validation()
    results["checks"]["model_validation"] = {
        "status": "pass" if model_success else "fail",
        "errors": model_errors
    }
    
    # Check API integration
    logger.info("Checking API integration...")
    api_integration_results = check_api_integration()
    
    # Determine overall API integration status
    required_integrations = ["schwab", "alpha_vantage", "finnhub", "fmp"]
    api_integration_success = all(
        api_integration_results.get(integration, {}).get("status") == "configured" 
        or api_integration_results.get(integration, {}).get("status") == "available"
        for integration in required_integrations
    )
    
    results["checks"]["api_integration"] = {
        "status": "pass" if api_integration_success else "fail",
        "providers": api_integration_results
    }
    
    # Try API health check if server is running
    logger.info(f"Checking API health at {args.health_url}...")
    try:
        health_success, health_message, health_data = check_api_health(args.health_url)
        results["checks"]["api_health"] = {
            "status": "pass" if health_success else "fail",
            "message": health_message
        }
        if health_data:
            results["checks"]["api_health"]["data"] = health_data
    except Exception as e:
        results["checks"]["api_health"] = {
            "status": "fail",
            "message": f"Health check error: {str(e)}"
        }
    
    # Try WebSocket check if server is running
    logger.info(f"Checking WebSocket availability at {args.websocket_host}:{args.websocket_port}...")
    try:
        ws_success, ws_message = check_websocket_availability(args.websocket_host, args.websocket_port)
        results["checks"]["websocket"] = {
            "status": "pass" if ws_success else "fail",
            "message": ws_message
        }
    except Exception as e:
        results["checks"]["websocket"] = {
            "status": "fail",
            "message": f"WebSocket check error: {str(e)}"
        }
    
    # Calculate overall status
    critical_checks = ["environment_variables", "database_connection", "redis_connection", 
                      "database_migrations", "model_validation", "api_integration"]
    
    critical_status = all(
        results["checks"].get(check, {}).get("status") == "pass"
        for check in critical_checks if check in results["checks"]
    )
    
    results["overall_status"] = "pass" if critical_status else "fail"
    results["execution_time"] = time.time() - start_time
    
    # Print summary
    print("\n=== Production Readiness Check Summary ===")
    print(f"Overall Status: {'✅ PASS' if results['overall_status'] == 'pass' else '❌ FAIL'}")
    print("\nResults by category:")
    
    for check, check_results in results["checks"].items():
        status_icon = "✅" if check_results.get("status") == "pass" else "❌"
        print(f"{status_icon} {check.replace('_', ' ').title()}: {check_results.get('message', '')}")
    
    print(f"\nExecution time: {results['execution_time']:.2f} seconds")
    
    # Save results to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main()