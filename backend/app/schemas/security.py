"""
Security Schemas

Pydantic models for security-related API requests and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class DeviceStatusEnum(str, Enum):
    PENDING = "pending"
    TRUSTED = "trusted"
    REVOKED = "revoked"


class AlertSeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertTypeEnum(str, Enum):
    NEW_DEVICE = "new_device"
    SUSPICIOUS_LOGIN = "suspicious_login"
    FAILED_LOGIN = "failed_login"
    PASSWORD_CHANGE = "password_change"
    TWO_FACTOR_DISABLED = "2fa_disabled"
    UNUSUAL_ACTIVITY = "unusual_activity"
    IP_BLOCKED = "ip_blocked"
    ACCOUNT_LOCKED = "account_locked"


# Device schemas
class DeviceBase(BaseModel):
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None


class DeviceRegisterRequest(DeviceBase):
    fingerprint: Optional[str] = None


class DeviceVerifyRequest(BaseModel):
    device_id: str = Field(..., description="Device ID to verify")
    verification_code: str = Field(..., description="Verification code")


class DeviceResponse(DeviceBase):
    id: int
    device_id: str
    ip_address: Optional[str] = None
    location: Optional[str] = None
    status: DeviceStatusEnum
    is_current: bool
    last_used: datetime
    created_at: datetime
    verified_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int


class DeviceUpdateNameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


# Session schemas
class SessionResponse(BaseModel):
    id: int
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    is_current: bool = False
    expires_at: datetime
    created_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


class TerminateSessionsRequest(BaseModel):
    session_ids: Optional[List[int]] = Field(None, description="Specific session IDs to terminate. If empty, terminates all except current.")
    terminate_all: bool = Field(False, description="Terminate all sessions including current")


class ExtendSessionRequest(BaseModel):
    extend_minutes: int = Field(60, ge=1, le=1440, description="Minutes to extend session")


# Two-factor authentication schemas
class TwoFactorConfigResponse(BaseModel):
    is_enabled: bool
    preferred_method: str
    recovery_email: Optional[str] = None
    phone_number: Optional[str] = None
    has_backup_codes: bool = False
    last_verified: Optional[datetime] = None

    class Config:
        from_attributes = True


class Enable2FARequest(BaseModel):
    method: str = Field("totp", description="2FA method: totp, sms, or email")
    phone_number: Optional[str] = None
    recovery_email: Optional[str] = None


class Enable2FAResponse(BaseModel):
    secret: Optional[str] = None  # For TOTP
    qr_code_url: Optional[str] = None  # QR code data URL
    backup_codes: List[str] = []
    message: str


class Verify2FARequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=8, description="Verification code")


class Verify2FAResponse(BaseModel):
    success: bool
    message: str


class Disable2FARequest(BaseModel):
    code: str = Field(..., description="Current 2FA code or backup code")
    password: str = Field(..., description="Account password for verification")


class RegenerateBackupCodesResponse(BaseModel):
    backup_codes: List[str]
    message: str


# Security settings schemas
class SecuritySettingsResponse(BaseModel):
    require_2fa: bool = False
    login_notification: bool = True
    new_device_notification: bool = True
    session_timeout_minutes: int = 60
    max_concurrent_sessions: int = 5
    ip_whitelist_enabled: bool = False
    ip_whitelist: List[str] = []
    require_2fa_for_trading: bool = False
    require_2fa_for_withdrawals: bool = True

    class Config:
        from_attributes = True


class SecuritySettingsUpdateRequest(BaseModel):
    require_2fa: Optional[bool] = None
    login_notification: Optional[bool] = None
    new_device_notification: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440)
    max_concurrent_sessions: Optional[int] = Field(None, ge=1, le=20)
    ip_whitelist_enabled: Optional[bool] = None
    require_2fa_for_trading: Optional[bool] = None
    require_2fa_for_withdrawals: Optional[bool] = None


# Login history schemas
class LoginHistoryResponse(BaseModel):
    id: int
    ip_address: Optional[str] = None
    location: Optional[str] = None
    device_name: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None
    two_factor_used: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginHistoryListResponse(BaseModel):
    history: List[LoginHistoryResponse]
    total: int


# Security alert schemas
class SecurityAlertResponse(BaseModel):
    id: int
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    is_read: bool
    is_dismissed: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SecurityAlertListResponse(BaseModel):
    alerts: List[SecurityAlertResponse]
    unread_count: int
    total: int


# IP whitelist schemas
class AddIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to whitelist")
    description: Optional[str] = None


class IPWhitelistResponse(BaseModel):
    success: bool
    message: str
    ip_whitelist: List[str]


# Emergency actions schemas
class LockAccountRequest(BaseModel):
    reason: Optional[str] = None
    password: str = Field(..., description="Current password for verification")


class LockAccountResponse(BaseModel):
    success: bool
    message: str
    locked_until: Optional[datetime] = None


class ReportSuspiciousRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=2000)
    suspicious_activity_type: Optional[str] = None
    additional_details: Optional[Dict[str, Any]] = None


class ReportSuspiciousResponse(BaseModel):
    success: bool
    message: str
    report_id: str


# Audit log schemas
class SecurityAuditLogResponse(BaseModel):
    id: int
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityAuditLogListResponse(BaseModel):
    logs: List[SecurityAuditLogResponse]
    total: int


# Device fingerprint schema
class DeviceFingerprintResponse(BaseModel):
    fingerprint: str
    components: Dict[str, Any]


# WebAuthn / Biometric authentication schemas
class WebAuthnCredentialResponse(BaseModel):
    id: int
    credential_id: str
    credential_name: Optional[str] = None
    device_type: Optional[str] = None
    authenticator_type: Optional[str] = None
    is_active: bool
    last_used: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebAuthnCredentialListResponse(BaseModel):
    credentials: List[WebAuthnCredentialResponse]
    total: int


class WebAuthnRegistrationStartRequest(BaseModel):
    credential_name: Optional[str] = Field(None, description="Friendly name for the credential (e.g., 'MacBook Touch ID')")


class WebAuthnRegistrationStartResponse(BaseModel):
    challenge: str
    rp_id: str
    rp_name: str
    user_id: str
    user_name: str
    user_display_name: str
    pub_key_cred_params: List[Dict[str, Any]]
    timeout: int
    attestation: str
    authenticator_selection: Dict[str, Any]


class WebAuthnRegistrationCompleteRequest(BaseModel):
    credential_id: str = Field(..., description="Base64url encoded credential ID")
    client_data_json: str = Field(..., description="Base64url encoded client data JSON")
    attestation_object: str = Field(..., description="Base64url encoded attestation object")
    credential_name: Optional[str] = None
    authenticator_type: Optional[str] = Field(None, description="'platform' or 'cross-platform'")


class WebAuthnRegistrationCompleteResponse(BaseModel):
    success: bool
    message: str
    credential_id: Optional[int] = None


class WebAuthnAuthenticationStartRequest(BaseModel):
    username: Optional[str] = Field(None, description="Optional username for authentication")


class WebAuthnAuthenticationStartResponse(BaseModel):
    challenge: str
    rp_id: str
    timeout: int
    user_verification: str
    allowed_credentials: List[Dict[str, str]]


class WebAuthnAuthenticationCompleteRequest(BaseModel):
    credential_id: str = Field(..., description="Base64url encoded credential ID")
    client_data_json: str = Field(..., description="Base64url encoded client data JSON")
    authenticator_data: str = Field(..., description="Base64url encoded authenticator data")
    signature: str = Field(..., description="Base64url encoded signature")
    user_handle: Optional[str] = Field(None, description="Base64url encoded user handle")


class WebAuthnAuthenticationCompleteResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class WebAuthnCredentialUpdateRequest(BaseModel):
    credential_name: str = Field(..., min_length=1, max_length=255)


class WebAuthnCredentialDeleteResponse(BaseModel):
    success: bool
    message: str
