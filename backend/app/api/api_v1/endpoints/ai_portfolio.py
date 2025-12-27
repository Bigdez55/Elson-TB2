from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.services.ai_portfolio_manager import (
    AIPortfolioManager,
    OptimizationMethod,
    PortfolioOptimizationResult,
    MarketTimingResult,
)

router = APIRouter()


class OptimizationRequest(BaseModel):
    """Request model for portfolio optimization."""

    method: OptimizationMethod = OptimizationMethod.EFFICIENT_FRONTIER
    risk_tolerance: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Risk tolerance (0.0 = conservative, 1.0 = aggressive)",
    )
    symbols: Optional[List[str]] = Field(
        None, description="Optional list of symbols to include"
    )


class OptimizationResponse(BaseModel):
    """Response model for portfolio optimization."""

    user_id: int
    method: str
    target_allocation: dict
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    trade_recommendations: List[dict]
    confidence_score: float
    optimization_timestamp: datetime
    metadata: dict

    @classmethod
    def from_result(cls, result: PortfolioOptimizationResult) -> "OptimizationResponse":
        """Create response from optimization result."""
        return cls(
            user_id=result.user_id,
            method=result.method.value,
            target_allocation=result.target_allocation,
            expected_return=result.expected_return,
            expected_risk=result.expected_risk,
            sharpe_ratio=result.sharpe_ratio,
            trade_recommendations=result.trade_recommendations,
            confidence_score=result.confidence_score,
            optimization_timestamp=result.optimization_timestamp,
            metadata=result.metadata,
        )


class MarketTimingResponse(BaseModel):
    """Response model for market timing signals."""

    symbol: str
    signal: str
    confidence: float
    recommendation: str
    technical_indicators: dict
    ml_prediction: float
    optimal_time_window_start: datetime
    optimal_time_window_end: datetime
    metadata: dict

    @classmethod
    def from_result(cls, result: MarketTimingResult) -> "MarketTimingResponse":
        """Create response from timing result."""
        return cls(
            symbol=result.symbol,
            signal=result.signal.value,
            confidence=result.confidence,
            recommendation=result.recommendation,
            technical_indicators=result.technical_indicators,
            ml_prediction=result.ml_prediction,
            optimal_time_window_start=result.optimal_time_window[0],
            optimal_time_window_end=result.optimal_time_window[1],
            metadata=result.metadata,
        )


class RebalanceRequest(BaseModel):
    """Request model for AI rebalancing."""

    optimization_method: OptimizationMethod = OptimizationMethod.EFFICIENT_FRONTIER
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0)
    dry_run: bool = Field(
        True, description="If true, only simulate trades without executing"
    )


class RebalanceResponse(BaseModel):
    """Response model for AI rebalancing."""

    user_id: int
    trade_ids: List[str]
    dry_run: bool
    optimization_used: OptimizationResponse
    message: str


class ScheduleRequest(BaseModel):
    """Request model for scheduling portfolio optimization."""

    method: OptimizationMethod = OptimizationMethod.EFFICIENT_FRONTIER
    frequency_days: int = Field(
        7, ge=1, le=365, description="Frequency in days for automatic rebalancing"
    )


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_portfolio(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Optimize portfolio using AI algorithms.

    Supports multiple optimization methods:
    - efficient_frontier: Modern Portfolio Theory
    - black_litterman: Black-Litterman with ML views
    - risk_parity: Equal risk contribution
    - ml_enhanced: ML-enhanced optimization
    """
    try:
        ai_manager = AIPortfolioManager(db)

        result = await ai_manager.optimize_portfolio(
            user_id=int(current_user.id),
            method=request.method,
            risk_tolerance=request.risk_tolerance,
            symbols=request.symbols,
        )

        return OptimizationResponse.from_result(result)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio optimization failed: {str(e)}",
        )


@router.get("/optimization-result", response_model=Optional[OptimizationResponse])
async def get_latest_optimization_result(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get the latest optimization result for the current user.

    Returns cached result if available, otherwise returns None.
    """
    try:
        # Try to get cached result - this would require implementing cache retrieval
        # For now, we'll return None and suggest running a new optimization

        return None

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve optimization result: {str(e)}",
        )


@router.get("/market-timing/{symbol}", response_model=MarketTimingResponse)
async def get_market_timing_signal(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get market timing signal for a specific symbol.

    Combines technical analysis with ML predictions to provide
    optimal entry/exit timing recommendations.
    """
    try:
        ai_manager = AIPortfolioManager(db)

        result = await ai_manager.get_market_timing_signal(symbol.upper())

        return MarketTimingResponse.from_result(result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market timing signal: {str(e)}",
        )


@router.post("/rebalance", response_model=RebalanceResponse)
async def execute_ai_rebalance(
    request: RebalanceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Execute AI-driven portfolio rebalancing.

    First optimizes the portfolio, then executes trades to achieve
    the target allocation. Can be run in dry-run mode for testing.
    """
    try:
        ai_manager = AIPortfolioManager(db)

        # First optimize the portfolio
        optimization_result = await ai_manager.optimize_portfolio(
            user_id=int(current_user.id),
            method=request.optimization_method,
            risk_tolerance=request.risk_tolerance,
        )

        # Execute rebalancing
        trade_ids = await ai_manager.execute_ai_rebalance(
            user_id=int(current_user.id),
            optimization_result=optimization_result,
            dry_run=request.dry_run,
        )

        message = f"{'Simulated' if request.dry_run else 'Executed'} {len(trade_ids)} rebalancing trades"

        return RebalanceResponse(
            user_id=int(current_user.id),
            trade_ids=trade_ids,
            dry_run=request.dry_run,
            optimization_used=OptimizationResponse.from_result(optimization_result),
            message=message,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI rebalancing failed: {str(e)}",
        )


@router.post("/schedule-optimization")
async def schedule_portfolio_optimization(
    request: ScheduleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Schedule automatic portfolio optimization.

    Sets up recurring optimization based on the specified frequency.
    This would typically integrate with a task queue system.
    """
    try:
        ai_manager = AIPortfolioManager(db)

        success = await ai_manager.schedule_portfolio_optimization(
            user_id=int(current_user.id),
            method=request.method,
            frequency_days=request.frequency_days,
        )

        if success:
            return {
                "message": f"Portfolio optimization scheduled every {request.frequency_days} days using {request.method.value}",
                "user_id": int(current_user.id),
                "method": request.method.value,
                "frequency_days": request.frequency_days,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to schedule portfolio optimization",
            )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scheduling failed: {str(e)}",
        )


@router.get("/methods")
async def get_optimization_methods(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get available portfolio optimization methods.

    Returns information about each optimization method including
    descriptions and recommended use cases.
    """
    methods = {
        "efficient_frontier": {
            "name": "Efficient Frontier",
            "description": "Modern Portfolio Theory optimization maximizing risk-adjusted returns",
            "best_for": "Balanced portfolios with clear risk preferences",
            "complexity": "Medium",
            "requires_ml": False,
        },
        "black_litterman": {
            "name": "Black-Litterman",
            "description": "Enhanced portfolio optimization incorporating ML predictions as market views",
            "best_for": "Sophisticated investors who want to incorporate market predictions",
            "complexity": "High",
            "requires_ml": True,
        },
        "risk_parity": {
            "name": "Risk Parity",
            "description": "Equal risk contribution from each asset for maximum diversification",
            "best_for": "Conservative investors seeking balanced risk exposure",
            "complexity": "Low",
            "requires_ml": False,
        },
        "ml_enhanced": {
            "name": "ML-Enhanced",
            "description": "Combines multiple optimization approaches with machine learning insights",
            "best_for": "Advanced portfolios leveraging AI for optimal allocation",
            "complexity": "Very High",
            "requires_ml": True,
        },
    }

    return {
        "available_methods": list(methods.keys()),
        "method_details": methods,
        "default_method": OptimizationMethod.EFFICIENT_FRONTIER.value,
        "user_permissions": {
            "can_use_ml_methods": True,  # Could be based on user subscription level
            "max_symbols": 50,  # Could be based on user tier
            "optimization_frequency_limit": "daily",
        },
    }


@router.get("/portfolio-analysis")
async def get_portfolio_analysis(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get comprehensive portfolio analysis including risk metrics,
    diversification analysis, and AI-powered insights.
    """
    try:
        # This would be a comprehensive analysis method
        # For now, return a placeholder structure

        analysis = {
            "user_id": int(current_user.id),
            "analysis_timestamp": datetime.utcnow(),
            "portfolio_summary": {
                "total_value": 0.0,
                "total_return": 0.0,
                "total_return_percentage": 0.0,
                "risk_score": 0.0,
                "diversification_score": 0.0,
            },
            "asset_allocation": {
                "by_sector": {},
                "by_asset_class": {},
                "geographic_distribution": {},
            },
            "risk_metrics": {
                "portfolio_beta": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "volatility": 0.0,
            },
            "ai_insights": {
                "risk_assessment": "Portfolio analysis requires implementation",
                "rebalancing_suggestions": [],
                "market_outlook": "Analysis pending",
                "optimization_opportunities": [],
            },
            "benchmarks": {"sp500_comparison": 0.0, "risk_adjusted_performance": 0.0},
        }

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio analysis failed: {str(e)}",
        )
