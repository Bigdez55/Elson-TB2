"""Secrets management module for the Elson application.

This module handles secure storage and retrieval of sensitive information
such as API keys, database credentials, and other secrets.
It supports multiple backends including HashiCorp Vault and AWS Secrets Manager.
"""

import json
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import boto3
import hvac
from botocore.exceptions import ClientError
from pydantic import BaseModel

try:
    from google.cloud import secretmanager
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

from .config import settings

logger = logging.getLogger(__name__)


class SecretBackend(str, Enum):
    """Supported secret backends."""

    VAULT = "vault"
    AWS = "aws"
    GCP = "gcp"
    ENV = "env"  # Fallback to environment variables


class SecretManager:
    """Secret manager for retrieving sensitive information."""

    def __init__(self, backend: SecretBackend = SecretBackend.ENV):
        """Initialize the secret manager with the specified backend."""
        self.backend = backend
        self._vault_client = None
        self._aws_client = None
        self._gcp_client = None

        # Initialize the appropriate client based on the backend
        if self.backend == SecretBackend.VAULT and settings.VAULT_ENABLED:
            self._init_vault_client()
        elif self.backend == SecretBackend.AWS and settings.AWS_SECRETS_ENABLED:
            self._init_aws_client()
        elif self.backend == SecretBackend.GCP and settings.GCP_SECRETS_ENABLED:
            self._init_gcp_client()

    def _init_vault_client(self) -> None:
        """Initialize the HashiCorp Vault client."""
        try:
            self._vault_client = hvac.Client(
                url=settings.VAULT_URL,
                token=settings.VAULT_TOKEN,
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
            self._aws_client = boto3.client(
                "secretsmanager",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS Secrets Manager client: {e}")
            # Fall back to environment variables
            self.backend = SecretBackend.ENV
    
    def _init_gcp_client(self) -> None:
        """Initialize the GCP Secret Manager client."""
        if not GCP_AVAILABLE:
            logger.error("Google Cloud Secret Manager not available. Install google-cloud-secret-manager.")
            self.backend = SecretBackend.ENV
            return
        
        try:
            credentials = None
            
            # Try to load credentials from service account key
            if settings.GCP_SERVICE_ACCOUNT_KEY_PATH:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GCP_SERVICE_ACCOUNT_KEY_PATH
                )
            elif settings.GCP_SERVICE_ACCOUNT_KEY_JSON:
                key_data = json.loads(settings.GCP_SERVICE_ACCOUNT_KEY_JSON)
                credentials = service_account.Credentials.from_service_account_info(key_data)
            
            # Initialize the client
            if credentials:
                self._gcp_client = secretmanager.SecretManagerServiceClient(
                    credentials=credentials
                )
            else:
                # Use application default credentials
                self._gcp_client = secretmanager.SecretManagerServiceClient()
                
        except Exception as e:
            logger.error(f"Failed to initialize GCP Secret Manager client: {e}")
            # Fall back to environment variables
            self.backend = SecretBackend.ENV

    def get_secret(
        self, key: str, default: Optional[Any] = None
    ) -> Union[str, Dict, None]:
        """Get a secret from the configured backend."""
        if self.backend == SecretBackend.VAULT and self._vault_client:
            return self._get_vault_secret(key, default)
        elif self.backend == SecretBackend.AWS and self._aws_client:
            return self._get_aws_secret(key, default)
        elif self.backend == SecretBackend.GCP and self._gcp_client:
            return self._get_gcp_secret(key, default)
        else:
            # Fallback to environment variables
            return os.environ.get(key, default)

    def _get_vault_secret(
        self, key: str, default: Optional[Any] = None
    ) -> Union[str, Dict, None]:
        """Get a secret from HashiCorp Vault."""
        try:
            path_parts = key.split("/")

            # Handle either direct key or path/key format
            if len(path_parts) > 1:
                path = "/".join(path_parts[:-1])
                secret_key = path_parts[-1]
                secret_data = self._vault_client.secrets.kv.v2.read_secret_version(
                    path=path
                )

                if (
                    secret_data
                    and "data" in secret_data
                    and "data" in secret_data["data"]
                ):
                    return secret_data["data"]["data"].get(secret_key, default)
            else:
                # Direct key lookup in the default path
                secret_data = self._vault_client.secrets.kv.v2.read_secret_version(
                    path=settings.VAULT_SECRET_PATH
                )

                if (
                    secret_data
                    and "data" in secret_data
                    and "data" in secret_data["data"]
                ):
                    return secret_data["data"]["data"].get(key, default)

            return default
        except Exception as e:
            logger.error(f"Failed to retrieve secret from Vault: {e}")
            return default

    def _get_aws_secret(
        self, key: str, default: Optional[Any] = None
    ) -> Union[str, Dict, None]:
        """Get a secret from AWS Secrets Manager."""
        try:
            response = self._aws_client.get_secret_value(SecretId=key)

            # Return the secret value or default
            if "SecretString" in response:
                return response["SecretString"]
            return default
        except ClientError as e:
            logger.error(f"Failed to retrieve secret from AWS Secrets Manager: {e}")
            return default
    
    def _get_gcp_secret(
        self, key: str, default: Optional[Any] = None
    ) -> Union[str, Dict, None]:
        """Get a secret from GCP Secret Manager."""
        try:
            # Format the secret name with project ID and prefix
            secret_name = f"projects/{settings.GCP_PROJECT_ID}/secrets/{settings.GCP_SECRET_PREFIX}-{key}/versions/latest"
            
            response = self._gcp_client.access_secret_version(
                request={"name": secret_name}
            )
            
            # Return the secret value
            secret_value = response.payload.data.decode("UTF-8")
            
            # Try to parse as JSON if possible
            try:
                return json.loads(secret_value)
            except (json.JSONDecodeError, TypeError):
                return secret_value
                
        except Exception as e:
            logger.warning(f"Failed to retrieve secret '{key}' from GCP Secret Manager: {e}")
            return default

    def set_secret(self, key: str, value: Union[str, Dict]) -> bool:
        """Set a secret in the configured backend."""
        if self.backend == SecretBackend.VAULT and self._vault_client:
            return self._set_vault_secret(key, value)
        elif self.backend == SecretBackend.AWS and self._aws_client:
            return self._set_aws_secret(key, value)
        elif self.backend == SecretBackend.GCP and self._gcp_client:
            return self._set_gcp_secret(key, value)
        else:
            # Fallback to environment variables (not ideal for setting, just for testing)
            os.environ[key] = str(value)
            return True

    def _set_vault_secret(self, key: str, value: Union[str, Dict]) -> bool:
        """Set a secret in HashiCorp Vault."""
        try:
            path_parts = key.split("/")

            # Handle either direct key or path/key format
            if len(path_parts) > 1:
                path = "/".join(path_parts[:-1])
                secret_key = path_parts[-1]

                # First read existing data
                try:
                    existing_data = (
                        self._vault_client.secrets.kv.v2.read_secret_version(path=path)
                    )
                    if (
                        existing_data
                        and "data" in existing_data
                        and "data" in existing_data["data"]
                    ):
                        # Update existing data
                        secret_data = existing_data["data"]["data"]
                        secret_data[secret_key] = value
                    else:
                        # Create new data
                        secret_data = {secret_key: value}
                except Exception:
                    # Key doesn't exist yet
                    secret_data = {secret_key: value}

                # Write data back
                self._vault_client.secrets.kv.v2.create_or_update_secret(
                    path=path, secret=secret_data
                )
            else:
                # Direct key in default path
                # First read existing data
                try:
                    existing_data = (
                        self._vault_client.secrets.kv.v2.read_secret_version(
                            path=settings.VAULT_SECRET_PATH
                        )
                    )
                    if (
                        existing_data
                        and "data" in existing_data
                        and "data" in existing_data["data"]
                    ):
                        # Update existing data
                        secret_data = existing_data["data"]["data"]
                        secret_data[key] = value
                    else:
                        # Create new data
                        secret_data = {key: value}
                except Exception:
                    # Key doesn't exist yet
                    secret_data = {key: value}

                # Write data back
                self._vault_client.secrets.kv.v2.create_or_update_secret(
                    path=settings.VAULT_SECRET_PATH, secret=secret_data
                )

            return True
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False

    def _set_aws_secret(self, key: str, value: Union[str, Dict]) -> bool:
        """Set a secret in AWS Secrets Manager."""
        try:
            self._aws_client.create_secret(
                Name=key,
                SecretString=str(value)
                if isinstance(value, str)
                else json.dumps(value),
            )
            return True
        except ClientError as e:
            # If the secret already exists, update it
            if e.response["Error"]["Code"] == "ResourceExistsException":
                try:
                    self._aws_client.update_secret(
                        SecretId=key,
                        SecretString=str(value)
                        if isinstance(value, str)
                        else json.dumps(value),
                    )
                    return True
                except Exception as update_error:
                    logger.error(
                        f"Failed to update secret in AWS Secrets Manager: {update_error}"
                    )
                    return False
            else:
                logger.error(f"Failed to create secret in AWS Secrets Manager: {e}")
                return False
    
    def _set_gcp_secret(self, key: str, value: Union[str, Dict]) -> bool:
        """Set a secret in GCP Secret Manager."""
        try:
            # Format the secret name with project ID and prefix
            secret_id = f"{settings.GCP_SECRET_PREFIX}-{key}"
            parent = f"projects/{settings.GCP_PROJECT_ID}"
            
            # Convert value to string if it's a dict
            secret_value = json.dumps(value) if isinstance(value, dict) else str(value)
            
            try:
                # Try to create the secret first
                self._gcp_client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            except Exception:
                # Secret already exists, which is fine
                pass
            
            # Add the secret version
            secret_name = f"projects/{settings.GCP_PROJECT_ID}/secrets/{secret_id}"
            self._gcp_client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set secret in GCP Secret Manager: {e}")
            return False
    
    def rotate_secret(self, key: str) -> bool:
        """Rotate a secret by generating a new value."""
        try:
            # Generate a new secure random value
            import secrets as secure_secrets
            new_value = secure_secrets.token_urlsafe(32)
            
            # Set the new secret
            success = self.set_secret(key, new_value)
            
            if success:
                logger.info(f"Successfully rotated secret: {key}")
            else:
                logger.error(f"Failed to rotate secret: {key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rotate secret '{key}': {e}")
            return False
    
    def list_secrets(self) -> List[str]:
        """List all available secrets."""
        secrets_list = []
        
        try:
            if self.backend == SecretBackend.GCP and self._gcp_client:
                parent = f"projects/{settings.GCP_PROJECT_ID}"
                
                for secret in self._gcp_client.list_secrets(request={"parent": parent}):
                    secret_name = secret.name.split("/")[-1]
                    # Remove prefix if present
                    if secret_name.startswith(f"{settings.GCP_SECRET_PREFIX}-"):
                        secret_name = secret_name[len(f"{settings.GCP_SECRET_PREFIX}-"):]
                    secrets_list.append(secret_name)
                    
            elif self.backend == SecretBackend.AWS and self._aws_client:
                paginator = self._aws_client.get_paginator('list_secrets')
                
                for page in paginator.paginate():
                    for secret in page['SecretList']:
                        secrets_list.append(secret['Name'])
                        
            elif self.backend == SecretBackend.VAULT and self._vault_client:
                # List secrets from Vault
                response = self._vault_client.secrets.kv.v2.list_secrets(
                    path=settings.VAULT_SECRET_PATH
                )
                if response and 'data' in response and 'keys' in response['data']:
                    secrets_list = response['data']['keys']
                    
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            
        return secrets_list


# Global instance for dependency injection
secret_manager = SecretManager(
    backend=SecretBackend(settings.SECRET_BACKEND)
    if hasattr(settings, "SECRET_BACKEND")
    else SecretBackend.ENV
)


def get_secret_manager() -> SecretManager:
    """Dependency injection for SecretManager."""
    return secret_manager


def get_secret(key: str, default: Optional[Any] = None) -> Union[str, Dict, None]:
    """
    Helper function to get a secret directly from the global secret manager.

    Args:
        key: The secret key to retrieve
        default: The default value to return if the secret is not found

    Returns:
        The secret value or the default value if not found
    """
    return secret_manager.get_secret(key, default)


def set_secret(key: str, value: Union[str, Dict]) -> bool:
    """
    Helper function to set a secret directly in the global secret manager.

    Args:
        key: The secret key to set
        value: The secret value to store

    Returns:
        True if the secret was set successfully, False otherwise
    """
    return secret_manager.set_secret(key, value)


def rotate_secret(key: str) -> bool:
    """
    Helper function to rotate a secret directly in the global secret manager.

    Args:
        key: The secret key to rotate

    Returns:
        True if the secret was rotated successfully, False otherwise
    """
    return secret_manager.rotate_secret(key)


def list_secrets() -> List[str]:
    """
    Helper function to list all secrets from the global secret manager.

    Returns:
        A list of secret keys
    """
    return secret_manager.list_secrets()
