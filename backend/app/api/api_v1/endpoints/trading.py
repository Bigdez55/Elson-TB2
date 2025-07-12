from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.base import get_db
from app.models.trade import Trade, TradeStatus
from app.models.user import User
from app.schemas.trading import (
    OrderCancelRequest,
    PositionResponse,
    TradeOrderRequest,
    TradeResponse,
    TradingStatsResponse,
)
from app.services.trading import trading_service

router = APIRouter()


@router.post("/order", response_model=TradeResponse)
async def place_order(
    order_request: TradeOrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Place a trading order"""
    try:
        trade_data = order_request.dict()
        trade = await trading_service.place_order(trade_data, current_user, db)
        return TradeResponse.from_orm(trade)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place order: {str(e)}")


@router.post("/cancel", response_model=TradeResponse)
async def cancel_order(
    cancel_request: OrderCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending order"""
    try:
        trade = await trading_service.cancel_order(cancel_request.trade_id, current_user, db)
        return TradeResponse.from_orm(trade)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")


@router.get("/orders", response_model=List[TradeResponse])
async def get_open_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get open orders"""
    try:
        orders = await trading_service.get_open_orders(current_user, db)
        return [TradeResponse.from_orm(order) for order in orders]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")


@router.get("/history", response_model=List[TradeResponse])
async def get_trade_history(
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TradeStatus] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get trade history"""
    try:
        trades = await trading_service.get_trade_history(current_user, db, limit)

        # Filter by status if provided
        if status:
            trades = [trade for trade in trades if trade.status == status]

        return [TradeResponse.from_orm(trade) for trade in trades]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trade history: {str(e)}")


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current positions"""
    try:
        from app.models.portfolio import Portfolio

        # Get user's active portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.owner_id == current_user.id, Portfolio.is_active).first()

        if not portfolio:
            return []

        positions = []
        for holding in portfolio.holdings:
            if holding.quantity > 0:  # Only show positions with positive quantity
                positions.append(
                    PositionResponse(
                        symbol=holding.symbol,
                        quantity=holding.quantity,
                        average_cost=holding.average_cost,
                        current_price=holding.current_price,
                        market_value=holding.market_value,
                        unrealized_gain_loss=holding.unrealized_gain_loss,
                        unrealized_gain_loss_percentage=(holding.unrealized_gain_loss_percentage),
                        asset_type=holding.asset_type,
                    )
                )

        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")


@router.get("/stats", response_model=TradingStatsResponse)
async def get_trading_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get trading statistics"""
    try:
        from app.models.portfolio import Portfolio

        # Get all filled trades
        trades = (
            db.query(Trade)
            .join(Portfolio)
            .filter(
                Portfolio.owner_id == current_user.id,
                Trade.status == TradeStatus.FILLED,
            )
            .all()
        )

        if not trades:
            return TradingStatsResponse(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_profit_loss=0.0,
                average_profit_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                total_commission=0.0,
            )

        # Calculate statistics
        total_trades = len(trades)
        total_commission = sum(trade.commission + trade.fees for trade in trades)

        # Group trades by symbol to calculate P&L
        profit_losses = []
        winning_trades = 0
        losing_trades = 0

        # For simplicity, calculate P&L per trade (this could be enhanced)
        for trade in trades:
            if trade.trade_type.value == "buy":
                continue  # Skip buy trades for P&L calculation

            # This is simplified - in reality, you'd match buy/sell pairs
            # For now, just use the difference from average cost if available
            pnl = 0.0  # Placeholder

            if pnl > 0:
                winning_trades += 1
            elif pnl < 0:
                losing_trades += 1

            profit_losses.append(pnl)

        total_profit_loss = sum(profit_losses)
        win_rate = (winning_trades / max(total_trades, 1)) * 100
        average_profit_loss = total_profit_loss / max(len(profit_losses), 1)
        largest_win = max(profit_losses) if profit_losses else 0.0
        largest_loss = min(profit_losses) if profit_losses else 0.0

        return TradingStatsResponse(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_profit_loss=total_profit_loss,
            average_profit_loss=average_profit_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            total_commission=total_commission,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trading stats: {str(e)}")


@router.get("/validate/{symbol}")
async def validate_symbol(symbol: str, current_user: User = Depends(get_current_active_user)):
    """Validate if a symbol is tradeable"""
    try:
        from app.services.market_data import market_data_service

        symbol = symbol.upper()
        quote = await market_data_service.get_quote(symbol)

        if quote:
            return {
                "symbol": symbol,
                "valid": True,
                "current_price": quote.get("price"),
                "change": quote.get("change"),
                "change_percent": quote.get("change_percent"),
            }
        else:
            return {
                "symbol": symbol,
                "valid": False,
                "error": "Symbol not found or market data unavailable",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate symbol: {str(e)}")
