import os
import secrets
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, validator
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
    VERSION: str = "1.0.0-beta"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = (
        "development"  # "development", "staging", "production", "testing"
    )

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    JWT_ENCRYPTION_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    COOKIE_ENCRYPTION_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    DATABASE_ENCRYPTION_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # Database
    DATABASE_URL: str = Field(default="")
    DB_POOL_SIZE: int = 10  # Increased pool size for better concurrency
    DB_MAX_OVERFLOW: int = 20  # Increased overflow for peak loads
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    DB_ECHO_SQL: bool = False  # Set to True to log all SQL queries (dev only)
    
    # Cloud SQL Configuration
    CLOUD_SQL_CONNECTION_NAME: Optional[str] = None
    CLOUD_SQL_DATABASE_NAME: str = "elson_production"
    CLOUD_SQL_USERNAME: str = "elson_app"
    CLOUD_SQL_PASSWORD: str = Field(default="")
    CLOUD_SQL_HOST: str = "127.0.0.1"
    CLOUD_SQL_PORT: int = 5432

    # Broker Selection
    DEFAULT_BROKER: BrokerEnum = BrokerEnum.PAPER
    BROKER_PRIORITY_LIST: List[BrokerEnum] = [
        BrokerEnum.SCHWAB,
        BrokerEnum.ALPACA,
        BrokerEnum.PAPER,
    ]
    BROKER_FAILURE_THRESHOLD: int = 3
    BROKER_RETRY_INTERVAL: int = 60  # seconds

    # Paper Trading Settings
    PAPER_TRADING_ENABLED: bool = True
    PAPER_TRADING_SLIPPAGE: float = 0.0005  # 0.05% slippage
    PAPER_TRADING_COMMISSION: float = 0.99  # Fixed commission per trade
    PAPER_TRADING_DELAY_SECONDS: int = 1  # Simulated execution delay

    # Schwab API
    SCHWAB_API_KEY: Optional[str] = None
    SCHWAB_SECRET: Optional[str] = None
    SCHWAB_ORDER_LIMIT: int = 120

    # Alpaca API
    ALPACA_API_KEY_ID: Optional[str] = None
    ALPACA_API_SECRET: Optional[str] = None
    ALPACA_PAPER_TRADING: bool = True

    # Legacy naming for compatibility
    ALPACA_API_KEY: Optional[str] = None
    ALPACA_SECRET_KEY: Optional[str] = None

    # External API Providers
    ALPHA_VANTAGE_API_KEY: str = Field(default="")
    FINNHUB_API_KEY: str = Field(default="")
    FMP_API_KEY: str = Field(default="")
    POLYGON_API_KEY: Optional[str] = None
    COINBASE_API_KEY: Optional[str] = None

    # API Provider Configuration
    DEFAULT_API_PROVIDER_PRIORITY: List[ApiProviderEnum] = [
        ApiProviderEnum.ALPHA_VANTAGE,
        ApiProviderEnum.FINNHUB,
        ApiProviderEnum.FMP,
        ApiProviderEnum.POLYGON,
        ApiProviderEnum.COINBASE,
    ]

    # Feature-specific provider priorities
    MARKET_DATA_PROVIDER_PRIORITY: List[ApiProviderEnum] = [
        ApiProviderEnum.ALPHA_VANTAGE,
        ApiProviderEnum.FINNHUB,
        ApiProviderEnum.POLYGON,
    ]

    COMPANY_DATA_PROVIDER_PRIORITY: List[ApiProviderEnum] = [
        ApiProviderEnum.FMP,
        ApiProviderEnum.ALPHA_VANTAGE,
        ApiProviderEnum.FINNHUB,
    ]

    CRYPTO_DATA_PROVIDER_PRIORITY: List[ApiProviderEnum] = [
        ApiProviderEnum.COINBASE,
        ApiProviderEnum.ALPHA_VANTAGE,
    ]

    # API rate limiting and error handling
    API_FAILURE_THRESHOLD: int = 3
    API_RETRY_INTERVAL: int = 300  # seconds

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
    ]

    # Redis (for caching and rate limiting)
    REDIS_URL: str = "redis://redis:6379"
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_TIMEOUT: int = 2  # Connection timeout in seconds
    USE_MOCK_REDIS: bool = False  # Use mock Redis implementation for development

    # Redis Sentinel for High Availability
    REDIS_SENTINEL_ENABLED: bool = False
    REDIS_SENTINEL_MASTER: str = "mymaster"
    REDIS_SENTINEL_HOSTS: List[str] = [
        "sentinel1:26379",
        "sentinel2:26379",
        "sentinel3:26379",
    ]
    REDIS_PASSWORD: Optional[str] = None

    # Redis Cluster for Horizontal Scaling (alternative to Sentinel)
    REDIS_CLUSTER_ENABLED: bool = False
    REDIS_CLUSTER_NODES: List[str] = [
        "redis-node1:6379",
        "redis-node2:6379",
        "redis-node3:6379",
    ]

    # Session Management
    SESSION_ENABLED: bool = True
    SESSION_EXPIRY_MINUTES: int = 60 * 24  # 24 hours
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_REFRESH_THRESHOLD_MINUTES: int = (
        30  # Refresh session if less than this time left
    )

    # Caching Settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SHORT: int = 60  # 1 minute for frequently changing data
    CACHE_TTL_MEDIUM: int = 300  # 5 minutes for moderate data
    CACHE_TTL_LONG: int = 3600  # 1 hour for static data
    CACHE_TTL_VERY_LONG: int = 86400  # 24 hours for reference data

    # Performance Settings
    BACKGROUND_WORKERS: int = 10  # Number of background worker threads
    QUERY_TIMEOUT_SECONDS: int = 30  # Database query timeout
    MAX_REQUEST_CONCURRENCY: int = 50  # Maximum concurrent API requests
    RATE_LIMIT_ENABLED: bool = True  # Enable API rate limiting
    RATE_LIMIT_DEFAULT: int = 100  # Default requests per minute limit

    # Trading Settings
    DEFAULT_COMMISSION_RATE: float = 0.0035  # 0.35%
    MIN_ORDER_AMOUNT: float = 1.0
    MAX_ORDER_AMOUNT: float = 1000000.0
    RISK_FREE_RATE: float = 0.02  # 2% annual risk-free rate

    # Market Data Configuration
    USE_REAL_MARKET_DATA: bool = False
    ALPACA_WS_URL: str = "wss://stream.data.alpaca.markets/v2/iex"

    # Fractional Share Settings
    FRACTIONAL_SHARE_ENABLED: bool = True
    MIN_FRACTIONAL_AMOUNT: float = 1.0  # Minimum dollar amount for fractional orders
    MIN_FRACTIONAL_QUANTITY: float = 0.0001  # Minimum fractional share quantity
    FRACTIONAL_PRECISION: int = 8  # Decimal places for fractional quantities
    AUTO_AGGREGATE_FRACTIONAL_ORDERS: bool = True  # Auto-aggregate fractional orders
    AGGREGATION_THRESHOLD: float = 100.0  # Min amount to trigger immediate aggregation
    MAX_AGGREGATION_DELAY_MINUTES: int = 15  # Max time to wait for aggregation

    # System Accounts for Aggregation
    SYSTEM_USER_ID: int = 1  # System user ID for aggregated orders
    SYSTEM_PORTFOLIO_ID: int = 1  # System portfolio for aggregation

    # First superuser credentials
    FIRST_SUPERUSER_EMAIL: str = "admin@elsonwealth.com"
    FIRST_SUPERUSER_USERNAME: str = "admin"
    FIRST_SUPERUSER_PASSWORD: str = Field(default_factory=lambda: secrets.token_urlsafe(16))

    # Model Settings
    MODEL_UPDATE_INTERVAL: int = 24  # hours
    PREDICTION_CACHE_TTL: int = 300  # seconds
    MIN_TRAINING_DAYS: int = 365
    CONFIDENCE_THRESHOLD: float = 0.7

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "trading_bot.log"
    LOG_RETENTION_DAYS: int = 90  # Log retention period in days
    LOG_BACKUP_COUNT: int = 10  # Number of backup log files to keep

    # Secrets Management
    SECRET_BACKEND: str = "env"  # "env", "vault", "aws", or "gcp"

    # HashiCorp Vault
    VAULT_ENABLED: bool = False
    VAULT_URL: Optional[str] = None
    VAULT_TOKEN: Optional[str] = None
    VAULT_SECRET_PATH: str = "elson/secrets"

    # AWS Secrets Manager
    AWS_SECRETS_ENABLED: bool = False
    AWS_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # GCP Secret Manager
    GCP_SECRETS_ENABLED: bool = False
    GCP_PROJECT_ID: Optional[str] = None
    GCP_SERVICE_ACCOUNT_KEY_PATH: Optional[str] = None
    GCP_SERVICE_ACCOUNT_KEY_JSON: Optional[str] = None  # For inline key
    GCP_SECRET_PREFIX: str = "elson"

    # Alerting Configuration
    ALERT_THROTTLE_WINDOW_SECONDS: int = 300  # 5 minutes
    ALERT_THROTTLE_MAX_ALERTS: int = 5  # Maximum alerts in window

    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: Optional[str] = None
    SMTP_FROM_EMAIL: str = "alerts@elson.com"
    ALERT_RECIPIENTS: List[str] = ["alerts@elson.com"]

    # Slack Configuration
    SLACK_ENABLED: bool = True
    SLACK_CHANNEL: str = "#alerts"

    # PagerDuty Configuration
    PAGERDUTY_ENABLED: bool = False
    PAGERDUTY_SERVICE_KEY: Optional[str] = None

    # On-Call Schedule
    ON_CALL_ROTATION_ENABLED: bool = True

    # Centralized Logging (ELK)
    ELK_LOGGING_ENABLED: bool = False
    ELK_HOST: Optional[str] = None
    ELK_PORT: Optional[int] = None

    # Server Configuration
    WEBSOCKET_HOST: str = "127.0.0.1"
    WEBSOCKET_PORT: int = 8001
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Educational Mode Settings
    EDUCATIONAL_MODE_ENABLED: bool = True
    EDUCATIONAL_MODE_TOOLTIPS: bool = True
    EDUCATIONAL_MODE_SIMPLIFIED_UI: bool = True
    EDUCATIONAL_MODE_RISK_LIMITS: bool = True

    # Stripe Settings
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_WEBHOOK_ENDPOINT_SECRET: Optional[str] = None

    # PayPal Settings
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_WEBHOOK_ID: Optional[str] = None
    PAYPAL_SANDBOX_MODE: bool = True

    # Subscription Price IDs for Stripe
    STRIPE_PRICE_IDS: Dict[str, Dict[str, str]] = {
        "premium": {
            "monthly": "price_premium_monthly",
            "annually": "price_premium_annually",
        },
        "family": {
            "monthly": "price_family_monthly",
            "annually": "price_family_annually",
        },
    }

    # Age-based Permission Settings
    MINOR_AGE_RANGES: dict = {
        "children": {"min": 8, "max": 12},
        "teens": {"min": 13, "max": 17},
    }
    MINOR_TRADE_LIMITS: dict = {
        "children": {"max_order_amount": 100.0, "requires_approval": True},
        "teens": {"max_order_amount": 500.0, "requires_approval": True},
    }

    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        """Ensure SECRET_KEY is at least 32 characters long."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v, values):
        """Validate database URL or construct from Cloud SQL settings."""
        if v:
            return v
        
        # Try to construct from Cloud SQL settings
        if values.get("CLOUD_SQL_CONNECTION_NAME"):
            return (
                f"postgresql://{values.get('CLOUD_SQL_USERNAME', 'elson_app')}:"
                f"{values.get('CLOUD_SQL_PASSWORD', '')}"
                f"@/{values.get('CLOUD_SQL_DATABASE_NAME', 'elson_production')}"
                f"?host=/cloudsql/{values.get('CLOUD_SQL_CONNECTION_NAME')}"
            )
        
        # Fallback to regular PostgreSQL connection
        if values.get("CLOUD_SQL_PASSWORD"):
            return (
                f"postgresql://{values.get('CLOUD_SQL_USERNAME', 'elson_app')}:"
                f"{values.get('CLOUD_SQL_PASSWORD', '')}"
                f"@{values.get('CLOUD_SQL_HOST', '127.0.0.1')}:"
                f"{values.get('CLOUD_SQL_PORT', 5432)}"
                f"/{values.get('CLOUD_SQL_DATABASE_NAME', 'elson_production')}"
            )
        
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment value."""
        valid_environments = ["development", "staging", "production", "testing"]
        if v not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of {valid_environments}")
        return v
    
    def get_secret_from_manager(self, key: str, default: Any = None) -> Any:
        """Get secret from configured secret manager."""
        from .secrets import get_secret
        return get_secret(key, default)
    
    def validate_required_secrets(self) -> List[str]:
        """Validate that all required secrets are available."""
        missing_secrets = []
        
        # Critical secrets required for production
        critical_secrets = [
            "SECRET_KEY",
            "DATABASE_URL",
            "ALPHA_VANTAGE_API_KEY",
            "FINNHUB_API_KEY",
            "FMP_API_KEY",
        ]
        
        for secret in critical_secrets:
            value = getattr(self, secret, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_secrets.append(secret)
        
        # Environment-specific validation
        if self.ENVIRONMENT == "production":
            production_secrets = [
                "STRIPE_API_KEY",
                "STRIPE_WEBHOOK_SECRET",
                "SCHWAB_API_KEY",
                "SCHWAB_SECRET",
            ]
            
            for secret in production_secrets:
                value = getattr(self, secret, None)
                if not value or (isinstance(value, str) and not value.strip()):
                    missing_secrets.append(secret)
        
        return missing_secrets
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True


def get_env_file():
    """
    Determine which environment file to use based on ENVIRONMENT variable
    or ENV_FILE override.
    """
    # Check if a specific env file was provided
    if os.environ.get("ENV_FILE"):
        env_file = os.environ.get("ENV_FILE")
        if os.path.exists(env_file):
            return env_file
        else:
            print(
                f"Warning: Specified env file {env_file} not found, falling back to config lookup"
            )

    # Otherwise, use the environment-specific config file
    env = os.environ.get("ENVIRONMENT", "development")

    # Look for config in several locations
    config_paths = [
        # Project root config
        Path("/workspaces/Elson/genconfig"),
        # Elson app config (for environment files)
        Path("/workspaces/Elson/Elson/config"),
        # Config relative to this file (various depths)
        Path(__file__).parent.parent.parent.parent.parent / "config",
        Path(__file__).parent.parent.parent.parent / "config",
        Path(__file__).parent.parent.parent / "config",
        # Current directory and parent directories
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent,
    ]

    for config_path in config_paths:
        env_file = config_path / f"{env}.env"
        if env_file.exists():
            print(f"Loading config from: {env_file}")
            return str(env_file)

    # Fallback to looking for .env in current directory
    if Path(".env").exists():
        return ".env"

    # If no config file found, use default values but log a warning
    print(f"Warning: No environment file found for {env}, using default values")
    return None


@lru_cache()
def get_settings() -> Settings:
    """Get settings with appropriate environment file."""
    env_file = get_env_file()
    return Settings(_env_file=env_file)


# Initialize settings
settings = get_settings()
