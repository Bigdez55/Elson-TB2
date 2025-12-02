import os
from typing import List, Optional, Dict
from functools import lru_cache
from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings


class BrokerEnum(str, Enum):
    """Supported broker types."""
    PAPER = "paper"
    SCHWAB = "schwab"
    ALPACA = "alpaca"


class ApiProviderEnum(str, Enum):
    """Supported API providers."""
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    FMP = "fmp"
    POLYGON = "polygon"
    COINBASE = "coinbase"


class Settings(BaseSettings):
    # Application Settings
    PROJECT_NAME: str = "Elson Wealth"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = "development"  # "development", "staging", "production", "testing"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "elson-trading-super-secret-key-for-development-change-in-production-32-chars-minimum")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trading_platform.db")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    DB_ECHO_SQL: bool = False

    # Broker Configuration
    DEFAULT_BROKER: str = os.getenv("DEFAULT_BROKER", "alpaca")
    BROKER_PRIORITY_LIST: List[str] = ["alpaca", "paper"]
    BROKER_FAILURE_THRESHOLD: int = 3
    BROKER_RETRY_INTERVAL: int = 60  # seconds
    LIVE_TRADING_ENABLED: bool = os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"
    USE_PAPER_TRADING: bool = os.getenv("USE_PAPER_TRADING", "true").lower() == "true"

    # Paper Trading Settings
    PAPER_TRADING_ENABLED: bool = True
    PAPER_TRADING_SLIPPAGE: float = 0.0005  # 0.05% slippage
    PAPER_TRADING_COMMISSION: float = 0.99  # Fixed commission per trade
    PAPER_TRADING_DELAY_SECONDS: int = 1  # Simulated execution delay

    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:8000",
    ]

    # API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    POLYGON_API_KEY: Optional[str] = os.getenv("POLYGON_API_KEY")
    ALPACA_API_KEY: Optional[str] = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY: Optional[str] = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    FINNHUB_API_KEY: Optional[str] = os.getenv("FINNHUB_API_KEY")
    FMP_API_KEY: Optional[str] = os.getenv("FMP_API_KEY")
    COINBASE_API_KEY: Optional[str] = os.getenv("COINBASE_API_KEY")

    # API Provider Priority Lists
    DEFAULT_API_PROVIDER_PRIORITY: List[str] = [
        "alpha_vantage",
        "finnhub",
        "fmp",
        "polygon",
        "coinbase"
    ]
    MARKET_DATA_PROVIDER_PRIORITY: List[str] = [
        "alpha_vantage",
        "finnhub",
        "polygon"
    ]
    COMPANY_DATA_PROVIDER_PRIORITY: List[str] = [
        "fmp",
        "alpha_vantage",
        "finnhub"
    ]
    CRYPTO_DATA_PROVIDER_PRIORITY: List[str] = [
        "coinbase",
        "alpha_vantage"
    ]
    API_FAILURE_THRESHOLD: int = 3
    API_RETRY_INTERVAL: int = 300  # seconds

    # Redis Configuration
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_TIMEOUT: int = 2  # Connection timeout in seconds

    # Redis Sentinel for High Availability
    REDIS_SENTINEL_ENABLED: bool = False
    REDIS_SENTINEL_MASTER: str = "mymaster"
    REDIS_SENTINEL_HOSTS: List[str] = ["sentinel1:26379", "sentinel2:26379", "sentinel3:26379"]
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    # Redis Cluster for Horizontal Scaling
    REDIS_CLUSTER_ENABLED: bool = False
    REDIS_CLUSTER_NODES: List[str] = ["redis-node1:6379", "redis-node2:6379", "redis-node3:6379"]

    # Caching Settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SHORT: int = 60           # 1 minute
    CACHE_TTL_MEDIUM: int = 300         # 5 minutes
    CACHE_TTL_LONG: int = 3600          # 1 hour
    CACHE_TTL_VERY_LONG: int = 86400    # 24 hours

    # Stripe Payment Processing
    STRIPE_API_KEY: Optional[str] = os.getenv("STRIPE_API_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Subscription Price IDs for Stripe
    STRIPE_PRICE_IDS: Dict[str, Dict[str, str]] = {
        "premium": {
            "monthly": os.getenv("STRIPE_PREMIUM_MONTHLY_PRICE_ID", "price_premium_monthly"),
            "annually": os.getenv("STRIPE_PREMIUM_ANNUAL_PRICE_ID", "price_premium_annually"),
        },
        "family": {
            "monthly": os.getenv("STRIPE_FAMILY_MONTHLY_PRICE_ID", "price_family_monthly"),
            "annually": os.getenv("STRIPE_FAMILY_ANNUAL_PRICE_ID", "price_family_annually"),
        }
    }

    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "trading_bot.log"
    LOG_RETENTION_DAYS: int = 90
    LOG_BACKUP_COUNT: int = 10

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 100

    # Trading Settings
    DEFAULT_COMMISSION_RATE: float = 0.0035  # 0.35%
    MIN_ORDER_AMOUNT: float = 1.0
    MAX_ORDER_AMOUNT: float = 1000000.0
    RISK_FREE_RATE: float = 0.02  # 2% annual risk-free rate

    # Fractional Share Settings
    FRACTIONAL_SHARE_ENABLED: bool = True
    MIN_FRACTIONAL_AMOUNT: float = 1.0
    MIN_FRACTIONAL_QUANTITY: float = 0.0001
    FRACTIONAL_PRECISION: int = 8
    AUTO_AGGREGATE_FRACTIONAL_ORDERS: bool = True
    AGGREGATION_THRESHOLD: float = 100.0
    MAX_AGGREGATION_DELAY_MINUTES: int = 15

    # Secrets Management
    SECRET_BACKEND: str = "env"  # "env", "vault", or "aws"

    # HashiCorp Vault
    VAULT_ENABLED: bool = False
    VAULT_URL: Optional[str] = os.getenv("VAULT_URL")
    VAULT_TOKEN: Optional[str] = os.getenv("VAULT_TOKEN")
    VAULT_SECRET_PATH: str = "elson/secrets"

    # AWS Secrets Manager
    AWS_SECRETS_ENABLED: bool = False
    AWS_REGION: Optional[str] = os.getenv("AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")

    # Educational Mode Settings
    EDUCATIONAL_MODE_ENABLED: bool = True
    EDUCATIONAL_MODE_TOOLTIPS: bool = True
    EDUCATIONAL_MODE_SIMPLIFIED_UI: bool = True
    EDUCATIONAL_MODE_RISK_LIMITS: bool = True

    # Age-based Permission Settings
    MINOR_AGE_RANGES: dict = {
        "children": {"min": 8, "max": 12},
        "teens": {"min": 13, "max": 17}
    }
    MINOR_TRADE_LIMITS: dict = {
        "children": {"max_order_amount": 100.0, "requires_approval": True},
        "teens": {"max_order_amount": 500.0, "requires_approval": True}
    }

    # Model Settings
    MODEL_UPDATE_INTERVAL: int = 24  # hours
    PREDICTION_CACHE_TTL: int = 300  # seconds
    MIN_TRAINING_DAYS: int = 365
    CONFIDENCE_THRESHOLD: float = 0.7

    # Performance Settings
    BACKGROUND_WORKERS: int = 10
    QUERY_TIMEOUT_SECONDS: int = 30
    MAX_REQUEST_CONCURRENCY: int = 50

    # Cloud Run specific
    PORT: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
