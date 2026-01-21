"""
Auto Trading API Endpoints

Provides REST API for managing automated trading strategies.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.auto_trading_service import AutoTradingService
from app.trading_engine.strategies.registry import StrategyCategory, StrategyRegistry

router = APIRouter()


# Request/Response Models
class StartAutoTradingRequest(BaseModel):
    """Request to start automated trading"""

    portfolio_id: int = Field(..., description="Portfolio ID to trade")
    strategy_names: List[str] = Field(..., description="Strategies to enable")
    symbols: List[str] = Field(..., description="Symbols to trade")
    parameters: Optional[Dict[str, Dict]] = Field(
        None, description="Optional parameters for each strategy"
    )


class AutoTradingStatusResponse(BaseModel):
    """Auto trading status"""

    is_active: bool
    active_strategies: Dict[str, Dict]
    portfolio_id: Optional[int] = None


class AddStrategyRequest(BaseModel):
    """Request to add a strategy"""

    strategy_name: str
    symbol: str
    parameters: Optional[Dict] = None


class AvailableStrategy(BaseModel):
    """Available strategy information"""

    name: str
    category: str
    description: str
    risk_level: str
    default_parameters: Dict
    timeframes: List[str]


@router.post("/start", response_model=Dict[str, str])
async def start_auto_trading(
    request: StartAutoTradingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Start automated trading with specified strategies.

    Enables continuous strategy execution and automatic trade placement
    based on generated signals.
    """
    try:
        # Verify portfolio ownership
        portfolio = (
            db.query(Portfolio)
            .filter(
                Portfolio.id == request.portfolio_id,
                Portfolio.user_id == current_user.id,
            )
            .first()
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        # Verify strategies exist
        for strategy_name in request.strategy_names:
            if not StrategyRegistry.get_info(strategy_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Strategy not found: {strategy_name}",
                )

        # Start auto trading
        success = await AutoTradingService.start_auto_trading(
            user_id=current_user.id,
            portfolio_id=request.portfolio_id,
            strategy_names=request.strategy_names,
            symbols=request.symbols,
            db=db,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start auto-trading",
            )

        return {
            "status": "success",
            "message": f"Auto-trading started with {len(request.strategy_names)} strategies",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/stop", response_model=Dict[str, str])
async def stop_auto_trading(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Stop automated trading for the current user.

    Disables all active strategies and stops automatic trade execution.
    """
    try:
        success = await AutoTradingService.stop_auto_trading(
            user_id=current_user.id, db=db
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop auto-trading",
            )

        return {"status": "success", "message": "Auto-trading stopped"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/status", response_model=AutoTradingStatusResponse)
async def get_auto_trading_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current auto-trading status and active strategies.

    Returns information about whether auto-trading is enabled and
    which strategies are currently running.
    """
    try:
        is_active = AutoTradingService.is_auto_trading_active(current_user.id)
        active_strategies = AutoTradingService.get_active_strategies(current_user.id)

        return AutoTradingStatusResponse(
            is_active=is_active,
            active_strategies=active_strategies,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/strategies/add", response_model=Dict[str, str])
async def add_strategy(
    request: AddStrategyRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a new strategy to an active auto-trading session.

    Allows adding strategies without stopping and restarting auto-trading.
    """
    try:
        # Verify auto-trading is active
        if not AutoTradingService.is_auto_trading_active(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Auto-trading is not active",
            )

        # Verify strategy exists
        if not StrategyRegistry.get_info(request.strategy_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {request.strategy_name}",
            )

        # Add strategy
        success = await AutoTradingService.add_strategy(
            user_id=current_user.id,
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            parameters=request.parameters,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add strategy",
            )

        return {
            "status": "success",
            "message": f"Added strategy {request.strategy_name} for {request.symbol}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/strategies/remove", response_model=Dict[str, str])
async def remove_strategy(
    strategy_name: str,
    symbol: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Remove a strategy from an active auto-trading session.
    """
    try:
        success = await AutoTradingService.remove_strategy(
            user_id=current_user.id,
            strategy_name=strategy_name,
            symbol=symbol,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
            )

        return {
            "status": "success",
            "message": f"Removed strategy {strategy_name} for {symbol}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/strategies/available", response_model=List[AvailableStrategy])
async def list_available_strategies(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    List all available trading strategies.

    Optionally filter by category (technical, momentum, mean_reversion, etc.)
    """
    try:
        # Get category filter
        cat_filter = None
        if category:
            try:
                cat_filter = StrategyCategory(category)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category: {category}",
                )

        # Get all strategy info
        all_strategies = StrategyRegistry.get_all_info()

        # Filter and format
        strategies = []
        for name, info in all_strategies.items():
            if cat_filter and info["category"] != cat_filter.value:
                continue

            strategies.append(
                AvailableStrategy(
                    name=name,
                    category=info["category"],
                    description=info["description"],
                    risk_level=info["risk_level"],
                    default_parameters=info["default_parameters"],
                    timeframes=info["timeframes"],
                )
            )

        return strategies

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/strategies/categories", response_model=List[str])
async def list_strategy_categories(
    current_user: User = Depends(get_current_active_user),
):
    """List all available strategy categories."""
    return [cat.value for cat in StrategyRegistry.list_categories()]
