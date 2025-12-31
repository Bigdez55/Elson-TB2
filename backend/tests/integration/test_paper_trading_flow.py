import asyncio
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.holding import Position
from app.models.trade import InvestmentType, Trade, TradeStatus
from app.services.market_simulation import MarketSimulationService
from app.services.paper_trading import PaperTradingService


@pytest.mark.asyncio
async def test_paper_trade_creation(db_session: Session, client: TestClient):
    """Test creating a paper trade."""
    # Create test user and portfolio
    user_id = 1  # Assumes test user exists

    # Create portfolio for testing
    portfolio = Portfolio(
        user_id=user_id,
        name="Test Paper Trading Portfolio",
        description="For testing paper trading",
        cash_balance=10000.0,
        total_value=10000.0,
        is_active=True,
    )
    db_session.add(portfolio)
    db_session.commit()

    # Create paper trading service
    market_service = MarketSimulationService()
    paper_service = PaperTradingService(
        db=db_session, market_data_service=market_service
    )

    # Create a paper trade
    result = await paper_service.create_paper_trade(
        user_id=user_id,
        portfolio_id=portfolio.id,
        symbol="AAPL",
        trade_type="buy",
        quantity=10.0,
    )

    # Check that trade was created
    assert result is not None
    assert "id" in result

    # Check database record
    trade = db_session.query(Trade).filter(Trade.id == result["id"]).first()
    assert trade is not None
    assert trade.symbol == "AAPL"
    assert trade.quantity == 10.0
    assert trade.is_paper_trade is True

    # Clean up
    db_session.delete(trade)
    db_session.delete(portfolio)
    db_session.commit()


@pytest.mark.asyncio
async def test_paper_trade_execution(db_session: Session, client: TestClient):
    """Test executing a paper trade."""
    # Create test user and portfolio
    user_id = 1  # Assumes test user exists

    # Create portfolio for testing
    portfolio = Portfolio(
        user_id=user_id,
        name="Test Paper Trading Portfolio",
        description="For testing paper trading",
        cash_balance=10000.0,
        total_value=10000.0,
        is_active=True,
    )
    db_session.add(portfolio)
    db_session.commit()

    # Create paper trading service
    market_service = MarketSimulationService()
    paper_service = PaperTradingService(
        db=db_session, market_data_service=market_service
    )

    # Create a paper trade
    create_result = await paper_service.create_paper_trade(
        user_id=user_id,
        portfolio_id=portfolio.id,
        symbol="AAPL",
        trade_type="buy",
        quantity=10.0,
    )

    # Execute the trade
    trade = db_session.query(Trade).filter(Trade.id == create_result["id"]).first()
    execute_result = await paper_service.execute_trade(trade.id, user_id)

    # Check execution result
    assert execute_result is not None
    assert "status" in execute_result
    assert execute_result["status"] == TradeStatus.FILLED.value

    # Check database record
    updated_trade = db_session.query(Trade).filter(Trade.id == trade.id).first()
    assert updated_trade.status == TradeStatus.FILLED
    assert updated_trade.executed_at is not None
    assert updated_trade.filled_quantity == 10.0
    assert updated_trade.average_price is not None

    # Clean up
    db_session.delete(updated_trade)
    db_session.delete(portfolio)
    db_session.commit()


@pytest.mark.asyncio
async def test_paper_dollar_based_investment(db_session: Session, client: TestClient):
    """Test creating a dollar-based paper investment (fractional shares)."""
    # Create test user and portfolio
    user_id = 1  # Assumes test user exists

    # Create portfolio for testing
    portfolio = Portfolio(
        user_id=user_id,
        name="Test Paper Trading Portfolio",
        description="For testing paper trading",
        cash_balance=10000.0,
        total_value=10000.0,
        is_active=True,
    )
    db_session.add(portfolio)
    db_session.commit()

    # Create paper trading service
    market_service = MarketSimulationService()
    paper_service = PaperTradingService(
        db=db_session, market_data_service=market_service
    )

    # Create a dollar-based paper investment
    result = await paper_service.create_paper_dollar_investment(
        user_id=user_id,
        portfolio_id=portfolio.id,
        symbol="AAPL",
        investment_amount=100.0,
    )

    # Check that trade was created
    assert result is not None
    assert "id" in result

    # Check database record
    trade = db_session.query(Trade).filter(Trade.id == result["id"]).first()
    assert trade is not None
    assert trade.symbol == "AAPL"
    assert trade.investment_amount == 100.0
    assert trade.investment_type == InvestmentType.DOLLAR_BASED
    assert trade.is_fractional is True
    assert trade.is_paper_trade is True

    # Check that trade is executed (dollar-based are executed immediately)
    assert trade.status == TradeStatus.FILLED
    assert trade.filled_quantity is not None
    assert trade.average_price is not None

    # Clean up
    db_session.delete(trade)
    db_session.delete(portfolio)
    db_session.commit()


@pytest.mark.asyncio
async def test_paper_portfolio_value(db_session: Session, client: TestClient):
    """Test retrieving paper portfolio value."""
    # Create test user and portfolio
    user_id = 1  # Assumes test user exists

    # Create portfolio for testing
    portfolio = Portfolio(
        user_id=user_id,
        name="Test Paper Trading Portfolio",
        description="For testing paper trading",
        cash_balance=10000.0,
        total_value=10000.0,
        is_active=True,
    )
    db_session.add(portfolio)
    db_session.commit()

    # Create a position
    current_price = Decimal("150.0")
    position = Position(
        portfolio_id=portfolio.id,
        symbol="AAPL",
        quantity=Decimal("10"),
        average_price=Decimal("145.0"),
        current_price=current_price,
        is_fractional=False,
    )
    db_session.add(position)
    db_session.commit()

    # Create paper trading service
    market_service = MarketSimulationService()
    paper_service = PaperTradingService(
        db=db_session, market_data_service=market_service
    )

    # Get portfolio value
    value_result = await paper_service.get_paper_portfolio_value(portfolio.id)

    # Check portfolio value results
    assert value_result is not None
    assert "portfolio_id" in value_result
    assert value_result["portfolio_id"] == portfolio.id
    assert "cash_balance" in value_result
    assert "total_value" in value_result
    assert "positions" in value_result

    # Check that position is included
    assert len(value_result["positions"]) == 1
    assert value_result["positions"][0]["symbol"] == "AAPL"
    assert value_result["positions"][0]["quantity"] == float(position.quantity)

    # Clean up
    db_session.delete(position)
    db_session.delete(portfolio)
    db_session.commit()


@pytest.mark.asyncio
async def test_paper_trade_history(db_session: Session, client: TestClient):
    """Test retrieving paper trade history."""
    # Create test user and portfolio
    user_id = 1  # Assumes test user exists

    # Create portfolio for testing
    portfolio = Portfolio(
        user_id=user_id,
        name="Test Paper Trading Portfolio",
        description="For testing paper trading",
        cash_balance=10000.0,
        total_value=10000.0,
        is_active=True,
    )
    db_session.add(portfolio)
    db_session.commit()

    # Create a trade
    trade = Trade(
        user_id=user_id,
        portfolio_id=portfolio.id,
        symbol="AAPL",
        quantity=10.0,
        trade_type="buy",
        order_type="market",
        status=TradeStatus.FILLED,
        is_paper_trade=True,
        average_price=150.0,
        filled_quantity=10.0,
        commission=1.50,
        total_amount=1501.50,
    )
    db_session.add(trade)
    db_session.commit()

    # Create paper trading service
    market_service = MarketSimulationService()
    paper_service = PaperTradingService(
        db=db_session, market_data_service=market_service
    )

    # Get trade history
    history_result = await paper_service.get_paper_trade_history(portfolio.id)

    # Check trade history results
    assert history_result is not None
    assert len(history_result) == 1
    assert history_result[0]["symbol"] == "AAPL"
    assert history_result[0]["quantity"] == 10.0
    assert history_result[0]["status"] == "filled"

    # Clean up
    db_session.delete(trade)
    db_session.delete(portfolio)
    db_session.commit()
