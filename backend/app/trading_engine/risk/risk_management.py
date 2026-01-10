import enum
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.account import Account, AccountType
from app.models.portfolio import Portfolio
from app.models.holding import Position
from app.models.trade import Trade, TradeStatus
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class RiskProfile(str, enum.Enum):
    """Risk profiles for portfolios"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class RiskCheckResult:
    def __init__(self, approved: bool, reason: Optional[str] = None):
        self.approved = approved
        self.reason = reason


class RiskManager:
    """
    Handles risk management for all trades, with special handling for minor accounts.
    Integrates with the trading engine's risk management system.
    """

    # Default allowed symbols for minors (this would be expanded/managed via admin)
    ALLOWED_SYMBOLS_MINORS = {
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "SPY",
        "VTI",
        "VOO",
        "QQQ",
        "VXUS",
        "BND",
        "AGG",
        "VB",
        "IJR",
    }

    # Risk profile mapping by age
    AGE_RISK_PROFILE_MAP = {
        # Under 13: Conservative
        range(0, 13): RiskProfile.CONSERVATIVE,
        # 13-17: Moderate
        range(13, 18): RiskProfile.MODERATE,
        # 18+: Aggressive (default for adults)
        range(18, 100): RiskProfile.AGGRESSIVE,
    }

    def __init__(self, db: Session):
        self.db = db
        self.config_dir = os.path.join(
            os.path.dirname(__file__), "../../../trading_engine/config"
        )
        # Cache for risk profile configurations
        self.risk_profiles = self._load_risk_profiles()

    def _load_risk_profiles(self) -> Dict[str, Dict]:
        """Load risk profiles from YAML configuration files"""
        profiles = {}
        for profile in RiskProfile:
            if profile == RiskProfile.CUSTOM:
                continue

            config_file = os.path.join(
                self.config_dir, f"{profile.value}_risk_profile.yaml"
            )
            if os.path.exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        profiles[profile.value] = yaml.safe_load(f)
                    logger.info(f"Loaded risk profile: {profile.value}")
                except Exception as e:
                    logger.error(
                        f"Error loading risk profile {profile.value}: {str(e)}"
                    )
                    profiles[profile.value] = {}
            else:
                logger.warning(f"Risk profile file not found: {config_file}")
                profiles[profile.value] = {}

        return profiles

    def get_user_risk_profile(self, user: User) -> RiskProfile:
        """
        Determine the appropriate risk profile for a user based on age and account type.
        """
        # Default to moderate for all users
        profile = RiskProfile.MODERATE

        # If user has a birthdate, determine profile based on age
        if user.birthdate:
            today = date.today()
            age = (
                today.year
                - user.birthdate.year
                - (
                    (today.month, today.day)
                    < (user.birthdate.month, user.birthdate.day)
                )
            )

            # Find the age range that applies
            for age_range, risk_profile in self.AGE_RISK_PROFILE_MAP.items():
                if age in age_range:
                    profile = risk_profile
                    break

        # Minors always use more conservative profiles regardless of age
        if user.role == UserRole.MINOR:
            # Ensure minors never get aggressive profiles
            if profile == RiskProfile.AGGRESSIVE:
                profile = RiskProfile.MODERATE

        return profile

    def get_profile_param(self, user: User, param_path: str) -> Any:
        """
        Get a risk parameter for a specific user based on their risk profile

        Args:
            user: User object
            param_path: Parameter path (e.g., 'position_sizing.max_position_size')

        Returns:
            Parameter value or None if not found
        """
        profile = self.get_user_risk_profile(user)
        profile_key = profile.value

        if profile_key not in self.risk_profiles:
            logger.warning(f"Risk profile {profile_key} not found, using moderate")
            profile_key = RiskProfile.MODERATE.value

        # Navigate the parameter path
        parts = param_path.split(".")
        config = self.risk_profiles.get(profile_key, {})

        try:
            for part in parts:
                config = config[part]
            return config
        except (KeyError, TypeError):
            logger.warning(f"Parameter {param_path} not found in {profile_key} profile")
            return None

    def check_trade(self, user_id: int, trade: Trade) -> RiskCheckResult:
        """
        Main method to check if a trade passes all risk checks.
        Returns a RiskCheckResult object with approval status and reason if rejected.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return RiskCheckResult(False, "User not found")

        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        )
        if not portfolio:
            return RiskCheckResult(False, "Portfolio not found")

        # Run all relevant checks
        symbol_check = self.check_allowed_symbols(user, trade.symbol)
        if not symbol_check.approved:
            return symbol_check

        position_limit_check = self.check_position_limits(user, portfolio, trade)
        if not position_limit_check.approved:
            return position_limit_check

        # Check age-based risk limits
        risk_limit_check = self.check_risk_profile_limits(user, portfolio, trade)
        if not risk_limit_check.approved:
            return risk_limit_check

        # Add more checks as needed:
        # - Day trade limits
        # - Market hours checks
        # - Options trading restrictions for minors
        # - etc.

        return RiskCheckResult(True)

    def check_allowed_symbols(self, user: User, symbol: str) -> RiskCheckResult:
        """
        Check if the symbol is allowed for the user based on their role and risk profile.
        Adults can trade anything, minors are restricted to a safe list.
        Additionally checks against restricted assets in the risk profile.
        """
        # For minors, check against the allowed symbols list
        if user.role == UserRole.MINOR and symbol not in self.ALLOWED_SYMBOLS_MINORS:
            return RiskCheckResult(
                False,
                f"Symbol {symbol} is not allowed for minors. Please choose from the approved list.",
            )

        # Check restricted assets from the risk profile
        restricted_assets = (
            self.get_profile_param(user, "trade_limitations.restricted_assets") or []
        )

        # This is a simplified check - in a real implementation we would have
        # a way to map symbols to asset classes (options, futures, leveraged ETFs, etc.)
        # For now, let's assume we can simply check if the symbol contains indicator strings
        is_option = "OPTION_" in symbol
        is_future = "FUT_" in symbol
        is_leveraged_etf = any(
            x in symbol for x in ["2X", "3X", "BULL", "BEAR", "INVERSE"]
        )
        is_crypto = symbol.startswith("CRYPTO_") or symbol in ["BTC", "ETH", "LTC"]

        # Check if any of these asset classes are restricted
        if (
            (is_option and "options" in restricted_assets)
            or (is_future and "futures" in restricted_assets)
            or (is_leveraged_etf and "leveraged_etfs" in restricted_assets)
            or (is_crypto and "crypto" in restricted_assets)
        ):
            profile = self.get_user_risk_profile(user)
            return RiskCheckResult(
                False,
                f"This asset type is restricted by your {profile.value} risk profile.",
            )

        return RiskCheckResult(True)

    def check_position_limits(
        self, user: User, portfolio: Portfolio, trade: Trade
    ) -> RiskCheckResult:
        """
        Check if the trade would exceed position limits relative to the portfolio.
        Limits are based on the user's risk profile.
        """
        # Get current position if it exists
        current_position = 0
        current_value = 0

        # Find the position in the detailed positions
        position = (
            self.db.query(Position)
            .filter(
                Position.portfolio_id == portfolio.id, Position.symbol == trade.symbol
            )
            .first()
        )

        if position:
            current_position = position.quantity
            current_value = position.quantity * position.current_price

        # Calculate new position after trade
        new_position = current_position
        if trade.trade_type.lower() == "buy":
            new_position += trade.quantity
        else:  # Sell
            new_position -= trade.quantity

            # Can't sell more than you have
            if new_position < 0:
                return RiskCheckResult(
                    False,
                    f"Insufficient shares to sell. You have {current_position} shares.",
                )

        # Calculate new position value
        new_position_value = new_position * trade.price

        # Skip concentration check if portfolio total value is too small
        if portfolio.total_value < 1000:
            return RiskCheckResult(True)

        # Get max position size from risk profile
        max_position_size = self.get_profile_param(
            user, "position_sizing.max_position_size"
        )
        if max_position_size is None:
            # Fall back to defaults if not found in profile
            max_position_size = 0.10 if user.role == UserRole.ADULT else 0.05

        # Convert to percentage for easier comparison
        max_position_pct = max_position_size  # Already a decimal, e.g., 0.10 = 10%

        # Calculate position percentage
        new_portfolio_value = portfolio.total_value - current_value + new_position_value
        position_pct = (
            new_position_value / new_portfolio_value if new_portfolio_value > 0 else 0
        )

        if position_pct > max_position_pct:
            max_allowed = max_position_pct * 100
            actual_pct = position_pct * 100
            profile = self.get_user_risk_profile(user)
            return RiskCheckResult(
                False,
                f"Position would be {actual_pct:.1f}% of portfolio. "
                f"Maximum allowed is {max_allowed:.1f}% for your {profile.value} risk profile.",
            )

        return RiskCheckResult(True)

    def check_risk_profile_limits(
        self, user: User, portfolio: Portfolio, trade: Trade
    ) -> RiskCheckResult:
        """
        Check various limits from the risk profile:
        - Max trades per day
        - Minimum holding period
        - Portfolio exposure limits
        """
        # Get max trades per day from risk profile
        max_trades_per_day = self.get_profile_param(
            user, "trade_limitations.max_trades_per_day"
        )
        if max_trades_per_day is not None:
            # Count trades made today
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_trades = (
                self.db.query(Trade)
                .filter(Trade.user_id == user.id, Trade.created_at >= today_start)
                .count()
            )

            if today_trades >= max_trades_per_day:
                profile = self.get_user_risk_profile(user)
                return RiskCheckResult(
                    False,
                    f"You've reached the maximum of {max_trades_per_day} trades per day "
                    f"for your {profile.value} risk profile.",
                )

        # Check if selling a recently purchased position
        min_holding_period_days = self.get_profile_param(
            user, "trade_limitations.min_holding_period_days"
        )
        if min_holding_period_days is not None and trade.trade_type.lower() == "sell":
            # Find when this position was acquired
            most_recent_buy = (
                self.db.query(Trade)
                .filter(
                    Trade.user_id == user.id,
                    Trade.symbol == trade.symbol,
                    Trade.trade_type.ilike("buy"),
                    Trade.status == TradeStatus.COMPLETED,
                )
                .order_by(Trade.created_at.desc())
                .first()
            )

            if most_recent_buy:
                holding_days = (datetime.now() - most_recent_buy.created_at).days
                if holding_days < min_holding_period_days:
                    profile = self.get_user_risk_profile(user)
                    return RiskCheckResult(
                        False,
                        f"Minimum holding period is {min_holding_period_days} days for your "
                        f"{profile.value} risk profile. You've held this position for {holding_days} days.",
                    )

        return RiskCheckResult(True)


# Enhanced portfolio risk assessment


def calculate_portfolio_volatility(portfolio: Portfolio) -> float:
    """
    Calculate the portfolio volatility based on position weights and historical data.
    This is a placeholder that would be implemented with real market data.
    """
    # In a real implementation, this would use historical price data and correlation matrix
    # For now, estimate based on position count as a simple proxy
    position_count = (
        len(portfolio.positions_detail) if portfolio.positions_detail else 0
    )

    # Simple estimation - more positions generally means lower volatility due to diversification
    if position_count == 0:
        return 0.0
    elif position_count == 1:
        return 0.25  # Single position - high volatility
    elif position_count <= 3:
        return 0.20
    elif position_count <= 7:
        return 0.15
    elif position_count <= 15:
        return 0.12
    else:
        return 0.10  # Well-diversified


def calculate_portfolio_risk_metrics(
    portfolio: Portfolio, risk_profile: Optional[RiskProfile] = None
) -> Dict[str, float]:
    """
    Calculate comprehensive risk metrics for a portfolio.
    Optionally compare against a target risk profile.
    Returns a dictionary of risk metrics.
    """
    # Initialize metrics
    metrics = {
        "diversification_score": 0.0,
        "volatility": 0.0,
        "beta": 1.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "value_at_risk": 0.0,
        "expected_return": 0.0,
        "risk_rating": 5.0,  # Scale of 1-10
    }

    # Get position count
    position_count = (
        len(portfolio.positions_detail) if portfolio.positions_detail else 0
    )

    # Simple diversification score based on number of positions
    if position_count <= 1:
        metrics["diversification_score"] = 0.1
    elif position_count <= 3:
        metrics["diversification_score"] = 0.3
    elif position_count <= 7:
        metrics["diversification_score"] = 0.6
    elif position_count <= 15:
        metrics["diversification_score"] = 0.8
    else:
        metrics["diversification_score"] = 0.9

    # Calculate volatility
    metrics["volatility"] = calculate_portfolio_volatility(portfolio)

    # Estimate other metrics based on volatility and diversification
    metrics["beta"] = metrics["volatility"] / 0.15  # Assuming market volatility of 15%
    metrics["max_drawdown"] = metrics["volatility"] * 2  # Rough estimate
    metrics["value_at_risk"] = metrics["volatility"] * 1.65  # 95% VaR approximation

    # Estimate Sharpe ratio (assuming 2% risk-free rate and 8% expected return)
    risk_free_rate = 0.02
    expected_return = 0.08
    metrics["expected_return"] = expected_return

    if metrics["volatility"] > 0:
        metrics["sharpe_ratio"] = (expected_return - risk_free_rate) / metrics[
            "volatility"
        ]
    else:
        metrics["sharpe_ratio"] = 0

    # Calculate an overall risk rating on a scale of 1-10
    # Higher is riskier
    metrics["risk_rating"] = min(10, max(1, 5 * metrics["volatility"] / 0.15))

    return metrics


def get_risk_profile_report(
    user: User, portfolio: Portfolio, risk_manager: RiskManager
) -> Dict:
    """
    Generate a comprehensive risk report comparing the portfolio's risk
    to the user's risk profile.
    """
    # Get user's risk profile
    profile = risk_manager.get_user_risk_profile(user)

    # Calculate portfolio risk metrics
    metrics = calculate_portfolio_risk_metrics(portfolio)

    # Get risk profile limits
    max_volatility = (
        risk_manager.get_profile_param(
            user, "volatility_limits.max_portfolio_volatility"
        )
        or 0.15
    )
    max_drawdown = (
        risk_manager.get_profile_param(user, "drawdown_limits.max_total_drawdown")
        or 0.12
    )

    # Check if portfolio is within profile limits
    is_within_volatility = metrics["volatility"] <= max_volatility
    is_within_drawdown = metrics["max_drawdown"] <= max_drawdown

    # Generate warnings
    warnings = []
    if not is_within_volatility:
        warnings.append(
            f"Portfolio volatility of {metrics['volatility']*100:.1f}% exceeds the "
            f"{profile.value} profile limit of {max_volatility*100:.1f}%"
        )
    if not is_within_drawdown:
        warnings.append(
            f"Portfolio potential drawdown of {metrics['max_drawdown']*100:.1f}% exceeds the "
            f"{profile.value} profile limit of {max_drawdown*100:.1f}%"
        )

    return {
        "user_id": user.id,
        "risk_profile": profile.value,
        "portfolio_id": portfolio.id,
        "metrics": metrics,
        "limits": {"max_volatility": max_volatility, "max_drawdown": max_drawdown},
        "is_compliant": is_within_volatility and is_within_drawdown,
        "warnings": warnings,
        "recommendations": generate_risk_recommendations(
            user, portfolio, metrics, profile, risk_manager
        ),
    }


def generate_risk_recommendations(
    user: User,
    portfolio: Portfolio,
    metrics: Dict[str, float],
    profile: RiskProfile,
    risk_manager: RiskManager,
) -> List[str]:
    """
    Generate tailored recommendations to improve the portfolio's risk profile.
    """
    recommendations = []

    # Get risk profile parameters
    max_volatility = (
        risk_manager.get_profile_param(
            user, "volatility_limits.max_portfolio_volatility"
        )
        or 0.15
    )
    max_position_size = (
        risk_manager.get_profile_param(user, "position_sizing.max_position_size")
        or 0.10
    )
    min_cash_allocation = (
        risk_manager.get_profile_param(user, "exposure_limits.min_cash_allocation")
        or 0.05
    )

    # Check diversification
    if metrics["diversification_score"] < 0.5:
        if len(portfolio.positions_detail) <= 3:
            recommendations.append(
                "Increase portfolio diversification by adding more positions across different sectors. "
                "Consider adding index ETFs for broad market exposure."
            )

    # Check volatility
    if metrics["volatility"] > max_volatility:
        recommendations.append(
            f"Reduce portfolio volatility by replacing volatile positions with more stable investments. "
            f"Consider adding bonds or dividend-focused stocks."
        )

    # Check for over-concentrated positions
    for position in portfolio.positions_detail:
        position_size = position.quantity * position.current_price
        position_pct = (
            position_size / portfolio.total_value if portfolio.total_value else 0
        )

        if position_pct > max_position_size:
            recommendations.append(
                f"Reduce exposure to {position.symbol} from {position_pct*100:.1f}% to under "
                f"{max_position_size*100:.1f}% to align with your {profile.value} risk profile."
            )

    # Check cash allocation
    cash_position = next(
        (p for p in portfolio.positions_detail if p.symbol == "CASH"), None
    )
    cash_pct = 0
    if cash_position:
        cash_pct = (
            cash_position.quantity / portfolio.total_value
            if portfolio.total_value
            else 0
        )

    if cash_pct < min_cash_allocation:
        recommendations.append(
            f"Increase cash allocation from {cash_pct*100:.1f}% to at least {min_cash_allocation*100:.1f}% "
            f"to provide flexibility and reduce overall portfolio risk."
        )

    # Add educational recommendations for minors
    if user.role == UserRole.MINOR:
        recommendations.append(
            "Consider adding educational ETFs to your portfolio to learn about different sectors "
            "and investment strategies while maintaining a conservative risk profile."
        )

    return recommendations


class RiskManagementService:
    """
    High-level service for handling risk management across the application.
    Provides a facade over the RiskManager class with additional features.
    """

    def __init__(self, db: Session):
        """Initialize risk management service with a database session."""
        self.db = db
        self.risk_manager = RiskManager(db)

    def check_trade(self, user_id: int, trade: Trade) -> Tuple[bool, Optional[str]]:
        """
        Check if a trade passes all risk management checks.

        Returns:
            Tuple of (is_approved, reason_if_rejected)
        """
        result = self.risk_manager.check_trade(user_id, trade)
        return result.approved, result.reason

    def get_risk_profile(self, user_id: int) -> RiskProfile:
        """Get the risk profile for a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return RiskProfile.MODERATE  # Default to moderate if user not found

        return self.risk_manager.get_user_risk_profile(user)

    def get_portfolio_risk_assessment(
        self, user_id: int, portfolio_id: int
    ) -> Dict[str, Any]:
        """
        Get a comprehensive risk assessment for a portfolio.

        Returns:
            Dictionary with risk metrics, compliance status, and recommendations
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        )

        if not user or not portfolio:
            return {
                "error": "User or portfolio not found",
                "is_compliant": False,
                "metrics": {},
                "recommendations": [],
            }

        return get_risk_profile_report(user, portfolio, self.risk_manager)

    def get_investment_limits(self, user_id: int) -> Dict[str, Any]:
        """
        Get investment limits for a user based on their risk profile.

        Returns:
            Dictionary of investment limits
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        profile = self.risk_manager.get_user_risk_profile(user)

        # Get limits from the risk profile
        max_position_size = (
            self.risk_manager.get_profile_param(
                user, "position_sizing.max_position_size"
            )
            or 0.10
        )
        max_sector_exposure = (
            self.risk_manager.get_profile_param(
                user, "exposure_limits.max_sector_exposure"
            )
            or 0.30
        )
        max_trades_per_day = (
            self.risk_manager.get_profile_param(
                user, "trade_limitations.max_trades_per_day"
            )
            or 10
        )

        return {
            "risk_profile": profile.value,
            "max_position_size_pct": max_position_size * 100,
            "max_sector_exposure_pct": max_sector_exposure * 100,
            "max_trades_per_day": max_trades_per_day,
            "allowed_symbols": list(self.risk_manager.ALLOWED_SYMBOLS_MINORS)
            if user.role == UserRole.MINOR
            else None,
        }

    def get_risk_recommendations(self, user_id: int, portfolio_id: int) -> List[str]:
        """
        Get risk management recommendations for a portfolio.

        Returns:
            List of recommendation strings
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        portfolio = (
            self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        )

        if not user or not portfolio:
            return ["No data available for risk analysis"]

        metrics = calculate_portfolio_risk_metrics(portfolio)
        profile = self.risk_manager.get_user_risk_profile(user)

        return generate_risk_recommendations(
            user, portfolio, metrics, profile, self.risk_manager
        )
