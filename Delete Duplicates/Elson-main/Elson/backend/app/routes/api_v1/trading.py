from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path, Body, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

from ...db.database import get_db
from ...models.trade import Trade, OrderType, OrderSide, TradeStatus, InvestmentType
from ...services.trading_service import TradingService
from ...services.paper_trading_service import PaperTradingService
from ...services.order_aggregator import OrderAggregator
from ...services.market_data import MarketDataService
from ...schemas.trade import (
    TradeCreate,
    TradeResponse,
    DollarBasedInvestmentCreate,
    OrderBook,
    MarketDataResponse,
    QuantityBasedTradeCreate,
    TradeUpdate,
    WSMarketData,
    TradingConfig
)
from ...core.auth import get_current_user, get_current_user_with_permissions, get_current_user_optional
from ...models.user import User, UserRole
from ...core.config import settings

router = APIRouter()


# Regular trading endpoints
@router.post("/trades", response_model=TradeResponse)
async def create_trade(
    trade_data: QuantityBasedTradeCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new quantity-based trade order."""
    trading_service = TradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await trading_service.create_trade(
            user_id=current_user.id,
            portfolio_id=trade_data.portfolio_id,
            symbol=trade_data.symbol,
            trade_type=trade_data.trade_type,
            order_type="market",  # Default to market orders for now
            quantity=float(trade_data.quantity),
            price=float(trade_data.price) if trade_data.price else None,
            is_fractional=getattr(trade_data, 'is_fractional', False)
        )
        
        # Add background task to update portfolio value
        background_tasks.add_task(
            trading_service._update_portfolio_value,
            db.query(Trade).filter(Trade.id == result["id"]).first().portfolio
        )
        
        return TradeResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trades/dollar", response_model=TradeResponse)
async def create_dollar_based_trade(
    trade_data: DollarBasedInvestmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dollar-based investment (fractional shares)."""
    trading_service = TradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await trading_service.create_trade(
            user_id=current_user.id,
            portfolio_id=trade_data.portfolio_id,
            symbol=trade_data.symbol,
            trade_type=trade_data.trade_type,
            order_type="market",  # Dollar-based are always market orders
            investment_amount=float(trade_data.investment_amount),
            investment_type="dollar_based",
            is_fractional=True
        )
        
        # Add background task to update portfolio value
        background_tasks.add_task(
            trading_service._update_portfolio_value,
            db.query(Trade).filter(Trade.id == result["id"]).first().portfolio
        )
        
        return TradeResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trades/{trade_id}/execute", response_model=TradeResponse)
async def execute_trade(
    trade_id: int = Path(..., title="The ID of the trade to execute"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a pending trade."""
    trading_service = TradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await trading_service.execute_trade(trade_id, current_user.id)
        return TradeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trades/{trade_id}/cancel")
async def cancel_trade(
    trade_id: int = Path(..., title="The ID of the trade to cancel"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending trade."""
    trading_service = TradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await trading_service.cancel_trade(trade_id, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    portfolio_id: Optional[int] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trades with optional filters."""
    query = db.query(Trade).filter(Trade.user_id == current_user.id)
    
    if status:
        query = query.filter(Trade.status == status)
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    if portfolio_id:
        query = query.filter(Trade.portfolio_id == portfolio_id)
        
    # Order by created_at desc and limit results
    trades = query.order_by(Trade.created_at.desc()).limit(limit).all()
    
    return [TradeResponse.from_orm(trade) for trade in trades]


@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int = Path(..., title="The ID of the trade to get"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific trade by ID."""
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return TradeResponse.from_orm(trade)


# Paper trading specific endpoints
@router.post("/trades/paper", response_model=TradeResponse)
async def create_paper_trade(
    trade_data: QuantityBasedTradeCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new paper trade for practice trading."""
    paper_trading_service = PaperTradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await paper_trading_service.create_paper_trade(
            user_id=current_user.id,
            portfolio_id=trade_data.portfolio_id,
            symbol=trade_data.symbol,
            trade_type=trade_data.trade_type,
            order_type="market",  # Default to market orders for now
            quantity=float(trade_data.quantity),
            limit_price=float(trade_data.price) if trade_data.price else None,
            is_fractional=getattr(trade_data, 'is_fractional', False)
        )
        
        # Add background task to update portfolio value
        background_tasks.add_task(
            paper_trading_service._update_portfolio_value,
            db.query(Trade).filter(Trade.id == result["id"]).first().portfolio
        )
        
        return TradeResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trades/paper/dollar", response_model=TradeResponse)
async def create_paper_dollar_investment(
    trade_data: DollarBasedInvestmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dollar-based paper investment (fractional shares)."""
    paper_trading_service = PaperTradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await paper_trading_service.create_paper_dollar_investment(
            user_id=current_user.id,
            portfolio_id=trade_data.portfolio_id,
            symbol=trade_data.symbol,
            investment_amount=float(trade_data.investment_amount),
            trade_type=trade_data.trade_type
        )
        
        # Add background task to update portfolio value
        background_tasks.add_task(
            paper_trading_service._update_portfolio_value,
            db.query(Trade).filter(Trade.id == result["id"]).first().portfolio
        )
        
        return TradeResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trades/paper/{trade_id}/execute", response_model=TradeResponse)
async def execute_paper_trade(
    trade_id: int = Path(..., title="The ID of the paper trade to execute"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a pending paper trade."""
    paper_trading_service = PaperTradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        # Verify this is a paper trade (could add a field to the Trade model)
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        result = await paper_trading_service.execute_trade(trade_id, current_user.id)
        return TradeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolios/{portfolio_id}/paper", response_model=Dict[str, Any])
async def get_paper_portfolio(
    portfolio_id: int = Path(..., title="The ID of the portfolio"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paper trading portfolio information with positions."""
    paper_trading_service = PaperTradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        # Verify portfolio belongs to user
        portfolio = db.query(Trade).filter(
            Trade.id == portfolio_id, 
            Trade.user_id == current_user.id
        ).first()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        result = await paper_trading_service.get_paper_portfolio_value(portfolio_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolios/{portfolio_id}/paper/history", response_model=List[Dict[str, Any]])
async def get_paper_trade_history(
    portfolio_id: int = Path(..., title="The ID of the portfolio"),
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paper trading history for a portfolio."""
    paper_trading_service = PaperTradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        # Verify portfolio belongs to user or is a custodial portfolio they manage
        portfolio_exists = False
        
        # Check if portfolio belongs to user directly
        portfolio = db.query(Trade).filter(
            Trade.id == portfolio_id, 
            Trade.user_id == current_user.id
        ).first()
        
        if portfolio:
            portfolio_exists = True
        else:
            # Check if user is guardian for this portfolio's owner
            minor_portfolio = db.query(Trade).join(
                Account, Account.user_id == Trade.user_id
            ).filter(
                Trade.id == portfolio_id,
                Account.guardian_id == current_user.id
            ).first()
            
            if minor_portfolio:
                portfolio_exists = True
        
        if not portfolio_exists:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        result = await paper_trading_service.get_paper_trade_history(portfolio_id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Market data endpoints
@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str = Path(..., title="The stock symbol to get data for"),
    current_user: User = Depends(get_current_user)
):
    """Get real-time market data for a symbol."""
    market_service = MarketDataService()
    try:
        data = await market_service.get_quote(symbol)
        return MarketDataResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orderbook/{symbol}", response_model=Dict[str, Any])
async def get_order_book(
    symbol: str = Path(..., title="The stock symbol to get order book for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current order book for a symbol."""
    trading_service = TradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await trading_service.get_order_book(symbol)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/market-depth/{symbol}", response_model=Dict[str, Any])
async def get_market_depth(
    symbol: str = Path(..., title="The stock symbol to get market depth for"),
    levels: int = Query(5, title="Number of price levels to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get simulated market depth (order book) for a symbol."""
    paper_trading_service = PaperTradingService(
        db=db,
        market_data_service=MarketDataService()
    )
    
    try:
        result = await paper_trading_service.get_market_depth(symbol, levels)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config", response_model=TradingConfig)
async def get_trading_config(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get trading configuration including fractional share settings."""
    logger = logging.getLogger(__name__)
    logger.info(f"Getting trading configuration for user: {current_user.username if current_user else 'anonymous'}")
    
    # Get minimum investment amounts from settings
    min_investment = float(getattr(settings, "MIN_FRACTIONAL_AMOUNT", 1.00))
    max_investment = float(getattr(settings, "MAX_INVESTMENT_AMOUNT", 100000.00))
    fractional_enabled = bool(getattr(settings, "FRACTIONAL_SHARES_ENABLED", True))
    
    # Adjust min investment for user age (if applicable)
    age_appropriate_min = min_investment
    if current_user and hasattr(current_user, 'age') and current_user.age:
        if current_user.age < 13:
            age_appropriate_min = max(min_investment, 1.00)  # $1 minimum for kids
        elif current_user.age < 18:
            age_appropriate_min = max(min_investment, 5.00)  # $5 minimum for teens
    
    # Return configuration
    return TradingConfig(
        minInvestmentAmount=age_appropriate_min,
        maxInvestmentAmount=max_investment,
        fractionalSharesEnabled=fractional_enabled,
        dollarBasedTradingEnabled=fractional_enabled,
        supportedOrderTypes=[
            OrderType.MARKET,
            OrderType.LIMIT
        ],
        availableTradingHours={
            'open': '09:30',
            'close': '16:00',
            'timezone': 'America/New_York'
        },
        minFractionalQuantity=0.000001,
        investmentTiers=[
            {'name': 'Starter', 'min': age_appropriate_min, 'max': 100.00},
            {'name': 'Investor', 'min': 100.01, 'max': 1000.00},
            {'name': 'Advanced', 'min': 1000.01, 'max': max_investment}
        ]
    )