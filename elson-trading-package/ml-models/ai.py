from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from redis.client import Redis
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.db.database import get_db, get_redis
from app.models.trade import Trade, TradeStatus
from app.models.user import User, UserRole
from app.schemas.ai import (
    CreateTradeRequest,
    MarketTimingRequest,
    MarketTimingResponse,
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse,
    RebalanceRequest,
    RebalanceResponse,
    RecommendationResponse,
    ScheduleOptimizationRequest,
    ScheduleOptimizationResponse,
    StrategyInfoResponse,
    TradeResponse,
)
from app.services.advisor import AdvisorService, Recommendation
from app.services.ai_portfolio_manager import (
    AIPortfolioManager,
    MarketTimingSignal,
    PortfolioOptimizationResult,
)
from app.services.market_data import MarketDataService
from app.services.market_data_processor import MarketDataProcessor
from app.services.market_integration import get_market_integration_service
from app.services.neural_network import NeuralNetworkService
from app.services.notifications import NotificationService

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ai", tags=["ai"])


def get_ai_portfolio_manager(
    db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)
) -> AIPortfolioManager:
    """Dependency for getting the AIPortfolioManager service."""
    market_integration = get_market_integration_service(db=db)
    neural_network = NeuralNetworkService()
    return AIPortfolioManager(
        db, market_integration.market_data, neural_network, redis_client
    )


@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get AI-driven investment recommendations for the current user.
    """
    # Initialize advisor service
    advisor_service = AdvisorService(db)

    # Get recommendations - now using async method
    recommendations = await advisor_service.get_recommendations_for_user(
        current_user.id, limit=limit
    )

    # Convert to response format
    recommendation_responses = []
    for rec in recommendations:
        recommendation_responses.append(
            RecommendationResponse(
                symbol=rec.symbol,
                action=rec.action,
                quantity=rec.quantity,
                price=rec.price,
                confidence=rec.confidence,
                strategy=rec.strategy,
                reason=rec.reason,
                timestamp=rec.timestamp,
            )
        )

    # If we have recommendations, send a notification
    if recommendation_responses and len(recommendation_responses) > 0:
        notification_service = NotificationService(db)
        notification_service.send_new_recommendations_notification(
            current_user.id, count=len(recommendation_responses)
        )

    return recommendation_responses


@router.post("/rebalance", response_model=RebalanceResponse)
async def rebalance_portfolio(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Trigger an AI-based portfolio rebalance.
    Generates trades to bring the portfolio in line with target allocations.
    """
    # Initialize advisor service
    advisor_service = AdvisorService(db)

    # Generate rebalance trades
    # Note: rebalance_portfolio is still a synchronous method in AdvisorService
    trades = advisor_service.rebalance_portfolio(current_user.id)

    # Convert to response format
    trade_responses = []
    for trade in trades:
        trade_responses.append(
            TradeResponse(
                id=trade.id,
                symbol=trade.symbol,
                quantity=trade.quantity,
                price=trade.price,
                trade_type=trade.trade_type,
                order_type=trade.order_type.value,
                status=trade.status.value,
                total_amount=trade.total_amount,
                created_at=trade.created_at,
            )
        )

    return RebalanceResponse(
        trades=trade_responses,
        trade_count=len(trade_responses),
        message=f"Generated {len(trade_responses)} trades to rebalance your portfolio.",
    )


@router.post("/recommendations/execute", response_model=TradeResponse)
async def execute_recommendation(
    trade_request: CreateTradeRequest = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a trade from an AI recommendation.
    """
    # Initialize advisor service
    advisor_service = AdvisorService(db)

    # Create a recommendation object from the request
    recommendation = Recommendation(
        symbol=trade_request.symbol,
        action=trade_request.trade_type,
        quantity=trade_request.quantity,
        price=trade_request.price,
        confidence=1.0,  # User-initiated, so high confidence
        strategy="user_initiated",
        reason="User-initiated from recommendation",
    )

    # Create the trade - now using async method
    trade, error = await advisor_service.create_trade_from_recommendation(
        current_user.id, recommendation
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not trade:
        raise HTTPException(status_code=500, detail="Failed to create trade")

    # For minor users, notify the guardian about the trade request
    if (
        current_user.role == UserRole.MINOR
        and trade.status == TradeStatus.PENDING_APPROVAL
    ):
        notification_service = NotificationService(db)
        notification_service.send_trade_request_notification(trade)

    # Return the created trade
    return TradeResponse(
        id=trade.id,
        symbol=trade.symbol,
        quantity=trade.quantity,
        price=trade.price,
        trade_type=trade.trade_type,
        order_type=trade.order_type.value,
        status=trade.status.value,
        total_amount=trade.total_amount,
        created_at=trade.created_at,
    )


@router.get("/strategies", response_model=List[StrategyInfoResponse])
async def get_available_strategies(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get information about available trading strategies.
    """
    # In a real implementation, this would come from a database or configuration
    strategies = [
        StrategyInfoResponse(
            id="combined",
            name="Combined Strategy",
            description="A comprehensive strategy that combines multiple approaches including trend following, momentum, and volatility analysis.",
            risk_level="moderate",
            recommended_for=["Long-term investors", "Balanced portfolios"],
        ),
        StrategyInfoResponse(
            id="moving_average",
            name="Moving Average",
            description="Uses simple and exponential moving averages to identify trends and potential entry/exit points.",
            risk_level="low",
            recommended_for=["Conservative investors", "Retirement accounts"],
        ),
        StrategyInfoResponse(
            id="momentum",
            name="Momentum",
            description="Focuses on stocks showing strong recent performance, based on the principle that trends tend to continue.",
            risk_level="high",
            recommended_for=["Growth-oriented investors", "Bull markets"],
        ),
    ]

    # Filter strategies based on user role (minors only get low-risk strategies)
    if current_user.role == UserRole.MINOR:
        strategies = [s for s in strategies if s.risk_level == "low"]

    return strategies


@router.get("/strategy/active", response_model=StrategyInfoResponse)
async def get_active_strategy(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get information about the user's currently active trading strategy.
    """
    # In a real implementation, you'd look up the user's portfolio and get the strategy
    # For now, just return a default

    # Find the user's portfolio risk profile
    portfolio = (
        db.query("Portfolio").filter("Portfolio.user_id" == current_user.id).first()
    )

    risk_level = "moderate"
    if portfolio:
        risk_level = portfolio.risk_profile

    strategy_map = {
        "conservative": "moving_average",
        "moderate": "combined",
        "aggressive": "momentum",
    }

    strategy_id = strategy_map.get(risk_level, "combined")

    # Map to a strategy info object
    strategy_info = {
        "moving_average": StrategyInfoResponse(
            id="moving_average",
            name="Moving Average",
            description="Uses simple and exponential moving averages to identify trends and potential entry/exit points.",
            risk_level="low",
            recommended_for=["Conservative investors", "Retirement accounts"],
        ),
        "combined": StrategyInfoResponse(
            id="combined",
            name="Combined Strategy",
            description="A comprehensive strategy that combines multiple approaches including trend following, momentum, and volatility analysis.",
            risk_level="moderate",
            recommended_for=["Long-term investors", "Balanced portfolios"],
        ),
        "momentum": StrategyInfoResponse(
            id="momentum",
            name="Momentum",
            description="Focuses on stocks showing strong recent performance, based on the principle that trends tend to continue.",
            risk_level="high",
            recommended_for=["Growth-oriented investors", "Bull markets"],
        ),
    }

    return strategy_info.get(strategy_id, strategy_info["combined"])


# New AI Portfolio Management Endpoints


@router.post("/optimize-portfolio", response_model=PortfolioOptimizationResponse)
async def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    current_user: User = Depends(get_current_active_user),
    ai_manager: AIPortfolioManager = Depends(get_ai_portfolio_manager),
):
    """
    Optimize portfolio allocation using modern portfolio theory and AI
    """
    result = ai_manager.optimize_portfolio(
        user_id=current_user.id,
        method=request.method,
        risk_tolerance=request.risk_tolerance,
        lookback_days=request.lookback_days,
        min_allocation=request.min_allocation,
        max_allocation=request.max_allocation,
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Portfolio optimization failed. Check that you have enough historical data and positions.",
        )

    trade_count = len(result.rebalance_trades) if result.rebalance_trades else 0

    return PortfolioOptimizationResponse(
        target_allocation=result.target_allocation,
        expected_return=result.expected_return,
        expected_risk=result.expected_risk,
        sharpe_ratio=result.sharpe_ratio,
        optimization_method=result.optimization_method,
        confidence_score=result.confidence_score,
        trade_count=trade_count,
        created_at=result.created_at.isoformat(),
    )


@router.post("/market-timing", response_model=MarketTimingResponse)
async def get_market_timing(
    request: MarketTimingRequest,
    current_user: User = Depends(get_current_active_user),
    ai_manager: AIPortfolioManager = Depends(get_ai_portfolio_manager),
):
    """
    Get market timing signal for a specific symbol
    """
    signal = ai_manager.get_market_timing_signal(
        user_id=current_user.id,
        symbol=request.symbol,
        prediction_horizon=request.prediction_horizon,
    )

    if not signal:
        raise HTTPException(
            status_code=400,
            detail="Failed to generate market timing signal. Insufficient data or model error.",
        )

    return MarketTimingResponse(
        symbol=signal.symbol,
        signal_type=signal.signal_type,
        strength=signal.strength,
        time_window=signal.time_window,
        prediction_horizon=signal.prediction_horizon,
        confidence=signal.confidence,
        signals=signal.signals,
        market_conditions=signal.market_conditions,
        created_at=signal.created_at.isoformat(),
    )


@router.post("/rebalance-ai", response_model=RebalanceResponse)
async def rebalance_portfolio_ai(
    request: RebalanceRequest,
    current_user: User = Depends(get_current_active_user),
    ai_manager: AIPortfolioManager = Depends(get_ai_portfolio_manager),
):
    """
    Rebalance portfolio using AI optimization and smart timing
    """
    trades, optimization_result = ai_manager.rebalance_portfolio_ai(
        user_id=current_user.id,
        optimization_method=request.optimization_method,
        risk_tolerance=request.risk_tolerance,
        consider_timing=request.consider_timing,
        max_trades=request.max_trades,
        min_trade_impact=request.min_trade_impact,
    )

    if not trades or not optimization_result:
        return RebalanceResponse(
            success=False,
            message="No rebalancing needed or insufficient data for optimization",
            trade_count=0,
            optimization_details=None,
        )

    return RebalanceResponse(
        success=True,
        message=f"Successfully created {len(trades)} rebalancing trades",
        trade_count=len(trades),
        optimization_details=PortfolioOptimizationResponse(
            target_allocation=optimization_result.target_allocation,
            expected_return=optimization_result.expected_return,
            expected_risk=optimization_result.expected_risk,
            sharpe_ratio=optimization_result.sharpe_ratio,
            optimization_method=optimization_result.optimization_method,
            confidence_score=optimization_result.confidence_score,
            trade_count=len(trades),
            created_at=optimization_result.created_at.isoformat(),
        ),
    )


@router.post("/schedule-optimization", response_model=ScheduleOptimizationResponse)
async def schedule_recurring_optimization(
    request: ScheduleOptimizationRequest,
    current_user: User = Depends(get_current_active_user),
    ai_manager: AIPortfolioManager = Depends(get_ai_portfolio_manager),
):
    """
    Schedule recurring portfolio optimization
    """
    success = ai_manager.schedule_recurring_optimization(
        user_id=current_user.id,
        schedule=request.schedule,
        optimization_method=request.optimization_method,
        auto_execute=request.auto_execute,
    )

    if not success:
        raise HTTPException(
            status_code=400, detail="Failed to schedule recurring optimization"
        )

    return ScheduleOptimizationResponse(
        success=True,
        schedule=request.schedule,
        optimization_method=request.optimization_method,
        auto_execute=request.auto_execute,
        message="Successfully scheduled recurring portfolio optimization",
    )


# New endpoints that use the market integration service


class MarketPredictionRequest(BaseModel):
    """Request model for market prediction."""

    symbol: str
    days_ahead: int = 5


class MarketPredictionResponse(BaseModel):
    """Response model for market prediction."""

    symbol: str
    predicted_price: Optional[float] = None
    confidence: Optional[float] = None
    prediction_date: Optional[str] = None
    generated_at: str
    model_name: str
    error: Optional[str] = None


@router.post("/market-prediction", response_model=MarketPredictionResponse)
async def get_market_prediction(
    request: MarketPredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get market prediction for a symbol using the market integration service.
    """
    # Initialize advisor service
    advisor_service = AdvisorService(db)

    # Get market prediction
    prediction = await advisor_service.get_market_prediction(
        symbol=request.symbol, days_ahead=request.days_ahead
    )

    # Check for error
    if "error" in prediction:
        return MarketPredictionResponse(
            symbol=request.symbol,
            error=prediction["error"],
            generated_at=datetime.now().isoformat(),
            model_name="unknown",
        )

    # Return prediction response
    return MarketPredictionResponse(
        symbol=request.symbol,
        predicted_price=prediction.get("predicted_price"),
        confidence=prediction.get("confidence"),
        prediction_date=prediction.get("prediction_date"),
        generated_at=prediction.get("generated_at"),
        model_name=prediction.get("model_name", "default"),
    )


class UpdatePortfolioPricesResponse(BaseModel):
    """Response model for portfolio price update."""

    success: bool
    updated_count: int
    message: str


@router.post("/update-portfolio-prices", response_model=UpdatePortfolioPricesResponse)
async def update_portfolio_prices(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Update current market prices for all positions in the user's portfolio.
    """
    # Initialize advisor service
    advisor_service = AdvisorService(db)

    # Update portfolio prices
    success = await advisor_service.update_portfolio_prices(current_user.id)

    if not success:
        return UpdatePortfolioPricesResponse(
            success=False, updated_count=0, message="Failed to update portfolio prices"
        )

    return UpdatePortfolioPricesResponse(
        success=True,
        updated_count=1,  # This would ideally be the actual count from the service
        message="Successfully updated portfolio prices",
    )
