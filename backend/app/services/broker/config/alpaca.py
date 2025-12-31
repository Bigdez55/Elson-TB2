"""Alpaca broker configuration.

This module contains constants and configuration for the Alpaca broker integration.
"""

from typing import Any, Dict

# API endpoints for Alpaca brokerage
PROD_API_BASE_URL = "https://api.alpaca.markets/v2"
PAPER_API_BASE_URL = "https://paper-api.alpaca.markets/v2"
DATA_API_BASE_URL = "https://data.alpaca.markets/v2"

# Endpoint paths
ORDER_ENDPOINT = "/orders"
ACCOUNT_ENDPOINT = "/account"
POSITIONS_ENDPOINT = "/positions"
ASSETS_ENDPOINT = "/assets"
WATCHLISTS_ENDPOINT = "/watchlists"
CALENDAR_ENDPOINT = "/calendar"
CLOCK_ENDPOINT = "/clock"
PORTFOLIO_HISTORY_ENDPOINT = "/account/portfolio/history"

# Rate limiting settings (requests per minute)
# https://alpaca.markets/docs/api-references/trading-api/#rate-limit
RATE_LIMIT = 200

# Default timeout settings (in seconds)
DEFAULT_TIMEOUT = 30
LONG_TIMEOUT = 60

# Default retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 0.5,
    "status_forcelist": [429, 500, 502, 503, 504],
    "allowed_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
}

# Authentication configuration
AUTH_METHOD = "api_key"

# Order type mapping
ORDER_TYPE_MAP = {
    "market": "market",
    "limit": "limit",
    "stop": "stop",
    "stop_limit": "stop_limit",
    "trailing_stop": "trailing_stop",
}

# Order side mapping
ORDER_SIDE_MAP = {"buy": "buy", "sell": "sell"}

# Time in force options
TIME_IN_FORCE_OPTIONS = ["day", "gtc", "opg", "cls", "ioc", "fok"]

# Default time in force
DEFAULT_TIME_IN_FORCE = "day"

# Status mapping (Alpaca API status → internal status)
STATUS_MAP = {
    "filled": "FILLED",
    "partially_filled": "PARTIALLY_FILLED",
    "new": "PENDING",
    "accepted": "PENDING",
    "pending_new": "PENDING",
    "accepted_for_bidding": "PENDING",
    "stopped": "PENDING",
    "rejected": "REJECTED",
    "canceled": "CANCELED",
    "pending_cancel": "PENDING_CANCEL",
    "expired": "EXPIRED",
    "done_for_day": "PENDING",
    "replaced": "PENDING",
    "pending_replace": "PENDING",
}

# Error codes and messages
ERROR_CODES = {
    "40010001": "Account is not authorized for trading",
    "40010002": "Account is not active",
    "40310000": "Invalid order quantity",
    "40310001": "Insufficient buying power",
    "40310002": "Insufficient shortable asset shares",
    "40310003": "Insufficient position shares",
    "40310004": "Symbol not shortable",
    "40310005": "Extended hours trading not available",
    "40310006": "Orders are not accepted in current account status",
    "40310007": "Price is too high relative to the last trade price",
    "40310008": "Price is too low relative to the last trade price",
    "40310009": "Notional value is too small",
    "40310010": "Notional value is too large",
    "40310011": "Invalid side",
    "40310013": "Invalid time in force",
    "40310014": "Invalid limit price",
    "40310015": "Invalid stop price",
    "40310016": "Invalid trail price or percent",
    "40310017": "Symbol not found or not tradable",
    "40310018": "Order would have executed on entry (market order protection)",
    "40310019": "Order would have executed on entry (stop/limit validation)",
    "40310020": "Self-trade prevention activated",
}

# Feature support flags
SUPPORTS_FRACTIONAL = True
SUPPORTS_EXTENDED_HOURS = True
SUPPORTS_BRACKET_ORDERS = True
SUPPORTS_TRAILING_STOPS = True
SUPPORTS_OTO_ORDERS = True
SUPPORTS_OCO_ORDERS = False  # Alpaca doesn't directly support OCO orders


def get_paper_config() -> Dict[str, Any]:
    """Get configuration for paper trading environment."""
    return {
        "api_base_url": PAPER_API_BASE_URL,
        "data_api_base_url": DATA_API_BASE_URL,
        "auth_method": AUTH_METHOD,
        "retry_config": RETRY_CONFIG,
        "timeout": DEFAULT_TIMEOUT,
        "rate_limit": RATE_LIMIT,
    }


def get_production_config() -> Dict[str, Any]:
    """Get configuration for production environment."""
    return {
        "api_base_url": PROD_API_BASE_URL,
        "data_api_base_url": DATA_API_BASE_URL,
        "auth_method": AUTH_METHOD,
        "retry_config": RETRY_CONFIG,
        "timeout": DEFAULT_TIMEOUT,
        "rate_limit": RATE_LIMIT,
    }
