"""Secrets management module for the Elson application.

This module handles secure storage and retrieval of sensitive information
such as API keys, database credentials, and other secrets.
It supports multiple backends including HashiCorp Vault and AWS Secrets Manager.
"""

import os
import logging
from typing import Dict, Optional, Any, Union
from enum import Enum

import hvac
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

from .config import settings

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
        if self.backend == SecretBackend.VAULT and settings.VAULT_ENABLED:
            self._init_vault_client()
        elif self.backend == SecretBackend.AWS and settings.AWS_SECRETS_ENABLED:
            self._init_aws_client()
    
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
                'secretsmanager',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
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
                secret_data = self._vault_client.secrets.kv.v2.read_secret_version(
                    path=settings.VAULT_SECRET_PATH
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
                # First read existing data
                try:
                    existing_data = self._vault_client.secrets.kv.v2.read_secret_version(
                        path=settings.VAULT_SECRET_PATH
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
                    path=settings.VAULT_SECRET_PATH,
                    secret=secret_data
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
                SecretString=str(value) if isinstance(value, str) else json.dumps(value)
            )
            return True
        except ClientError as e:
            # If the secret already exists, update it
            if e.response['Error']['Code'] == 'ResourceExistsException':
                try:
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


# Global instance for dependency injection
secret_manager = SecretManager(
    backend=SecretBackend(settings.SECRET_BACKEND) if hasattr(settings, 'SECRET_BACKEND') else SecretBackend.ENV
)


def get_secret_manager() -> SecretManager:
    """Dependency injection for SecretManager."""
    return secret_manager