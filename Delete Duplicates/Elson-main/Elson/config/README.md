# Elson Wealth Platform Configuration

This directory contains environment-specific configuration files for the Elson Wealth Trading Platform.

## Available Configurations

- `development.env`: For local development
- `testing.env`: For automated tests
- `production.env`: For production deployment

## Using Environment Configurations

The application loads configuration based on the ENVIRONMENT variable or specified environment file.

### Starting the server with a specific environment

```bash
# Using environment name
python Elson/backend/start_server.py --env development

# Using specific environment file
python Elson/backend/start_server.py --env-file config/production.env
```

### Initializing the database

```bash
# Using environment name
python Elson/backend/init_db.py --env development

# Add the --seed flag to populate with sample data (for development only)
python Elson/backend/init_db.py --env development --seed
```

### Using the setup script

For convenience, you can use the setup script to initialize the entire environment:

```bash
# Setup development environment with sample data
./setup_environment.sh --env development --seed

# Setup production environment
./setup_environment.sh --env production
```

## Configuration Variables

Each environment file should define the following variables:

### Database Configuration
- `DATABASE_URL`: Database connection string
- `DB_POOL_SIZE`: Database connection pool size
- `DB_MAX_OVERFLOW`: Maximum overflow connections
- `DB_POOL_TIMEOUT`: Connection acquisition timeout in seconds
- `DB_POOL_RECYCLE`: Connection recycling time in seconds
- `DB_ECHO_SQL`: Whether to echo SQL statements (for debugging)

### Redis Configuration
- `REDIS_URL`: Redis connection string
- `REDIS_PASSWORD`: Redis password (if required)
- `REDIS_MAX_CONNECTIONS`: Maximum Redis connections
- `REDIS_TIMEOUT`: Redis connection timeout
- `REDIS_SENTINEL_ENABLED`: Whether Redis Sentinel is enabled
- `REDIS_SENTINEL_HOSTS`: List of Redis Sentinel hosts (comma-separated)
- `REDIS_SENTINEL_MASTER`: Name of the Redis master

### Security Configuration
- `SECRET_KEY`: Secret key for JWT token generation
- `DEBUG`: Whether debug mode is enabled
- `ENVIRONMENT`: Environment name
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)

### API Keys
- `ALPHA_VANTAGE_API_KEY`: AlphaVantage API key
- `FINNHUB_API_KEY`: Finnhub API key
- `FMP_API_KEY`: Financial Modeling Prep API key
- `SCHWAB_API_KEY`: Schwab API key
- `SCHWAB_SECRET`: Schwab API secret

### Stripe Configuration
- `STRIPE_API_KEY`: Stripe API key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret

### Service Configuration
- `DEFAULT_BROKER`: Default broker ("paper", "schwab", "alpaca")
- `WEBSOCKET_HOST`: WebSocket server host
- `WEBSOCKET_PORT`: WebSocket server port
- `API_HOST`: API server host
- `API_PORT`: API server port

## Example Environment File

```
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/elson
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO_SQL=false

# Redis Configuration
REDIS_URL=redis://:password@localhost:6379/0
REDIS_PASSWORD=password
REDIS_MAX_CONNECTIONS=20
REDIS_TIMEOUT=5
REDIS_SENTINEL_ENABLED=false

# Security Configuration
SECRET_KEY=your_secret_key_at_least_32_characters_long
DEBUG=false
ENVIRONMENT=production
ALLOWED_ORIGINS=https://app.elsonwealth.com

# API Keys
ALPHA_VANTAGE_API_KEY=your_api_key
FINNHUB_API_KEY=your_api_key
FMP_API_KEY=your_api_key
SCHWAB_API_KEY=your_api_key
SCHWAB_SECRET=your_api_secret

# Stripe Configuration
STRIPE_API_KEY=your_stripe_api_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Service Configuration
DEFAULT_BROKER=schwab
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8001
API_HOST=0.0.0.0
API_PORT=8000
```

## Security Note

**IMPORTANT:** Production environment files contain sensitive information and should never be committed to version control. The production.env file in this repository is a template and should be replaced with actual values in the production environment.

In production, consider using a secrets management solution like HashiCorp Vault or AWS Secrets Manager instead of environment files.