"""
Advanced Trading API Endpoints

Provides sophisticated trading functionality with AI/ML integration,
quantum-inspired models, and comprehensive risk management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user as get_current_user
from app.db.base import get_db
from app.models.portfolio import Portfolio
from app.models.user import User

# Note: Schema imports removed as they are not used in current implementation
from app.services.advanced_trading import AdvancedTradingService
from app.services.market_data import MarketDataService
from app.trading_engine.engine.circuit_breaker import (
    CircuitBreakerType,
    get_circuit_breaker,
)
from app.trading_engine.engine.risk_config import RiskProfile, get_risk_config

router = APIRouter()


# Request/Response Models
class InitializeStrategyRequest(BaseModel):
    symbols: List[str]
    risk_profile: str = "moderate"
    enable_ai_models: bool = True


class TradingSignalsRequest(BaseModel):
    portfolio_id: int
    symbols: Optional[List[str]] = None


class ExecuteTradesRequest(BaseModel):
    portfolio_id: int
    auto_execute: bool = False


class PositionMonitoringResponse(BaseModel):
    total_positions: int
    total_value: float
    unrealized_pnl: float
    risk_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class PerformanceSummaryResponse(BaseModel):
    performance_metrics: Dict[str, Any]
    active_strategies: int
    trained_ai_models: int
    risk_profile: str
    circuit_breaker_status: Dict[str, Any]


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_advanced_trading(
    request: InitializeStrategyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initialize advanced trading system with strategies and AI models
    """
    try:
        # Validate risk profile
        try:
            risk_profile = RiskProfile(request.risk_profile.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid risk profile: {request.risk_profile}. "
                    f"Must be one of: conservative, moderate, aggressive"
                ),
            )

        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service, risk_profile=risk_profile
        )

        # Initialize strategies
        await trading_service.initialize_strategies(request.symbols)

        # Initialize AI models if requested
        if request.enable_ai_models:
            background_tasks.add_task(
                trading_service.initialize_ai_models, request.symbols
            )

        return {
            "status": "success",
            "message": f"Initialized trading system for {len(request.symbols)} symbols",
            "symbols": request.symbols,
            "risk_profile": risk_profile.value,
            "ai_models_enabled": request.enable_ai_models,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error initializing trading system: {str(e)}"
        )


@router.post("/signals", response_model=List[Dict[str, Any]])
async def generate_trading_signals(
    request: TradingSignalsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate trading signals for the specified portfolio
    """
    try:
        # Get portfolio
        portfolio = (
            db.query(Portfolio)
            .filter(
                Portfolio.id == request.portfolio_id,
                Portfolio.owner_id == current_user.id,
            )
            .first()
        )

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service
        )

        # Initialize strategies for requested symbols or all holdings
        symbols = request.symbols
        if not symbols:
            # Get symbols from portfolio holdings
            symbols = [holding.symbol for holding in portfolio.holdings]

        if not symbols:
            return []

        await trading_service.initialize_strategies(symbols)
        await trading_service.initialize_ai_models(symbols)

        # Generate signals
        signals = await trading_service.generate_trading_signals(portfolio)

        return signals

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating trading signals: {str(e)}"
        )


@router.post("/execute", response_model=Dict[str, Any])
async def execute_trades(
    request: ExecuteTradesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute trades based on generated signals
    """
    try:
        # Get portfolio
        portfolio = (
            db.query(Portfolio)
            .filter(
                Portfolio.id == request.portfolio_id,
                Portfolio.owner_id == current_user.id,
            )
            .first()
        )

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service
        )

        # Get holdings symbols
        symbols = [holding.symbol for holding in portfolio.holdings]
        if not symbols:
            return {
                "status": "success",
                "message": "No holdings to trade",
                "executed_trades": [],
            }

        await trading_service.initialize_strategies(symbols)
        await trading_service.initialize_ai_models(symbols)

        # Generate signals
        signals = await trading_service.generate_trading_signals(portfolio)

        if not signals:
            return {
                "status": "success",
                "message": "No trading signals generated",
                "executed_trades": [],
            }

        executed_trades = []
        if request.auto_execute:
            # Execute trades automatically
            executed_trades = await trading_service.execute_trades(signals, portfolio)

            # Commit trades to database
            for trade in executed_trades:
                db.add(trade)
            db.commit()

        return {
            "status": "success",
            "message": f"Generated {len(signals)} signals, executed {len(executed_trades)} trades",
            "signals": signals,
            "executed_trades": [
                {
                    "id": str(trade.id),
                    "symbol": trade.symbol,
                    "side": trade.side.value,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "status": trade.status.value,
                }
                for trade in executed_trades
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing trades: {str(e)}")


@router.get("/monitor/{portfolio_id}", response_model=PositionMonitoringResponse)
async def monitor_positions(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Monitor portfolio positions and risk metrics
    """
    try:
        # Get portfolio
        portfolio = (
            db.query(Portfolio)
            .filter(Portfolio.id == portfolio_id, Portfolio.owner_id == current_user.id)
            .first()
        )

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service
        )

        # Monitor positions
        monitoring_data = await trading_service.monitor_positions(portfolio)

        return PositionMonitoringResponse(**monitoring_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error monitoring positions: {str(e)}"
        )


@router.get("/performance", response_model=PerformanceSummaryResponse)
async def get_performance_summary(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get trading performance summary
    """
    try:
        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service
        )

        # Get performance summary
        performance_data = trading_service.get_performance_summary()

        return PerformanceSummaryResponse(**performance_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting performance summary: {str(e)}"
        )


@router.post("/risk-profile", response_model=Dict[str, Any])
async def update_risk_profile(
    risk_profile: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update risk profile for trading
    """
    try:
        # Validate risk profile
        try:
            new_profile = RiskProfile(risk_profile.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid risk profile: {risk_profile}. Must be one of: conservative, moderate, aggressive",
            )

        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service, risk_profile=new_profile
        )

        # Update risk profile
        success = await trading_service.update_risk_profile(new_profile)

        if success:
            # Get updated risk configuration
            risk_config = get_risk_config(new_profile)
            profile_summary = risk_config.get_profile_summary()

            return {
                "status": "success",
                "message": f"Risk profile updated to {new_profile.value}",
                "risk_profile": new_profile.value,
                "configuration": profile_summary,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update risk profile")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating risk profile: {str(e)}"
        )


@router.get("/circuit-breakers", response_model=Dict[str, Any])
async def get_circuit_breaker_status(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get current circuit breaker status
    """
    try:
        circuit_breaker = get_circuit_breaker()
        status = circuit_breaker.get_status()

        # Check if trading is allowed
        trading_allowed, breaker_status = circuit_breaker.check()

        return {
            "trading_allowed": trading_allowed,
            "breaker_status": breaker_status.value,
            "active_breakers": status,
            "position_sizing_multiplier": circuit_breaker.get_position_sizing(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting circuit breaker status: {str(e)}"
        )


@router.post("/circuit-breakers/reset", response_model=Dict[str, Any])
async def reset_circuit_breaker(
    breaker_type: str,
    scope: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset a specific circuit breaker
    """
    try:
        # Validate breaker type
        try:
            breaker_type_enum = CircuitBreakerType(breaker_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid circuit breaker type: {breaker_type}"
            )

        circuit_breaker = get_circuit_breaker()
        success = circuit_breaker.reset(breaker_type_enum, scope)

        if success:
            return {
                "status": "success",
                "message": f"Circuit breaker {breaker_type} reset successfully",
                "breaker_type": breaker_type,
                "scope": scope,
            }
        else:
            return {
                "status": "warning",
                "message": f"No active circuit breaker found for {breaker_type}",
                "breaker_type": breaker_type,
                "scope": scope,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error resetting circuit breaker: {str(e)}"
        )


@router.get("/ai-models/status", response_model=Dict[str, Any])
async def get_ai_models_status(
    symbols: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get status of AI models for trading
    """
    try:
        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service
        )

        # If symbols provided, initialize models for those symbols
        if symbols:
            await trading_service.initialize_ai_models(symbols)

        # Get model status
        model_status = {}
        for symbol, models in trading_service.ai_models.items():
            quantum_model = models["quantum_classifier"]
            model_status[symbol] = {
                "is_trained": models["is_trained"],
                "last_prediction": models["last_prediction"],
                "prediction_confidence": models["prediction_confidence"],
                "training_summary": quantum_model.get_training_summary()
                if models["is_trained"]
                else None,
            }

        return {
            "status": "success",
            "total_models": len(model_status),
            "trained_models": sum(
                1 for status in model_status.values() if status["is_trained"]
            ),
            "models": model_status,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting AI model status: {str(e)}"
        )


@router.post("/ai-models/retrain", response_model=Dict[str, Any])
async def retrain_ai_models(
    symbols: List[str],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrain AI models for specified symbols
    """
    try:
        # Initialize services
        market_data_service = MarketDataService()
        trading_service = AdvancedTradingService(
            db=db, market_data_service=market_data_service
        )

        # Add retraining task to background
        background_tasks.add_task(trading_service.initialize_ai_models, symbols)

        return {
            "status": "success",
            "message": f"AI model retraining started for {len(symbols)} symbols",
            "symbols": symbols,
            "note": "Retraining is running in the background and may take several minutes",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting AI model retraining: {str(e)}"
        )
