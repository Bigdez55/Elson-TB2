"""Schwab broker configuration.

This module contains constants and configuration for the Schwab broker integration.
"""

from typing import Any, Dict

# API endpoints for Schwab brokerage
PROD_API_BASE_URL = "https://api.schwab.com/trade/v1"
SANDBOX_API_BASE_URL = "https://api-sandbox.schwab.com/trade/v1"

# Endpoint paths
ORDER_ENDPOINT = "/orders"
ACCOUNT_ENDPOINT = "/accounts"
QUOTES_ENDPOINT = "/market/quotes"
POSITIONS_ENDPOINT = "/positions"
MARKET_HOURS_ENDPOINT = "/market/hours"
EXECUTIONS_ENDPOINT = "/executions"

# Rate limiting settings (requests per minute)
RATE_LIMIT = 120

# Default timeout settings (in seconds)
DEFAULT_TIMEOUT = 30
LONG_TIMEOUT = 60

# Default retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 0.5,
    "status_forcelist": [429, 500, 502, 503, 504],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
}

# Authentication configuration
AUTH_CONFIG = {
    "token_url": "https://api.schwab.com/auth/oauth/v2/token",
    "auth_method": "oauth2",
    "token_expiry": 3600,  # 1 hour in seconds
}

# Sandbox authentication configuration
SANDBOX_AUTH_CONFIG = {
    "token_url": "https://api-sandbox.schwab.com/auth/oauth/v2/token",
    "auth_method": "oauth2",
    "token_expiry": 3600,  # 1 hour in seconds
}

# Order type mapping
ORDER_TYPE_MAP = {
    "market": "MARKET",
    "limit": "LIMIT",
    "stop": "STOP",
    "stop_limit": "STOP_LIMIT",
    "trailing_stop": "TRAILING_STOP",
}

# Order side mapping
ORDER_SIDE_MAP = {
    "buy": "BUY",
    "sell": "SELL",
    "buy_to_cover": "BUY_TO_COVER",
    "sell_short": "SELL_SHORT",
}

# Time in force options
TIME_IN_FORCE_OPTIONS = ["DAY", "GTC", "IOC", "FOK", "EXT"]

# Default time in force
DEFAULT_TIME_IN_FORCE = "DAY"

# Asset type mapping
ASSET_TYPE_MAP = {
    "equity": "EQUITY",
    "option": "OPTION",
    "etf": "ETF",
    "mutual_fund": "MUTUAL_FUND",
    "bond": "BOND",
}

# Status mapping (Schwab API status → internal status)
STATUS_MAP = {
    "FILLED": "FILLED",
    "PARTIALLY_FILLED": "PARTIALLY_FILLED",
    "PENDING": "PENDING",
    "NEW": "PENDING",
    "QUEUED": "PENDING",
    "ACCEPTED": "PENDING",
    "WORKING": "PENDING",
    "REJECTED": "REJECTED",
    "CANCELED": "CANCELED",
    "EXPIRED": "EXPIRED",
    "ERROR": "ERROR",
    "REPLACED": "PENDING",
}

# Error codes and messages
ERROR_CODES = {
    "INSUFFICIENT_FUNDS": "Account has insufficient funds for this transaction",
    "INVALID_SYMBOL": "The requested symbol is invalid or not tradable",
    "MARKET_CLOSED": "The market is currently closed for this security",
    "INVALID_QUANTITY": "The requested quantity is invalid",
    "INVALID_PRICE": "The requested price is invalid",
    "ACCOUNT_RESTRICTED": "The account is restricted from trading",
    "INVALID_ORDER_TYPE": "The order type is invalid for this security",
    "INVALID_TIME_IN_FORCE": "The time in force is invalid for this order type",
}

# Feature support flags
SUPPORTS_FRACTIONAL = True
SUPPORTS_EXTENDED_HOURS = True
SUPPORTS_BRACKET_ORDERS = True
SUPPORTS_TRAILING_STOPS = True
SUPPORTS_OTO_ORDERS = True
SUPPORTS_OCO_ORDERS = True


def get_sandbox_config() -> Dict[str, Any]:
    """Get configuration for sandbox environment."""
    return {
        "api_base_url": SANDBOX_API_BASE_URL,
        "auth_config": SANDBOX_AUTH_CONFIG,
        "retry_config": RETRY_CONFIG,
        "timeout": DEFAULT_TIMEOUT,
        "rate_limit": RATE_LIMIT,
    }


def get_production_config() -> Dict[str, Any]:
    """Get configuration for production environment."""
    return {
        "api_base_url": PROD_API_BASE_URL,
        "auth_config": AUTH_CONFIG,
        "retry_config": RETRY_CONFIG,
        "timeout": DEFAULT_TIMEOUT,
        "rate_limit": RATE_LIMIT,
    }
