"""
Security Models

Database models for security-related features including device management,
session tracking, two-factor authentication, and security alerts.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class DeviceStatus(str, Enum):
    """Device trust status"""

    PENDING = "pending"
    TRUSTED = "trusted"
    REVOKED = "revoked"


class AlertSeverity(str, Enum):
    """Security alert severity levels"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Security alert types"""

    NEW_DEVICE = "new_device"
    SUSPICIOUS_LOGIN = "suspicious_login"
    FAILED_LOGIN = "failed_login"
    PASSWORD_CHANGE = "password_change"
    TWO_FACTOR_DISABLED = "2fa_disabled"
    UNUSUAL_ACTIVITY = "unusual_activity"
    IP_BLOCKED = "ip_blocked"
    ACCOUNT_LOCKED = "account_locked"


class Device(Base):
    """Registered device model for device management"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    location = Column(String(255), nullable=True)
    fingerprint = Column(String(255), nullable=True)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.PENDING)
    is_current = Column(Boolean, default=False)
    last_used = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="devices")


class Session(Base):
    """User session model for session management"""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")
    device = relationship("Device")


class TwoFactorConfig(Base):
    """Two-factor authentication configuration"""

    __tablename__ = "two_factor_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    is_enabled = Column(Boolean, default=False)
    secret_key = Column(String(255), nullable=True)  # Encrypted TOTP secret
    backup_codes = Column(Text, nullable=True)  # JSON array of encrypted backup codes
    recovery_email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    preferred_method = Column(String(20), default="totp")  # totp, sms, email
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="two_factor_config")


class SecuritySettings(Base):
    """User security settings"""

    __tablename__ = "security_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Login settings
    require_2fa = Column(Boolean, default=False)
    login_notification = Column(Boolean, default=True)
    new_device_notification = Column(Boolean, default=True)

    # Session settings
    session_timeout_minutes = Column(Integer, default=60)
    max_concurrent_sessions = Column(Integer, default=5)

    # Security settings
    ip_whitelist_enabled = Column(Boolean, default=False)
    ip_whitelist = Column(Text, nullable=True)  # JSON array of whitelisted IPs

    # Trading security
    require_2fa_for_trading = Column(Boolean, default=False)
    require_2fa_for_withdrawals = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="security_settings")


class SecurityAlert(Base):
    """Security alerts for user notification"""

    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.LOW)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON additional details
    ip_address = Column(String(45), nullable=True)
    device_info = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="security_alerts")


class LoginHistory(Base):
    """Login history for audit purposes"""

    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    location = Column(String(255), nullable=True)
    success = Column(Boolean, default=True)
    failure_reason = Column(String(255), nullable=True)
    two_factor_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="login_history")
    device = relationship("Device")


class SecurityAuditLog(Base):
    """Security audit log for tracking all security-related actions"""

    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(
        String(100), nullable=False
    )  # e.g., "2fa_enabled", "device_trusted"
    details = Column(Text, nullable=True)  # JSON details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), default="success")  # success, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="security_audit_logs")


class WebAuthnCredential(Base):
    """WebAuthn credentials for biometric authentication (fingerprint/Face ID)"""

    __tablename__ = "webauthn_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Credential identification
    credential_id = Column(String(512), unique=True, nullable=False, index=True)
    credential_name = Column(
        String(255), nullable=True
    )  # User-friendly name like "MacBook Touch ID"

    # WebAuthn credential data
    public_key = Column(Text, nullable=False)  # Base64 encoded public key
    sign_count = Column(Integer, default=0)  # Signature counter for replay protection

    # Credential metadata
    credential_type = Column(
        String(50), default="public-key"
    )  # Always "public-key" for WebAuthn
    authenticator_type = Column(
        String(50), nullable=True
    )  # "platform" (built-in) or "cross-platform" (USB key)

    # Device info
    device_type = Column(
        String(100), nullable=True
    )  # e.g., "Touch ID", "Face ID", "Windows Hello", "YubiKey"
    aaguid = Column(String(36), nullable=True)  # Authenticator Attestation GUID

    # Status tracking
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="webauthn_credentials")
