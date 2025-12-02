"""Investment service for handling dollar-based investments.

This module provides functionality for handling dollar-based investments,
including fractional shares, recurring investments, and investment goals.
"""

import logging
from decimal import Decimal
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.trade import Trade, TradeStatus, InvestmentType, TradeSource, OrderType
from app.models.portfolio import Portfolio
from app.models.user import User, UserRole
from app.models.account import RecurringInvestment, RecurringFrequency
from app.schemas.trade import (
    DollarBasedInvestmentCreate,
    RecurringInvestmentCreate,
    RecurringInvestmentUpdate,
    RecurringInvestmentResponse,
    TradeResponse
)
from app.services.market_data import MarketDataService
from app.services.trading import TradingService
from app.services.order_aggregator import OrderAggregator
from app.core.config import settings

logger = logging.getLogger(__name__)


class InvestmentService:
    """Service for handling dollar-based investments."""
    
    def __init__(
        self, 
        db: Session,
        market_data_service: MarketDataService,
        trading_service: TradingService,
        order_aggregator: OrderAggregator
    ):
        """Initialize with required services."""
        self.db = db
        self.market_data = market_data_service
        self.trading = trading_service
        self.order_aggregator = order_aggregator
        
        # Configuration
        self.min_investment_amount = Decimal('1.00')  # Minimum $1 for fractional orders
        self.min_quantity = Decimal('0.0001')         # Minimum 0.0001 shares
    
    def create_dollar_based_investment(
        self, 
        user_id: int, 
        investment_data: DollarBasedInvestmentCreate
    ) -> Trade:
        """Create a new dollar-based investment."""
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify portfolio exists and belongs to user
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == investment_data.portfolio_id,
            Portfolio.user_id == user_id
        ).first()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found or does not belong to user"
            )
        
        # Validate investment amount
        investment_amount = Decimal(str(investment_data.investment_amount))
        if investment_amount < self.min_investment_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Investment amount must be at least ${self.min_investment_amount}"
            )
        
        # Get current price
        try:
            current_price = Decimal(str(self.market_data.get_current_price(investment_data.symbol)))
        except Exception as e:
            logger.error(f"Failed to get current price for {investment_data.symbol}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to get current price for {investment_data.symbol}"
            )
        
        # Calculate estimated quantity (for display purposes only)
        estimated_quantity = investment_amount / current_price
        
        # Minor needs guardian approval
        needs_approval = user.role == UserRole.MINOR
        initial_status = TradeStatus.PENDING_APPROVAL if needs_approval else TradeStatus.PENDING
        
        # Create the trade record
        trade = Trade(
            user_id=user_id,
            portfolio_id=investment_data.portfolio_id,
            symbol=investment_data.symbol,
            quantity=None,  # Not determined yet
            price=current_price,  # Current price for reference
            investment_amount=investment_amount,
            investment_type=InvestmentType.DOLLAR_BASED,
            trade_type=investment_data.trade_type,
            order_type=OrderType.MARKET,
            status=initial_status,
            is_fractional=True,
            trade_source=TradeSource.USER_INITIATED,
            total_amount=investment_amount,
            created_at=datetime.utcnow()
        )
        
        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)
        
        # If auto-aggregation is enabled, trigger aggregation cycle
        if settings.AUTO_AGGREGATE_FRACTIONAL_ORDERS:
            try:
                self.order_aggregator.run_aggregation_cycle()
            except Exception as e:
                logger.error(f"Failed to run aggregation cycle: {e}")
                # Don't fail the request if aggregation fails
        
        return trade
    
    def create_recurring_investment(
        self, 
        user_id: int, 
        investment_data: RecurringInvestmentCreate
    ) -> Union[RecurringInvestment, Dict[str, Any]]:
        """Set up a recurring dollar-based investment."""
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify portfolio exists and belongs to user
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == investment_data.portfolio_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
            
        # Either the portfolio should belong to the user directly or the user should be the guardian
        if portfolio.user_id != user_id and portfolio.guardian_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Unauthorized access to portfolio"
            )
        
        try:
            # Verify symbol exists
            current_price = self.market_data.get_current_price(investment_data.symbol)
            if not current_price or current_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid price for {investment_data.symbol}"
                )
        except Exception as e:
            logger.error(f"Error getting price for {investment_data.symbol}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error validating symbol: {str(e)}"
            )
        
        # Calculate start date and next investment date
        start_date = investment_data.start_date or datetime.utcnow()
        
        # Create recurring investment record
        recurring_investment = RecurringInvestment(
            user_id=user_id,
            portfolio_id=investment_data.portfolio_id,
            symbol=investment_data.symbol,
            investment_amount=investment_data.investment_amount,
            frequency=RecurringFrequency(investment_data.frequency),
            start_date=start_date,
            end_date=investment_data.end_date,
            next_investment_date=start_date,
            is_active=True,
            description=investment_data.description,
            execution_count=0
        )
        
        # Save to database
        self.db.add(recurring_investment)
        self.db.flush()  # Get the ID
        
        # Create the first investment immediately if the start date is today or in the past
        if start_date.date() <= datetime.utcnow().date():
            # Create a trade for the initial investment
            initial_investment = DollarBasedInvestmentCreate(
                symbol=investment_data.symbol,
                investment_amount=investment_data.investment_amount,
                portfolio_id=investment_data.portfolio_id,
                trade_type=investment_data.trade_type,
                note=f"Recurring investment: {investment_data.frequency}"
            )
            
            # Create the trade
            trade = self.create_dollar_based_investment(user_id, initial_investment)
            
            # Update the trade to link to the recurring investment
            trade.trade_source = TradeSource.RECURRING
            trade.recurring_investment_id = recurring_investment.id
            
            # Set the next investment date
            recurring_investment.next_investment_date = self._calculate_next_investment_date(
                start_date, 
                RecurringFrequency(investment_data.frequency)
            )
        
        self.db.commit()
        self.db.refresh(recurring_investment)
        return recurring_investment
    
    def _calculate_next_investment_date(
        self, 
        current_date: datetime, 
        frequency: RecurringFrequency
    ) -> datetime:
        """Calculate the next investment date based on frequency."""
        if frequency == RecurringFrequency.DAILY:
            return current_date + timedelta(days=1)
        elif frequency == RecurringFrequency.WEEKLY:
            return current_date + timedelta(weeks=1)
        elif frequency == RecurringFrequency.MONTHLY:
            # Approximate month as 30 days
            return current_date + timedelta(days=30)
        elif frequency == RecurringFrequency.QUARTERLY:
            # Add three months (roughly)
            return current_date + timedelta(days=90)
        else:
            # Default to monthly if unknown
            return current_date + timedelta(days=30)
    
    def get_pending_dollar_investments(self, user_id: Optional[int] = None) -> List[Trade]:
        """Get pending dollar-based investments for a user or all users."""
        query = self.db.query(Trade).filter(
            Trade.investment_type == InvestmentType.DOLLAR_BASED,
            Trade.status == TradeStatus.PENDING
        )
        
        if user_id:
            query = query.filter(Trade.user_id == user_id)
            
        return query.all()
    
    def aggregate_investments(self) -> Dict[str, int]:
        """Trigger order aggregation for dollar-based investments."""
        result = self.order_aggregator.run_aggregation_cycle()
        return result
    
    def get_investment_history(
        self, 
        user_id: int, 
        portfolio_id: Optional[int] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Trade]:
        """Get investment history for a user."""
        query = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.investment_type == InvestmentType.DOLLAR_BASED
        )
        
        if portfolio_id:
            query = query.filter(Trade.portfolio_id == portfolio_id)
            
        if symbol:
            query = query.filter(Trade.symbol == symbol)
            
        if start_date:
            query = query.filter(Trade.created_at >= start_date)
            
        if end_date:
            query = query.filter(Trade.created_at <= end_date)
            
        return query.order_by(Trade.created_at.desc()).all()
    
    def calculate_performance(
        self, 
        user_id: int, 
        portfolio_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Calculate performance of dollar-based investments."""
        # Get completed investments
        investments = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.investment_type == InvestmentType.DOLLAR_BASED,
            Trade.status == TradeStatus.FILLED
        )
        
        if portfolio_id:
            investments = investments.filter(Trade.portfolio_id == portfolio_id)
            
        investments = investments.all()
        
        # Performance metrics
        total_invested = Decimal('0')
        current_value = Decimal('0')
        
        for investment in investments:
            # Calculate total invested
            investment_amount = Decimal(str(investment.investment_amount or 0))
            total_invested += investment_amount
            
            # Get current price
            try:
                current_price = Decimal(str(self.market_data.get_current_price(investment.symbol)))
                
                # Calculate current value
                quantity = Decimal(str(investment.filled_quantity or 0))
                position_value = quantity * current_price
                current_value += position_value
            except Exception as e:
                logger.error(f"Failed to get current price for {investment.symbol}: {e}")
                # Skip this investment if we can't get current price
                
        # Calculate performance metrics
        total_return = current_value - total_invested
        percent_return = (total_return / total_invested * 100) if total_invested > 0 else Decimal('0')
        
        return {
            "total_invested": float(total_invested),
            "current_value": float(current_value),
            "total_return": float(total_return),
            "percent_return": float(percent_return)
        }
    
    # New methods for managing recurring investments
    
    def get_recurring_investments(self, user_id: int) -> List[RecurringInvestment]:
        """Get all recurring investments for a user."""
        return self.db.query(RecurringInvestment).filter(
            RecurringInvestment.user_id == user_id
        ).all()
    
    def get_recurring_investment(self, recurring_id: int, user_id: int) -> Optional[RecurringInvestment]:
        """Get a specific recurring investment."""
        return self.db.query(RecurringInvestment).filter(
            RecurringInvestment.id == recurring_id,
            RecurringInvestment.user_id == user_id
        ).first()
    
    def get_recurring_investments_by_portfolio(self, portfolio_id: int) -> List[RecurringInvestment]:
        """Get all recurring investments for a specific portfolio."""
        return self.db.query(RecurringInvestment).filter(
            RecurringInvestment.portfolio_id == portfolio_id
        ).all()
    
    def update_recurring_investment(
        self, 
        recurring_id: int, 
        user_id: int, 
        update_data: RecurringInvestmentUpdate
    ) -> Union[RecurringInvestment, Dict[str, Any]]:
        """Update an existing recurring investment."""
        try:
            # Get the recurring investment
            recurring = self.get_recurring_investment(recurring_id, user_id)
            if not recurring:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recurring investment not found"
                )
            
            # Apply the updates
            if update_data.investment_amount is not None:
                recurring.investment_amount = update_data.investment_amount
                
            if update_data.frequency is not None:
                recurring.frequency = RecurringFrequency(update_data.frequency)
                
            if update_data.end_date is not None:
                recurring.end_date = update_data.end_date
                
            if update_data.is_active is not None:
                recurring.is_active = update_data.is_active
                
            if update_data.description is not None:
                recurring.description = update_data.description
            
            # Update the last modified time
            recurring.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(recurring)
            return recurring
            
        except HTTPException as he:
            raise he
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating recurring investment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating recurring investment: {str(e)}"
            )
    
    def cancel_recurring_investment(self, recurring_id: int, user_id: int) -> Dict[str, Any]:
        """Cancel a recurring investment."""
        try:
            # Get the recurring investment
            recurring = self.get_recurring_investment(recurring_id, user_id)
            if not recurring:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recurring investment not found"
                )
            
            # Mark as inactive
            recurring.is_active = False
            recurring.end_date = datetime.utcnow()
            recurring.updated_at = datetime.utcnow()
            
            self.db.commit()
            return {"message": "Recurring investment cancelled successfully"}
            
        except HTTPException as he:
            raise he
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling recurring investment: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error cancelling recurring investment: {str(e)}"
            )
            
    def get_due_recurring_investments(self) -> List[RecurringInvestment]:
        """Get recurring investments that are due to be executed."""
        now = datetime.utcnow()
        
        # Find recurring investments where:
        # 1. next_investment_date is in the past
        # 2. end_date is in the future or None
        # 3. is_active is True
        due_investments = self.db.query(RecurringInvestment).filter(
            RecurringInvestment.next_investment_date <= now,
            RecurringInvestment.is_active == True,
            (RecurringInvestment.end_date >= now) | (RecurringInvestment.end_date.is_(None))
        ).all()
        
        return due_investments
        
    def process_recurring_investments(self) -> Dict[str, Any]:
        """Process all due recurring investments."""
        results = {
            "total_due": 0,
            "processed": 0,
            "errors": 0,
            "trade_ids": []
        }
        
        due_investments = self.get_due_recurring_investments()
        results["total_due"] = len(due_investments)
        
        for investment in due_investments:
            try:
                # Create trade for the recurring investment
                trade_data = DollarBasedInvestmentCreate(
                    symbol=investment.symbol,
                    investment_amount=float(investment.investment_amount),
                    portfolio_id=investment.portfolio_id,
                    trade_type="buy",  # Recurring investments are always buys
                    note=f"Recurring investment ({investment.frequency.value})"
                )
                
                # Create the trade
                trade = self.create_dollar_based_investment(investment.user_id, trade_data)
                
                # Update trade source to RECURRING
                trade.trade_source = TradeSource.RECURRING
                trade.recurring_investment_id = investment.id
                
                # Update recurring investment
                investment.next_investment_date = self._calculate_next_investment_date(
                    datetime.utcnow(), 
                    investment.frequency
                )
                investment.last_execution_date = datetime.utcnow()
                investment.execution_count = (investment.execution_count or 0) + 1
                
                self.db.commit()
                
                results["processed"] += 1
                results["trade_ids"].append(trade.id)
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error processing recurring investment {investment.id}: {e}")
                results["errors"] += 1
        
        return results