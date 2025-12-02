#!/usr/bin/env python3
"""
Script to migrate secrets between different backends (env, vault, aws).

Usage:
    python -m app.scripts.migrate_secrets source_backend target_backend

Example:
    python -m app.scripts.migrate_secrets env vault
"""

import os
import sys
import json
import logging
from typing import Dict, List

# Add the parent directory to the path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.secrets import SecretManager, SecretBackend
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# List of secrets to migrate
# Add all the secrets that should be migrated between backends
SECRETS_TO_MIGRATE = [
    "SCHWAB_API_KEY",
    "SCHWAB_SECRET",
    "SECRET_KEY",
    "DB_USER",
    "DB_PASSWORD",
    # Add more secrets as needed
]

def get_env_secrets() -> Dict[str, str]:
    """Get secrets from environment variables."""
    secrets = {}
    for key in SECRETS_TO_MIGRATE:
        value = os.environ.get(key)
        if value:
            secrets[key] = value
    return secrets

def migrate_secrets(source_backend: str, target_backend: str) -> None:
    """Migrate secrets from one backend to another."""
    # Validate backends
    try:
        source = SecretBackend(source_backend)
        target = SecretBackend(target_backend)
    except ValueError:
        logger.error(f"Invalid backend specified. Valid options are: {', '.join([b.value for b in SecretBackend])}")
        sys.exit(1)
    
    logger.info(f"Migrating secrets from {source.value} to {target.value}")
    
    # Initialize secret managers
    source_manager = SecretManager(backend=source)
    target_manager = SecretManager(backend=target)
    
    # Get secrets from source backend
    secrets = {}
    for key in SECRETS_TO_MIGRATE:
        value = source_manager.get_secret(key)
        if value:
            secrets[key] = value
            logger.info(f"Retrieved secret: {key}")
        else:
            logger.warning(f"Secret not found in source backend: {key}")
    
    if not secrets:
        logger.error("No secrets found to migrate")
        sys.exit(1)
    
    # Store secrets in target backend
    success_count = 0
    for key, value in secrets.items():
        success = target_manager.set_secret(key, value)
        if success:
            logger.info(f"Successfully migrated secret: {key}")
            success_count += 1
        else:
            logger.error(f"Failed to migrate secret: {key}")
    
    logger.info(f"Migration complete: {success_count}/{len(secrets)} secrets migrated successfully")

def main():
    """Main entry point for the script."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} source_backend target_backend")
        print(f"Valid backends: {', '.join([b.value for b in SecretBackend])}")
        sys.exit(1)
    
    source_backend = sys.argv[1]
    target_backend = sys.argv[2]
    
    migrate_secrets(source_backend, target_backend)

if __name__ == "__main__":
    main()