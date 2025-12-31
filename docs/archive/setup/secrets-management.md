---
title: "Secrets Management"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Secrets Management in Elson

This document explains the secrets management approach implemented in the Elson Trading Bot platform, providing guidelines for secure handling of sensitive information.

## Overview

The Elson platform uses a flexible secrets management system that supports multiple backends:

1. **Environment Variables** (default for development)
2. **HashiCorp Vault** (recommended for production)
3. **AWS Secrets Manager** (alternative for production)

## Configuration

Secret management is configured via environment variables, which can be set in the `.env` file or directly in the environment.

### Core Configuration

```
# Choose the secret backend: env, vault, or aws
SECRET_BACKEND=vault
```

### HashiCorp Vault Configuration

```
VAULT_ENABLED=true
VAULT_URL=https://vault.example.com:8200
VAULT_TOKEN=s.your-vault-token
VAULT_SECRET_PATH=elson/secrets/prod
```

### AWS Secrets Manager Configuration

```
AWS_SECRETS_ENABLED=true
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Usage in Code

The secret management system is accessed through the `SecretManager` class in `app/core/secrets.py`. This provides a consistent interface regardless of which backend is being used.

### Retrieving Secrets

```python
from app.core.secrets import get_secret_manager

# Get the secret manager
secret_manager = get_secret_manager()

# Retrieve a secret
api_key = secret_manager.get_secret("SCHWAB_API_KEY")
```

### Setting Secrets

```python
from app.core.secrets import get_secret_manager

# Get the secret manager
secret_manager = get_secret_manager()

# Set a secret
secret_manager.set_secret("NEW_API_KEY", "your-api-key-value")
```

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use different secret paths** for development, staging, and production
3. **Restrict access** to the secrets management system
4. **Rotate secrets** regularly
5. **Audit access** to sensitive information

## Development Setup

For development, you can use environment variables by setting `SECRET_BACKEND=env` in your `.env` file.

## Production Setup

For production, we recommend using HashiCorp Vault:

1. Deploy a HashiCorp Vault instance
2. Create secret paths for the application
3. Set up access policies
4. Configure the application to use Vault:
   ```
   SECRET_BACKEND=vault
   VAULT_ENABLED=true
   VAULT_URL=https://your-vault-url:8200
   VAULT_TOKEN=your-vault-token
   VAULT_SECRET_PATH=elson/secrets/prod
   ```

## Migrating Secrets

To migrate secrets from environment variables to HashiCorp Vault:

1. Start with the environment variables backend
2. Run the migration script:
   ```
   python -m app.scripts.migrate_secrets env vault
   ```

## Secret Rotation

Implement regular secret rotation by:

1. Creating new secrets in the secret manager
2. Updating the application to use the new secrets
3. Verifying functionality
4. Revoking the old secrets