"""
Test module for PII field encryption.

These tests verify that the PII field encryption is working correctly.
"""

import pytest
from datetime import datetime, date
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.user import User, UserRole
from app.models.account import Account, AccountType
from app.core.encryption import encrypt_sensitive_data, decrypt_sensitive_data
from app.core.field_encryption import EncryptedField, EncryptedString
from app.db.database import Base

# Create an in-memory SQLite database for testing
@pytest.fixture
def db_session():
    """Create a database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_encrypt_decrypt_data():
    """Test the basic encryption and decryption functions."""
    # Test data
    test_data = "sensitive_data_123"
    
    # Encrypt the data
    encrypted = encrypt_sensitive_data(test_data)
    
    # Verify encrypted data is a dictionary with the expected keys
    assert isinstance(encrypted, dict)
    assert "version" in encrypted
    assert "master_key_id" in encrypted
    assert "iv" in encrypted
    assert "encrypted_data_key" in encrypted
    assert "encrypted_data" in encrypted
    assert "mac" in encrypted
    
    # Decrypt the data
    decrypted = decrypt_sensitive_data(encrypted)
    
    # Verify decryption worked
    assert decrypted.decode('utf-8') == test_data


def test_user_encrypted_fields(db_session: Session):
    """Test that encrypted fields in the User model work correctly."""
    # Create a user with PII data
    user = User(
        email="test@example.com",
        hashed_password="hashedpw123",
        first_name="John",
        last_name="Doe",
        role=UserRole.ADULT,
        birthdate=date(1990, 1, 1),
        is_active=True
    )
    
    # Sync the encrypted email
    user.sync_encrypted_email()
    
    # Add to database
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Verify encrypted email exists
    assert user._encrypted_email is not None
    
    # Verify first and last name were encrypted via the hybrid property
    assert user._first_name is not None
    assert user._last_name is not None
    
    # Retrieve the user and ensure the decrypted fields match
    retrieved_user = db_session.query(User).filter(User.id == user.id).first()
    assert retrieved_user.first_name == "John"
    assert retrieved_user.last_name == "Doe"
    
    # Just update the first name directly using the model property
    retrieved_user.first_name = "Jane"
    db_session.commit()
    db_session.refresh(retrieved_user)
    
    # Check the decrypted value
    assert retrieved_user.first_name == "Jane"


def test_account_encrypted_fields(db_session: Session):
    """Test that encrypted fields in the Account model work correctly."""
    # Create a user first
    user = User(
        email="account-test@example.com",
        hashed_password="hashedpw123",
        role=UserRole.ADULT,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Create an account with sensitive data
    account = Account(
        user_id=user.id,
        account_type=AccountType.PERSONAL,
        account_number="ACCT-12345-67890",
        institution="Test Bank",
        is_active=True
    )
    
    # Sync the encrypted account number
    account.sync_encrypted_account_number()
    
    # Add to database
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    
    # Verify encrypted account number exists
    assert account._encrypted_account_number is not None
    
    # Retrieve the account and ensure account number can be decrypted
    retrieved_account = db_session.query(Account).filter(Account.id == account.id).first()
    
    # Make sure we can access the encrypted account number using the property
    assert retrieved_account.encrypted_account_number == "ACCT-12345-67890"
    
    # Also check that updating it works
    retrieved_account.encrypted_account_number = "NEW-98765-43210"
    db_session.commit()
    db_session.refresh(retrieved_account)
    assert retrieved_account.encrypted_account_number == "NEW-98765-43210"