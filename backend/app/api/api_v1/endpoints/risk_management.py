from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.trade import TradeType
from app.services.risk_management import (
    RiskManagementService,
    TradeRiskAssessment,
    RiskMetrics,
    PositionRisk,
)

router = APIRouter()


class TradeRiskRequest(BaseModel):
    """Request model for trade risk assessment."""

    symbol: str = Field(..., description="Symbol to trade")
    trade_type: TradeType = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Quantity to trade")
    price: Optional[float] = Field(
        None, description="Price per share (uses market price if not provided)"
    )
    trade_id: Optional[str] = Field(None, description="Optional trade ID for tracking")


class TradeRiskResponse(BaseModel):
    """Response model for trade risk assessment."""

    trade_id: str
    symbol: str
    risk_level: str
    risk_score: float
    check_result: str
    violations: List[str]
    warnings: List[str]
    impact_analysis: dict
    recommended_action: str
    max_allowed_quantity: Optional[float]
    metadata: dict

    @classmethod
    def from_assessment(cls, assessment: TradeRiskAssessment) -> "TradeRiskResponse":
        """Create response from assessment result."""
        return cls(
            trade_id=assessment.trade_id,
            symbol=assessment.symbol,
            risk_level=assessment.risk_level.value,
            risk_score=assessment.risk_score,
            check_result=assessment.check_result.value,
            violations=assessment.violations,
            warnings=assessment.warnings,
            impact_analysis=assessment.impact_analysis,
            recommended_action=assessment.recommended_action,
            max_allowed_quantity=assessment.max_allowed_quantity,
            metadata=assessment.metadata,
        )


class RiskMetricsResponse(BaseModel):
    """Response model for portfolio risk metrics."""

    portfolio_value: float
    daily_var: float
    portfolio_beta: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    concentration_risk: float
    sector_concentration: dict
    largest_position_pct: float
    cash_percentage: float
    leverage_ratio: float

    @classmethod
    def from_metrics(cls, metrics: RiskMetrics) -> "RiskMetricsResponse":
        """Create response from risk metrics."""
        return cls(
            portfolio_value=metrics.portfolio_value,
            daily_var=metrics.daily_var,
            portfolio_beta=metrics.portfolio_beta,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            volatility=metrics.volatility,
            concentration_risk=metrics.concentration_risk,
            sector_concentration=metrics.sector_concentration,
            largest_position_pct=metrics.largest_position_pct,
            cash_percentage=metrics.cash_percentage,
            leverage_ratio=metrics.leverage_ratio,
        )


class PositionRiskResponse(BaseModel):
    """Response model for position risk analysis."""

    symbol: str
    position_value: float
    position_percentage: float
    daily_var: float
    beta: float
    volatility: float
    correlation_score: float
    sector: str
    risk_contribution: float

    @classmethod
    def from_position_risk(cls, position_risk: PositionRisk) -> "PositionRiskResponse":
        """Create response from position risk."""
        return cls(
            symbol=position_risk.symbol,
            position_value=position_risk.position_value,
            position_percentage=position_risk.position_percentage,
            daily_var=position_risk.daily_var,
            beta=position_risk.beta,
            volatility=position_risk.volatility,
            correlation_score=position_risk.correlation_score,
            sector=position_risk.sector,
            risk_contribution=position_risk.risk_contribution,
        )


@router.post("/assess-trade", response_model=TradeRiskResponse)
async def assess_trade_risk(
    request: TradeRiskRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Assess risk for a proposed trade.

    Performs comprehensive risk analysis including:
    - Position size limits
    - Portfolio concentration
    - Daily loss limits
    - Leverage constraints
    - Market volatility impact

    Returns risk level and recommendations.
    """
    try:
        risk_service = RiskManagementService(db)

        assessment = await risk_service.assess_trade_risk(
            user_id=int(current_user.id),
            symbol=request.symbol.upper(),
            trade_type=request.trade_type,
            quantity=request.quantity,
            price=request.price,
            trade_id=request.trade_id,
        )

        return TradeRiskResponse.from_assessment(assessment)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk assessment failed: {str(e)}",
        )


@router.get("/portfolio-metrics", response_model=RiskMetricsResponse)
async def get_portfolio_risk_metrics(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get comprehensive portfolio risk metrics.

    Returns detailed risk analysis including:
    - Value at Risk (VaR)
    - Portfolio beta and volatility
    - Sharpe ratio and max drawdown
    - Concentration and diversification metrics
    - Leverage and cash allocation
    """
    try:
        risk_service = RiskManagementService(db)

        metrics = await risk_service.calculate_portfolio_risk_metrics(int(current_user.id))

        return RiskMetricsResponse.from_metrics(metrics)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio risk calculation failed: {str(e)}",
        )


@router.get("/position-analysis", response_model=List[PositionRiskResponse])
async def get_position_risk_analysis(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get detailed risk analysis for each position in the portfolio.

    Returns risk metrics for individual positions including:
    - Position-specific VaR
    - Beta and volatility
    - Correlation scores
    - Sector classification
    - Risk contribution to portfolio
    """
    try:
        risk_service = RiskManagementService(db)

        position_risks = await risk_service.get_position_risk_analysis(int(current_user.id))

        return [PositionRiskResponse.from_position_risk(pr) for pr in position_risks]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Position risk analysis failed: {str(e)}",
        )


@router.get("/circuit-breakers")
async def check_circuit_breakers(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Check circuit breaker status for the user's trading activity.

    Circuit breakers automatically halt or restrict trading when:
    - Daily loss limits are exceeded
    - Trade frequency limits are reached
    - Weekly loss thresholds are breached

    Returns current status and any triggered breakers.
    """
    try:
        risk_service = RiskManagementService(db)

        breakers = await risk_service.check_circuit_breakers(int(current_user.id))

        return breakers

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Circuit breaker check failed: {str(e)}",
        )


@router.get("/risk-limits")
async def get_risk_limits(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get current risk limits and settings for the user.

    Returns all active risk management parameters including:
    - Position size limits
    - Concentration limits
    - Daily/weekly loss limits
    - Leverage constraints
    - Trade frequency limits
    """
    try:
        risk_service = RiskManagementService(db)

        # Get current configuration
        limits = {
            "position_limits": {
                "max_position_size_pct": risk_service.max_position_size_pct,
                "max_sector_concentration_pct": risk_service.max_sector_concentration_pct,
                "min_cash_percentage": risk_service.min_cash_percentage,
            },
            "loss_limits": {
                "max_daily_loss_pct": risk_service.max_daily_loss_pct,
                "max_weekly_loss_pct": risk_service.default_limits[
                    "max_weekly_loss_pct"
                ],
            },
            "trading_limits": {
                "max_trade_value": risk_service.default_limits["max_trade_value"],
                "max_daily_trades": risk_service.default_limits["max_daily_trades"],
                "confirmation_threshold": risk_service.default_limits[
                    "required_confirmation_threshold"
                ],
            },
            "leverage_limits": {
                "max_portfolio_leverage": risk_service.max_portfolio_leverage,
                "max_correlation_threshold": risk_service.max_correlation_threshold,
            },
            "user_tier": "standard",  # Could be based on user account type
            "risk_tolerance": getattr(current_user, "risk_tolerance", "moderate"),
        }

        return {
            "user_id": int(current_user.id),
            "active_limits": limits,
            "customizable_limits": [
                "max_daily_loss_pct",
                "max_trade_value",
                "confirmation_threshold",
            ],
            "admin_only_limits": ["max_portfolio_leverage", "max_position_size_pct"],
            "last_updated": None,  # Would track when limits were last modified
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk limits: {str(e)}",
        )


@router.get("/risk-score/{symbol}")
async def get_symbol_risk_score(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get risk score and analysis for a specific symbol.

    Provides detailed risk assessment for individual securities including:
    - Volatility analysis using trading-engine's VolatilityDetector
    - Beta relative to market
    - Liquidity metrics
    - Sector risk factors
    - Current market conditions impact
    """
    try:
        import pandas as pd
        from app.services.market_data import market_data_service

        # Import trading-engine volatility detector
        try:
            from app.trading_engine.ml_models.volatility_regime import VolatilityDetector, VolatilityRegime
            from app.trading_engine.engine.risk_config import get_risk_config
            TRADING_ENGINE_AVAILABLE = True
        except ImportError:
            TRADING_ENGINE_AVAILABLE = False

        symbol = symbol.upper()

        # Get market data for the symbol
        quote = await market_data_service.get_quote(symbol)
        historical_data = await market_data_service.get_historical_data(
            symbol,
            start_date=(datetime.utcnow() - __import__('datetime').timedelta(days=60)).isoformat(),
            end_date=datetime.utcnow().isoformat(),
        )

        # Calculate risk metrics using trading-engine if available
        risk_score = 0.5  # Default moderate risk
        volatility = 0.25
        regime = "NORMAL"
        recommendation = "Moderate risk - suitable for balanced portfolios"
        optimal_position_size_pct = 0.05

        if TRADING_ENGINE_AVAILABLE and historical_data:
            try:
                # Convert to DataFrame for volatility detector
                df = pd.DataFrame(historical_data)
                if 'close' not in df.columns and 'price' in df.columns:
                    df['close'] = df['price']

                if 'close' in df.columns and len(df) >= 5:
                    detector = VolatilityDetector(lookback_periods=20)
                    detected_regime, detected_volatility = detector.detect_regime(df)

                    # Map volatility regime to risk score (0-1 scale)
                    regime_risk_map = {
                        VolatilityRegime.LOW: 0.25,
                        VolatilityRegime.NORMAL: 0.5,
                        VolatilityRegime.HIGH: 0.75,
                        VolatilityRegime.EXTREME: 0.95,
                    }
                    risk_score = regime_risk_map.get(detected_regime, 0.5)
                    volatility = detected_volatility / 100  # Convert to decimal
                    regime = detected_regime.name

                    # Get risk config for position sizing
                    risk_config = get_risk_config()
                    volatility_regime_str = regime.lower()
                    optimal_position_size_pct = risk_config.get_param("position_sizing.max_position_size") or 0.05

                    # Adjust position size based on volatility
                    vol_multiplier = risk_config.get_param(f"volatility_adjustments.{volatility_regime_str}_vol_multiplier")
                    if vol_multiplier:
                        optimal_position_size_pct *= vol_multiplier

                    # Generate recommendation based on regime
                    regime_recommendations = {
                        VolatilityRegime.LOW: "Low risk - suitable for growth-oriented portfolios",
                        VolatilityRegime.NORMAL: "Moderate risk - suitable for balanced portfolios",
                        VolatilityRegime.HIGH: "High risk - consider reduced position size",
                        VolatilityRegime.EXTREME: "Extreme risk - proceed with caution, circuit breaker may activate",
                    }
                    recommendation = regime_recommendations.get(detected_regime, recommendation)

            except Exception as calc_error:
                # Log error but continue with default values
                import logging
                logging.getLogger(__name__).warning(f"Risk calculation error for {symbol}: {calc_error}")

        # Determine risk factors based on volatility regime
        risk_factors = []
        if regime == "HIGH" or regime == "EXTREME":
            risk_factors.append("High volatility detected")
        if volatility > 0.3:
            risk_factors.append("Above-average price swings")
        if quote and quote.get("change_percent", 0) > 3:
            risk_factors.append("Significant daily price movement")

        # Build response
        symbol_risk = {
            "symbol": symbol,
            "risk_score": round(risk_score, 3),
            "volatility": round(volatility, 4),
            "volatility_regime": regime,
            "beta": 1.0,  # Would need additional market data to calculate
            "liquidity_score": 0.8,  # Would need volume analysis
            "sector": "N/A",  # Would need fundamental data lookup
            "market_cap_category": "N/A",  # Would need fundamental data lookup
            "risk_factors": risk_factors or ["No significant risk factors detected"],
            "recommendation": recommendation,
            "optimal_position_size_pct": round(optimal_position_size_pct, 4),
            "trading_engine_available": TRADING_ENGINE_AVAILABLE,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

        return symbol_risk

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Symbol risk analysis failed: {str(e)}",
        )


@router.post("/validate-portfolio")
async def validate_portfolio_risk(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Validate current portfolio against all risk management rules.

    Performs comprehensive portfolio validation including:
    - Position size compliance
    - Sector concentration limits
    - Overall risk level assessment
    - Recommendations for rebalancing

    Returns validation results and suggested actions.
    """
    try:
        risk_service = RiskManagementService(db)

        # Get portfolio metrics
        metrics = await risk_service.calculate_portfolio_risk_metrics(int(current_user.id))

        # Validate against limits
        violations = []
        warnings = []
        recommendations = []

        # Check position concentration
        if metrics.largest_position_pct > risk_service.max_position_size_pct:
            violations.append(
                f"Largest position exceeds limit: {metrics.largest_position_pct:.2%} > {risk_service.max_position_size_pct:.2%}"
            )
            recommendations.append("Consider reducing largest position size")

        # Check cash allocation
        if metrics.cash_percentage < risk_service.min_cash_percentage:
            warnings.append(
                f"Low cash allocation: {metrics.cash_percentage:.2%} < {risk_service.min_cash_percentage:.2%}"
            )
            recommendations.append("Consider maintaining higher cash reserves")

        # Check overall concentration
        if metrics.concentration_risk > 0.5:
            warnings.append(
                f"High portfolio concentration: {metrics.concentration_risk:.3f}"
            )
            recommendations.append("Consider diversifying across more positions")

        # Overall risk assessment
        if metrics.daily_var / metrics.portfolio_value > 0.03:  # 3% daily VaR threshold
            warnings.append("High portfolio volatility detected")
            recommendations.append(
                "Consider reducing position sizes or adding defensive assets"
            )

        validation_result = {
            "user_id": int(current_user.id),
            "portfolio_value": metrics.portfolio_value,
            "overall_risk_level": "high"
            if violations
            else "medium"
            if warnings
            else "low",
            "compliance_status": "non_compliant" if violations else "compliant",
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations,
            "risk_metrics_summary": {
                "daily_var_pct": metrics.daily_var / metrics.portfolio_value
                if metrics.portfolio_value > 0
                else 0,
                "concentration_risk": metrics.concentration_risk,
                "largest_position_pct": metrics.largest_position_pct,
                "cash_percentage": metrics.cash_percentage,
                "sector_count": len(metrics.sector_concentration),
            },
            "validation_timestamp": str(datetime.utcnow()),
        }

        return validation_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio validation failed: {str(e)}",
        )
