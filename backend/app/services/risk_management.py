from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio

import numpy as np
from app.core.logging_config import (
    log_risk_event,
    log_system_error,
    LogOperationContext,
)
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.trade import Trade, TradeType, TradeStatus
from app.models.user import User
from app.services.market_data import MarketDataService
# Import canonical RiskLevel from models
from app.models.risk import RiskLevel

logger = logging.getLogger(__name__)


class RiskCheckResult(str, Enum):
    """Results of risk checks."""

    APPROVED = "approved"
    WARNING = "warning"
    REJECTED = "rejected"
    REQUIRES_CONFIRMATION = "requires_confirmation"


@dataclass
class RiskMetrics:
    """Portfolio risk metrics."""

    portfolio_value: float
    daily_var: float  # Value at Risk (95% confidence)
    portfolio_beta: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    concentration_risk: float
    sector_concentration: Dict[str, float]
    largest_position_pct: float
    cash_percentage: float
    leverage_ratio: float


@dataclass
class TradeRiskAssessment:
    """Risk assessment for a trade."""

    trade_id: str
    symbol: str
    risk_level: RiskLevel
    risk_score: float
    check_result: RiskCheckResult
    violations: List[str]
    warnings: List[str]
    impact_analysis: Dict[str, Any]
    recommended_action: str
    max_allowed_quantity: Optional[float]
    metadata: Dict[str, Any]


@dataclass
class PositionRisk:
    """Risk metrics for individual positions."""

    symbol: str
    position_value: float
    position_percentage: float
    daily_var: float
    beta: float
    volatility: float
    correlation_score: float
    sector: str
    risk_contribution: float


class RiskManagementService:
    """
    Comprehensive risk management service for trading platform.

    Provides real-time risk assessment, position sizing, portfolio risk metrics,
    and automated risk controls to prevent excessive losses.
    """

    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService()

        # Risk management configuration
        self.max_position_size_pct = getattr(
            settings, "MAX_POSITION_SIZE_PCT", 0.15
        )  # 15% max per position
        self.max_sector_concentration_pct = getattr(
            settings, "MAX_SECTOR_CONCENTRATION_PCT", 0.30
        )  # 30% max per sector
        self.max_daily_loss_pct = getattr(
            settings, "MAX_DAILY_LOSS_PCT", 0.05
        )  # 5% max daily loss
        self.max_portfolio_leverage = getattr(
            settings, "MAX_PORTFOLIO_LEVERAGE", 2.0
        )  # 2x max leverage
        self.min_cash_percentage = getattr(
            settings, "MIN_CASH_PERCENTAGE", 0.05
        )  # 5% min cash
        self.max_correlation_threshold = getattr(
            settings, "MAX_CORRELATION_THRESHOLD", 0.8
        )  # 80% max correlation

        # User-specific limits (could be based on experience level, account type, etc.)
        self.default_limits = {
            "max_trade_value": 50000.0,  # $50k max per trade
            "max_daily_trades": 20,
            "max_weekly_loss_pct": 0.10,  # 10% max weekly loss
            "required_confirmation_threshold": 10000.0,  # Require confirmation for trades > $10k
        }

    async def assess_trade_risk(
        self,
        user_id: int,
        symbol: str,
        trade_type: TradeType,
        quantity: float,
        price: Optional[float] = None,
        trade_id: Optional[str] = None,
    ) -> TradeRiskAssessment:
        """
        Perform comprehensive risk assessment for a proposed trade.

        Args:
            user_id: User placing the trade
            symbol: Symbol being traded
            trade_type: BUY or SELL
            quantity: Number of shares/units
            price: Price per share (uses current market price if None)
            trade_id: Optional trade ID for tracking

        Returns:
            TradeRiskAssessment with risk level and recommendations
        """
        try:
            # Get current price if not provided
            if price is None:
                price = await self.market_data_service.get_current_price(symbol)
                if not price:
                    return self._create_error_assessment(
                        trade_id or "unknown",
                        symbol,
                        "Unable to get current market price",
                    )

            trade_value = quantity * price

            # Get user portfolio
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.owner_id == user_id).first()
            )
            if not portfolio:
                return self._create_error_assessment(
                    trade_id or "unknown", symbol, "No portfolio found for user"
                )

            # Perform risk checks
            violations = []
            warnings = []
            risk_scores = []

            # 1. Position size check
            (
                position_risk_score,
                position_violations,
                position_warnings,
            ) = await self._check_position_size(
                portfolio, symbol, trade_type, trade_value
            )
            risk_scores.append(position_risk_score)
            violations.extend(position_violations)
            warnings.extend(position_warnings)

            # 2. Portfolio concentration check
            (
                concentration_score,
                conc_violations,
                conc_warnings,
            ) = await self._check_concentration_risk(portfolio, symbol, trade_value)
            risk_scores.append(concentration_score)
            violations.extend(conc_violations)
            warnings.extend(conc_warnings)

            # 3. Daily loss limit check
            (
                daily_loss_score,
                loss_violations,
                loss_warnings,
            ) = await self._check_daily_loss_limits(user_id, trade_value, trade_type)
            risk_scores.append(daily_loss_score)
            violations.extend(loss_violations)
            warnings.extend(loss_warnings)

            # 4. Leverage check
            (
                leverage_score,
                lev_violations,
                lev_warnings,
            ) = await self._check_leverage_limits(portfolio, trade_value, trade_type)
            risk_scores.append(leverage_score)
            violations.extend(lev_violations)
            warnings.extend(lev_warnings)

            # 5. User-specific limits
            (
                user_limit_score,
                user_violations,
                user_warnings,
            ) = await self._check_user_limits(user_id, trade_value)
            risk_scores.append(user_limit_score)
            violations.extend(user_violations)
            warnings.extend(user_warnings)

            # 6. Market volatility check
            (
                volatility_score,
                vol_violations,
                vol_warnings,
            ) = await self._check_market_volatility(symbol, trade_value)
            risk_scores.append(volatility_score)
            violations.extend(vol_violations)
            warnings.extend(vol_warnings)

            # Calculate overall risk score and level
            overall_risk_score = np.mean(risk_scores) if risk_scores else 0.0
            risk_level = self._calculate_risk_level(overall_risk_score)

            # Determine check result and log risk events
            if violations:
                check_result = RiskCheckResult.REJECTED
                recommended_action = "Trade rejected due to risk violations"
                max_allowed_quantity = await self._calculate_max_allowed_quantity(
                    portfolio, symbol, trade_type, price
                )

                # Log risk violation
                log_risk_event(
                    event_type="trade_risk_violation",
                    severity="critical",
                    message=f"Trade rejected: {'; '.join(violations)}",
                    user_id=user_id,
                    portfolio_id=portfolio.id,
                    trade_id=trade_id,
                    risk_score=overall_risk_score,
                    symbol=symbol,
                    trade_value=trade_value,
                    violations=violations,
                )

            elif warnings and overall_risk_score > 0.7:
                check_result = RiskCheckResult.REQUIRES_CONFIRMATION
                recommended_action = (
                    "Trade requires manual confirmation due to high risk"
                )
                max_allowed_quantity = quantity

                # Log high risk trade requiring confirmation
                log_risk_event(
                    event_type="high_risk_trade",
                    severity="warning",
                    message=f"High risk trade requires confirmation: {'; '.join(warnings)}",
                    user_id=user_id,
                    portfolio_id=portfolio.id,
                    trade_id=trade_id,
                    risk_score=overall_risk_score,
                    symbol=symbol,
                    trade_value=trade_value,
                    warnings=warnings,
                )

            elif warnings:
                check_result = RiskCheckResult.WARNING
                recommended_action = "Proceed with caution - risk warnings present"
                max_allowed_quantity = quantity

                # Log risk warnings
                log_risk_event(
                    event_type="trade_risk_warning",
                    severity="info",
                    message=f"Trade warnings: {'; '.join(warnings)}",
                    user_id=user_id,
                    portfolio_id=portfolio.id,
                    trade_id=trade_id,
                    risk_score=overall_risk_score,
                    symbol=symbol,
                    trade_value=trade_value,
                    warnings=warnings,
                )

            else:
                check_result = RiskCheckResult.APPROVED
                recommended_action = "Trade approved"
                max_allowed_quantity = quantity

            # Impact analysis
            impact_analysis = await self._calculate_trade_impact(
                portfolio, symbol, trade_type, quantity, price
            )

            return TradeRiskAssessment(
                trade_id=trade_id
                or f"{symbol}_{trade_type}_{datetime.utcnow().timestamp()}",
                symbol=symbol,
                risk_level=risk_level,
                risk_score=overall_risk_score,
                check_result=check_result,
                violations=violations,
                warnings=warnings,
                impact_analysis=impact_analysis,
                recommended_action=recommended_action,
                max_allowed_quantity=max_allowed_quantity,
                metadata={
                    "trade_value": trade_value,
                    "price_used": price,
                    "individual_risk_scores": {
                        "position_size": position_risk_score,
                        "concentration": concentration_score,
                        "daily_loss": daily_loss_score,
                        "leverage": leverage_score,
                        "user_limits": user_limit_score,
                        "volatility": volatility_score,
                    },
                    "assessment_timestamp": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Risk assessment failed for {symbol}: {e}")
            return self._create_error_assessment(
                trade_id or "unknown", symbol, f"Risk assessment error: {str(e)}"
            )

    async def calculate_portfolio_risk_metrics(self, user_id: int) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a user's portfolio.

        Returns detailed risk analysis including VaR, beta, Sharpe ratio, etc.
        """
        try:
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.owner_id == user_id).first()
            )
            if not portfolio:
                raise ValueError(f"No portfolio found for user {user_id}")

            holdings = (
                self.db.query(Holding)
                .filter(Holding.portfolio_id == portfolio.id)
                .all()
            )
            if not holdings:
                # Empty portfolio - return default metrics
                return RiskMetrics(
                    portfolio_value=portfolio.total_value or 0.0,
                    daily_var=0.0,
                    portfolio_beta=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    volatility=0.0,
                    concentration_risk=0.0,
                    sector_concentration={},
                    largest_position_pct=0.0,
                    cash_percentage=1.0,
                    leverage_ratio=0.0,
                )

            # Get current portfolio value and positions
            portfolio_value = portfolio.total_value or 0.0
            positions = []
            sector_allocation = {}

            for holding in holdings:
                position_value = holding.market_value or 0.0
                position_pct = (
                    position_value / portfolio_value if portfolio_value > 0 else 0.0
                )

                positions.append(
                    {
                        "symbol": holding.symbol,
                        "value": position_value,
                        "percentage": position_pct,
                        "quantity": holding.quantity,
                        "sector": getattr(
                            holding, "sector", "Unknown"
                        ),  # Would need to add sector to Holding model
                    }
                )

                # Sector concentration
                sector = getattr(holding, "sector", "Unknown")
                sector_allocation[sector] = (
                    sector_allocation.get(sector, 0.0) + position_pct
                )

            # Calculate basic portfolio metrics
            largest_position_pct = (
                max([p["percentage"] for p in positions]) if positions else 0.0
            )
            cash_percentage = (
                portfolio.cash_balance / portfolio_value if portfolio_value > 0 else 1.0
            )

            # Calculate concentration risk (Herfindahl index)
            concentration_risk = (
                sum([p["percentage"] ** 2 for p in positions]) if positions else 0.0
            )

            # Get historical data for risk calculations
            symbols = [p["symbol"] for p in positions]
            risk_metrics = await self._calculate_historical_risk_metrics(
                symbols, positions, portfolio_value
            )

            return RiskMetrics(
                portfolio_value=portfolio_value,
                daily_var=risk_metrics.get("daily_var", 0.0),
                portfolio_beta=risk_metrics.get("portfolio_beta", 0.0),
                sharpe_ratio=risk_metrics.get("sharpe_ratio", 0.0),
                max_drawdown=risk_metrics.get("max_drawdown", 0.0),
                volatility=risk_metrics.get("volatility", 0.0),
                concentration_risk=concentration_risk,
                sector_concentration=sector_allocation,
                largest_position_pct=largest_position_pct,
                cash_percentage=cash_percentage,
                leverage_ratio=risk_metrics.get("leverage_ratio", 0.0),
            )

        except Exception as e:
            logger.error(f"Portfolio risk calculation failed for user {user_id}: {e}")
            raise

    async def get_position_risk_analysis(self, user_id: int) -> List[PositionRisk]:
        """
        Get detailed risk analysis for each position in the portfolio.
        """
        try:
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.owner_id == user_id).first()
            )
            if not portfolio:
                return []

            holdings = (
                self.db.query(Holding)
                .filter(Holding.portfolio_id == portfolio.id)
                .all()
            )
            if not holdings:
                return []

            position_risks = []
            portfolio_value = portfolio.total_value or 0.0

            for holding in holdings:
                if holding.quantity <= 0:
                    continue

                position_value = holding.market_value or 0.0
                position_pct = (
                    position_value / portfolio_value if portfolio_value > 0 else 0.0
                )

                # Calculate position-specific risk metrics
                position_risk = await self._calculate_position_risk_metrics(
                    holding.symbol, position_value, position_pct
                )

                position_risks.append(
                    PositionRisk(
                        symbol=holding.symbol,
                        position_value=position_value,
                        position_percentage=position_pct,
                        daily_var=position_risk.get("daily_var", 0.0),
                        beta=position_risk.get("beta", 0.0),
                        volatility=position_risk.get("volatility", 0.0),
                        correlation_score=position_risk.get("correlation_score", 0.0),
                        sector=position_risk.get("sector", "Unknown"),
                        risk_contribution=position_risk.get("risk_contribution", 0.0),
                    )
                )

            # Sort by risk contribution (highest first)
            position_risks.sort(key=lambda x: x.risk_contribution, reverse=True)

            return position_risks

        except Exception as e:
            logger.error(f"Position risk analysis failed for user {user_id}: {e}")
            return []

    async def check_circuit_breakers(self, user_id: int) -> Dict[str, Any]:
        """
        Check if any circuit breakers should be triggered based on portfolio performance.

        Circuit breakers automatically halt trading when losses exceed predefined thresholds.
        """
        try:
            # Get today's trading activity and P&L
            today = datetime.utcnow().date()

            # Calculate daily P&L
            daily_trades = (
                self.db.query(Trade)
                .filter(
                    Trade.portfolio_id.in_(
                        self.db.query(Portfolio.id).filter(
                            Portfolio.owner_id == user_id
                        )
                    ),
                    func.date(Trade.created_at) == today,
                    Trade.status == TradeStatus.FILLED,
                )
                .all()
            )

            daily_pnl = sum(
                [
                    (trade.filled_price - trade.price) * trade.filled_quantity
                    if trade.trade_type == TradeType.SELL
                    else (trade.price - trade.filled_price) * trade.filled_quantity
                    for trade in daily_trades
                    if trade.filled_price and trade.price
                ]
            )

            # Get portfolio value for percentage calculation
            portfolio = (
                self.db.query(Portfolio).filter(Portfolio.owner_id == user_id).first()
            )
            portfolio_value = portfolio.total_value if portfolio else 0.0

            daily_loss_pct = (
                abs(daily_pnl) / portfolio_value
                if portfolio_value > 0 and daily_pnl < 0
                else 0.0
            )

            # Check circuit breakers
            breakers_triggered = []

            # Daily loss limit
            if daily_loss_pct > self.max_daily_loss_pct:
                breakers_triggered.append(
                    {
                        "type": "daily_loss_limit",
                        "threshold": self.max_daily_loss_pct,
                        "current_value": daily_loss_pct,
                        "severity": "critical",
                        "action": "suspend_trading",
                        "message": f"Daily loss limit exceeded: {daily_loss_pct:.2%} > {self.max_daily_loss_pct:.2%}",
                    }
                )

            # Number of trades limit
            if len(daily_trades) > self.default_limits["max_daily_trades"]:
                breakers_triggered.append(
                    {
                        "type": "trade_frequency_limit",
                        "threshold": self.default_limits["max_daily_trades"],
                        "current_value": len(daily_trades),
                        "severity": "warning",
                        "action": "require_confirmation",
                        "message": f"Daily trade limit approached: {len(daily_trades)} trades today",
                    }
                )

            # Weekly loss check
            week_ago = datetime.utcnow() - timedelta(days=7)
            weekly_trades = (
                self.db.query(Trade)
                .filter(
                    Trade.portfolio_id.in_(
                        self.db.query(Portfolio.id).filter(
                            Portfolio.owner_id == user_id
                        )
                    ),
                    Trade.created_at >= week_ago,
                    Trade.status == TradeStatus.FILLED,
                )
                .all()
            )

            weekly_pnl = sum(
                [
                    (trade.filled_price - trade.price) * trade.filled_quantity
                    if trade.trade_type == TradeType.SELL
                    else (trade.price - trade.filled_price) * trade.filled_quantity
                    for trade in weekly_trades
                    if trade.filled_price and trade.price
                ]
            )

            weekly_loss_pct = (
                abs(weekly_pnl) / portfolio_value
                if portfolio_value > 0 and weekly_pnl < 0
                else 0.0
            )

            if weekly_loss_pct > self.default_limits["max_weekly_loss_pct"]:
                breakers_triggered.append(
                    {
                        "type": "weekly_loss_limit",
                        "threshold": self.default_limits["max_weekly_loss_pct"],
                        "current_value": weekly_loss_pct,
                        "severity": "critical",
                        "action": "require_admin_approval",
                        "message": f"Weekly loss limit exceeded: {weekly_loss_pct:.2%} > {self.default_limits['max_weekly_loss_pct']:.2%}",
                    }
                )

            return {
                "user_id": user_id,
                "circuit_breakers_triggered": breakers_triggered,
                "trading_suspended": any(
                    cb["action"] == "suspend_trading" for cb in breakers_triggered
                ),
                "requires_confirmation": any(
                    cb["action"] in ["require_confirmation", "require_admin_approval"]
                    for cb in breakers_triggered
                ),
                "daily_stats": {
                    "trades_count": len(daily_trades),
                    "daily_pnl": daily_pnl,
                    "daily_loss_pct": daily_loss_pct,
                },
                "weekly_stats": {
                    "trades_count": len(weekly_trades),
                    "weekly_pnl": weekly_pnl,
                    "weekly_loss_pct": weekly_loss_pct,
                },
                "check_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Circuit breaker check failed for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "circuit_breakers_triggered": [],
                "trading_suspended": False,
                "requires_confirmation": False,
                "error": str(e),
            }

    # Private helper methods

    async def _check_position_size(
        self,
        portfolio: Portfolio,
        symbol: str,
        trade_type: TradeType,
        trade_value: float,
    ) -> Tuple[float, List[str], List[str]]:
        """Check position size limits."""
        violations = []
        warnings = []
        risk_score = 0.0

        portfolio_value = portfolio.total_value or 0.0
        if portfolio_value == 0:
            return 0.0, [], []

        # Get current position
        current_holding = (
            self.db.query(Holding)
            .filter(Holding.portfolio_id == portfolio.id, Holding.symbol == symbol)
            .first()
        )

        current_position_value = (
            current_holding.market_value if current_holding else 0.0
        )

        # Calculate new position value after trade
        if trade_type == TradeType.BUY:
            new_position_value = current_position_value + trade_value
        else:  # SELL
            new_position_value = max(0, current_position_value - trade_value)

        new_position_pct = new_position_value / portfolio_value

        # Check against limits
        if new_position_pct > self.max_position_size_pct:
            violations.append(
                f"Position size limit exceeded: {new_position_pct:.2%} > {self.max_position_size_pct:.2%}"
            )
            risk_score = 1.0
        elif new_position_pct > self.max_position_size_pct * 0.8:
            warnings.append(
                f"Approaching position size limit: {new_position_pct:.2%} (limit: {self.max_position_size_pct:.2%})"
            )
            risk_score = 0.8
        else:
            risk_score = new_position_pct / self.max_position_size_pct

        return risk_score, violations, warnings

    async def _check_concentration_risk(
        self, portfolio: Portfolio, symbol: str, trade_value: float
    ) -> Tuple[float, List[str], List[str]]:
        """Check portfolio concentration risk."""
        violations = []
        warnings = []
        risk_score = 0.0

        # This would require sector information - simplified for now
        # In a full implementation, you'd check sector concentration

        # Calculate Herfindahl index for concentration
        holdings = (
            self.db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        )
        total_value = portfolio.total_value or 0.0

        if total_value == 0:
            return 0.0, [], []

        concentration_score = sum(
            [
                (holding.market_value / total_value) ** 2
                for holding in holdings
                if holding.market_value
            ]
        )

        # High concentration (>0.5) indicates risk
        if concentration_score > 0.5:
            warnings.append(
                f"High portfolio concentration detected: {concentration_score:.3f}"
            )
            risk_score = min(1.0, concentration_score)
        else:
            risk_score = concentration_score

        return risk_score, violations, warnings

    async def _check_daily_loss_limits(
        self, user_id: int, trade_value: float, trade_type: TradeType
    ) -> Tuple[float, List[str], List[str]]:
        """Check daily loss limits."""
        violations = []
        warnings = []
        risk_score = 0.0

        # This is a simplified check - in practice you'd track unrealized P&L too
        if trade_value > self.default_limits["max_trade_value"]:
            violations.append(
                f"Trade value exceeds limit: ${trade_value:,.2f} > ${self.default_limits['max_trade_value']:,.2f}"
            )
            risk_score = 1.0
        elif trade_value > self.default_limits["max_trade_value"] * 0.8:
            warnings.append(
                f"Large trade value: ${trade_value:,.2f} (limit: ${self.default_limits['max_trade_value']:,.2f})"
            )
            risk_score = 0.8
        else:
            risk_score = trade_value / self.default_limits["max_trade_value"]

        return risk_score, violations, warnings

    async def _check_leverage_limits(
        self, portfolio: Portfolio, trade_value: float, trade_type: TradeType
    ) -> Tuple[float, List[str], List[str]]:
        """Check leverage limits."""
        violations = []
        warnings = []
        risk_score = 0.0

        # Simplified leverage check
        cash_balance = portfolio.cash_balance or 0.0

        if trade_type == TradeType.BUY and trade_value > cash_balance:
            if cash_balance > 0:
                leverage_ratio = trade_value / cash_balance
                if leverage_ratio > self.max_portfolio_leverage:
                    violations.append(
                        f"Leverage limit exceeded: {leverage_ratio:.2f}x > {self.max_portfolio_leverage:.2f}x"
                    )
                    risk_score = 1.0
                else:
                    risk_score = leverage_ratio / self.max_portfolio_leverage
            else:
                violations.append("Insufficient cash balance for trade")
                risk_score = 1.0

        return risk_score, violations, warnings

    async def _check_user_limits(
        self, user_id: int, trade_value: float
    ) -> Tuple[float, List[str], List[str]]:
        """Check user-specific trading limits."""
        violations = []
        warnings = []
        risk_score = 0.0

        # Check if trade requires confirmation
        if trade_value > self.default_limits["required_confirmation_threshold"]:
            warnings.append(
                f"Large trade requires confirmation: ${trade_value:,.2f} > ${self.default_limits['required_confirmation_threshold']:,.2f}"
            )
            risk_score = 0.7

        # Count today's trades
        today = datetime.utcnow().date()
        daily_trades_count = (
            self.db.query(Trade)
            .filter(
                Trade.portfolio_id.in_(
                    self.db.query(Portfolio.id).filter(Portfolio.owner_id == user_id)
                ),
                func.date(Trade.created_at) == today,
            )
            .count()
        )

        if daily_trades_count >= self.default_limits["max_daily_trades"]:
            violations.append(
                f"Daily trade limit exceeded: {daily_trades_count} >= {self.default_limits['max_daily_trades']}"
            )
            risk_score = max(risk_score, 1.0)
        elif daily_trades_count >= self.default_limits["max_daily_trades"] * 0.8:
            warnings.append(
                f"Approaching daily trade limit: {daily_trades_count}/{self.default_limits['max_daily_trades']}"
            )
            risk_score = max(risk_score, 0.8)

        return risk_score, violations, warnings

    async def _check_market_volatility(
        self, symbol: str, trade_value: float
    ) -> Tuple[float, List[str], List[str]]:
        """Check market volatility for additional risk."""
        violations = []
        warnings = []
        risk_score = 0.0

        try:
            # Get recent volatility - this would use historical data
            # For now, return low risk
            risk_score = 0.3

            # In practice, you'd:
            # 1. Get recent price data
            # 2. Calculate volatility
            # 3. Compare to historical norms
            # 4. Adjust risk based on current market conditions

        except Exception as e:
            logger.warning(f"Volatility check failed for {symbol}: {e}")
            risk_score = 0.5  # Default moderate risk if can't determine

        return risk_score, violations, warnings

    def _calculate_risk_level(self, risk_score: float) -> RiskLevel:
        """Calculate risk level from numeric score."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _calculate_max_allowed_quantity(
        self, portfolio: Portfolio, symbol: str, trade_type: TradeType, price: float
    ) -> Optional[float]:
        """Calculate maximum allowed quantity for a trade."""
        try:
            portfolio_value = portfolio.total_value or 0.0
            if portfolio_value == 0:
                return 0.0

            max_position_value = portfolio_value * self.max_position_size_pct

            # Get current position
            current_holding = (
                self.db.query(Holding)
                .filter(Holding.portfolio_id == portfolio.id, Holding.symbol == symbol)
                .first()
            )

            current_position_value = (
                current_holding.market_value if current_holding else 0.0
            )

            if trade_type == TradeType.BUY:
                remaining_capacity = max_position_value - current_position_value
                max_quantity = max(0, remaining_capacity / price)
            else:  # SELL
                max_quantity = current_holding.quantity if current_holding else 0.0

            return max_quantity

        except Exception as e:
            logger.error(f"Max quantity calculation failed: {e}")
            return None

    async def _calculate_trade_impact(
        self,
        portfolio: Portfolio,
        symbol: str,
        trade_type: TradeType,
        quantity: float,
        price: float,
    ) -> Dict[str, Any]:
        """Calculate the impact of a trade on portfolio metrics."""
        try:
            trade_value = quantity * price
            portfolio_value = portfolio.total_value or 0.0

            return {
                "trade_value": trade_value,
                "portfolio_impact_pct": trade_value / portfolio_value
                if portfolio_value > 0
                else 0.0,
                "new_position_size_pct": trade_value / portfolio_value
                if portfolio_value > 0
                else 0.0,
                "estimated_commission": trade_value
                * 0.001,  # 0.1% estimated commission
                "market_impact_estimate": "low",  # Would calculate based on volume/liquidity
                "liquidity_impact": "minimal",
            }

        except Exception as e:
            logger.error(f"Trade impact calculation failed: {e}")
            return {}

    async def _calculate_historical_risk_metrics(
        self, symbols: List[str], positions: List[Dict], portfolio_value: float
    ) -> Dict[str, float]:
        """Calculate risk metrics based on historical data."""
        try:
            # This would fetch historical data and calculate:
            # - Portfolio volatility
            # - Beta relative to market
            # - Value at Risk
            # - Sharpe ratio
            # - Maximum drawdown

            # For now, return placeholder values
            return {
                "daily_var": portfolio_value * 0.02,  # 2% VaR
                "portfolio_beta": 1.0,
                "sharpe_ratio": 0.8,
                "max_drawdown": 0.15,
                "volatility": 0.20,
                "leverage_ratio": 1.0,
            }

        except Exception as e:
            logger.error(f"Historical risk metrics calculation failed: {e}")
            return {}

    async def _calculate_position_risk_metrics(
        self, symbol: str, position_value: float, position_pct: float
    ) -> Dict[str, Any]:
        """Calculate risk metrics for individual position."""
        try:
            # This would calculate position-specific metrics
            # For now, return placeholder values
            return {
                "daily_var": position_value * 0.025,
                "beta": 1.0,
                "volatility": 0.25,
                "correlation_score": 0.5,
                "sector": "Technology",  # Would lookup from asset database
                "risk_contribution": position_pct
                * 0.25,  # Simplified risk contribution
            }

        except Exception as e:
            logger.error(f"Position risk calculation failed for {symbol}: {e}")
            return {}

    def _create_error_assessment(
        self, trade_id: str, symbol: str, error_message: str
    ) -> TradeRiskAssessment:
        """Create error assessment when risk check fails."""
        return TradeRiskAssessment(
            trade_id=trade_id,
            symbol=symbol,
            risk_level=RiskLevel.CRITICAL,
            risk_score=1.0,
            check_result=RiskCheckResult.REJECTED,
            violations=[error_message],
            warnings=[],
            impact_analysis={},
            recommended_action="Trade rejected due to system error",
            max_allowed_quantity=0.0,
            metadata={"error": error_message},
        )


# Alias for backward compatibility
RiskManager = RiskManagementService
