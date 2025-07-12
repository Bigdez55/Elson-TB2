from typing import Dict, List, Optional, Union, Any
import os
import logging
import yaml
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskProfile(str, Enum):
    """Risk profiles for portfolios"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class RiskConfigManager:
    """
    Manages risk configuration parameters for the trading system.
    
    This class provides methods to:
    - Load risk parameters from configuration files
    - Access risk parameters based on risk profile (aggressive, moderate, conservative)
    - Update and save risk parameters
    - Log changes to risk parameters
    """
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        profile: RiskProfile = RiskProfile.MODERATE
    ):
        """
        Initialize the risk configuration manager
        
        Args:
            config_dir: Directory containing configuration files
            profile: Default risk profile to use
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), '../config')
        self.profile = profile
        
        # Default configuration for each profile
        self.default_config = {
            "conservative": {
                "position_sizing": {
                    "max_position_size": 0.05,           # 5% max position size
                    "max_sector_exposure": 0.20,         # 20% max sector exposure
                    "base_quantity_percent": 0.02        # Base position size is 2% of portfolio
                },
                "volatility_limits": {
                    "max_portfolio_volatility": 0.10,    # 10% annual volatility limit
                    "volatility_scaling_factor": 0.50,   # Scale positions by 0.5 for high volatility
                    "vix_cutoff_threshold": 25.0         # Reduce position sizing when VIX > 25
                },
                "drawdown_limits": {
                    "max_daily_drawdown": 0.015,         # 1.5% max daily drawdown
                    "max_total_drawdown": 0.07,          # 7% max total drawdown
                    "drawdown_recovery_factor": 0.5      # Reduce position size by 50% after drawdown
                },
                "trade_limitations": {
                    "max_trades_per_day": 5,             # Max 5 trades per day
                    "min_holding_period_days": 7,        # Minimum holding period of 7 days
                    "restricted_assets": ["futures", "options", "leveraged_etfs", "crypto"]
                },
                "correlation_limits": {
                    "max_correlation": 0.70,             # Max 70% correlation between positions
                    "correlation_penalty_factor": 0.8    # Reduce position size by 20% for high correlation
                },
                "exposure_limits": {
                    "max_equity_exposure": 0.80,         # 80% max exposure to equities
                    "max_fixed_income_exposure": 0.60,   # 60% max exposure to fixed income
                    "max_alternative_exposure": 0.10,    # 10% max exposure to alternatives
                    "min_cash_allocation": 0.10          # Minimum 10% cash allocation
                }
            },
            "moderate": {
                "position_sizing": {
                    "max_position_size": 0.08,           # 8% max position size
                    "max_sector_exposure": 0.30,         # 30% max sector exposure
                    "base_quantity_percent": 0.03        # Base position size is 3% of portfolio
                },
                "volatility_limits": {
                    "max_portfolio_volatility": 0.15,    # 15% annual volatility limit
                    "volatility_scaling_factor": 0.70,   # Scale positions by 0.7 for high volatility
                    "vix_cutoff_threshold": 30.0         # Reduce position sizing when VIX > 30
                },
                "drawdown_limits": {
                    "max_daily_drawdown": 0.02,          # 2% max daily drawdown
                    "max_total_drawdown": 0.12,          # 12% max total drawdown
                    "drawdown_recovery_factor": 0.7      # Reduce position size by 30% after drawdown
                },
                "trade_limitations": {
                    "max_trades_per_day": 10,            # Max 10 trades per day
                    "min_holding_period_days": 3,        # Minimum holding period of 3 days
                    "restricted_assets": ["options", "leveraged_etfs"]
                },
                "correlation_limits": {
                    "max_correlation": 0.80,             # Max 80% correlation between positions
                    "correlation_penalty_factor": 0.9    # Reduce position size by 10% for high correlation
                },
                "exposure_limits": {
                    "max_equity_exposure": 0.90,         # 90% max exposure to equities
                    "max_fixed_income_exposure": 0.70,   # 70% max exposure to fixed income
                    "max_alternative_exposure": 0.20,    # 20% max exposure to alternatives
                    "min_cash_allocation": 0.05          # Minimum 5% cash allocation
                }
            },
            "aggressive": {
                "position_sizing": {
                    "max_position_size": 0.12,           # 12% max position size
                    "max_sector_exposure": 0.40,         # 40% max sector exposure
                    "base_quantity_percent": 0.05        # Base position size is 5% of portfolio
                },
                "volatility_limits": {
                    "max_portfolio_volatility": 0.25,    # 25% annual volatility limit
                    "volatility_scaling_factor": 0.85,   # Scale positions by 0.85 for high volatility
                    "vix_cutoff_threshold": 35.0         # Reduce position sizing when VIX > 35
                },
                "drawdown_limits": {
                    "max_daily_drawdown": 0.03,          # 3% max daily drawdown
                    "max_total_drawdown": 0.18,          # 18% max total drawdown
                    "drawdown_recovery_factor": 0.85     # Reduce position size by 15% after drawdown
                },
                "trade_limitations": {
                    "max_trades_per_day": 20,            # Max 20 trades per day
                    "min_holding_period_days": 1,        # Minimum holding period of 1 day
                    "restricted_assets": []              # No restricted assets
                },
                "correlation_limits": {
                    "max_correlation": 0.90,             # Max 90% correlation between positions
                    "correlation_penalty_factor": 0.95   # Reduce position size by 5% for high correlation
                },
                "exposure_limits": {
                    "max_equity_exposure": 1.0,          # 100% max exposure to equities
                    "max_fixed_income_exposure": 0.80,   # 80% max exposure to fixed income
                    "max_alternative_exposure": 0.30,    # 30% max exposure to alternatives
                    "min_cash_allocation": 0.02          # Minimum 2% cash allocation
                }
            }
        }
        
        # Load configuration
        self.config = self._load_config()
        
        # Audit log for changes
        self.audit_log_file = os.path.join(self.config_dir, "risk_config_audit.log")
        
    def _load_config(self) -> Dict:
        """Load configuration from files or use defaults"""
        config = {}
        
        # Iterate through risk profiles
        for profile in RiskProfile:
            if profile.value == RiskProfile.CUSTOM.value:
                continue
                
            config_file = os.path.join(self.config_dir, f"{profile.value}_risk_profile.yaml")
            
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config[profile.value] = yaml.safe_load(f)
                    logger.info(f"Loaded risk configuration for {profile.value} profile")
                except Exception as e:
                    logger.error(f"Error loading risk configuration for {profile.value}: {str(e)}")
                    config[profile.value] = self.default_config.get(profile.value, {})
            else:
                config[profile.value] = self.default_config.get(profile.value, {})
                
                # Save default to file
                try:
                    os.makedirs(self.config_dir, exist_ok=True)
                    with open(config_file, 'w') as f:
                        yaml.dump(self.default_config.get(profile.value, {}), f, default_flow_style=False)
                    logger.info(f"Created default configuration for {profile.value} profile")
                except Exception as e:
                    logger.error(f"Error creating default configuration for {profile.value}: {str(e)}")
        
        return config
        
    def get_param(self, param_path: str, profile: Optional[RiskProfile] = None) -> Any:
        """
        Get a risk parameter value
        
        Args:
            param_path: Path to the parameter (e.g., 'position_sizing.max_position_size')
            profile: Optional risk profile to use (defaults to current profile)
            
        Returns:
            Parameter value or None if not found
        """
        profile_key = profile.value if profile else self.profile.value
        
        if profile_key not in self.config:
            logger.warning(f"Risk profile {profile_key} not found, using moderate profile")
            profile_key = RiskProfile.MODERATE.value
            
        # Navigate the parameter path
        parts = param_path.split('.')
        value = self.config[profile_key]
        
        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Parameter {param_path} not found in {profile_key} profile")
            return None
            
    def set_param(
        self, 
        param_path: str, 
        value: Any, 
        profile: Optional[RiskProfile] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Set a risk parameter value
        
        Args:
            param_path: Path to the parameter (e.g., 'position_sizing.max_position_size')
            value: New parameter value
            profile: Optional risk profile to update (defaults to current profile)
            reason: Optional reason for the change (for audit log)
            
        Returns:
            bool: True if successful, False otherwise
        """
        profile_key = profile.value if profile else self.profile.value
        
        if profile_key not in self.config:
            logger.warning(f"Risk profile {profile_key} not found, using moderate profile")
            profile_key = RiskProfile.MODERATE.value
            
        # Navigate to the parameter's parent
        parts = param_path.split('.')
        param_name = parts[-1]
        current = self.config[profile_key]
        
        try:
            # Navigate to the parent object
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
                
            # Record old value for audit log
            old_value = current.get(param_name)
            
            # Update value
            current[param_name] = value
            
            # Save to file
            self._save_config(profile_key)
            
            # Log the change
            self._log_param_change(param_path, old_value, value, profile_key, reason)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting parameter {param_path}: {str(e)}")
            return False
            
    def set_profile(self, profile: RiskProfile) -> None:
        """
        Change the active risk profile
        
        Args:
            profile: New risk profile to use
        """
        self.profile = profile
        logger.info(f"Changed active risk profile to {profile.value}")
        
    def get_profile_params(self, profile: Optional[RiskProfile] = None) -> Dict:
        """
        Get all parameters for a risk profile
        
        Args:
            profile: Optional risk profile (defaults to current profile)
            
        Returns:
            Dict containing all profile parameters
        """
        profile_key = profile.value if profile else self.profile.value
        
        if profile_key not in self.config:
            logger.warning(f"Risk profile {profile_key} not found, using moderate profile")
            return self.config[RiskProfile.MODERATE.value]
            
        return self.config[profile_key]
        
    def _save_config(self, profile_key: str) -> None:
        """Save configuration for a specific profile to file"""
        config_file = os.path.join(self.config_dir, f"{profile_key}_risk_profile.yaml")
        
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(config_file, 'w') as f:
                yaml.dump(self.config[profile_key], f, default_flow_style=False)
            logger.info(f"Saved configuration for {profile_key} profile")
        except Exception as e:
            logger.error(f"Error saving configuration for {profile_key}: {str(e)}")
            
    def _log_param_change(
        self, 
        param_path: str, 
        old_value: Any, 
        new_value: Any, 
        profile: str,
        reason: Optional[str] = None
    ) -> None:
        """Log parameter changes to audit log"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "profile": profile,
            "parameter": param_path,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason or "No reason provided"
        }
        
        try:
            os.makedirs(os.path.dirname(self.audit_log_file), exist_ok=True)
            with open(self.audit_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Error writing to audit log: {str(e)}")
            
        logger.info(
            f"Risk parameter changed - Profile: {profile}, Parameter: {param_path}, "
            f"Old: {old_value}, New: {new_value}, Reason: {reason or 'No reason provided'}"
        )

    def create_custom_profile(self, template_profile: RiskProfile) -> Dict:
        """
        Create a custom risk profile based on a template
        
        Args:
            template_profile: Profile to use as template
            
        Returns:
            Dict containing the custom profile parameters
        """
        if template_profile.value not in self.config:
            template_profile = RiskProfile.MODERATE
            
        # Copy the template profile
        custom_profile = self.config[template_profile.value].copy()
        
        # Set as custom profile
        self.config[RiskProfile.CUSTOM.value] = custom_profile
        
        # Save to file
        self._save_config(RiskProfile.CUSTOM.value)
        
        return custom_profile


# Singleton instance
_risk_config_instance = None

def get_risk_config(
    config_dir: Optional[str] = None,
    profile: RiskProfile = RiskProfile.MODERATE
) -> RiskConfigManager:
    """Get or create the risk configuration manager instance"""
    global _risk_config_instance
    if _risk_config_instance is None:
        _risk_config_instance = RiskConfigManager(config_dir, profile)
    return _risk_config_instance