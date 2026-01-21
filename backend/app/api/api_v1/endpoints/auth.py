from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    check_login_rate_limit,
    create_access_token,
    create_refresh_token,
    get_client_ip,
    get_current_active_user,
    get_password_hash,
    refresh_access_token,
    reset_login_attempts,
    revoke_token,
    security,
    verify_password,
    verify_token,
)
from app.db.base import get_db
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse

router = APIRouter()

# Paper trading accounts start with $100,000 virtual cash
PAPER_TRADING_INITIAL_BALANCE = 100000.0


@router.post("/register", response_model=Token)
def register(user_data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        risk_tolerance=user_data.risk_tolerance,
        trading_style=user_data.trading_style,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create default portfolio for the user with paper trading funds
    default_portfolio = Portfolio(
        name="My Portfolio",
        description="Default personal trading portfolio",
        owner_id=new_user.id,
        cash_balance=PAPER_TRADING_INITIAL_BALANCE,
        total_value=PAPER_TRADING_INITIAL_BALANCE,
    )
    db.add(default_portfolio)
    db.commit()

    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": new_user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(new_user),
    }


@router.post("/login", response_model=Token)
def login(
    user_data: UserLogin, request: Request, db: Session = Depends(get_db)
) -> Token:
    """Login user with rate limiting"""
    client_ip = get_client_ip(request)

    # Check rate limiting
    if not check_login_rate_limit(client_ip, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Reset login attempts on successful login
    reset_login_attempts(client_ip, user_data.email)

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user),
    }


@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """OAuth2 compatible token login with rate limiting"""
    client_ip = get_client_ip(request)

    # Check rate limiting
    if not check_login_rate_limit(client_ip, form_data.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Reset login attempts on successful login
    reset_login_attempts(client_ip, form_data.username)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user),
    }


@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token"""
    try:
        new_access_token = refresh_access_token(credentials.credentials)
        return {
            "access_token": new_access_token,
            "refresh_token": credentials.credentials,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Logout user by revoking tokens"""
    try:
        revoke_token(credentials.credentials)
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not logout",
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user information"""
    return UserResponse.from_orm(current_user)


@router.get("/verify")
def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify if a token is valid"""
    try:
        payload = verify_token(credentials.credentials)
        return {"valid": True, "email": payload.get("sub")}
    except HTTPException:
        return {"valid": False}
    except Exception:
        return {"valid": False}
