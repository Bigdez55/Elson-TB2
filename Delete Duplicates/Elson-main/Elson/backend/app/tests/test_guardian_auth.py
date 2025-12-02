"""Tests for guardian authentication requirements."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User, UserRole
from app.models.account import Account, AccountType
from app.core.auth.guardian_auth import (
    require_guardian_2fa,
    check_guardian_authentication,
    is_guardian,
    get_guardian_stats
)
from app.core.auth.two_factor import TwoFactorAuth


@pytest.fixture
def setup_test_data(db: Session):
    """Create test users and accounts."""
    # Create adult user with 2FA enabled
    adult_with_2fa = User(
        email="adult1@example.com",
        hashed_password="hashed_password",
        first_name="Adult",
        last_name="WithTwoFactor",
        role=UserRole.ADULT,
        two_factor_enabled=True,
        two_factor_secret="TESTSECRET",
        is_active=True,
    )
    db.add(adult_with_2fa)
    
    # Create adult user without 2FA
    adult_without_2fa = User(
        email="adult2@example.com",
        hashed_password="hashed_password",
        first_name="Adult",
        last_name="WithoutTwoFactor",
        role=UserRole.ADULT,
        two_factor_enabled=False,
        is_active=True,
    )
    db.add(adult_without_2fa)
    
    # Create minor user
    minor = User(
        email="minor@example.com",
        hashed_password="hashed_password",
        first_name="Minor",
        last_name="User",
        role=UserRole.MINOR,
        is_active=True,
    )
    db.add(minor)
    
    db.commit()
    
    # Create custodial account linking the minor to the guardian without 2FA
    custodial_account = Account(
        user_id=minor.id,
        guardian_id=adult_without_2fa.id,
        account_type=AccountType.CUSTODIAL,
        account_number=f"CUST-{minor.id}-{datetime.utcnow().strftime('%Y%m%d')}",
        institution="Elson Wealth",
        is_active=True
    )
    db.add(custodial_account)
    db.commit()
    
    return {
        "adult_with_2fa": adult_with_2fa,
        "adult_without_2fa": adult_without_2fa,
        "minor": minor
    }


async def test_require_guardian_2fa(db: Session, setup_test_data):
    """Test require_guardian_2fa function."""
    two_factor_auth = TwoFactorAuth()
    
    # Adult with 2FA should pass
    try:
        await require_guardian_2fa(setup_test_data["adult_with_2fa"], db, two_factor_auth)
        assert True  # Should not raise exception
    except HTTPException:
        assert False, "Should not raise exception for guardian with 2FA"
    
    # Adult without 2FA who is a guardian should raise exception
    with pytest.raises(HTTPException) as excinfo:
        await require_guardian_2fa(setup_test_data["adult_without_2fa"], db, two_factor_auth)
    assert excinfo.value.status_code == 403
    assert "Two-factor authentication is required for guardian accounts" in excinfo.value.detail
    
    # Minor should pass since they are not a guardian
    try:
        await require_guardian_2fa(setup_test_data["minor"], db, two_factor_auth)
        assert True  # Should not raise exception
    except HTTPException:
        assert False, "Should not raise exception for non-guardian users"


def test_is_guardian(db: Session, setup_test_data):
    """Test is_guardian function."""
    # Adult without 2FA is a guardian
    assert is_guardian(setup_test_data["adult_without_2fa"], db) is True
    
    # Adult with 2FA is not a guardian in our test setup
    assert is_guardian(setup_test_data["adult_with_2fa"], db) is False
    
    # Minor is not a guardian
    assert is_guardian(setup_test_data["minor"], db) is False


def test_get_guardian_stats(db: Session, setup_test_data):
    """Test get_guardian_stats function."""
    # Get stats for guardian
    stats = get_guardian_stats(setup_test_data["adult_without_2fa"], db)
    assert stats["is_guardian"] is True
    assert stats["minor_count"] > 0
    
    # Get stats for non-guardian
    stats = get_guardian_stats(setup_test_data["adult_with_2fa"], db)
    assert stats["is_guardian"] is False
    assert stats["minor_count"] == 0