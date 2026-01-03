"""Micro-investing service for managing roundups and micro-investments.

This module provides functionality for handling micro-investments, including:
- Fractional share investments as small as $1
- Transaction roundups (e.g., round $3.75 to $4.00 and invest $0.25)
- Scheduling and aggregating small investments
- Educational content integration
"""

import logging
from decimal import Decimal, ROUND_UP
from typing import List, Dict, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status

from app.models.trade import (
    Trade,
    TradeStatus,
    TradeType,
    InvestmentType,
    TradeSource,
    OrderType,
    RoundupTransaction,
)
from app.models.user import User, UserRole
from app.models.user_settings import UserSettings, RoundupFrequency, MicroInvestTarget
from app.models.portfolio import Portfolio
from app.schemas.micro_invest import (
    RoundupTransactionCreate,
    UserSettingsCreate,
    MicroInvestmentCreate,
    UserSettingsUpdate,
    RoundupTransactionUpdate,
    RoundupSummary,
    MicroInvestStats,
)
from app.services.market_data import MarketDataService
from app.services.trading import TradingService
from app.services.notifications import NotificationService
from app.core.config import settings

logger = logging.getLogger(__name__)


class MicroInvestService:
    """Service for handling micro-investments and roundups."""

    def __init__(
        self,
        db: Session,
        market_data_service: MarketDataService,
        trading_service: TradingService,
        notification_service: NotificationService,
    ):
        """Initialize with required services."""
        self.db = db
        self.market_data = market_data_service
        self.trading = trading_service
        self.notification_service = notification_service

        # Configuration
        self.min_micro_amount = Decimal("0.01")  # Minimum 1 cent for micro-investments
        self.min_roundup_investment = Decimal(
            "1.00"
        )  # Minimum $1 to trigger roundup investment
        self.default_etfs = {
            "conservative": "VTIP",  # Conservative ETF
            "moderate": "VTI",  # Moderate ETF
            "growth": "QQQ",  # Growth ETF
            "aggressive": "ARKK",  # Aggressive ETF
        }

    # User Settings Management

    def get_user_settings(self, user_id: int) -> Optional[UserSettings]:
        """Get user's micro-investing settings."""
        return (
            self.db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        )

    def create_user_settings(self, settings_data: UserSettingsCreate) -> UserSettings:
        """Create micro-investing settings for a user."""
        # Check if user exists
        user = self.db.query(User).filter(User.id == settings_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if settings already exist
        existing_settings = self.get_user_settings(settings_data.user_id)
        if existing_settings:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Settings already exist for this user",
            )

        # Create new settings
        settings = UserSettings(
            user_id=settings_data.user_id,
            micro_investing_enabled=settings_data.micro_investing_enabled,
            roundup_enabled=settings_data.roundup_enabled,
            roundup_multiplier=settings_data.roundup_multiplier,
            roundup_frequency=RoundupFrequency(settings_data.roundup_frequency),
            roundup_threshold=settings_data.roundup_threshold,
            micro_invest_target_type=MicroInvestTarget(
                settings_data.micro_invest_target_type
            ),
            micro_invest_portfolio_id=settings_data.micro_invest_portfolio_id,
            micro_invest_symbol=settings_data.micro_invest_symbol,
            notify_on_roundup=settings_data.notify_on_roundup,
            notify_on_investment=settings_data.notify_on_investment,
            max_weekly_roundup=settings_data.max_weekly_roundup,
            max_monthly_micro_invest=settings_data.max_monthly_micro_invest,
        )

        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def update_user_settings(
        self, user_id: int, settings_data: UserSettingsUpdate
    ) -> UserSettings:
        """Update micro-investing settings for a user."""
        settings = self.get_user_settings(user_id)
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User settings not found"
            )

        # Update only provided fields
        update_data = settings_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            # Handle enum fields
            if key == "roundup_frequency" and value is not None:
                setattr(settings, key, RoundupFrequency(value))
            elif key == "micro_invest_target_type" and value is not None:
                setattr(settings, key, MicroInvestTarget(value))
            else:
                setattr(settings, key, value)

        self.db.commit()
        self.db.refresh(settings)
        return settings

    # Roundup Management

    def process_transaction_for_roundup(
        self, transaction_data: RoundupTransactionCreate
    ) -> RoundupTransaction:
        """Process a financial transaction for roundup and save it."""
        # Get user settings
        settings = self.get_user_settings(transaction_data.user_id)
        if not settings or not settings.roundup_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Roundups not enabled for this user",
            )

        # Create roundup transaction
        roundup = RoundupTransaction(
            user_id=transaction_data.user_id,
            transaction_amount=transaction_data.transaction_amount,
            roundup_amount=transaction_data.roundup_amount,
            transaction_date=datetime.utcnow(),
            description=transaction_data.description,
            source=transaction_data.source,
            status="pending",
        )

        self.db.add(roundup)
        self.db.commit()
        self.db.refresh(roundup)

        # Send notification if enabled
        if settings.notify_on_roundup:
            try:
                self.notification_service.create_notification(
                    user_id=transaction_data.user_id,
                    title="New Roundup Collected",
                    message=f"${roundup.roundup_amount:.2f} was rounded up from your ${roundup.transaction_amount:.2f} transaction.",
                    notification_type="micro_invest",
                    data={"roundup_id": roundup.id},
                )
            except Exception as e:
                logger.error(f"Failed to send roundup notification: {e}")

        # Process roundups if threshold reached
        if settings.roundup_frequency == RoundupFrequency.THRESHOLD:
            self._process_threshold_based_roundups(transaction_data.user_id)

        return roundup

    def calculate_roundup(
        self, transaction_amount: float, multiplier: float = 1.0
    ) -> float:
        """Calculate the roundup amount for a transaction."""
        # Convert to decimal for accurate rounding
        amount = Decimal(str(transaction_amount))

        # Calculate next dollar amount
        next_dollar = amount.quantize(Decimal("1"), rounding=ROUND_UP)

        # Calculate roundup
        roundup = (next_dollar - amount) * Decimal(str(multiplier))

        # Ensure minimum of 1 cent
        if roundup < self.min_micro_amount:
            roundup = self.min_micro_amount

        return float(roundup)

    def get_pending_roundups(
        self, user_id: int
    ) -> Tuple[List[RoundupTransaction], float]:
        """Get pending roundups and total amount for a user."""
        roundups = (
            self.db.query(RoundupTransaction)
            .filter(
                RoundupTransaction.user_id == user_id,
                RoundupTransaction.status == "pending",
            )
            .order_by(RoundupTransaction.transaction_date)
            .all()
        )

        total_amount = sum(r.roundup_amount for r in roundups)

        return roundups, total_amount

    def _process_threshold_based_roundups(
        self, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Process roundups if threshold is reached."""
        settings = self.get_user_settings(user_id)
        if not settings:
            return None

        roundups, total_amount = self.get_pending_roundups(user_id)

        # Check if threshold reached
        if total_amount < settings.roundup_threshold:
            return None

        # Process the roundups
        return self.invest_pending_roundups(user_id)

    def invest_pending_roundups(self, user_id: int) -> Dict[str, Any]:
        """Invest all pending roundups for a user."""
        # Get user settings
        settings = self.get_user_settings(user_id)
        if not settings or not settings.roundup_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Roundups not enabled for this user",
            )

        # Get pending roundups
        roundups, total_amount = self.get_pending_roundups(user_id)

        if not roundups:
            return {"status": "no_pending_roundups", "invested": 0}

        if total_amount < self.min_roundup_investment:
            return {"status": "below_minimum", "amount": total_amount}

        # Get investment target
        symbol, portfolio_id = self._get_investment_target(user_id, settings)

        # Create investment
        try:
            # Create trade directly since we don't have dollar-based investment service
            current_price = self.market_data.get_current_price(symbol)

            # Validate we can calculate a valid share quantity
            if current_price <= 0:
                raise ValueError(f"Invalid price for {symbol}: {current_price}")

            shares = float(total_amount) / current_price

            # Validate that we have a meaningful quantity to trade
            if shares <= 0:
                raise ValueError(
                    f"Investment amount ${total_amount:.2f} too small to purchase any shares of {symbol} at ${current_price:.2f}"
                )

            trade = Trade(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=shares,
                price=current_price,
                investment_amount=float(total_amount),
                investment_type=InvestmentType.ROUNDUP,
                type=TradeType.BUY,
                trade_type=TradeType.BUY,
                side=TradeType.BUY,
                order_type=OrderType.MARKET,
                status=TradeStatus.PENDING,
                is_fractional=True,
                trade_source=TradeSource.ROUNDUP,
                total_amount=float(total_amount),
                notes=f"Roundup investment (${total_amount:.2f})",
            )

            self.db.add(trade)
            self.db.flush()  # Get the trade ID

            # Update trade properties
            trade.investment_type = InvestmentType.ROUNDUP
            trade.trade_source = TradeSource.ROUNDUP
            trade.metadata = {
                "roundup_count": len(roundups),
                "roundup_ids": [r.id for r in roundups],
            }

            # Update roundups
            for roundup in roundups:
                roundup.status = "invested"
                roundup.invested_at = datetime.utcnow()
                roundup.trade_id = trade.id

            self.db.commit()

            # Send notification if enabled
            if settings.notify_on_investment:
                try:
                    self.notification_service.create_notification(
                        user_id=user_id,
                        title="Roundups Invested",
                        message=f"${total_amount:.2f} from {len(roundups)} roundups was invested in {symbol}.",
                        notification_type="micro_invest",
                        data={"trade_id": trade.id},
                    )
                except Exception as e:
                    logger.error(f"Failed to send roundup investment notification: {e}")

            return {
                "status": "success",
                "trade_id": trade.id,
                "amount": total_amount,
                "roundup_count": len(roundups),
                "symbol": symbol,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to invest roundups: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to invest roundups: {str(e)}",
            )

    def _get_investment_target(
        self, user_id: int, settings: UserSettings
    ) -> Tuple[str, int]:
        """Get the symbol and portfolio ID for investment based on settings."""
        if settings.micro_invest_target_type == MicroInvestTarget.SPECIFIC_SYMBOL:
            # Make sure we have a symbol
            if not settings.micro_invest_symbol:
                raise ValueError("Investment symbol not specified in settings")

            # Get default portfolio if not specified
            portfolio_id = settings.micro_invest_portfolio_id
            if not portfolio_id:
                default_portfolio = (
                    self.db.query(Portfolio)
                    .filter(Portfolio.user_id == user_id, Portfolio.is_default)
                    .first()
                )

                if not default_portfolio:
                    raise ValueError("No default portfolio found")

                portfolio_id = default_portfolio.id

            return settings.micro_invest_symbol, portfolio_id

        elif settings.micro_invest_target_type == MicroInvestTarget.SPECIFIC_PORTFOLIO:
            # Make sure we have a portfolio ID
            if not settings.micro_invest_portfolio_id:
                raise ValueError("Investment portfolio not specified in settings")

            # Get portfolio's default symbol or use VTI
            portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.id == settings.micro_invest_portfolio_id)
                .first()
            )

            if not portfolio:
                raise ValueError("Portfolio not found")

            # Use portfolio's primary ETF or default to VTI
            symbol = getattr(portfolio, "primary_etf", "VTI")

            return symbol, settings.micro_invest_portfolio_id

        elif settings.micro_invest_target_type == MicroInvestTarget.RECOMMENDED_ETF:
            # Get user's risk profile or default to moderate
            user = self.db.query(User).filter(User.id == user_id).first()
            risk_profile = getattr(user, "risk_profile", "moderate")

            # Get appropriate ETF
            symbol = self.default_etfs.get(risk_profile, "VTI")

            # Get default portfolio
            default_portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.user_id == user_id, Portfolio.is_default)
                .first()
            )

            if not default_portfolio:
                raise ValueError("No default portfolio found")

            return symbol, default_portfolio.id

        else:  # Default portfolio
            default_portfolio = (
                self.db.query(Portfolio)
                .filter(Portfolio.user_id == user_id, Portfolio.is_default)
                .first()
            )

            if not default_portfolio:
                raise ValueError("No default portfolio found")

            # Use default ETF
            symbol = "VTI"

            return symbol, default_portfolio.id

    # Scheduled Processing

    def process_scheduled_roundups(self) -> Dict[str, Any]:
        """Process scheduled roundups based on frequency.

        Includes idempotency checks to prevent double-processing on the same day.
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        result = {
            "daily": 0,
            "weekly": 0,
            "threshold": 0,
            "total_invested": 0,
            "errors": 0,
            "skipped_already_processed": 0,
        }

        # Get all users with enabled roundups
        users_with_roundups = (
            self.db.query(UserSettings)
            .filter(
                UserSettings.roundup_enabled,
                UserSettings.micro_investing_enabled,
            )
            .all()
        )

        for settings in users_with_roundups:
            try:
                process_now = False

                # Check if we should process based on frequency
                if settings.roundup_frequency == RoundupFrequency.DAILY:
                    process_now = True

                elif settings.roundup_frequency == RoundupFrequency.WEEKLY:
                    # Process on Monday
                    if now.weekday() == 0:  # Monday
                        process_now = True

                elif settings.roundup_frequency == RoundupFrequency.THRESHOLD:
                    # Check if threshold reached
                    _, total_amount = self.get_pending_roundups(settings.user_id)
                    if total_amount >= settings.roundup_threshold:
                        process_now = True

                # Idempotency check: Skip if already processed today for daily/weekly
                if process_now and settings.roundup_frequency in [RoundupFrequency.DAILY, RoundupFrequency.WEEKLY]:
                    # Check if we already have an invested roundup today for this user
                    already_processed = (
                        self.db.query(RoundupTransaction)
                        .filter(
                            RoundupTransaction.user_id == settings.user_id,
                            RoundupTransaction.status == "invested",
                            RoundupTransaction.invested_at >= today_start,
                        )
                        .first()
                    )

                    if already_processed:
                        logger.info(
                            f"Skipping user {settings.user_id}: already processed roundups today"
                        )
                        result["skipped_already_processed"] += 1
                        continue

                # Process if needed
                if process_now:
                    investment_result = self.invest_pending_roundups(settings.user_id)

                    if investment_result.get("status") == "success":
                        result[settings.roundup_frequency.value] += 1
                        result["total_invested"] += investment_result.get("amount", 0)

            except Exception as e:
                logger.error(
                    f"Error processing roundups for user {settings.user_id}: {e}"
                )
                result["errors"] += 1

        return result

    # Statistics and Reporting

    def get_roundup_summary(self, user_id: int) -> RoundupSummary:
        """Get summary statistics for a user's roundups."""
        # Total roundups
        total_count = (
            self.db.query(func.count(RoundupTransaction.id))
            .filter(RoundupTransaction.user_id == user_id)
            .scalar()
            or 0
        )

        # Total amount
        total_amount = (
            self.db.query(func.sum(RoundupTransaction.roundup_amount))
            .filter(RoundupTransaction.user_id == user_id)
            .scalar()
            or 0
        )

        # Pending amount
        pending_amount = (
            self.db.query(func.sum(RoundupTransaction.roundup_amount))
            .filter(
                RoundupTransaction.user_id == user_id,
                RoundupTransaction.status == "pending",
            )
            .scalar()
            or 0
        )

        # Invested amount
        invested_amount = (
            self.db.query(func.sum(RoundupTransaction.roundup_amount))
            .filter(
                RoundupTransaction.user_id == user_id,
                RoundupTransaction.status == "invested",
            )
            .scalar()
            or 0
        )

        # Total investments
        total_investments = (
            self.db.query(func.count(RoundupTransaction.trade_id.distinct()))
            .filter(
                RoundupTransaction.user_id == user_id,
                RoundupTransaction.status == "invested",
            )
            .scalar()
            or 0
        )

        # Last investment date
        last_investment = (
            self.db.query(RoundupTransaction)
            .filter(
                RoundupTransaction.user_id == user_id,
                RoundupTransaction.status == "invested",
            )
            .order_by(desc(RoundupTransaction.invested_at))
            .first()
        )

        last_investment_date = last_investment.invested_at if last_investment else None

        return RoundupSummary(
            total_roundups=total_count,
            total_amount=float(total_amount),
            pending_amount=float(pending_amount),
            invested_amount=float(invested_amount),
            total_investments=total_investments,
            last_investment_date=last_investment_date,
        )

    def get_micro_invest_statistics(self, user_id: int) -> MicroInvestStats:
        """Get comprehensive statistics for a user's micro-investing activity."""
        # Get total micro-invested
        total_invested = (
            self.db.query(func.sum(Trade.investment_amount))
            .filter(
                Trade.user_id == user_id,
                Trade.investment_type.in_(
                    [InvestmentType.MICRO, InvestmentType.ROUNDUP]
                ),
                Trade.status != TradeStatus.CANCELED,
            )
            .scalar()
            or 0
        )

        # Total transactions
        total_transactions = (
            self.db.query(func.count(Trade.id))
            .filter(
                Trade.user_id == user_id,
                Trade.investment_type.in_(
                    [InvestmentType.MICRO, InvestmentType.ROUNDUP]
                ),
                Trade.status != TradeStatus.CANCELED,
            )
            .scalar()
            or 0
        )

        # Average transaction
        avg_transaction = (
            total_invested / total_transactions if total_transactions > 0 else 0
        )

        # Roundup specific stats
        total_roundups = (
            self.db.query(func.count(RoundupTransaction.id))
            .filter(RoundupTransaction.user_id == user_id)
            .scalar()
            or 0
        )

        total_roundup_amount = (
            self.db.query(func.sum(RoundupTransaction.roundup_amount))
            .filter(
                RoundupTransaction.user_id == user_id,
                RoundupTransaction.status == "invested",
            )
            .scalar()
            or 0
        )

        # This month
        this_month_start = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        this_month_invested = (
            self.db.query(func.sum(Trade.investment_amount))
            .filter(
                Trade.user_id == user_id,
                Trade.investment_type.in_(
                    [InvestmentType.MICRO, InvestmentType.ROUNDUP]
                ),
                Trade.status != TradeStatus.CANCELED,
                Trade.created_at >= this_month_start,
            )
            .scalar()
            or 0
        )

        this_month_count = (
            self.db.query(func.count(Trade.id))
            .filter(
                Trade.user_id == user_id,
                Trade.investment_type.in_(
                    [InvestmentType.MICRO, InvestmentType.ROUNDUP]
                ),
                Trade.status != TradeStatus.CANCELED,
                Trade.created_at >= this_month_start,
            )
            .scalar()
            or 0
        )

        # Last month
        last_month_end = this_month_start - timedelta(seconds=1)
        last_month_start = (this_month_start - timedelta(days=30)).replace(day=1)

        last_month_invested = (
            self.db.query(func.sum(Trade.investment_amount))
            .filter(
                Trade.user_id == user_id,
                Trade.investment_type.in_(
                    [InvestmentType.MICRO, InvestmentType.ROUNDUP]
                ),
                Trade.status != TradeStatus.CANCELED,
                Trade.created_at >= last_month_start,
                Trade.created_at <= last_month_end,
            )
            .scalar()
            or 0
        )

        last_month_count = (
            self.db.query(func.count(Trade.id))
            .filter(
                Trade.user_id == user_id,
                Trade.investment_type.in_(
                    [InvestmentType.MICRO, InvestmentType.ROUNDUP]
                ),
                Trade.status != TradeStatus.CANCELED,
                Trade.created_at >= last_month_start,
                Trade.created_at <= last_month_end,
            )
            .scalar()
            or 0
        )

        return MicroInvestStats(
            total_micro_invested=float(total_invested),
            total_transactions=total_transactions,
            average_transaction=float(avg_transaction),
            total_roundups=total_roundups,
            total_roundup_amount=float(total_roundup_amount),
            this_month={
                "invested": float(this_month_invested),
                "count": this_month_count,
            },
            last_month={
                "invested": float(last_month_invested),
                "count": last_month_count,
            },
        )

    # Direct Micro-Investments

    def create_micro_investment(
        self, user_id: int, investment_data: MicroInvestmentCreate
    ) -> Trade:
        """Create a small dollar-based investment (as low as $0.01)."""
        # Verify user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Verify micro-investing is enabled
        settings = self.get_user_settings(user_id)
        if not settings or not settings.micro_investing_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Micro-investing not enabled for this user",
            )

        # Verify portfolio exists and belongs to user
        portfolio = (
            self.db.query(Portfolio)
            .filter(Portfolio.id == investment_data.portfolio_id)
            .first()
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found"
            )

        # Either the portfolio should belong to the user directly or the user should be the guardian
        if portfolio.user_id != user_id and portfolio.guardian_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access to portfolio",
            )

        # Validate investment amount
        investment_amount = Decimal(str(investment_data.investment_amount))
        if investment_amount < self.min_micro_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Investment amount must be at least ${self.min_micro_amount}",
            )

        try:
            # Get current price
            current_price = Decimal(
                str(self.market_data.get_current_price(investment_data.symbol))
            )
        except Exception as e:
            logger.error(
                f"Failed to get current price for {investment_data.symbol}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to get current price for {investment_data.symbol}",
            )

        # Minor needs guardian approval
        needs_approval = user.role == UserRole.MINOR
        initial_status = (
            TradeStatus.PENDING_APPROVAL if needs_approval else TradeStatus.PENDING
        )

        # Create the trade record
        trade = Trade(
            user_id=user_id,
            portfolio_id=investment_data.portfolio_id,
            symbol=investment_data.symbol,
            quantity=None,  # Not determined yet
            price=current_price,  # Current price for reference
            investment_amount=investment_amount,
            investment_type=InvestmentType.MICRO,
            type=TradeType.BUY,
            order_type=OrderType.MARKET,
            status=initial_status,
            is_fractional=True,
            trade_source=TradeSource.MICRO_DEPOSIT,
            total_amount=investment_amount,
            created_at=datetime.utcnow(),
        )

        self.db.add(trade)
        self.db.commit()
        self.db.refresh(trade)

        return trade
