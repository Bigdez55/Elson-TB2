"""
WebAuthn / Biometric Authentication Endpoints - SECURITY HARDENED

This module implements secure biometric authentication using the WebAuthn standard.
All cryptographic verification is properly implemented.
"""

import base64
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers.exceptions import (
    InvalidAuthenticationResponse,
    InvalidRegistrationResponse,
)
from webauthn.helpers.structs import (
    AuthenticationCredential,
    AuthenticatorAssertionResponse,
    AuthenticatorAttestationResponse,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    UserVerificationRequirement,
)

from app.api.deps import get_current_active_user, get_db, get_redis
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.security import SecurityAuditLog, WebAuthnCredential
from app.models.user import User
from app.schemas.security import (
    WebAuthnAuthenticationCompleteRequest,
    WebAuthnAuthenticationCompleteResponse,
    WebAuthnAuthenticationStartRequest,
    WebAuthnAuthenticationStartResponse,
    WebAuthnCredentialDeleteResponse,
    WebAuthnCredentialListResponse,
    WebAuthnCredentialResponse,
    WebAuthnCredentialUpdateRequest,
    WebAuthnRegistrationCompleteRequest,
    WebAuthnRegistrationCompleteResponse,
    WebAuthnRegistrationStartRequest,
    WebAuthnRegistrationStartResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# WebAuthn configuration
RP_ID = getattr(settings, "WEBAUTHN_RP_ID", "localhost")
RP_NAME = getattr(settings, "WEBAUTHN_RP_NAME", "Elson Trading Platform")
ORIGIN = getattr(settings, "WEBAUTHN_ORIGIN", "http://localhost:3000")
CHALLENGE_TIMEOUT_MINUTES = getattr(settings, "WEBAUTHN_CHALLENGE_TIMEOUT", 5)

# Rate limiting configuration
MAX_ATTEMPTS_PER_HOUR = 10
MAX_REGISTRATIONS_PER_DAY = 5


def safe_b64decode(data: str) -> bytes:
    """Safely decode base64url string with automatic padding"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def log_security_event(
    user_id: int,
    action: str,
    success: bool,
    ip_address: str,
    details: dict,
    db: Session,
):
    """Log security-related events for audit trail"""
    try:
        audit_log = SecurityAuditLog(
            user_id=user_id,
            action=action,
            status="success" if success else "failed",
            ip_address=ip_address,
            details=json.dumps(details),
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")


async def check_rate_limit(
    redis_client, key: str, max_attempts: int, window_seconds: int
) -> bool:
    """Check if rate limit is exceeded"""
    try:
        current = redis_client.get(key)
        if current and int(current) >= max_attempts:
            return False

        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        pipe.execute()
        return True
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open for availability
        return True


@router.get("/credentials", response_model=WebAuthnCredentialListResponse)
async def list_credentials(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all registered biometric credentials for the current user"""
    credentials = (
        db.query(WebAuthnCredential)
        .filter(WebAuthnCredential.user_id == current_user.id)
        .all()
    )

    return WebAuthnCredentialListResponse(
        credentials=[
            WebAuthnCredentialResponse.model_validate(cred) for cred in credentials
        ],
        total=len(credentials),
    )


@router.post("/register/start", response_model=WebAuthnRegistrationStartResponse)
async def start_registration(
    request: WebAuthnRegistrationStartRequest,
    request_obj: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Start WebAuthn registration process (Step 1)
    Returns challenge and options for the browser's WebAuthn API
    """
    ip_address = get_client_ip(request_obj)

    # Rate limiting - max 5 registrations per day per user
    rate_limit_key = f"webauthn:reg_limit:{current_user.id}"
    if not await check_rate_limit(
        redis_client, rate_limit_key, MAX_REGISTRATIONS_PER_DAY, 86400
    ):
        logger.warning(
            f"Rate limit exceeded for user {current_user.id} from {ip_address}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )

    # Get existing credentials to exclude them
    existing_credentials = (
        db.query(WebAuthnCredential)
        .filter(
            WebAuthnCredential.user_id == current_user.id,
            WebAuthnCredential.is_active == True,
        )
        .all()
    )

    exclude_credentials = []
    for cred in existing_credentials:
        try:
            exclude_credentials.append(
                PublicKeyCredentialDescriptor(id=safe_b64decode(cred.credential_id))
            )
        except Exception as e:
            logger.error(f"Failed to decode credential {cred.id}: {e}")
            continue

    # Generate registration options
    user_id = str(current_user.id).encode("utf-8")

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id,
        user_name=current_user.email,
        user_display_name=current_user.full_name or current_user.email,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )

    # Store challenge in Redis with unique ID and TTL
    challenge_id = str(uuid.uuid4())
    challenge_data = {
        "challenge": base64.urlsafe_b64encode(options.challenge).decode(),
        "user_id": current_user.id,
        "credential_name": request.credential_name,
        "timestamp": datetime.utcnow().isoformat(),
    }

    redis_key = f"webauthn:reg:{current_user.id}:{challenge_id}"
    redis_client.setex(
        redis_key,
        timedelta(minutes=CHALLENGE_TIMEOUT_MINUTES),
        json.dumps(challenge_data),
    )

    # Log the registration attempt
    await log_security_event(
        user_id=current_user.id,
        action="webauthn_registration_started",
        success=True,
        ip_address=ip_address,
        details={"challenge_id": challenge_id},
        db=db,
    )

    # Convert options to JSON-serializable format
    options_dict = options_to_json(options)
    options_parsed = json.loads(options_dict)

    return WebAuthnRegistrationStartResponse(
        challenge=base64.urlsafe_b64encode(options.challenge).decode().rstrip("="),
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=base64.urlsafe_b64encode(user_id).decode().rstrip("="),
        user_name=current_user.email,
        user_display_name=current_user.full_name or current_user.email,
        pub_key_cred_params=options_parsed["pubKeyCredParams"],
        timeout=options.timeout,
        attestation=options.attestation,
        authenticator_selection={
            "userVerification": "preferred",
            "authenticatorAttachment": "platform",
        },
    )


@router.post("/register/complete", response_model=WebAuthnRegistrationCompleteResponse)
async def complete_registration(
    request: WebAuthnRegistrationCompleteRequest,
    request_obj: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Complete WebAuthn registration (Step 2)
    Verify and store the credential with full cryptographic verification
    """
    ip_address = get_client_ip(request_obj)

    # Find the challenge in Redis (check all challenges for this user)
    pattern = f"webauthn:reg:{current_user.id}:*"
    keys = redis_client.keys(pattern)

    stored_data = None
    redis_key = None
    for key in keys:
        data = redis_client.get(key)
        if data:
            stored_data = json.loads(data)
            redis_key = key
            break

    if not stored_data:
        logger.warning(f"No registration challenge found for user {current_user.id}")
        await log_security_event(
            user_id=current_user.id,
            action="webauthn_registration_failed",
            success=False,
            ip_address=ip_address,
            details={"reason": "No challenge found"},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No registration challenge found. Please start again.",
        )

    # Verify user_id matches
    if stored_data.get("user_id") != current_user.id:
        logger.error(
            f"User ID mismatch in registration: stored={stored_data.get('user_id')}, actual={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid registration request.",
        )

    try:
        # Decode the challenge
        expected_challenge = safe_b64decode(stored_data["challenge"])

        # Prepare credential for verification
        credential = RegistrationCredential(
            id=request.credential_id,
            raw_id=safe_b64decode(request.credential_id),
            response=AuthenticatorAttestationResponse(
                client_data_json=safe_b64decode(request.client_data_json),
                attestation_object=safe_b64decode(request.attestation_object),
            ),
            type="public-key",
        )

        # CRITICAL: Verify the registration response cryptographically
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
        )

        # Check if credential already exists
        existing = (
            db.query(WebAuthnCredential)
            .filter(WebAuthnCredential.credential_id == request.credential_id)
            .first()
        )

        if existing:
            logger.warning(
                f"Duplicate credential registration attempt: {request.credential_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This credential is already registered.",
            )

        # Create new credential with verified public key
        credential_name = (
            request.credential_name
            or stored_data.get("credential_name")
            or "Biometric Device"
        )

        # Store the verified public key (NOT the attestation object)
        public_key_b64 = base64.b64encode(verification.credential_public_key).decode()

        new_credential = WebAuthnCredential(
            user_id=current_user.id,
            credential_id=request.credential_id,
            credential_name=credential_name[:255],  # Truncate to prevent overflow
            public_key=public_key_b64,
            sign_count=verification.sign_count,
            authenticator_type=request.authenticator_type or "platform",
            device_type=_detect_device_type(request.authenticator_type),
            aaguid=verification.aaguid if hasattr(verification, "aaguid") else None,
        )

        db.add(new_credential)
        db.commit()
        db.refresh(new_credential)

        # Clean up challenge from Redis
        redis_client.delete(redis_key)

        # Log successful registration
        await log_security_event(
            user_id=current_user.id,
            action="webauthn_registration_completed",
            success=True,
            ip_address=ip_address,
            details={
                "credential_id": new_credential.id,
                "credential_name": credential_name,
                "authenticator_type": request.authenticator_type,
            },
            db=db,
        )

        return WebAuthnRegistrationCompleteResponse(
            success=True,
            message=f"Biometric credential registered successfully",
            credential_id=new_credential.id,
        )

    except InvalidRegistrationResponse as e:
        logger.error(
            f"Registration verification failed for user {current_user.id}: {e}"
        )
        await log_security_event(
            user_id=current_user.id,
            action="webauthn_registration_failed",
            success=False,
            ip_address=ip_address,
            details={"reason": "Verification failed"},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration verification failed. Please try again.",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in registration for user {current_user.id}: {e}",
            exc_info=True,
        )
        await log_security_event(
            user_id=current_user.id,
            action="webauthn_registration_failed",
            success=False,
            ip_address=ip_address,
            details={"reason": "Internal error"},
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again later.",
        )


@router.post("/authenticate/start", response_model=WebAuthnAuthenticationStartResponse)
async def start_authentication(
    request: WebAuthnAuthenticationStartRequest,
    request_obj: Request,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Start WebAuthn authentication (Step 1)
    Returns challenge for the browser's WebAuthn API
    """
    ip_address = get_client_ip(request_obj)

    # Rate limiting - max 10 attempts per hour
    rate_limit_key = f"webauthn:auth_limit:{ip_address}"
    if not await check_rate_limit(
        redis_client, rate_limit_key, MAX_ATTEMPTS_PER_HOUR, 3600
    ):
        logger.warning(f"Auth rate limit exceeded from {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
        )

    # If username provided, get user credentials
    # SECURITY FIX: Prevent user enumeration by always returning valid-looking response
    user = None
    if request.username:
        user = db.query(User).filter(User.email == request.username).first()

    # Get credentials - but don't reveal if user exists
    if user:
        credentials = (
            db.query(WebAuthnCredential)
            .filter(
                WebAuthnCredential.user_id == user.id,
                WebAuthnCredential.is_active == True,
            )
            .all()
        )
    else:
        # User doesn't exist - return fake challenge to prevent enumeration
        fake_challenge = secrets.token_bytes(32)
        challenge_b64 = base64.urlsafe_b64encode(fake_challenge).decode()

        return WebAuthnAuthenticationStartResponse(
            challenge=challenge_b64.rstrip("="),
            rp_id=RP_ID,
            timeout=60000,
            user_verification="preferred",
            allowed_credentials=[],  # Empty but valid
        )

    if not credentials:
        # User exists but has no credentials - return fake challenge
        fake_challenge = secrets.token_bytes(32)
        challenge_b64 = base64.urlsafe_b64encode(fake_challenge).decode()

        return WebAuthnAuthenticationStartResponse(
            challenge=challenge_b64.rstrip("="),
            rp_id=RP_ID,
            timeout=60000,
            user_verification="preferred",
            allowed_credentials=[],
        )

    # Generate authentication options
    challenge = secrets.token_bytes(32)
    challenge_b64 = base64.urlsafe_b64encode(challenge).decode()

    allowed_credentials = []
    for cred in credentials:
        try:
            allowed_credentials.append(
                {
                    "type": "public-key",
                    "id": cred.credential_id,
                }
            )
        except Exception as e:
            logger.error(f"Failed to process credential {cred.id}: {e}")
            continue

    # Store challenge in Redis with unique ID
    challenge_id = str(uuid.uuid4())
    challenge_data = {
        "challenge": challenge_b64,
        "user_id": user.id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    redis_key = f"webauthn:auth:{challenge_id}"
    redis_client.setex(
        redis_key,
        timedelta(minutes=CHALLENGE_TIMEOUT_MINUTES),
        json.dumps(challenge_data),
    )

    return WebAuthnAuthenticationStartResponse(
        challenge=challenge_b64.rstrip("="),
        rp_id=RP_ID,
        timeout=60000,
        user_verification="preferred",
        allowed_credentials=allowed_credentials,
    )


@router.post(
    "/authenticate/complete", response_model=WebAuthnAuthenticationCompleteResponse
)
async def complete_authentication(
    request: WebAuthnAuthenticationCompleteRequest,
    request_obj: Request,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
):
    """
    Complete WebAuthn authentication (Step 2)
    Verify signature and return JWT tokens with full cryptographic verification
    """
    ip_address = get_client_ip(request_obj)

    try:
        # Decode client data to get challenge
        client_data_bytes = safe_b64decode(request.client_data_json)
        client_data = json.loads(client_data_bytes.decode())
        challenge_b64 = client_data.get("challenge")

        if not challenge_b64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client data",
            )

        # Find challenge in Redis
        pattern = f"webauthn:auth:*"
        keys = redis_client.keys(pattern)

        stored_data = None
        redis_key = None
        for key in keys:
            data = redis_client.get(key)
            if data:
                data_obj = json.loads(data)
                # Match challenge (with flexible padding)
                stored_challenge = data_obj.get("challenge", "").rstrip("=")
                if stored_challenge == challenge_b64.rstrip("="):
                    stored_data = data_obj
                    redis_key = key
                    break

        if not stored_data:
            logger.warning(f"Invalid or expired challenge from {ip_address}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired challenge",
            )

        # Find credential
        credential = (
            db.query(WebAuthnCredential)
            .filter(
                WebAuthnCredential.credential_id == request.credential_id,
                WebAuthnCredential.is_active == True,
            )
            .first()
        )

        if not credential:
            logger.warning(f"Credential not found: {request.credential_id}")
            await log_security_event(
                user_id=stored_data.get("user_id", 0),
                action="webauthn_authentication_failed",
                success=False,
                ip_address=ip_address,
                details={"reason": "Credential not found"},
                db=db,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication failed",
            )

        # SECURITY: Verify credential belongs to the user who requested the challenge
        if stored_data.get("user_id") != credential.user_id:
            logger.error(
                f"User ID mismatch in auth: stored={stored_data.get('user_id')}, credential={credential.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentication failed",
            )

        # Get user
        user = db.query(User).filter(User.id == credential.user_id).first()
        if not user or not user.is_active:
            logger.warning(f"User not found or inactive: {credential.user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication failed",
            )

        # Decode stored public key
        credential_public_key = base64.b64decode(credential.public_key)

        # Prepare credential for verification
        auth_credential = AuthenticationCredential(
            id=request.credential_id,
            raw_id=safe_b64decode(request.credential_id),
            response=AuthenticatorAssertionResponse(
                client_data_json=client_data_bytes,
                authenticator_data=safe_b64decode(request.authenticator_data),
                signature=safe_b64decode(request.signature),
                user_handle=(
                    safe_b64decode(request.user_handle) if request.user_handle else None
                ),
            ),
            type="public-key",
        )

        # CRITICAL: Verify the authentication response cryptographically
        expected_challenge = safe_b64decode(stored_data["challenge"])

        verification = verify_authentication_response(
            credential=auth_credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=credential_public_key,
            credential_current_sign_count=credential.sign_count,
        )

        # SECURITY: Check sign count for replay attack protection
        if (
            verification.new_sign_count <= credential.sign_count
            and verification.new_sign_count != 0
        ):
            logger.error(
                f"Possible replay attack detected for credential {credential.id}: old={credential.sign_count}, new={verification.new_sign_count}"
            )
            await log_security_event(
                user_id=user.id,
                action="webauthn_replay_attack_detected",
                success=False,
                ip_address=ip_address,
                details={
                    "credential_id": credential.id,
                    "old_sign_count": credential.sign_count,
                    "new_sign_count": verification.new_sign_count,
                },
                db=db,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication failed",
            )

        # Update credential metadata
        credential.last_used = datetime.utcnow()
        credential.sign_count = verification.new_sign_count
        db.commit()

        # Generate tokens
        access_token = create_access_token(subject=user.email)
        refresh_token = create_refresh_token(subject=user.email)

        # Clean up challenge
        redis_client.delete(redis_key)

        # Log successful authentication
        await log_security_event(
            user_id=user.id,
            action="webauthn_authentication_success",
            success=True,
            ip_address=ip_address,
            details={"credential_id": credential.id},
            db=db,
        )

        return WebAuthnAuthenticationCompleteResponse(
            success=True,
            message="Authentication successful",
            access_token=access_token,
            refresh_token=refresh_token,
        )

    except InvalidAuthenticationResponse as e:
        logger.error(f"Authentication verification failed from {ip_address}: {e}")
        if "user" in locals():
            await log_security_event(
                user_id=user.id,
                action="webauthn_authentication_failed",
                success=False,
                ip_address=ip_address,
                details={"reason": "Verification failed"},
                db=db,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication failed",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in authentication from {ip_address}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred. Please try again later.",
        )


@router.put("/credentials/{credential_id}/name")
async def update_credential_name(
    credential_id: int,
    request: WebAuthnCredentialUpdateRequest,
    request_obj: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update the friendly name of a biometric credential"""
    credential = (
        db.query(WebAuthnCredential)
        .filter(
            WebAuthnCredential.id == credential_id,
            WebAuthnCredential.user_id == current_user.id,
        )
        .first()
    )

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    # Sanitize input (basic - can use bleach for more thorough sanitization)
    sanitized_name = request.credential_name.strip()[:255]
    credential.credential_name = sanitized_name
    db.commit()

    # Log the update
    ip_address = get_client_ip(request_obj)
    await log_security_event(
        user_id=current_user.id,
        action="webauthn_credential_renamed",
        success=True,
        ip_address=ip_address,
        details={"credential_id": credential_id, "new_name": sanitized_name},
        db=db,
    )

    return WebAuthnCredentialResponse.model_validate(credential)


@router.delete(
    "/credentials/{credential_id}", response_model=WebAuthnCredentialDeleteResponse
)
async def delete_credential(
    credential_id: int,
    request_obj: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a biometric credential"""
    credential = (
        db.query(WebAuthnCredential)
        .filter(
            WebAuthnCredential.id == credential_id,
            WebAuthnCredential.user_id == current_user.id,
        )
        .first()
    )

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    credential_name = credential.credential_name
    db.delete(credential)
    db.commit()

    # Log the deletion
    ip_address = get_client_ip(request_obj)
    await log_security_event(
        user_id=current_user.id,
        action="webauthn_credential_deleted",
        success=True,
        ip_address=ip_address,
        details={"credential_id": credential_id, "credential_name": credential_name},
        db=db,
    )

    return WebAuthnCredentialDeleteResponse(
        success=True,
        message="Biometric credential deleted successfully",
    )


def _detect_device_type(authenticator_type: Optional[str]) -> str:
    """Detect device type from authenticator type"""
    if authenticator_type == "platform":
        return "Platform Authenticator"
    elif authenticator_type == "cross-platform":
        return "Security Key"
    return "Unknown"
