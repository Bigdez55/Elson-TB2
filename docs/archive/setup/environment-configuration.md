---
title: "Environment Configuration"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Environment Configuration Guide

This guide explains the environment configuration system for the Elson Wealth Trading Platform and how to properly set up your environment for different deployment scenarios.

## Overview

The platform supports different environments (development, testing, production) with environment-specific configurations. This allows for varying settings and behaviors based on the deployment context.

## Environment Types

The platform supports the following environments:

- **Development**: Local development environment with debug features enabled
- **Testing**: For automated tests and CI/CD pipelines
- **Production**: Full production environment with optimized settings

## Configuration Files

Each environment has its own configuration file located in the `/config` directory:

- `development.env`: Development environment settings
- `testing.env`: Test environment settings
- `production.env`: Production environment settings

## Setting the Environment

There are multiple ways to specify which environment to use:

### 1. Environment Variable

Set the `ENVIRONMENT` environment variable:

```bash
export ENVIRONMENT=development
```

### 2. Environment File

Specify an environment file directly:

```bash
export ENV_FILE=/path/to/custom.env
```

### 3. Command Line Arguments

When using the application scripts, specify the environment:

```bash
# Start server with specific environment
python start_server.py --env development

# Initialize database with specific environment
python init_db.py --env development
```

## Environment Setup Script

For convenience, use the `setup_environment.sh` script to initialize the environment:

```bash
# Setup development environment
./setup_environment.sh --env development

# Setup development environment with sample data
./setup_environment.sh --env development --seed

# Setup production environment
./setup_environment.sh --env production
```

## Configuration Variables

Each environment file defines various configuration variables, categorized as follows:

### Database Configuration
- `DATABASE_URL`: Database connection string
- `DB_POOL_SIZE`: Database connection pool size
- `DB_MAX_OVERFLOW`: Maximum overflow connections
- `DB_POOL_TIMEOUT`: Connection acquisition timeout
- `DB_POOL_RECYCLE`: Connection recycling time
- `DB_ECHO_SQL`: Whether to echo SQL statements (for debugging)

### Redis Configuration
- `REDIS_URL`: Redis connection string
- `REDIS_PASSWORD`: Redis password
- `REDIS_MAX_CONNECTIONS`: Maximum Redis connections
- `REDIS_TIMEOUT`: Redis connection timeout
- `REDIS_SENTINEL_ENABLED`: Whether Redis Sentinel is enabled
- `REDIS_SENTINEL_HOSTS`: Redis Sentinel hosts
- `REDIS_SENTINEL_MASTER`: Redis master name
- `REDIS_CLUSTER_ENABLED`: Whether Redis Cluster is enabled
- `REDIS_CLUSTER_NODES`: Redis Cluster nodes

### Security Configuration
- `SECRET_KEY`: Secret key for JWT token generation
- `DEBUG`: Whether debug mode is enabled
- `ALLOWED_ORIGINS`: CORS allowed origins

### API Keys
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `FINNHUB_API_KEY`: Finnhub API key
- `FMP_API_KEY`: Financial Modeling Prep API key
- `SCHWAB_API_KEY`: Schwab API key
- `SCHWAB_SECRET`: Schwab API secret

### Payment Configuration
- `STRIPE_API_KEY`: Stripe API key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret

### Server Configuration
- `WEBSOCKET_HOST`: WebSocket server host
- `WEBSOCKET_PORT`: WebSocket server port
- `API_HOST`: API server host
- `API_PORT`: API server port

## Environment-Specific Behaviors

Different environments have different default behaviors:

### Development
- Debug mode enabled
- Detailed logging
- Mock Redis fallback when Redis is unavailable
- SQLite database by default
- Metrics logged rather than sent to Prometheus

### Testing
- Debug mode disabled
- Minimal logging
- Mock Redis for tests
- In-memory SQLite database
- No metrics recording

### Production
- Debug mode disabled
- Production-level logging
- Real Redis required
- PostgreSQL database required
- Metrics sent to Prometheus

## Creating a Custom Environment

To create a custom environment:

1. Create a new `.env` file in the `/config` directory
2. Copy settings from an existing environment file
3. Modify settings as needed
4. Use the environment by setting `ENVIRONMENT` or `ENV_FILE`

## Validating the Environment

To validate your environment configuration:

```bash
# Validate the current environment
python -m app.scripts.validate_env

# Validate a specific environment file
python -m app.scripts.validate_env --env-file /path/to/custom.env
```

## Production Readiness Check

To check if your environment is ready for production:

```bash
# Check production readiness
python -m app.scripts.check_production_readiness
```

## Troubleshooting

If you encounter issues with your environment configuration:

1. Verify that the correct environment file is being used
2. Check for missing or invalid configuration variables
3. Validate the environment using the validation script
4. Check the application logs for configuration-related errors

## Security Considerations

For production environments:

1. Never commit production credentials to version control
2. Consider using a secrets management solution like HashiCorp Vault
3. Rotate secrets regularly
4. Use strong, unique values for `SECRET_KEY` and other credentials