"""
Security API Endpoints

Endpoints for device management, session management, two-factor authentication,
security settings, and security alerts.
"""

import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, verify_password
from app.db.base import get_db
from app.models.security import (
    AlertSeverity,
    AlertType,
    Device,
    DeviceStatus,
    LoginHistory,
    SecurityAlert,
    SecurityAuditLog,
    SecuritySettings,
)
from app.models.security import Session as UserSession
from app.models.security import TwoFactorConfig
from app.models.user import User
from app.schemas.security import (
    AddIPRequest,
    DeviceFingerprintResponse,
    DeviceListResponse,
    DeviceRegisterRequest,
    DeviceResponse,
    DeviceUpdateNameRequest,
    DeviceVerifyRequest,
    Disable2FARequest,
    Enable2FARequest,
    Enable2FAResponse,
    ExtendSessionRequest,
    IPWhitelistResponse,
    LockAccountRequest,
    LockAccountResponse,
    LoginHistoryListResponse,
    LoginHistoryResponse,
    RegenerateBackupCodesResponse,
    ReportSuspiciousRequest,
    ReportSuspiciousResponse,
    SecurityAlertListResponse,
    SecurityAlertResponse,
    SecurityAuditLogListResponse,
    SecurityAuditLogResponse,
    SecuritySettingsResponse,
    SecuritySettingsUpdateRequest,
    SessionListResponse,
    SessionResponse,
    TerminateSessionsRequest,
    TwoFactorConfigResponse,
    Verify2FARequest,
    Verify2FAResponse,
)

router = APIRouter()


# Helper functions
def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    details: dict = None,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "success",
):
    """Create a security audit log entry"""
    log = SecurityAuditLog(
        user_id=user_id,
        action=action,
        details=json.dumps(details) if details else None,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
    )
    db.add(log)
    db.commit()
    return log


def get_client_info(request: Request):
    """Extract client info from request"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


# ==================== Device Management ====================


@router.get("/devices", response_model=DeviceListResponse)
async def get_devices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all registered devices for the current user"""
    devices = (
        db.query(Device)
        .filter(
            Device.user_id == current_user.id, Device.status != DeviceStatus.REVOKED
        )
        .order_by(Device.last_used.desc())
        .all()
    )
    return DeviceListResponse(
        devices=[DeviceResponse.model_validate(d) for d in devices],
        total=len(devices),
    )


@router.get("/devices/current", response_model=DeviceResponse)
async def get_current_device(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the current device information"""
    # Try to find device by fingerprint or create a placeholder
    client_info = get_client_info(request)
    device = (
        db.query(Device)
        .filter(
            Device.user_id == current_user.id,
            Device.ip_address == client_info["ip_address"],
            Device.status != DeviceStatus.REVOKED,
        )
        .first()
    )

    if not device:
        # Return a placeholder for unregistered device
        return DeviceResponse(
            id=0,
            device_id="current",
            device_name="Current Device",
            device_type="unknown",
            browser=None,
            os=None,
            ip_address=client_info["ip_address"],
            location=None,
            status=DeviceStatus.PENDING,
            is_current=True,
            last_used=datetime.utcnow(),
            created_at=datetime.utcnow(),
            verified_at=None,
        )

    device.is_current = True
    return DeviceResponse.model_validate(device)


@router.post("/devices/register", response_model=DeviceResponse)
async def register_device(
    request: Request,
    device_data: DeviceRegisterRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Register a new device"""
    client_info = get_client_info(request)

    # Generate unique device ID
    device_id = str(uuid.uuid4())

    device = Device(
        user_id=current_user.id,
        device_id=device_id,
        device_name=device_data.device_name or "Unknown Device",
        device_type=device_data.device_type,
        browser=device_data.browser,
        os=device_data.os,
        ip_address=client_info["ip_address"],
        fingerprint=device_data.fingerprint,
        status=DeviceStatus.PENDING,
        is_current=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    create_audit_log(
        db,
        current_user.id,
        "device_registered",
        {"device_id": device_id, "device_name": device.device_name},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return DeviceResponse.model_validate(device)


@router.post("/devices/verify", response_model=DeviceResponse)
async def verify_device(
    request: Request,
    verify_data: DeviceVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Verify a device with verification code"""
    device = (
        db.query(Device)
        .filter(
            Device.device_id == verify_data.device_id,
            Device.user_id == current_user.id,
        )
        .first()
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # In production, verify the code sent via email/SMS
    # For now, accept any 6-digit code
    if len(verify_data.verification_code) >= 6:
        device.status = DeviceStatus.TRUSTED
        device.verified_at = datetime.utcnow()
        db.commit()

        client_info = get_client_info(request)
        create_audit_log(
            db,
            current_user.id,
            "device_verified",
            {"device_id": device.device_id},
            client_info["ip_address"],
            client_info["user_agent"],
        )

        return DeviceResponse.model_validate(device)

    raise HTTPException(status_code=400, detail="Invalid verification code")


@router.put("/devices/{device_id}/trust", response_model=DeviceResponse)
async def trust_device(
    device_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark a device as trusted"""
    device = (
        db.query(Device)
        .filter(Device.device_id == device_id, Device.user_id == current_user.id)
        .first()
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = DeviceStatus.TRUSTED
    device.verified_at = datetime.utcnow()
    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "device_trusted",
        {"device_id": device_id},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return DeviceResponse.model_validate(device)


@router.delete("/devices/{device_id}/revoke")
async def revoke_device(
    device_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke a device's access"""
    device = (
        db.query(Device)
        .filter(Device.device_id == device_id, Device.user_id == current_user.id)
        .first()
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = DeviceStatus.REVOKED
    db.commit()

    # Also terminate any sessions from this device
    db.query(UserSession).filter(UserSession.device_id == device.id).update(
        {"is_active": False}
    )
    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "device_revoked",
        {"device_id": device_id},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return {"success": True, "message": "Device revoked successfully"}


@router.put("/devices/{device_id}/name", response_model=DeviceResponse)
async def update_device_name(
    device_id: str,
    name_data: DeviceUpdateNameRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a device's name"""
    device = (
        db.query(Device)
        .filter(Device.device_id == device_id, Device.user_id == current_user.id)
        .first()
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.device_name = name_data.name
    db.commit()

    return DeviceResponse.model_validate(device)


# ==================== Session Management ====================


@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all active sessions"""
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_active == True)
        .order_by(UserSession.last_activity.desc())
        .all()
    )

    session_responses = []
    for s in sessions:
        device = (
            db.query(Device).filter(Device.id == s.device_id).first()
            if s.device_id
            else None
        )
        session_responses.append(
            SessionResponse(
                id=s.id,
                device_id=s.device_id,
                device_name=device.device_name if device else None,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                is_active=s.is_active,
                is_current=False,  # Would need to match current session token
                expires_at=s.expires_at,
                created_at=s.created_at,
                last_activity=s.last_activity,
            )
        )

    return SessionListResponse(sessions=session_responses, total=len(session_responses))


@router.post("/sessions/terminate")
async def terminate_sessions(
    request: Request,
    terminate_data: TerminateSessionsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Terminate specified sessions or all sessions"""
    query = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True,
    )

    if terminate_data.session_ids:
        query = query.filter(UserSession.id.in_(terminate_data.session_ids))

    terminated_count = query.update({"is_active": False})
    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "sessions_terminated",
        {"count": terminated_count, "session_ids": terminate_data.session_ids},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return {"success": True, "message": f"Terminated {terminated_count} sessions"}


@router.post("/sessions/extend")
async def extend_session(
    extend_data: ExtendSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Extend the current session"""
    # In a real implementation, you'd identify the current session
    # For now, extend all active sessions
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_active == True)
        .all()
    )

    for session in sessions:
        session.expires_at = session.expires_at + timedelta(
            minutes=extend_data.extend_minutes
        )

    db.commit()

    return {
        "success": True,
        "message": f"Session extended by {extend_data.extend_minutes} minutes",
    }


# ==================== Two-Factor Authentication ====================


@router.get("/2fa", response_model=TwoFactorConfigResponse)
async def get_two_factor_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get 2FA configuration status"""
    config = (
        db.query(TwoFactorConfig)
        .filter(TwoFactorConfig.user_id == current_user.id)
        .first()
    )

    if not config:
        return TwoFactorConfigResponse(
            is_enabled=False,
            preferred_method="totp",
            recovery_email=None,
            phone_number=None,
            has_backup_codes=False,
            last_verified=None,
        )

    return TwoFactorConfigResponse(
        is_enabled=config.is_enabled,
        preferred_method=config.preferred_method,
        recovery_email=config.recovery_email,
        phone_number=config.phone_number,
        has_backup_codes=bool(config.backup_codes),
        last_verified=config.last_verified,
    )


@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    request: Request,
    enable_data: Enable2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Enable two-factor authentication"""
    # Check if already enabled
    existing = (
        db.query(TwoFactorConfig)
        .filter(TwoFactorConfig.user_id == current_user.id)
        .first()
    )

    if existing and existing.is_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled")

    # Generate secret and backup codes
    secret = secrets.token_hex(20)
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

    if existing:
        existing.secret_key = secret
        existing.backup_codes = json.dumps(backup_codes)
        existing.preferred_method = enable_data.method
        existing.recovery_email = enable_data.recovery_email
        existing.phone_number = enable_data.phone_number
        existing.is_enabled = False  # Not enabled until verified
        config = existing
    else:
        config = TwoFactorConfig(
            user_id=current_user.id,
            secret_key=secret,
            backup_codes=json.dumps(backup_codes),
            preferred_method=enable_data.method,
            recovery_email=enable_data.recovery_email,
            phone_number=enable_data.phone_number,
            is_enabled=False,
        )
        db.add(config)

    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "2fa_setup_initiated",
        {"method": enable_data.method},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    # Generate QR code URL (in production, use pyotp)
    qr_url = f"otpauth://totp/ElsonWealth:{current_user.email}?secret={secret}&issuer=ElsonWealth"

    return Enable2FAResponse(
        secret=secret,
        qr_code_url=qr_url,
        backup_codes=backup_codes,
        message="2FA setup initiated. Please verify with the code from your authenticator app.",
    )


@router.post("/2fa/verify", response_model=Verify2FAResponse)
async def verify_2fa(
    request: Request,
    verify_data: Verify2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Verify 2FA setup with code"""
    config = (
        db.query(TwoFactorConfig)
        .filter(TwoFactorConfig.user_id == current_user.id)
        .first()
    )

    if not config:
        raise HTTPException(status_code=400, detail="2FA not configured")

    # In production, verify TOTP code using pyotp
    # For now, accept any 6-digit code for testing
    if len(verify_data.code) >= 6:
        config.is_enabled = True
        config.last_verified = datetime.utcnow()
        current_user.two_factor_enabled = True
        db.commit()

        client_info = get_client_info(request)
        create_audit_log(
            db,
            current_user.id,
            "2fa_enabled",
            {},
            client_info["ip_address"],
            client_info["user_agent"],
        )

        return Verify2FAResponse(success=True, message="2FA enabled successfully")

    return Verify2FAResponse(success=False, message="Invalid verification code")


@router.post("/2fa/disable")
async def disable_2fa(
    request: Request,
    disable_data: Disable2FARequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Disable two-factor authentication"""
    # Verify password
    if not verify_password(disable_data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    config = (
        db.query(TwoFactorConfig)
        .filter(TwoFactorConfig.user_id == current_user.id)
        .first()
    )

    if not config or not config.is_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    # Verify 2FA code (in production, use pyotp)
    if len(disable_data.code) < 6:
        raise HTTPException(status_code=400, detail="Invalid 2FA code")

    config.is_enabled = False
    current_user.two_factor_enabled = False
    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "2fa_disabled",
        {},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    # Create security alert
    alert = SecurityAlert(
        user_id=current_user.id,
        alert_type=AlertType.TWO_FACTOR_DISABLED,
        severity=AlertSeverity.HIGH,
        title="Two-Factor Authentication Disabled",
        message="2FA has been disabled on your account. If you didn't do this, please secure your account immediately.",
        ip_address=client_info["ip_address"],
    )
    db.add(alert)
    db.commit()

    return {"success": True, "message": "2FA disabled successfully"}


@router.post(
    "/2fa/backup-codes/regenerate", response_model=RegenerateBackupCodesResponse
)
async def regenerate_backup_codes(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Regenerate backup codes"""
    config = (
        db.query(TwoFactorConfig)
        .filter(TwoFactorConfig.user_id == current_user.id)
        .first()
    )

    if not config:
        raise HTTPException(status_code=400, detail="2FA not configured")

    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
    config.backup_codes = json.dumps(backup_codes)
    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "backup_codes_regenerated",
        {},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return RegenerateBackupCodesResponse(
        backup_codes=backup_codes,
        message="New backup codes generated. Please store them securely.",
    )


# ==================== Security Settings ====================


@router.get("/settings", response_model=SecuritySettingsResponse)
async def get_security_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get security settings"""
    settings = (
        db.query(SecuritySettings)
        .filter(SecuritySettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        # Return defaults
        return SecuritySettingsResponse()

    ip_whitelist = json.loads(settings.ip_whitelist) if settings.ip_whitelist else []

    return SecuritySettingsResponse(
        require_2fa=settings.require_2fa,
        login_notification=settings.login_notification,
        new_device_notification=settings.new_device_notification,
        session_timeout_minutes=settings.session_timeout_minutes,
        max_concurrent_sessions=settings.max_concurrent_sessions,
        ip_whitelist_enabled=settings.ip_whitelist_enabled,
        ip_whitelist=ip_whitelist,
        require_2fa_for_trading=settings.require_2fa_for_trading,
        require_2fa_for_withdrawals=settings.require_2fa_for_withdrawals,
    )


@router.put("/settings", response_model=SecuritySettingsResponse)
async def update_security_settings(
    request: Request,
    update_data: SecuritySettingsUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update security settings"""
    settings = (
        db.query(SecuritySettings)
        .filter(SecuritySettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        settings = SecuritySettings(user_id=current_user.id)
        db.add(settings)

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if value is not None:
            setattr(settings, key, value)

    settings.updated_at = datetime.utcnow()
    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "security_settings_updated",
        update_dict,
        client_info["ip_address"],
        client_info["user_agent"],
    )

    ip_whitelist = json.loads(settings.ip_whitelist) if settings.ip_whitelist else []

    return SecuritySettingsResponse(
        require_2fa=settings.require_2fa,
        login_notification=settings.login_notification,
        new_device_notification=settings.new_device_notification,
        session_timeout_minutes=settings.session_timeout_minutes,
        max_concurrent_sessions=settings.max_concurrent_sessions,
        ip_whitelist_enabled=settings.ip_whitelist_enabled,
        ip_whitelist=ip_whitelist,
        require_2fa_for_trading=settings.require_2fa_for_trading,
        require_2fa_for_withdrawals=settings.require_2fa_for_withdrawals,
    )


# ==================== Login History ====================


@router.get("/login-history", response_model=LoginHistoryListResponse)
async def get_login_history(
    limit: int = Query(50, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get login history"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    history = (
        db.query(LoginHistory)
        .filter(
            LoginHistory.user_id == current_user.id,
            LoginHistory.created_at >= cutoff_date,
        )
        .order_by(LoginHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    history_responses = []
    for h in history:
        device = (
            db.query(Device).filter(Device.id == h.device_id).first()
            if h.device_id
            else None
        )
        history_responses.append(
            LoginHistoryResponse(
                id=h.id,
                ip_address=h.ip_address,
                location=h.location,
                device_name=device.device_name if device else None,
                browser=device.browser if device else None,
                os=device.os if device else None,
                success=h.success,
                failure_reason=h.failure_reason,
                two_factor_used=h.two_factor_used,
                created_at=h.created_at,
            )
        )

    return LoginHistoryListResponse(
        history=history_responses, total=len(history_responses)
    )


# ==================== Security Alerts ====================


@router.get("/alerts", response_model=SecurityAlertListResponse)
async def get_security_alerts(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get security alerts"""
    query = db.query(SecurityAlert).filter(
        SecurityAlert.user_id == current_user.id,
        SecurityAlert.is_dismissed == False,
    )

    if unread_only:
        query = query.filter(SecurityAlert.is_read == False)

    alerts = query.order_by(SecurityAlert.created_at.desc()).limit(100).all()

    unread_count = (
        db.query(SecurityAlert)
        .filter(
            SecurityAlert.user_id == current_user.id,
            SecurityAlert.is_read == False,
            SecurityAlert.is_dismissed == False,
        )
        .count()
    )

    return SecurityAlertListResponse(
        alerts=[SecurityAlertResponse.model_validate(a) for a in alerts],
        unread_count=unread_count,
        total=len(alerts),
    )


@router.put("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark an alert as read"""
    alert = (
        db.query(SecurityAlert)
        .filter(SecurityAlert.id == alert_id, SecurityAlert.user_id == current_user.id)
        .first()
    )

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    alert.read_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "Alert marked as read"}


@router.delete("/alerts/{alert_id}")
async def dismiss_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Dismiss an alert"""
    alert = (
        db.query(SecurityAlert)
        .filter(SecurityAlert.id == alert_id, SecurityAlert.user_id == current_user.id)
        .first()
    )

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_dismissed = True
    db.commit()

    return {"success": True, "message": "Alert dismissed"}


# ==================== IP Whitelist ====================


@router.post("/ip-whitelist", response_model=IPWhitelistResponse)
async def add_ip_to_whitelist(
    request: Request,
    ip_data: AddIPRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add an IP address to the whitelist"""
    settings = (
        db.query(SecuritySettings)
        .filter(SecuritySettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        settings = SecuritySettings(user_id=current_user.id)
        db.add(settings)

    ip_whitelist = json.loads(settings.ip_whitelist) if settings.ip_whitelist else []

    if ip_data.ip_address not in ip_whitelist:
        ip_whitelist.append(ip_data.ip_address)
        settings.ip_whitelist = json.dumps(ip_whitelist)
        db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "ip_added_to_whitelist",
        {"ip_address": ip_data.ip_address},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return IPWhitelistResponse(
        success=True,
        message=f"IP {ip_data.ip_address} added to whitelist",
        ip_whitelist=ip_whitelist,
    )


@router.delete("/ip-whitelist/{ip_address}")
async def remove_ip_from_whitelist(
    ip_address: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove an IP address from the whitelist"""
    settings = (
        db.query(SecuritySettings)
        .filter(SecuritySettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    ip_whitelist = json.loads(settings.ip_whitelist) if settings.ip_whitelist else []

    if ip_address in ip_whitelist:
        ip_whitelist.remove(ip_address)
        settings.ip_whitelist = json.dumps(ip_whitelist)
        db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "ip_removed_from_whitelist",
        {"ip_address": ip_address},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return {"success": True, "message": f"IP {ip_address} removed from whitelist"}


# ==================== Emergency Actions ====================


@router.post("/emergency/lock-account", response_model=LockAccountResponse)
async def lock_account(
    request: Request,
    lock_data: LockAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Emergency lock the account"""
    # Verify password
    if not verify_password(lock_data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    # Lock account for 24 hours
    lock_until = datetime.utcnow() + timedelta(hours=24)
    current_user.account_locked_until = lock_until
    current_user.is_active = False

    # Terminate all sessions
    db.query(UserSession).filter(UserSession.user_id == current_user.id).update(
        {"is_active": False}
    )

    db.commit()

    client_info = get_client_info(request)
    create_audit_log(
        db,
        current_user.id,
        "account_locked",
        {"reason": lock_data.reason, "locked_until": lock_until.isoformat()},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    return LockAccountResponse(
        success=True,
        message="Account has been locked. Contact support to unlock.",
        locked_until=lock_until,
    )


@router.post("/report-suspicious", response_model=ReportSuspiciousResponse)
async def report_suspicious_activity(
    request: Request,
    report_data: ReportSuspiciousRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Report suspicious activity"""
    report_id = str(uuid.uuid4())[:8].upper()

    client_info = get_client_info(request)

    # Create security alert
    alert = SecurityAlert(
        user_id=current_user.id,
        alert_type=AlertType.UNUSUAL_ACTIVITY,
        severity=AlertSeverity.HIGH,
        title="Suspicious Activity Reported",
        message=report_data.description,
        details=(
            json.dumps(report_data.additional_details)
            if report_data.additional_details
            else None
        ),
        ip_address=client_info["ip_address"],
    )
    db.add(alert)

    create_audit_log(
        db,
        current_user.id,
        "suspicious_activity_reported",
        {"report_id": report_id, "type": report_data.suspicious_activity_type},
        client_info["ip_address"],
        client_info["user_agent"],
    )

    db.commit()

    return ReportSuspiciousResponse(
        success=True,
        message="Your report has been submitted. Our security team will review it.",
        report_id=report_id,
    )


# ==================== Audit Log ====================


@router.get("/audit", response_model=SecurityAuditLogListResponse)
async def get_security_audit_log(
    limit: int = Query(50, ge=1, le=100),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get security audit log"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    logs = (
        db.query(SecurityAuditLog)
        .filter(
            SecurityAuditLog.user_id == current_user.id,
            SecurityAuditLog.created_at >= cutoff_date,
        )
        .order_by(SecurityAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    log_responses = []
    for log in logs:
        log_responses.append(
            SecurityAuditLogResponse(
                id=log.id,
                action=log.action,
                details=json.loads(log.details) if log.details else None,
                ip_address=log.ip_address,
                status=log.status,
                created_at=log.created_at,
            )
        )

    return SecurityAuditLogListResponse(logs=log_responses, total=len(log_responses))


# ==================== Device Fingerprint ====================


@router.get("/device-fingerprint", response_model=DeviceFingerprintResponse)
async def generate_device_fingerprint(
    request: Request,
):
    """Generate a device fingerprint based on request headers"""
    # In production, this would use browser fingerprinting library
    # For now, generate based on available headers
    client_info = get_client_info(request)

    fingerprint_data = {
        "user_agent": client_info["user_agent"],
        "ip_address": client_info["ip_address"],
        "accept_language": request.headers.get("accept-language"),
        "accept_encoding": request.headers.get("accept-encoding"),
    }

    # Simple fingerprint generation
    import hashlib

    fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
    fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

    return DeviceFingerprintResponse(
        fingerprint=fingerprint,
        components=fingerprint_data,
    )
