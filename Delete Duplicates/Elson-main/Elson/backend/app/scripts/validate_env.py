#!/usr/bin/env python
"""
Production Environment Validation Script

This script validates that all required environment variables for production
are properly set and configured according to production best practices.

Updated to work with the current codebase structure and fix various issues 
related to circular dependencies and environment validation.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
import argparse
from pydantic import ValidationError

# Add the project root to sys.path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import without causing circular dependencies
from app.core.config import settings
Settings = type(settings)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("env-validator")

def validate_settings() -> Dict[str, Any]:
    """Validate settings based on the configured environment"""
    issues = {
        "critical": [],
        "warning": [],
        "info": [],
    }
    
    # Try to load settings
    try:
        settings = Settings()
        logger.info(f"Successfully loaded settings for environment: {settings.ENVIRONMENT}")
        
        # Perform specific validations based on environment
        if settings.ENVIRONMENT == "production":
            validate_production_settings(settings, issues)
        elif settings.ENVIRONMENT == "staging":
            validate_staging_settings(settings, issues)
        elif settings.ENVIRONMENT == "development":
            validate_development_settings(settings, issues)
            
    except ValidationError as e:
        for error in e.errors():
            issues["critical"].append(f"Validation error: {error['loc'][0]} - {error['msg']}")
        logger.error(f"Failed to load settings due to validation errors")
    except Exception as e:
        issues["critical"].append(f"Unexpected error loading settings: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
        
    return issues

def validate_production_settings(settings: Settings, issues: Dict[str, List[str]]) -> None:
    """Validate production-specific settings"""
    # Check database URL
    if "sqlite" in settings.DATABASE_URL:
        issues["critical"].append("Using SQLite database in production is not allowed")
    if "localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL:
        issues["warning"].append("Database URL contains localhost - ensure this is intentional")
    
    # Check Redis configuration
    if not settings.REDIS_SENTINEL_ENABLED and not settings.REDIS_CLUSTER_ENABLED:
        issues["warning"].append("Neither Redis Sentinel nor Cluster is enabled in production - this reduces availability")
    
    if not settings.REDIS_PASSWORD:
        issues["critical"].append("Redis password is not set in production")
    
    # Check broker and API configurations
    if settings.DEFAULT_BROKER == "paper":
        issues["warning"].append("Using paper trading broker as default in production")
    
    if settings.DEFAULT_BROKER == "schwab" and (not settings.SCHWAB_API_KEY or not settings.SCHWAB_SECRET):
        issues["critical"].append("Schwab broker is set as default but API credentials are missing")
    
    # Check for test API keys
    test_api_keys = {
        "ALPHA_VANTAGE_API_KEY": "A8M59L08MN0B61O7",
        "FINNHUB_API_KEY": "cv4i511r01qn2gaaafk0cv4i511r01qn2gaaafkg",
        "FMP_API_KEY": "TXEInHh2qwGikT5fOwmqPQOjIntkYkVI"
    }
    
    for key_name, test_value in test_api_keys.items():
        if getattr(settings, key_name) == test_value:
            issues["critical"].append(f"Using test/development {key_name} in production")
    
    # Validate Stripe configuration
    if not settings.STRIPE_API_KEY or not settings.STRIPE_WEBHOOK_SECRET:
        issues["critical"].append("Stripe API key or webhook secret not configured in production")
    elif settings.STRIPE_API_KEY.startswith("sk_test_"):
        issues["critical"].append("Using Stripe test API key in production")
    
    # Check for secure settings
    if settings.SECRET_KEY == "testsecretkey123456789testsecretkey123456789":
        issues["critical"].append("Using test SECRET_KEY in production")
    
    if settings.DEBUG:
        issues["critical"].append("DEBUG mode is enabled in production")
    
    # Check allowed origins
    if not settings.ALLOWED_ORIGINS:
        issues["warning"].append("No ALLOWED_ORIGINS configured - this will block all CORS requests")
    else:
        found_prod_domain = False
        for origin in settings.ALLOWED_ORIGINS:
            if "localhost" in origin or "127.0.0.1" in origin:
                issues["warning"].append(f"ALLOWED_ORIGINS contains local development domain: {origin}")
            if "elsonwealth.com" in origin or "earlysolutionspro.com" in origin:
                found_prod_domain = True
        
        if not found_prod_domain:
            issues["warning"].append("No production domain found in ALLOWED_ORIGINS")
    
    # Validate centralized logging is enabled
    if not settings.ELK_LOGGING_ENABLED:
        issues["warning"].append("Centralized logging (ELK) is not enabled in production")

def validate_staging_settings(settings: Settings, issues: Dict[str, List[str]]) -> None:
    """Validate staging-specific settings"""
    # Add staging-specific validations
    if settings.DEBUG:
        issues["warning"].append("DEBUG mode is enabled in staging environment")
    
    # More staging validations can be added here

def validate_development_settings(settings: Settings, issues: Dict[str, List[str]]) -> None:
    """Validate development-specific settings"""
    # Check if any live API keys are being used in development
    if settings.STRIPE_API_KEY and settings.STRIPE_API_KEY.startswith("sk_live_"):
        issues["warning"].append("Using Stripe live API key in development environment")

def main():
    parser = argparse.ArgumentParser(description="Validate environment settings")
    parser.add_argument("--env-file", help="Path to .env file to load")
    args = parser.parse_args()
    
    # Load specified env file if provided
    if args.env_file:
        if os.path.exists(args.env_file):
            logger.info(f"Loading environment from: {args.env_file}")
            os.environ["ENV_FILE"] = args.env_file
        else:
            logger.error(f"Environment file not found: {args.env_file}")
            sys.exit(1)
    
    issues = validate_settings()
    
    # Print summary of issues
    if issues["critical"]:
        print("\n❌ CRITICAL ISSUES:")
        for issue in issues["critical"]:
            print(f"  - {issue}")
    
    if issues["warning"]:
        print("\n⚠️ WARNINGS:")
        for issue in issues["warning"]:
            print(f"  - {issue}")
    
    if issues["info"]:
        print("\nℹ️ INFORMATION:")
        for issue in issues["info"]:
            print(f"  - {issue}")
    
    if not issues["critical"] and not issues["warning"] and not issues["info"]:
        print("\n✅ All environment settings are valid!")
        sys.exit(0)
    elif not issues["critical"]:
        print("\n✅ No critical issues found. Fix warnings before deploying to production.")
        sys.exit(0)
    else:
        print("\n❌ Critical issues must be fixed before deploying to production.")
        sys.exit(1)

if __name__ == "__main__":
    main()