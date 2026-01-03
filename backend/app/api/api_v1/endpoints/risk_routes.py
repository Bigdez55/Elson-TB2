import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_current_admin_user
from app.db.base import get_db
from app.models.portfolio import Portfolio
from app.models.holding import Position
from app.models.user import User
from app.services.risk_management import RiskManagementService, RiskMetrics

# Compatibility aliases
get_current_user = get_current_active_user
get_current_superuser = get_current_admin_user
RiskManager = RiskManagementService


class UserRiskProfile:
    """User risk profile placeholder."""
    def __init__(self, level: str = "moderate"):
        self.level = level


def calculate_portfolio_risk_metrics(portfolio, db):
    """Calculate portfolio risk metrics - placeholder."""
    return {
        "volatility": 0.15,
        "beta": 1.0,
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.1,
    }


def get_risk_profile_report(user_id: int, db):
    """Get risk profile report - placeholder."""
    return {
        "user_id": user_id,
        "risk_level": "moderate",
        "risk_score": 50,
        "recommendations": [],
    }

# Import real implementations from trading-engine
try:
    from app.trading_engine.engine.circuit_breaker import (
        CircuitBreaker,
        CircuitBreakerType,
        CircuitBreakerStatus,
        get_circuit_breaker,
    )
    from app.trading_engine.engine.risk_config import (
        RiskProfile,
        RiskConfig,
        get_risk_config,
    )
    TRADING_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Trading engine not available: {e}")
    TRADING_ENGINE_AVAILABLE = False
    # Define fallback types for when trading-engine is not installed
    from enum import Enum
    class RiskProfile(str, Enum):
        CONSERVATIVE = "conservative"
        MODERATE = "moderate"
        AGGRESSIVE = "aggressive"
    class CircuitBreakerType(str, Enum):
        SYSTEM = "system"
        VOLATILITY = "volatility"
        DAILY_LOSS = "daily_loss"
    CircuitBreaker = None
    RiskConfig = None
    get_circuit_breaker = None
    get_risk_config = None

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/profiles")
async def get_risk_profiles(
    current_user: User = Depends(get_current_superuser),
) -> Dict:
    """Get all available risk profiles and their parameters"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        risk_config = get_risk_config()

        profiles = {}
        for profile in RiskProfile:
            # Get profile parameters from config
            profile_params = risk_config.config.get(profile.value, {})
            profiles[profile.value] = profile_params

        return {"profiles": profiles, "current_profile": risk_config.profile.value}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving risk profiles",
        )


@router.get("/profile/{profile}")
async def get_risk_profile(
    profile: str, current_user: User = Depends(get_current_superuser)
) -> Dict:
    """Get a specific risk profile and its parameters"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        risk_config = get_risk_config()

        # Validate profile
        try:
            profile_enum = RiskProfile(profile)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk profile: {profile}",
            )

        # Get profile parameters from config
        profile_params = risk_config.config.get(profile_enum.value, {})

        return {
            "profile": profile,
            "parameters": profile_params,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk profile {profile}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving risk profile {profile}",
        )


@router.post("/profile/{profile}/update")
async def update_risk_profile(
    profile: str,
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_superuser),
) -> Dict:
    """Update parameters for a risk profile"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        risk_config = get_risk_config()

        # Validate profile
        try:
            profile_enum = RiskProfile(profile)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk profile: {profile}",
            )

        # Temporarily switch to the target profile to update it
        original_profile = risk_config.profile
        risk_config.update_profile(profile_enum)

        # Update parameters using the trading-engine set_param API
        updated_params = []
        for param_path, value in parameters.items():
            if risk_config.set_param(param_path, value):
                updated_params.append(param_path)
                logger.info(f"Updated {param_path} by {current_user.email}")

        # Get updated profile params
        updated_profile = risk_config.config.get(profile_enum.value, {})

        # Restore original profile if different
        if original_profile != profile_enum:
            risk_config.update_profile(original_profile)

        return {
            "profile": profile,
            "updated_parameters": updated_params,
            "updated_profile": updated_profile,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk profile {profile}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating risk profile {profile}",
        )


@router.post("/profile/active")
async def set_active_profile(
    profile: str, current_user: User = Depends(get_current_superuser)
) -> Dict:
    """Set the active risk profile"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        risk_config = get_risk_config()

        # Validate profile
        try:
            profile_enum = RiskProfile(profile)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk profile: {profile}",
            )

        # Set active profile using trading-engine API
        risk_config.update_profile(profile_enum)

        # Get profile parameters
        profile_params = risk_config.config.get(profile_enum.value, {})

        return {
            "active_profile": profile,
            "parameters": profile_params,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active risk profile {profile}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting active risk profile {profile}",
        )


@router.get("/circuit-breakers")
async def get_circuit_breakers(current_user: User = Depends(get_current_user)) -> Dict:
    """Get all active circuit breakers"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        circuit_breaker = get_circuit_breaker()

        # Get all circuit breakers
        breakers = circuit_breaker.get_status()

        return {"breakers": breakers, "count": len(breakers)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting circuit breakers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving circuit breakers",
        )


@router.post("/circuit-breakers/trip")
async def trip_circuit_breaker(
    breaker_type: str,
    reason: str,
    scope: Optional[str] = None,
    reset_after: Optional[int] = None,
    current_user: User = Depends(get_current_superuser),
) -> Dict:
    """Manually trip a circuit breaker"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        circuit_breaker = get_circuit_breaker()

        # Validate breaker type
        try:
            breaker_type_enum = CircuitBreakerType(breaker_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid circuit breaker type: {breaker_type}",
            )

        # Trip the circuit breaker
        circuit_breaker.trip(breaker_type_enum, reason, scope, reset_after)

        return {
            "status": "success",
            "breaker_type": breaker_type,
            "scope": scope,
            "reason": reason,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tripping circuit breaker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error tripping circuit breaker",
        )


@router.post("/circuit-breakers/reset")
async def reset_circuit_breaker(
    breaker_type: str,
    scope: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
) -> Dict:
    """Reset a circuit breaker"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        circuit_breaker = get_circuit_breaker()

        # Validate breaker type
        try:
            breaker_type_enum = CircuitBreakerType(breaker_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid circuit breaker type: {breaker_type}",
            )

        # Reset the circuit breaker
        reset = circuit_breaker.reset(breaker_type_enum, scope)

        return {
            "status": "success" if reset else "not_found",
            "breaker_type": breaker_type,
            "scope": scope,
            "reset": reset,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting circuit breaker",
        )


@router.post("/circuit-breakers/reset-all")
async def reset_all_circuit_breakers(
    current_user: User = Depends(get_current_superuser),
) -> Dict:
    """Reset all circuit breakers"""
    try:
        if not TRADING_ENGINE_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Trading engine not available",
            )

        circuit_breaker = get_circuit_breaker()

        # Reset all circuit breakers
        circuit_breaker.reset_all()

        return {"status": "success", "message": "All circuit breakers reset"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting all circuit breakers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting all circuit breakers",
        )


@router.get("/user-profile")
async def get_user_risk_profile(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict:
    """Get the user's risk profile based on age and account type"""
    try:
        # Create risk manager with DB session
        risk_manager = RiskManager(db)

        # Get the user's risk profile
        risk_profile = risk_manager.get_user_risk_profile(current_user)

        # Get parameters for this profile from the risk manager
        profile_params = {}
        if risk_profile:
            for category in [
                "position_sizing",
                "volatility_limits",
                "drawdown_limits",
                "trade_limitations",
                "correlation_limits",
                "exposure_limits",
            ]:
                profile_params[category] = {}
                if category == "position_sizing":
                    profile_params[category][
                        "max_position_size"
                    ] = risk_manager.get_profile_param(
                        current_user, f"{category}.max_position_size"
                    )
                    profile_params[category][
                        "max_sector_exposure"
                    ] = risk_manager.get_profile_param(
                        current_user, f"{category}.max_sector_exposure"
                    )
                    profile_params[category][
                        "base_quantity_percent"
                    ] = risk_manager.get_profile_param(
                        current_user, f"{category}.base_quantity_percent"
                    )
                elif category == "trade_limitations":
                    profile_params[category][
                        "max_trades_per_day"
                    ] = risk_manager.get_profile_param(
                        current_user, f"{category}.max_trades_per_day"
                    )
                    profile_params[category][
                        "min_holding_period_days"
                    ] = risk_manager.get_profile_param(
                        current_user, f"{category}.min_holding_period_days"
                    )
                    profile_params[category][
                        "restricted_assets"
                    ] = risk_manager.get_profile_param(
                        current_user, f"{category}.restricted_assets"
                    )

        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value,
            "risk_profile": risk_profile.value,
            "profile_parameters": profile_params,
            "educational_mode": True if current_user.role == "minor" else False,
        }
    except Exception as e:
        logger.error(f"Error getting user risk profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user risk profile",
        )


@router.get("/portfolio-assessment")
async def get_portfolio_risk_assessment(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict:
    """Get a comprehensive risk assessment of the user's portfolio"""
    try:
        # Get portfolio for the current user
        portfolio = (
            db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        # Create risk manager
        risk_manager = RiskManager(db)

        # Get full portfolio risk report
        risk_report = get_risk_profile_report(current_user, portfolio, risk_manager)

        return risk_report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio risk assessment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving portfolio risk assessment",
        )


@router.get("/dashboard")
async def get_risk_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict:
    """Get risk dashboard data"""
    try:
        # Get portfolio for the current user
        portfolio = (
            db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        # Create risk manager
        risk_manager = RiskManager(db)

        # Calculate risk metrics
        risk_metrics = calculate_portfolio_risk_metrics(portfolio)

        # Get user's risk profile
        user_risk_profile = risk_manager.get_user_risk_profile(current_user)
        user_profile_params = {}
        categories = [
            "position_sizing",
            "volatility_limits",
            "drawdown_limits",
            "trade_limitations",
            "correlation_limits",
            "exposure_limits",
        ]
        for category in categories:
            user_profile_params[category] = {}
            # Only fetching key parameters to avoid excessive nesting
            if category == "position_sizing":
                user_profile_params[category][
                    "max_position_size"
                ] = risk_manager.get_profile_param(
                    current_user, f"{category}.max_position_size"
                )
            elif category == "volatility_limits":
                user_profile_params[category][
                    "max_portfolio_volatility"
                ] = risk_manager.get_profile_param(
                    current_user, f"{category}.max_portfolio_volatility"
                )
            elif category == "drawdown_limits":
                user_profile_params[category][
                    "max_total_drawdown"
                ] = risk_manager.get_profile_param(
                    current_user, f"{category}.max_total_drawdown"
                )

        # Get circuit breakers (if trading engine available)
        breakers = {}
        trading_engine_profile_name = "moderate"
        if TRADING_ENGINE_AVAILABLE and get_circuit_breaker:
            circuit_breaker = get_circuit_breaker()
            breakers = circuit_breaker.get_status()
        if TRADING_ENGINE_AVAILABLE and get_risk_config:
            trading_engine_profile_name = get_risk_config().profile.value

        # Build dashboard data
        dashboard = {
            "portfolio": {
                "id": portfolio.id,
                "total_value": float(portfolio.total_value),
                "cash_balance": float(portfolio.cash_balance),
                "last_updated": portfolio.updated_at.isoformat(),
            },
            "risk_metrics": risk_metrics,
            "user_risk_profile": {
                "name": user_risk_profile.value,
                "parameters": user_profile_params,
            },
            "trading_engine_profile": {"name": trading_engine_profile_name},
            "circuit_breakers": {"active": len(breakers) > 0, "breakers": breakers},
            "positions": [],
        }

        # Add positions
        for position in portfolio.positions_detail:
            position_data = {
                "symbol": position.symbol,
                "quantity": float(position.quantity),
                "current_price": float(position.current_price),
                "value": float(position.quantity * position.current_price),
                "weight": float(
                    position.quantity * position.current_price / portfolio.total_value
                )
                if portfolio.total_value
                else 0,
                "unrealized_pl": float(position.unrealized_pl),
            }
            dashboard["positions"].append(position_data)

        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving risk dashboard",
        )


@router.get("/audit-log")
async def get_risk_audit_log(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, gt=0, le=1000),
    current_user: User = Depends(get_current_superuser),
) -> Dict:
    """Get risk parameter audit log"""
    try:
        # Default to last 7 days if no dates provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # Define audit log file path
        audit_log_file = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..", "logs", "risk_audit.log"
        )

        # Read from audit log file
        audit_log = []
        if os.path.exists(audit_log_file):
            with open(audit_log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_date = datetime.fromisoformat(entry["timestamp"])

                        if start_date <= entry_date <= end_date:
                            audit_log.append(entry)

                        if len(audit_log) >= limit:
                            break
                    except Exception as e:
                        logger.debug(f"Skipping non-JSON audit log entry: {str(e)}")

        return {
            "audit_log": audit_log,
            "count": len(audit_log),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Error getting risk audit log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving risk audit log",
        )
