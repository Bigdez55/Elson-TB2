#!/usr/bin/env python
"""
Script to process pending recurring investments.

This script checks for recurring investments that are due to be executed
and creates the corresponding trades. It's designed to be run as a
scheduled job (e.g., daily cron job).
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

try:
    import schedule
    from sqlalchemy.orm import Session
    
    from app.db.database import get_db
    from app.models.trade import Trade, TradeStatus, InvestmentType, OrderType, TradeSource
    from app.models.portfolio import Portfolio
    from app.models.user import User, UserRole
    from app.models.account import RecurringInvestment, RecurringFrequency
    from app.services.market_data import MarketDataService
    from app.services.trading_service import TradingService
    from app.services.broker.factory import get_broker_client
    from app.core.config import settings
    from app.core.logging import setup_logging
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    sys.exit(1)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class RecurringInvestmentProcessor:
    """Processes recurring investments that are due to be executed."""
    
    def __init__(self, db: Session, dry_run: bool = False):
        """Initialize the processor with database session."""
        self.db = db
        self.dry_run = dry_run
        self.market_data = MarketDataService()
        self.trading_service = TradingService(db)
        
        # Get the broker client (only used for validation, not execution)
        self.broker_client = get_broker_client(settings.ACTIVE_BROKER)
        
        # Initialize metrics
        self.stats = {
            "total_processed": 0,
            "successful_trades": 0,
            "skipped_trades": 0,
            "error_count": 0,
            "market_closed_count": 0,
            "pending_approval_count": 0
        }
        
        logger.info(f"RecurringInvestmentProcessor initialized. Dry run: {dry_run}")
    
    def find_due_investments(self) -> List[RecurringInvestment]:
        """Find recurring investments that are due to be executed."""
        now = datetime.utcnow()
        
        try:
            # Find recurring investments where:
            # 1. next_investment_date is in the past
            # 2. end_date is in the future or None
            # 3. is_active is True
            # 4. Include blackout days from metadata
            due_investments = self.db.query(RecurringInvestment).filter(
                RecurringInvestment.next_investment_date <= now,
                RecurringInvestment.is_active == True,
                (RecurringInvestment.end_date >= now) | (RecurringInvestment.end_date.is_(None))
            ).all()
            
            # Further filter based on blackout days in metadata
            filtered_investments = []
            today = now.date()
            day_of_week = today.weekday()  # 0=Monday, 6=Sunday
            day_of_month = today.day
            
            for investment in due_investments:
                # Check for blackout days in metadata
                metadata = investment.metadata or {}
                blackout_days_of_week = metadata.get('blackout_days_of_week', [])
                blackout_days_of_month = metadata.get('blackout_days_of_month', [])
                
                # Skip if today is a blackout day
                if day_of_week in blackout_days_of_week or day_of_month in blackout_days_of_month:
                    logger.info(
                        f"Skipping investment {investment.id} due to blackout day "
                        f"(day of week: {day_of_week}, day of month: {day_of_month})"
                    )
                    continue
                
                filtered_investments.append(investment)
            
            logger.info(
                f"Found {len(due_investments)} recurring investments due for execution, "
                f"{len(filtered_investments)} after applying blackout days"
            )
            return filtered_investments
            
        except Exception as e:
            logger.error(f"Error finding due investments: {e}", exc_info=True)
            return []
    
    def calculate_next_date(self, investment: RecurringInvestment) -> datetime:
        """Calculate the next investment date based on frequency.
        
        Handles specific days of week/month when scheduled in the metadata.
        """
        import calendar
        from dateutil.relativedelta import relativedelta
        
        try:
            today = datetime.utcnow().date()
            next_date = investment.next_investment_date
            
            if next_date.date() < today:
                # If we're behind schedule, use today as the base
                next_date = datetime.combine(today, datetime.min.time())
            
            # Get custom scheduling preferences from metadata
            metadata = investment.metadata or {}
            specific_day = metadata.get('specific_day')
            
            # Check if we should skip weekends
            skip_weekends = metadata.get('skip_weekends', True)
            
            if investment.frequency == RecurringFrequency.DAILY:
                next_date = next_date + timedelta(days=1)
                
                # Skip weekends if specified
                if skip_weekends and next_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                    # Skip to Monday
                    days_to_add = 8 - next_date.weekday()  # 8-6=2 (Sunday->Tuesday), 8-5=3 (Saturday->Tuesday)
                    next_date = next_date + timedelta(days=days_to_add)
                
                return next_date
                
            elif investment.frequency == RecurringFrequency.WEEKLY:
                if specific_day and 0 <= int(specific_day) <= 6:  # 0 = Monday, 6 = Sunday
                    # Calculate next occurrence of specific day
                    target_weekday = int(specific_day)
                    current_weekday = next_date.weekday()
                    days_ahead = (target_weekday - current_weekday) % 7
                    
                    if days_ahead == 0:  # If today is the target day, move to next week
                        days_ahead = 7
                        
                    return next_date + timedelta(days=days_ahead)
                else:
                    # Default to 7 days from now if no specific day
                    return next_date + timedelta(days=7)
                    
            elif investment.frequency == RecurringFrequency.MONTHLY:
                # Use relative delta for accurate month calculations
                next_month = next_date + relativedelta(months=1)
                
                if specific_day:
                    try:
                        target_day = int(specific_day)
                        if 1 <= target_day <= 31:
                            # Calculate the target day in the next month
                            year, month = next_month.year, next_month.month
                            
                            # Check if the day exists in the next month
                            last_day_of_month = calendar.monthrange(year, month)[1]
                            if target_day > last_day_of_month:
                                target_day = last_day_of_month
                                
                            # Create the new date with the specific day
                            next_date = datetime(year, month, target_day)
                            
                            # Skip weekends if specified
                            if skip_weekends and next_date.weekday() >= 5:
                                # Move to previous Friday or next Monday based on metadata preference
                                weekend_handling = metadata.get('weekend_handling', 'previous')
                                if weekend_handling == 'previous':
                                    # Move to previous Friday
                                    days_to_subtract = next_date.weekday() - 4  # 5-4=1 (Sat->Fri), 6-4=2 (Sun->Fri)
                                    next_date = next_date - timedelta(days=days_to_subtract)
                                else:
                                    # Move to next Monday
                                    days_to_add = 7 - next_date.weekday()  # 7-5=2 (Sat->Mon), 7-6=1 (Sun->Mon)
                                    next_date = next_date + timedelta(days=days_to_add)
                            
                            return next_date
                            
                        elif target_day == -1:
                            # Last day of the month
                            year, month = next_month.year, next_month.month
                            last_day = calendar.monthrange(year, month)[1]
                            next_date = datetime(year, month, last_day)
                            
                            # Skip weekends if specified
                            if skip_weekends and next_date.weekday() >= 5:
                                # Last day of month is always moved to previous Friday
                                days_to_subtract = next_date.weekday() - 4
                                next_date = next_date - timedelta(days=days_to_subtract)
                            
                            return next_date
                            
                    except ValueError:
                        logger.warning(f"Invalid specific_day in metadata: {specific_day}")
                
                # Default to same day next month
                next_date = next_month
                
                # Skip weekends if specified
                if skip_weekends and next_date.weekday() >= 5:
                    # Move to previous Friday or next Monday based on metadata preference
                    weekend_handling = metadata.get('weekend_handling', 'previous')
                    if weekend_handling == 'previous':
                        # Move to previous Friday
                        days_to_subtract = next_date.weekday() - 4
                        next_date = next_date - timedelta(days=days_to_subtract)
                    else:
                        # Move to next Monday
                        days_to_add = 7 - next_date.weekday()
                        next_date = next_date + timedelta(days=days_to_add)
                
                return next_date
                
            elif investment.frequency == RecurringFrequency.QUARTERLY:
                # Use relative delta for accurate quarter calculations
                next_quarter = next_date + relativedelta(months=3)
                
                if specific_day:
                    try:
                        target_day = int(specific_day)
                        if 1 <= target_day <= 31:
                            # Calculate the target day in the next quarter
                            year, month = next_quarter.year, next_quarter.month
                            
                            # Check if the day exists in that month
                            last_day_of_month = calendar.monthrange(year, month)[1]
                            if target_day > last_day_of_month:
                                target_day = last_day_of_month
                                
                            # Create the new date with the specific day
                            next_date = datetime(year, month, target_day)
                            
                            # Skip weekends if specified
                            if skip_weekends and next_date.weekday() >= 5:
                                # Move to previous Friday or next Monday based on metadata preference
                                weekend_handling = metadata.get('weekend_handling', 'previous')
                                if weekend_handling == 'previous':
                                    days_to_subtract = next_date.weekday() - 4
                                    next_date = next_date - timedelta(days=days_to_subtract)
                                else:
                                    days_to_add = 7 - next_date.weekday()
                                    next_date = next_date + timedelta(days=days_to_add)
                            
                            return next_date
                            
                        elif target_day == -1:
                            # Last day of the month
                            year, month = next_quarter.year, next_quarter.month
                            last_day = calendar.monthrange(year, month)[1]
                            next_date = datetime(year, month, last_day)
                            
                            # Skip weekends if specified
                            if skip_weekends and next_date.weekday() >= 5:
                                # Last day is always moved to previous Friday
                                days_to_subtract = next_date.weekday() - 4
                                next_date = next_date - timedelta(days=days_to_subtract)
                            
                            return next_date
                            
                    except ValueError:
                        logger.warning(f"Invalid specific_day in metadata: {specific_day}")
                
                # Default to same day in 3 months
                next_date = next_quarter
                
                # Skip weekends if specified
                if skip_weekends and next_date.weekday() >= 5:
                    # Move to previous Friday or next Monday based on metadata preference
                    weekend_handling = metadata.get('weekend_handling', 'previous')
                    if weekend_handling == 'previous':
                        days_to_subtract = next_date.weekday() - 4
                        next_date = next_date - timedelta(days=days_to_subtract)
                    else:
                        days_to_add = 7 - next_date.weekday()
                        next_date = next_date + timedelta(days=days_to_add)
                
                return next_date
                
            else:
                logger.warning(f"Unknown frequency: {investment.frequency}, defaulting to monthly")
                return next_date + relativedelta(months=1)
                
        except Exception as e:
            logger.error(f"Error calculating next date for investment {investment.id}: {e}", exc_info=True)
            # Default to 30 days from now as a safe fallback
            return datetime.utcnow() + timedelta(days=30)
    
    def _check_investment_limits(self, investment: RecurringInvestment, user: User, portfolio: Portfolio) -> bool:
        """
        Check if the investment is within allowed limits.
        
        Args:
            investment: The recurring investment to check
            user: The user who owns the investment
            portfolio: The portfolio for the investment
            
        Returns:
            True if within limits, False otherwise
        """
        # Check portfolio cash balance (only for non-dry-run)
        if not self.dry_run:
            investment_amount = float(investment.investment_amount)
            cash_balance = float(portfolio.cash_balance)
            
            if investment_amount > cash_balance:
                logger.warning(
                    f"Insufficient funds for investment {investment.id}: "
                    f"requires ${investment_amount}, available ${cash_balance}"
                )
                return False
        
        # Check daily investment limit from metadata
        metadata = investment.metadata or {}
        daily_limit = metadata.get('daily_limit')
        
        if daily_limit:
            # Find total amount already invested today for this user
            today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())
            today_trades = self.db.query(Trade).filter(
                Trade.user_id == user.id,
                Trade.trade_source == TradeSource.RECURRING,
                Trade.created_at >= today_start
            ).all()
            
            total_today = sum(float(trade.investment_amount or 0) for trade in today_trades)
            
            if total_today + float(investment.investment_amount) > float(daily_limit):
                logger.warning(
                    f"Daily investment limit reached for user {user.id}: "
                    f"${total_today} already invested, limit is ${daily_limit}"
                )
                return False
        
        # Check monthly investment limit from metadata
        monthly_limit = metadata.get('monthly_limit')
        
        if monthly_limit:
            # Find total amount invested this month for this user
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_trades = self.db.query(Trade).filter(
                Trade.user_id == user.id,
                Trade.trade_source == TradeSource.RECURRING,
                Trade.created_at >= month_start
            ).all()
            
            total_month = sum(float(trade.investment_amount or 0) for trade in month_trades)
            
            if total_month + float(investment.investment_amount) > float(monthly_limit):
                logger.warning(
                    f"Monthly investment limit reached for user {user.id}: "
                    f"${total_month} already invested, limit is ${monthly_limit}"
                )
                return False
        
        return True
    
    def _get_trade_priority(self, investment: RecurringInvestment) -> int:
        """
        Get the priority of the trade (used for ordering execution).
        
        Higher values mean higher priority.
        
        Args:
            investment: The recurring investment
            
        Returns:
            Priority value (integer)
        """
        # Get priority from metadata, or default to medium priority (5)
        metadata = investment.metadata or {}
        return metadata.get('priority', 5)
    
    def execute_investment(self, investment: RecurringInvestment) -> Optional[int]:
        """Execute a single recurring investment by creating a trade."""
        # Start a new session transaction for isolation
        self.db.begin_nested()
        
        try:
            # Verify user and portfolio still exist
            user = self.db.query(User).filter(User.id == investment.user_id).first()
            portfolio = self.db.query(Portfolio).filter(Portfolio.id == investment.portfolio_id).first()
            
            if not user or not portfolio:
                logger.error(f"User {investment.user_id} or portfolio {investment.portfolio_id} not found")
                self.db.rollback()
                return None
            
            # Check investment limits
            if not self._check_investment_limits(investment, user, portfolio):
                logger.warning(f"Investment {investment.id} exceeds limits, skipping")
                self.stats["skipped_trades"] += 1
                
                # Still update the next investment date to avoid repeated failures
                investment.next_investment_date = self.calculate_next_date(investment)
                self.db.commit()
                return None
            
            # Validate the symbol is still tradable
            try:
                current_price = self.market_data.get_current_price(investment.symbol)
                if not current_price or current_price <= 0:
                    logger.error(f"Invalid price {current_price} for {investment.symbol}")
                    self.db.rollback()
                    return None
            except Exception as e:
                logger.error(f"Error getting price for {investment.symbol}: {e}")
                self.db.rollback()
                return None
            
            # Check if market is open
            market_open = self.broker_client.is_market_open()
            if not market_open:
                logger.info(f"Market is closed, queueing trade for next market open")
                self.stats["market_closed_count"] += 1
            
            # Create the trade with proper recurring source tracking
            trade = Trade(
                user_id=investment.user_id,
                portfolio_id=investment.portfolio_id,
                symbol=investment.symbol,
                investment_amount=investment.investment_amount,
                investment_type=InvestmentType.DOLLAR_BASED,
                trade_type="buy",  # Recurring investments are always buys
                order_type=OrderType.MARKET,
                status=TradeStatus.PENDING,
                is_fractional=True,
                trade_source=TradeSource.RECURRING,
                recurring_investment_id=investment.id,
                created_at=datetime.utcnow()
            )
            
            # Additional metadata from the recurring investment
            metadata = investment.metadata or {}
            trade_notes = metadata.get('trade_notes')
            if trade_notes:
                trade.notes = trade_notes
            
            # For minors, set to pending approval
            if user.role == UserRole.MINOR:
                trade.status = TradeStatus.PENDING_APPROVAL
                logger.info(f"Setting minor's trade to pending approval")
                self.stats["pending_approval_count"] += 1
            
            if self.dry_run:
                logger.info(
                    f"DRY RUN: Would create ${investment.investment_amount} recurring "
                    f"investment in {investment.symbol} for user {user.username}"
                )
                self.db.rollback()
                return 0
            
            # Prepare for cash balance update (if market is open)
            if market_open and trade.status != TradeStatus.PENDING_APPROVAL:
                # Reserve the funds by reducing cash balance
                current_cash = float(portfolio.cash_balance)
                investment_amount = float(investment.investment_amount)
                
                if current_cash < investment_amount:
                    logger.error(
                        f"Insufficient funds in portfolio {portfolio.id}: "
                        f"required ${investment_amount}, available ${current_cash}"
                    )
                    self.db.rollback()
                    return None
                
                # Subtract the amount from cash balance
                portfolio.cash_balance = Decimal(str(current_cash - investment_amount))
                self.db.add(portfolio)
            
            # Save the trade
            self.db.add(trade)
            self.db.flush()
            trade_id = trade.id
            
            # Update the recurring investment next date
            investment.next_investment_date = self.calculate_next_date(investment)
            investment.last_execution_date = datetime.utcnow()
            
            # Increment the count
            investment.execution_count = (investment.execution_count or 0) + 1
            self.db.add(investment)
            
            # Commit the nested transaction
            self.db.commit()
            
            logger.info(
                f"Created recurring investment trade {trade_id} for "
                f"${investment.investment_amount} in {investment.symbol} for user {user.id}"
            )
            
            self.stats["successful_trades"] += 1
            return trade_id
        
        except Exception as e:
            logger.error(f"Error executing recurring investment {investment.id}: {str(e)}", exc_info=True)
            self.db.rollback()
            self.stats["error_count"] += 1
            return None
    
    def process_all_due_investments(self) -> Dict[str, Any]:
        """Process all recurring investments that are due to be executed."""
        start_time = datetime.utcnow()
        
        results = {
            "total_due": 0,
            "processed": 0,
            "errors": 0,
            "trade_ids": [],
            "market_closed_count": 0,
            "pending_approval_count": 0,
            "skipped_count": 0
        }
        
        # Clear stats from previous runs
        self.stats = {
            "total_processed": 0,
            "successful_trades": 0,
            "skipped_trades": 0,
            "error_count": 0,
            "market_closed_count": 0,
            "pending_approval_count": 0
        }
        
        try:
            # Find due investments
            due_investments = self.find_due_investments()
            results["total_due"] = len(due_investments)
            
            if not due_investments:
                logger.info("No recurring investments due for execution")
                return results
            
            # Sort investments by priority
            priority_sorted = sorted(
                due_investments, 
                key=self._get_trade_priority, 
                reverse=True  # Higher priority values first
            )
            
            # Process them in order
            for investment in priority_sorted:
                try:
                    self.stats["total_processed"] += 1
                    trade_id = self.execute_investment(investment)
                    
                    if trade_id is not None:
                        results["processed"] += 1
                        results["trade_ids"].append(trade_id)
                except Exception as e:
                    logger.error(f"Unexpected error processing investment {investment.id}: {str(e)}", exc_info=True)
                    results["errors"] += 1
            
            # Update results with stats
            results["market_closed_count"] = self.stats["market_closed_count"]
            results["pending_approval_count"] = self.stats["pending_approval_count"]
            results["skipped_count"] = self.stats["skipped_trades"]
            results["errors"] = self.stats["error_count"]
            results["execution_time"] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Recurring investment processing complete: {results['processed']}/{results['total_due']} "
                f"investments processed with {results['errors']} errors in {results['execution_time']:.2f} seconds"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in process_all_due_investments: {str(e)}", exc_info=True)
            return {
                "total_due": 0,
                "processed": 0,
                "errors": 1,
                "trade_ids": [],
                "error_message": str(e),
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }


def process_recurring_investments(dry_run: bool = False) -> Dict[str, Any]:
    """Process all recurring investments."""
    db = next(get_db())
    try:
        processor = RecurringInvestmentProcessor(db, dry_run)
        results = processor.process_all_due_investments()
        return results
    except Exception as e:
        logger.error(f"Error in process_recurring_investments: {e}")
        return {"error": str(e), "processed": 0, "errors": 1}
    finally:
        db.close()


def job() -> None:
    """Job function to process recurring investments."""
    logger.info("Running recurring investment processing job")
    results = process_recurring_investments(dry_run=DRY_RUN)
    logger.info(f"Job complete: {results}")


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Process recurring investments")
    parser.add_argument("--dry-run", action="store_true", help="Run without executing trades")
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=1440, help="Interval in minutes between runs")
    
    args = parser.parse_args()
    
    global DRY_RUN
    DRY_RUN = args.dry_run
    
    if args.dry_run:
        logger.info("Running in DRY RUN mode, no trades will be executed")
    
    if args.run_once:
        job()
    else:
        logger.info(f"Scheduling job to run every {args.interval} minutes")
        schedule.every(args.interval).minutes.do(job)
        
        # Run immediately
        job()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main()