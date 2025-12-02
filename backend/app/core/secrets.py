"""Secure secrets management module.

This module provides a centralized way to manage API keys and other sensitive
information for broker integrations and external services.

Supports multiple backends:
- Environment variables (default, always available as fallback)
- HashiCorp Vault (production secret management)
- AWS Secrets Manager (cloud-native secret storage)
"""

import os
import logging
from typing import Dict, Optional, Any, Union
from enum import Enum

try:
    import hvac
    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecretBackend(str, Enum):
    """Supported secret backends."""

    VAULT = "vault"
    AWS = "aws"
    ENV = "env"  # Fallback to environment variables


class SecretManager:
    """Secret manager for retrieving sensitive information."""

    def __init__(self, backend: SecretBackend = SecretBackend.ENV):
        """Initialize the secret manager with the specified backend."""
        self.backend = backend
        self._vault_client = None
        self._aws_client = None

        # Initialize the appropriate client based on the backend
        if self.backend == SecretBackend.VAULT and HVAC_AVAILABLE:
            vault_enabled = getattr(settings, "VAULT_ENABLED", False)
            if vault_enabled:
                self._init_vault_client()
        elif self.backend == SecretBackend.AWS and BOTO3_AVAILABLE:
            aws_enabled = getattr(settings, "AWS_SECRETS_ENABLED", False)
            if aws_enabled:
                self._init_aws_client()

    def _init_vault_client(self) -> None:
        """Initialize the HashiCorp Vault client."""
        try:
            vault_url = getattr(settings, "VAULT_URL", None)
            vault_token = getattr(settings, "VAULT_TOKEN", None)

            if not vault_url or not vault_token:
                logger.warning("Vault credentials not configured, falling back to ENV")
                self.backend = SecretBackend.ENV
                return

            self._vault_client = hvac.Client(
                url=vault_url,
                token=vault_token,
            )

            if not self._vault_client.is_authenticated():
                logger.error("Failed to authenticate with Vault")
                # Fall back to environment variables
                self.backend = SecretBackend.ENV
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            # Fall back to environment variables
            self.backend = SecretBackend.ENV

    def _init_aws_client(self) -> None:
        """Initialize the AWS Secrets Manager client."""
        try:
            aws_region = getattr(settings, "AWS_REGION", None)
            aws_access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
            aws_secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)

            if not aws_region:
                logger.warning("AWS region not configured, falling back to ENV")
                self.backend = SecretBackend.ENV
                return

            self._aws_client = boto3.client(
                'secretsmanager',
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS Secrets Manager client: {e}")
            # Fall back to environment variables
            self.backend = SecretBackend.ENV

    def get_secret(self, key: str, default: Optional[Any] = None) -> Union[str, Dict, None]:
        """Get a secret from the configured backend."""
        if self.backend == SecretBackend.VAULT and self._vault_client:
            return self._get_vault_secret(key, default)
        elif self.backend == SecretBackend.AWS and self._aws_client:
            return self._get_aws_secret(key, default)
        else:
            # Fallback to environment variables
            return os.environ.get(key, default)

    def _get_vault_secret(self, key: str, default: Optional[Any] = None) -> Union[str, Dict, None]:
        """Get a secret from HashiCorp Vault."""
        try:
            path_parts = key.split('/')

            # Handle either direct key or path/key format
            if len(path_parts) > 1:
                path = '/'.join(path_parts[:-1])
                secret_key = path_parts[-1]
                secret_data = self._vault_client.secrets.kv.v2.read_secret_version(
                    path=path
                )

                if secret_data and 'data' in secret_data and 'data' in secret_data['data']:
                    return secret_data['data']['data'].get(secret_key, default)
            else:
                # Direct key lookup in the default path
                vault_path = getattr(settings, "VAULT_SECRET_PATH", "secret/data/trading")
                secret_data = self._vault_client.secrets.kv.v2.read_secret_version(
                    path=vault_path
                )

                if secret_data and 'data' in secret_data and 'data' in secret_data['data']:
                    return secret_data['data']['data'].get(key, default)

            return default
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            return default

    def _get_aws_secret(self, key: str, default: Optional[Any] = None) -> Union[str, Dict, None]:
        """Get a secret from AWS Secrets Manager."""
        try:
            response = self._aws_client.get_secret_value(
                SecretId=key
            )

            # Return the secret value or default
            if 'SecretString' in response:
                return response['SecretString']
            return default
        except ClientError as e:
            logger.error(f"Failed to retrieve secret from AWS Secrets Manager: {e}")
            return default

    def set_secret(self, key: str, value: Union[str, Dict]) -> bool:
        """Set a secret in the configured backend."""
        if self.backend == SecretBackend.VAULT and self._vault_client:
            return self._set_vault_secret(key, value)
        elif self.backend == SecretBackend.AWS and self._aws_client:
            return self._set_aws_secret(key, value)
        else:
            # Fallback to environment variables (not ideal for setting, just for testing)
            os.environ[key] = str(value)
            return True

    def _set_vault_secret(self, key: str, value: Union[str, Dict]) -> bool:
        """Set a secret in HashiCorp Vault."""
        try:
            path_parts = key.split('/')

            # Handle either direct key or path/key format
            if len(path_parts) > 1:
                path = '/'.join(path_parts[:-1])
                secret_key = path_parts[-1]

                # First read existing data
                try:
                    existing_data = self._vault_client.secrets.kv.v2.read_secret_version(
                        path=path
                    )
                    if existing_data and 'data' in existing_data and 'data' in existing_data['data']:
                        # Update existing data
                        secret_data = existing_data['data']['data']
                        secret_data[secret_key] = value
                    else:
                        # Create new data
                        secret_data = {secret_key: value}
                except:
                    # Key doesn't exist yet
                    secret_data = {secret_key: value}

                # Write data back
                self._vault_client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=secret_data
                )
            else:
                # Direct key in default path
                vault_path = getattr(settings, "VAULT_SECRET_PATH", "secret/data/trading")
                # First read existing data
                try:
                    existing_data = self._vault_client.secrets.kv.v2.read_secret_version(
                        path=vault_path
                    )
                    if existing_data and 'data' in existing_data and 'data' in existing_data['data']:
                        # Update existing data
                        secret_data = existing_data['data']['data']
                        secret_data[key] = value
                    else:
                        # Create new data
                        secret_data = {key: value}
                except:
                    # Key doesn't exist yet
                    secret_data = {key: value}

                # Write data back
                self._vault_client.secrets.kv.v2.create_or_update_secret(
                    path=vault_path,
                    secret=secret_data
                )

            return True
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False

    def _set_aws_secret(self, key: str, value: Union[str, Dict]) -> bool:
        """Set a secret in AWS Secrets Manager."""
        try:
            import json
            self._aws_client.create_secret(
                Name=key,
                SecretString=str(value) if isinstance(value, str) else json.dumps(value)
            )
            return True
        except ClientError as e:
            # If the secret already exists, update it
            if e.response['Error']['Code'] == 'ResourceExistsException':
                try:
                    import json
                    self._aws_client.update_secret(
                        SecretId=key,
                        SecretString=str(value) if isinstance(value, str) else json.dumps(value)
                    )
                    return True
                except Exception as update_error:
                    logger.error(f"Failed to update secret in AWS Secrets Manager: {update_error}")
                    return False
            else:
                logger.error(f"Failed to create secret in AWS Secrets Manager: {e}")
                return False


# ============================================================================
# Legacy functions for backward compatibility
# ============================================================================

def get_secret(key: str) -> Optional[str]:
    """Get secret from settings/environment with fallback.

    Args:
        key: The secret key to retrieve

    Returns:
        The secret value or None if not found

    Raises:
        ValueError: If key format is invalid
    """
    if not key or not isinstance(key, str):
        raise ValueError("Secret key must be a non-empty string")

    # Standard mapping for known secrets
    secret_mapping = {
        "ALPACA_API_KEY": settings.ALPACA_API_KEY,
        "ALPACA_API_SECRET": settings.ALPACA_SECRET_KEY,
        "ALPACA_SECRET_KEY": settings.ALPACA_SECRET_KEY,  # Alternative name
        "SCHWAB_API_KEY": getattr(settings, "SCHWAB_API_KEY", None),
        "SCHWAB_API_SECRET": getattr(settings, "SCHWAB_API_SECRET", None),
    }

    # Try settings first, then environment
    secret_value = secret_mapping.get(key)
    if secret_value is None:
        secret_value = os.getenv(key)

    return secret_value


def validate_broker_credentials(broker_name: str) -> bool:
    """Validate that required credentials are available for a broker.

    Args:
        broker_name: Name of the broker (e.g., 'alpaca', 'schwab')

    Returns:
        True if all required credentials are available
    """
    broker_requirements = {
        "alpaca": ["ALPACA_API_KEY", "ALPACA_API_SECRET"],
        "schwab": ["SCHWAB_API_KEY", "SCHWAB_API_SECRET"],
    }

    required_keys = broker_requirements.get(broker_name.lower(), [])
    return all(get_secret(key) is not None for key in required_keys)


def mask_secret(secret: Optional[str], visible_chars: int = 4) -> str:
    """Mask a secret for logging purposes.

    Args:
        secret: The secret to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked secret string
    """
    if not secret:
        return "None"

    if len(secret) <= visible_chars:
        return "*" * len(secret)

    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]


# ============================================================================
# Global instance for dependency injection
# ============================================================================

# Determine backend from settings
_backend = SecretBackend.ENV
if hasattr(settings, 'SECRET_BACKEND'):
    try:
        _backend = SecretBackend(settings.SECRET_BACKEND)
    except ValueError:
        logger.warning(f"Invalid SECRET_BACKEND: {settings.SECRET_BACKEND}, using ENV")

secret_manager = SecretManager(backend=_backend)


def get_secret_manager() -> SecretManager:
    """Dependency injection for SecretManager."""
    return secret_manager
