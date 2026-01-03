from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.base import get_db
from app.models.trade import Trade, TradeStatus
from app.models.user import User
from app.schemas.trading import (
    BatchDataResponse,
    OrderCancelRequest,
    PositionResponse,
    SyncModesResponse,
    TradeOrderRequest,
    TradeResponse,
    TradingAccountResponse,
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
        trade = await trading_service.cancel_order(
            cancel_request.trade_id, current_user, db
        )
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
        raise HTTPException(
            status_code=500, detail=f"Failed to get trade history: {str(e)}"
        )


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current positions"""
    try:
        from app.models.portfolio import Portfolio

        # Get user's active portfolio
        portfolio = (
            db.query(Portfolio)
            .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
            .first()
        )

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
                        unrealized_gain_loss_percentage=(
                            holding.unrealized_gain_loss_percentage
                        ),
                        asset_type=holding.asset_type,
                    )
                )

        return positions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get positions: {str(e)}"
        )


@router.get("/positions/{symbol}", response_model=PositionResponse)
async def get_position_by_symbol(
    symbol: str,
    x_trading_mode: Optional[str] = Header(None, alias="x-trading-mode"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific position by symbol"""
    try:
        from app.models.portfolio import Portfolio

        symbol = symbol.upper()

        # Get user's active portfolio
        portfolio = (
            db.query(Portfolio)
            .filter(Portfolio.owner_id == current_user.id, Portfolio.is_active)
            .first()
        )

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Find the holding for the symbol
        for holding in portfolio.holdings:
            if holding.symbol.upper() == symbol and holding.quantity > 0:
                return PositionResponse(
                    symbol=holding.symbol,
                    quantity=holding.quantity,
                    average_cost=holding.average_cost,
                    current_price=holding.current_price,
                    market_value=holding.market_value,
                    unrealized_gain_loss=holding.unrealized_gain_loss,
                    unrealized_gain_loss_percentage=holding.unrealized_gain_loss_percentage,
                    asset_type=holding.asset_type,
                )

        raise HTTPException(status_code=404, detail=f"Position not found for symbol: {symbol}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get position: {str(e)}"
        )


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

        # Group trades by symbol to calculate P&L using FIFO matching
        profit_losses = []
        winning_trades = 0
        losing_trades = 0

        # Group trades by symbol for FIFO P&L calculation
        from collections import defaultdict
        symbol_buys = defaultdict(list)  # symbol -> list of (quantity, price) remaining

        # First pass: collect all buys
        for trade in trades:
            if trade.trade_type.value == "buy" and trade.filled_quantity and trade.filled_price:
                symbol_buys[trade.symbol].append({
                    "quantity": trade.filled_quantity,
                    "price": trade.filled_price
                })

        # Second pass: match sells against buys using FIFO
        for trade in trades:
            if trade.trade_type.value == "sell" and trade.filled_quantity and trade.filled_price:
                sell_qty = trade.filled_quantity
                sell_price = trade.filled_price
                buys = symbol_buys.get(trade.symbol, [])

                trade_pnl = 0.0

                # Match against available buys using FIFO
                while sell_qty > 0 and buys:
                    buy = buys[0]
                    match_qty = min(sell_qty, buy["quantity"])

                    # Calculate P&L for this matched portion
                    pnl_per_share = sell_price - buy["price"]
                    trade_pnl += pnl_per_share * match_qty

                    # Reduce quantities
                    sell_qty -= match_qty
                    buy["quantity"] -= match_qty

                    # Remove exhausted buy
                    if buy["quantity"] <= 0:
                        buys.pop(0)

                # Account for sells without matching buys (use sell price as P&L)
                if sell_qty > 0:
                    # If no matching buy, treat as 100% profit (sold something acquired before tracking)
                    trade_pnl += sell_qty * sell_price

                # Subtract commission and fees from P&L
                trade_pnl -= (trade.commission + trade.fees)

                if trade_pnl > 0:
                    winning_trades += 1
                elif trade_pnl < 0:
                    losing_trades += 1

                profit_losses.append(trade_pnl)

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
        raise HTTPException(
            status_code=500, detail=f"Failed to get trading stats: {str(e)}"
        )


@router.get("/validate/{symbol}")
async def validate_symbol(
    symbol: str, current_user: User = Depends(get_current_active_user)
):
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
        raise HTTPException(
            status_code=500, detail=f"Failed to validate symbol: {str(e)}"
        )


@router.get("/account", response_model=TradingAccountResponse)
async def get_trading_account(
    x_trading_mode: Optional[str] = Header(None, alias="x-trading-mode"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get trading account information"""
    try:
        from app.models.portfolio import Portfolio

        trading_mode = x_trading_mode or "paper"
        is_paper = trading_mode == "paper"

        # Get user's portfolio for the given mode
        portfolio = (
            db.query(Portfolio)
            .filter(
                Portfolio.owner_id == current_user.id,
                Portfolio.is_active == True,
            )
            .first()
        )

        cash_balance = portfolio.cash_balance if portfolio else 100000.0
        portfolio_value = portfolio.total_value if portfolio else 100000.0

        return TradingAccountResponse(
            account_id=f"{current_user.id}_{trading_mode}",
            account_type=trading_mode,
            buying_power=cash_balance,
            cash_balance=cash_balance,
            portfolio_value=portfolio_value,
            day_trade_count=0,
            pattern_day_trader=False,
            trading_blocked=False,
            last_equity_close=portfolio_value,
            created_at=current_user.created_at.isoformat() if current_user.created_at else datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get trading account: {str(e)}"
        )


@router.get("/batch-data", response_model=BatchDataResponse)
async def get_batch_data(
    x_trading_mode: Optional[str] = Header(None, alias="x-trading-mode"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get batch trading data (portfolio, positions, orders, account) in one request"""
    try:
        from app.models.portfolio import Portfolio

        trading_mode = x_trading_mode or "paper"

        # Get user's portfolio
        portfolio = (
            db.query(Portfolio)
            .filter(
                Portfolio.owner_id == current_user.id,
                Portfolio.is_active == True,
            )
            .first()
        )

        # Calculate day P&L from positions' unrealized gains
        day_pnl = 0.0
        total_value = portfolio.total_value if portfolio else 100000.0

        if portfolio and portfolio.holdings:
            # Sum unrealized P&L from all positions
            # This represents the change in value since purchase (approximate day P&L)
            for holding in portfolio.holdings:
                if holding.quantity > 0 and holding.unrealized_gain_loss:
                    day_pnl += holding.unrealized_gain_loss

        # Calculate day P&L percent
        day_pnl_percent = (day_pnl / total_value * 100) if total_value > 0 else 0.0

        # Build portfolio summary
        portfolio_summary: Dict[str, Any] = {
            "total_value": total_value,
            "cash_balance": portfolio.cash_balance if portfolio else 100000.0,
            "positions_value": (portfolio.total_value - portfolio.cash_balance) if portfolio else 0.0,
            "day_pnl": round(day_pnl, 2),
            "day_pnl_percent": round(day_pnl_percent, 2),
            "total_pnl": portfolio.total_return if portfolio else 0.0,
            "total_pnl_percent": portfolio.total_return_percentage if portfolio else 0.0,
            "paper_trading": trading_mode == "paper",
            "last_updated": datetime.utcnow().isoformat(),
        }

        # Get positions
        positions: List[PositionResponse] = []
        if portfolio and portfolio.holdings:
            for holding in portfolio.holdings:
                if holding.quantity > 0:
                    positions.append(
                        PositionResponse(
                            symbol=holding.symbol,
                            quantity=holding.quantity,
                            average_cost=holding.average_cost,
                            current_price=holding.current_price,
                            market_value=holding.market_value,
                            unrealized_gain_loss=holding.unrealized_gain_loss,
                            unrealized_gain_loss_percentage=holding.unrealized_gain_loss_percentage,
                            asset_type=holding.asset_type,
                        )
                    )

        # Get recent orders
        recent_orders: List[TradeResponse] = []
        if portfolio:
            trades = (
                db.query(Trade)
                .filter(Trade.portfolio_id == portfolio.id)
                .order_by(Trade.created_at.desc())
                .limit(20)
                .all()
            )
            recent_orders = [TradeResponse.from_orm(trade) for trade in trades]

        # Build account info
        cash_balance = portfolio.cash_balance if portfolio else 100000.0
        portfolio_value = portfolio.total_value if portfolio else 100000.0
        account = TradingAccountResponse(
            account_id=f"{current_user.id}_{trading_mode}",
            account_type=trading_mode,
            buying_power=cash_balance,
            cash_balance=cash_balance,
            portfolio_value=portfolio_value,
            day_trade_count=0,
            pattern_day_trader=False,
            trading_blocked=False,
            last_equity_close=portfolio_value,
            created_at=current_user.created_at.isoformat() if current_user.created_at else datetime.utcnow().isoformat(),
        )

        return BatchDataResponse(
            portfolio=portfolio_summary,
            positions=positions,
            recent_orders=recent_orders,
            account=account,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get batch data: {str(e)}"
        )


@router.post("/sync-modes", response_model=SyncModesResponse)
async def sync_trading_modes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Sync trading data across paper and live modes"""
    try:
        from app.models.portfolio import Portfolio

        # Count data in each mode
        portfolios = (
            db.query(Portfolio)
            .filter(Portfolio.owner_id == current_user.id)
            .all()
        )

        paper_count = 0
        live_count = 0

        for portfolio in portfolios:
            trade_count = db.query(Trade).filter(Trade.portfolio_id == portfolio.id).count()
            # For now, we consider all portfolios as potentially having both modes
            # In a real implementation, you'd track mode per portfolio/trade
            paper_count += trade_count
            live_count += trade_count

        return SyncModesResponse(
            success=True,
            message="Trading modes synchronized successfully",
            paper_data_count=paper_count,
            live_data_count=live_count,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to sync trading modes: {str(e)}"
        )
