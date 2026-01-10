import logging
import os
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class RiskProfile(str, Enum):
    """Risk profile levels for trading"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"  # For user-customized risk settings


class RiskConfig:
    """
    Manages risk configuration parameters for the trading system.
    Supports different risk profiles and dynamic parameter adjustment.
    """

    def __init__(
        self,
        profile: RiskProfile = RiskProfile.MODERATE,
        config_path: Optional[str] = None,
    ):
        """
        Initialize risk configuration

        Args:
            profile: Risk profile to use
            config_path: Optional path to custom configuration file
        """
        self.profile = profile
        self.config: Dict[str, Any] = {}

        # Load configuration
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        else:
            self._load_default_config()

    def _load_config(self, config_path: str) -> None:
        """Load configuration from YAML file"""
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded risk configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading risk configuration: {str(e)}")
            self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default risk configuration"""
        self.config = {
            "conservative": {
                "position_sizing": {
                    "max_position_size": 0.05,  # 5% max position size
                    "min_signal_confidence": 0.7,  # 70% min confidence
                    "base_position_pct": 0.02,  # 2% base position
                    "confidence_multiplier": 2.0,
                },
                "drawdown_limits": {
                    "max_daily_drawdown": 0.015,  # 1.5% max daily loss
                    "max_weekly_drawdown": 0.05,  # 5% max weekly loss
                    "max_monthly_drawdown": 0.10,  # 10% max monthly loss
                    "max_total_drawdown": 0.07,  # 7% max total drawdown
                    "drawdown_recovery_factor": 0.5,  # Reduce position 50% after drawdown
                },
                "trade_limitations": {
                    "max_trades_per_day": 5,
                    "max_trades_per_week": 20,
                    "min_holding_period_days": 7,  # Minimum 7 day hold
                    "restricted_assets": ["penny_stocks", "options", "futures", "leveraged_etfs", "crypto"],
                    "min_market_cap": 1000000000,  # $1B min market cap
                },
                "correlation_limits": {
                    "max_correlation": 0.7,
                    "max_sector_concentration": 0.25,  # 25% max in one sector
                    "max_stock_concentration": 0.05,  # 5% max in one stock
                    "correlation_penalty_factor": 0.8,  # Reduce position 20% for high correlation
                },
                "volatility_adjustments": {
                    "low_vol_multiplier": 1.2,  # Increase position in low vol
                    "high_vol_multiplier": 0.6,  # Decrease position in high vol
                    "extreme_vol_multiplier": 0.2,  # Minimal position in extreme vol
                    "vix_cutoff_threshold": 25.0,  # Reduce positions when VIX > 25
                },
                "exposure_limits": {
                    "max_equity_exposure": 0.80,  # 80% max exposure to equities
                    "max_fixed_income_exposure": 0.60,  # 60% max to fixed income
                    "max_alternative_exposure": 0.10,  # 10% max to alternatives
                    "min_cash_allocation": 0.10,  # Minimum 10% cash
                },
            },
            "moderate": {
                "position_sizing": {
                    "max_position_size": 0.10,  # 10% max position size
                    "min_signal_confidence": 0.5,  # 50% min confidence
                    "base_position_pct": 0.05,  # 5% base position
                    "confidence_multiplier": 1.5,
                },
                "drawdown_limits": {
                    "max_daily_drawdown": 0.025,  # 2.5% max daily loss
                    "max_weekly_drawdown": 0.08,  # 8% max weekly loss
                    "max_monthly_drawdown": 0.15,  # 15% max monthly loss
                    "max_total_drawdown": 0.12,  # 12% max total drawdown
                    "drawdown_recovery_factor": 0.7,  # Reduce position 30% after drawdown
                },
                "trade_limitations": {
                    "max_trades_per_day": 10,
                    "max_trades_per_week": 40,
                    "min_holding_period_days": 3,  # Minimum 3 day hold
                    "restricted_assets": ["penny_stocks", "leveraged_etfs"],
                    "min_market_cap": 500000000,  # $500M min market cap
                },
                "correlation_limits": {
                    "max_correlation": 0.8,
                    "max_sector_concentration": 0.35,  # 35% max in one sector
                    "max_stock_concentration": 0.10,  # 10% max in one stock
                    "correlation_penalty_factor": 0.9,  # Reduce position 10% for high correlation
                },
                "volatility_adjustments": {
                    "low_vol_multiplier": 1.1,  # Slight increase in low vol
                    "high_vol_multiplier": 0.7,  # Decrease position in high vol
                    "extreme_vol_multiplier": 0.3,  # Reduced position in extreme vol
                    "vix_cutoff_threshold": 30.0,  # Reduce positions when VIX > 30
                },
                "exposure_limits": {
                    "max_equity_exposure": 0.90,  # 90% max exposure to equities
                    "max_fixed_income_exposure": 0.70,  # 70% max to fixed income
                    "max_alternative_exposure": 0.20,  # 20% max to alternatives
                    "min_cash_allocation": 0.05,  # Minimum 5% cash
                },
            },
            "aggressive": {
                "position_sizing": {
                    "max_position_size": 0.20,  # 20% max position size
                    "min_signal_confidence": 0.3,  # 30% min confidence
                    "base_position_pct": 0.10,  # 10% base position
                    "confidence_multiplier": 1.0,
                },
                "drawdown_limits": {
                    "max_daily_drawdown": 0.05,  # 5% max daily loss
                    "max_weekly_drawdown": 0.15,  # 15% max weekly loss
                    "max_monthly_drawdown": 0.25,  # 25% max monthly loss
                    "max_total_drawdown": 0.18,  # 18% max total drawdown
                    "drawdown_recovery_factor": 0.85,  # Reduce position 15% after drawdown
                },
                "trade_limitations": {
                    "max_trades_per_day": 20,
                    "max_trades_per_week": 80,
                    "min_holding_period_days": 1,  # Minimum 1 day hold
                    "restricted_assets": [],  # No restrictions
                    "min_market_cap": 100000000,  # $100M min market cap
                },
                "correlation_limits": {
                    "max_correlation": 0.9,
                    "max_sector_concentration": 0.50,  # 50% max in one sector
                    "max_stock_concentration": 0.20,  # 20% max in one stock
                    "correlation_penalty_factor": 0.95,  # Reduce position 5% for high correlation
                },
                "volatility_adjustments": {
                    "low_vol_multiplier": 1.0,  # No adjustment in low vol
                    "high_vol_multiplier": 0.8,  # Small decrease in high vol
                    "extreme_vol_multiplier": 0.5,  # Moderate position in extreme vol
                    "vix_cutoff_threshold": 35.0,  # Reduce positions when VIX > 35
                },
                "exposure_limits": {
                    "max_equity_exposure": 1.0,  # 100% max exposure to equities
                    "max_fixed_income_exposure": 0.80,  # 80% max to fixed income
                    "max_alternative_exposure": 0.30,  # 30% max to alternatives
                    "min_cash_allocation": 0.02,  # Minimum 2% cash
                },
            },
        }

    def get_param(self, param_path: str) -> Any:
        """
        Get a configuration parameter using dot notation

        Args:
            param_path: Parameter path like "position_sizing.max_position_size"

        Returns:
            Parameter value or None if not found
        """
        try:
            # Get the profile-specific config
            profile_config = self.config.get(self.profile.value, {})

            # Navigate through the parameter path
            current = profile_config
            for key in param_path.split("."):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None

            return current
        except Exception as e:
            logger.error(f"Error getting parameter {param_path}: {str(e)}")
            return None

    def set_param(self, param_path: str, value: Any) -> bool:
        """
        Set a configuration parameter using dot notation

        Args:
            param_path: Parameter path like "position_sizing.max_position_size"
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure profile config exists
            if self.profile.value not in self.config:
                self.config[self.profile.value] = {}

            # Navigate to the parent of the target parameter
            current = self.config[self.profile.value]
            keys = param_path.split(".")

            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set the final value
            current[keys[-1]] = value
            return True
        except Exception as e:
            logger.error(f"Error setting parameter {param_path}: {str(e)}")
            return False

    def update_profile(self, new_profile: RiskProfile) -> None:
        """
        Update the active risk profile

        Args:
            new_profile: New risk profile to use
        """
        self.profile = new_profile
        logger.info(f"Updated risk profile to {new_profile.value}")

    def get_profile_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current risk profile settings

        Returns:
            Dictionary with key risk parameters
        """
        return {
            "profile": self.profile.value,
            "max_position_size": self.get_param("position_sizing.max_position_size"),
            "max_daily_drawdown": self.get_param("drawdown_limits.max_daily_drawdown"),
            "max_trades_per_day": self.get_param(
                "trade_limitations.max_trades_per_day"
            ),
            "min_signal_confidence": self.get_param(
                "position_sizing.min_signal_confidence"
            ),
            "max_correlation": self.get_param("correlation_limits.max_correlation"),
        }

    def calculate_position_size(
        self,
        portfolio_value: float,
        signal_confidence: float,
        current_volatility: Optional[str] = None,
    ) -> float:
        """
        Calculate position size based on risk parameters

        Args:
            portfolio_value: Total portfolio value
            signal_confidence: Confidence in the trading signal (0-1)
            current_volatility: Current volatility regime ("low", "normal", "high", "extreme")

        Returns:
            Suggested position size in dollars
        """
        try:
            # Get base parameters
            base_pct = self.get_param("position_sizing.base_position_pct") or 0.05
            max_pct = self.get_param("position_sizing.max_position_size") or 0.10
            confidence_multiplier = (
                self.get_param("position_sizing.confidence_multiplier") or 1.0
            )
            min_confidence = (
                self.get_param("position_sizing.min_signal_confidence") or 0.3
            )

            # Check minimum confidence
            if signal_confidence < min_confidence:
                return 0.0

            # Calculate base position size
            position_pct = base_pct * signal_confidence * confidence_multiplier

            # Apply volatility adjustments
            if current_volatility:
                vol_param = (
                    f"volatility_adjustments.{current_volatility}_vol_multiplier"
                )
                vol_multiplier = self.get_param(vol_param)
                if vol_multiplier is not None:
                    position_pct *= vol_multiplier

            # Cap at maximum position size
            position_pct = min(position_pct, max_pct)

            # Convert to dollar amount
            position_size = portfolio_value * position_pct

            return position_size
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.0

    def is_asset_allowed(
        self,
        symbol: str,
        asset_class: Optional[str] = None,
        market_cap: Optional[float] = None,
    ) -> bool:
        """
        Check if an asset is allowed based on restrictions

        Args:
            symbol: Asset symbol
            asset_class: Asset class (e.g., "penny_stocks", "options")
            market_cap: Market capitalization

        Returns:
            True if asset is allowed, False otherwise
        """
        try:
            # Check restricted assets
            restricted_assets = (
                self.get_param("trade_limitations.restricted_assets") or []
            )
            if asset_class and asset_class in restricted_assets:
                return False

            # Check minimum market cap
            min_market_cap = self.get_param("trade_limitations.min_market_cap")
            if min_market_cap and market_cap and market_cap < min_market_cap:
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking asset allowance: {str(e)}")
            return False

    def save_config(self, file_path: str) -> bool:
        """
        Save current configuration to file

        Args:
            file_path: Path to save configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            logger.info(f"Saved risk configuration to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving risk configuration: {str(e)}")
            return False

    def set_param_with_audit(
        self,
        param_path: str,
        value: Any,
        reason: Optional[str] = None,
        audit_log_path: Optional[str] = None
    ) -> bool:
        """
        Set a configuration parameter with audit logging

        Args:
            param_path: Parameter path like "position_sizing.max_position_size"
            value: Value to set
            reason: Reason for the change (for audit log)
            audit_log_path: Path to audit log file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get old value for audit
            old_value = self.get_param(param_path)

            # Set the new value
            if not self.set_param(param_path, value):
                return False

            # Log the change
            if audit_log_path:
                self._log_param_change(param_path, old_value, value, reason, audit_log_path)

            return True
        except Exception as e:
            logger.error(f"Error setting parameter with audit {param_path}: {str(e)}")
            return False

    def _log_param_change(
        self,
        param_path: str,
        old_value: Any,
        new_value: Any,
        reason: Optional[str],
        audit_log_path: str
    ) -> None:
        """Log parameter changes to audit log"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "profile": self.profile.value,
            "parameter": param_path,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason or "No reason provided"
        }

        try:
            os.makedirs(os.path.dirname(audit_log_path), exist_ok=True)
            with open(audit_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Error writing to audit log: {str(e)}")

        logger.info(
            f"Risk parameter changed - Profile: {self.profile.value}, Parameter: {param_path}, "
            f"Old: {old_value}, New: {new_value}, Reason: {reason or 'No reason provided'}"
        )

    def create_custom_profile(self, template_profile: RiskProfile = RiskProfile.MODERATE) -> Dict[str, Any]:
        """
        Create a custom risk profile based on a template

        Args:
            template_profile: Profile to use as template

        Returns:
            Dict containing the custom profile parameters
        """
        if template_profile.value not in self.config:
            template_profile = RiskProfile.MODERATE

        # Deep copy the template profile
        import copy
        custom_profile = copy.deepcopy(self.config[template_profile.value])

        # Set as custom profile
        self.config[RiskProfile.CUSTOM.value] = custom_profile

        logger.info(f"Created custom profile based on {template_profile.value}")
        return custom_profile

    def get_exposure_limits(self) -> Dict[str, float]:
        """
        Get current exposure limits

        Returns:
            Dictionary with exposure limit values
        """
        return {
            "max_equity_exposure": self.get_param("exposure_limits.max_equity_exposure") or 1.0,
            "max_fixed_income_exposure": self.get_param("exposure_limits.max_fixed_income_exposure") or 1.0,
            "max_alternative_exposure": self.get_param("exposure_limits.max_alternative_exposure") or 1.0,
            "min_cash_allocation": self.get_param("exposure_limits.min_cash_allocation") or 0.0,
        }

    def get_vix_threshold(self) -> float:
        """Get the VIX threshold for position reduction"""
        return self.get_param("volatility_adjustments.vix_cutoff_threshold") or 30.0

    def get_drawdown_recovery_factor(self) -> float:
        """Get the drawdown recovery factor for position sizing after losses"""
        return self.get_param("drawdown_limits.drawdown_recovery_factor") or 0.7


# Global risk config instance
_risk_config_instance = None


def get_risk_config(
    profile: Optional[RiskProfile] = None, config_path: Optional[str] = None
) -> RiskConfig:
    """Get the global risk configuration instance"""
    global _risk_config_instance
    if _risk_config_instance is None:
        _risk_config_instance = RiskConfig(profile or RiskProfile.MODERATE, config_path)
    elif profile and profile != _risk_config_instance.profile:
        _risk_config_instance.update_profile(profile)
    return _risk_config_instance


def set_risk_profile(profile: RiskProfile) -> None:
    """Set the global risk profile"""
    risk_config = get_risk_config()
    risk_config.update_profile(profile)
