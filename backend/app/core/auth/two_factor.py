"""Two-factor authentication implementation."""
import secrets
from typing import List

import pyotp
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User


class UserTwoFactorCreate:
    """Schema for two-factor authentication setup."""

    def __init__(self, secret: str, code: str):
        self.secret = secret
        self.code = code


class TwoFactorAuth:
    """Two-factor authentication handler."""

    def __init__(self, issuer_name: str = "Elson Trading"):
        """Initialize TwoFactorAuth with issuer name."""
        self.issuer_name = issuer_name

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    def get_totp_uri(self, secret: str, username: str) -> str:
        """Get URI for TOTP QR code."""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username, issuer_name=self.issuer_name
        )

    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify a TOTP code against a secret."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for 2FA recovery."""
        return [secrets.token_hex(5).upper() for _ in range(count)]

    def setup_2fa(
        self, db: Session, user_id: int, two_factor_data: UserTwoFactorCreate
    ) -> bool:
        """Set up 2FA for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Verify TOTP code before enabling
        if not self.verify_totp(two_factor_data.secret, two_factor_data.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        # Generate backup codes
        backup_codes = self.generate_backup_codes()

        # Update user model with 2FA data
        # Note: These fields need to be added to the User model
        if hasattr(user, "two_factor_enabled"):
            user.two_factor_enabled = True
            user.two_factor_secret = two_factor_data.secret
            user.two_factor_backup_codes = backup_codes

        db.commit()
        return True

    def disable_2fa(self, db: Session, user_id: int) -> bool:
        """Disable 2FA for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Note: These fields need to be added to the User model
        if hasattr(user, "two_factor_enabled"):
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.two_factor_backup_codes = []

        db.commit()
        return True

    def verify_backup_code(self, db: Session, user_id: int, code: str) -> bool:
        """Verify a backup code for 2FA recovery."""
        user = db.query(User).filter(User.id == user_id).first()
        if (
            not user
            or not hasattr(user, "two_factor_backup_codes")
            or not user.two_factor_backup_codes
        ):
            return False

        if code in user.two_factor_backup_codes:
            # Remove used backup code
            user.two_factor_backup_codes.remove(code)
            db.commit()
            return True

        return False


# Global instance for dependency injection
two_factor_auth = TwoFactorAuth()


def get_two_factor_auth() -> TwoFactorAuth:
    """Dependency injection for TwoFactorAuth."""
    return two_factor_auth
