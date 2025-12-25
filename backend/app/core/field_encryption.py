"""
Field-level encryption for SQLAlchemy models.

This module provides tools to encrypt and decrypt sensitive fields in SQLAlchemy models
using hybrid properties and the envelope encryption system.
"""

import json
from datetime import datetime
from typing import Any, Optional, Type, TypeVar, Union, Dict
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import TypeDecorator, String

from .encryption import encrypt_sensitive_data, decrypt_sensitive_data

T = TypeVar("T")


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy column type for storing encrypted strings.

    This type transparently encrypts string values before storing them in the database
    and decrypts them when retrieved. It uses the envelope encryption system.
    """

    impl = String
    cache_ok = True

    def process_bind_param(
        self, value: Optional[Dict[str, str]], dialect
    ) -> Optional[str]:
        """
        Process the value before inserting into the database.

        Args:
            value: Encrypted data dictionary or None
            dialect: SQLAlchemy dialect

        Returns:
            JSON string representation of the encrypted data
        """
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(
        self, value: Optional[str], dialect
    ) -> Optional[Dict[str, str]]:
        """
        Process the value retrieved from the database.

        Args:
            value: JSON string from database or None
            dialect: SQLAlchemy dialect

        Returns:
            Dictionary with encrypted data and metadata
        """
        if value is None:
            return None
        return json.loads(value)


class EncryptedField:
    """
    Helper class to create encrypted fields in SQLAlchemy models.

    Usage:
        class User(Base):
            __tablename__ = "users"

            id = Column(Integer, primary_key=True)
            _email = Column(String, nullable=True)
            email = EncryptedField(_email)
    """

    def __init__(self, column_name: str):
        """
        Initialize with the name of the database column that stores encrypted data.

        Args:
            column_name: Name of the SQLAlchemy column storing the encrypted data
        """
        self.column_name = column_name

    def __set_name__(self, owner: Type, name: str) -> None:
        """Set the attribute name when the class is defined."""
        self.name = name

    def __get__(self, instance: Any, owner: Type) -> Union[hybrid_property, Any]:
        """
        Get the decrypted value.

        This is called when accessing the attribute.

        Args:
            instance: Model instance
            owner: Model class

        Returns:
            Decrypted value or hybrid property if called on class
        """
        if instance is None:
            # Return a hybrid_property when accessed from the class
            return hybrid_property(
                fget=lambda self: self._get_decrypted_value(
                    getattr(self, self.column_name)
                ),
                fset=lambda self, value: setattr(
                    self, self.column_name, self._get_encrypted_value(value)
                ),
                expr=lambda cls: getattr(cls, self.column_name),
            )

        # Return the decrypted value when accessed from an instance
        encrypted_value = getattr(instance, self.column_name)
        return self._get_decrypted_value(encrypted_value)

    def __set__(self, instance: Any, value: Any) -> None:
        """
        Set the encrypted value.

        This is called when setting the attribute.

        Args:
            instance: Model instance
            value: Value to encrypt and store
        """
        encrypted_value = self._get_encrypted_value(value)
        setattr(instance, self.column_name, encrypted_value)

    def _get_encrypted_value(self, value: Any) -> Optional[Dict[str, str]]:
        """
        Encrypt a value using envelope encryption.

        Args:
            value: Value to encrypt

        Returns:
            Dictionary with encrypted data and metadata
        """
        if value is None:
            return None

        if isinstance(value, datetime):
            # Convert datetime to ISO format string for encryption
            value = value.isoformat()

        # Convert value to string if needed
        if not isinstance(value, (str, bytes)):
            value = str(value)

        # Encrypt the value
        return encrypt_sensitive_data(value)

    def _get_decrypted_value(
        self, encrypted_value: Optional[Dict[str, str]]
    ) -> Optional[str]:
        """
        Decrypt a value that was encrypted with envelope encryption.

        Args:
            encrypted_value: Dictionary with encrypted data and metadata

        Returns:
            Decrypted value
        """
        if encrypted_value is None:
            return None

        try:
            # Decrypt the value
            decrypted = decrypt_sensitive_data(encrypted_value)
            return decrypted.decode("utf-8")
        except Exception as e:
            # Log the error and return None if decryption fails
            # This can happen if the key is rotated and we don't have access to the old key
            import logging

            logging.error(f"Failed to decrypt field: {e}")
            return None


def encrypt_model_fields(
    model_class: Type[DeclarativeBase], fields: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Encrypt multiple fields for a model instance.

    Args:
        model_class: SQLAlchemy model class
        fields: Dictionary of field values to encrypt

    Returns:
        Dictionary with encrypted field values
    """
    encrypted_fields = {}

    for field_name, value in fields.items():
        if hasattr(model_class, f"_{field_name}"):
            # The field has a private storage column
            encrypted_field = EncryptedField(f"_{field_name}")
            encrypted_fields[f"_{field_name}"] = encrypted_field._get_encrypted_value(
                value
            )
        else:
            # Not an encrypted field
            encrypted_fields[field_name] = value

    return encrypted_fields
