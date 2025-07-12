from typing import Dict, List, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta
import logging
import threading
import time
import json
import os
from enum import Enum
import yaml
import random

logger = logging.getLogger(__name__)

class CircuitBreakerType(str, Enum):
    """Types of circuit breakers that can be triggered"""
    SYSTEM = "system"                # General system-level circuit breaker
    VOLATILITY = "volatility"        # Market volatility triggered
    DAILY_LOSS = "daily_loss"        # Daily loss limit exceeded
    PER_STRATEGY = "per_strategy"    # Strategy-specific issues
    CORRELATION = "correlation"      # Position correlation limits exceeded
    API_FAILURE = "api_failure"      # External API connectivity issues
    LIQUIDITY = "liquidity"          # Market liquidity issues
    EXECUTION = "execution"          # Trade execution problems
    MANUAL = "manual"                # Manually triggered by administrator


class CircuitBreakerStatus(str, Enum):
    """Status of the circuit breaker"""
    OPEN = "open"                  # Trading suspended
    RESTRICTED = "restricted"      # Limited trading allowed with position sizing
    CAUTIOUS = "cautious"          # Trading allowed with additional risk controls
    CLOSED = "closed"              # Trading allowed normally
    HALF_OPEN = "half_open"        # Testing if it's safe to re-enable trading


class VolatilityLevel(str, Enum):
    """Volatility levels corresponding to the volatility regimes"""
    LOW = "low"                   # 0-15% annualized volatility
    NORMAL = "normal"             # 15-25% annualized volatility
    HIGH = "high"                 # 25-40% annualized volatility
    EXTREME = "extreme"           # >40% annualized volatility


class CircuitBreaker:
    """
    Implements a circuit breaker pattern to halt trading when risk thresholds 
    are exceeded or system issues are detected.
    
    Enhanced in Phase 2 to support:
    - Graduated responses based on volatility levels
    - Partial position sizing based on breaker status
    - Cool-down periods for re-entry after extreme volatility
    - Asset-specific circuit breaker customization
    - Hysteresis to prevent rapid switching
    
    Circuit breakers can be set at various levels:
    - System-wide: Halts all trading
    - Per strategy: Halts a specific strategy
    - Per symbol: Halts trading for a specific ticker
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the circuit breaker system
        
        Args:
            config_path: Path to the configuration file for circuit breaker thresholds
        """
        self.circuit_breakers: Dict[str, Dict] = {}
        self.config: Dict = {}
        self.lock = threading.RLock()
        self.volatility_history = {}  # Track recent volatility levels for hysteresis
        
        # Load configuration
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        else:
            # Default configuration
            self.config = {
                "volatility": {
                    "market_wide": {
                        "extreme": 0.35,   # 35% extreme volatility threshold (reduced from 38%)
                        "high": 0.20,      # 20% high volatility threshold (reduced from 22%)
                        "normal": 0.15,    # 15% normal volatility threshold (unchanged)
                        "position_sizing": {
                            "extreme": 0.03,  # 3% of normal position size (further reduced from 5%)
                            "high": 0.10,     # 10% of normal position size (further reduced from 15%)
                            "normal": 0.90,    # 90% of normal position size (reduced from 100%)
                            "low": 1.0        # 100% of normal position size (unchanged)
                        }
                    },
                    "symbol_specific": {
                        "extreme": 0.45,   # 45% symbol-specific extreme threshold
                        "high": 0.30,      # 30% symbol-specific high threshold
                        "normal": 0.18,    # 18% symbol-specific normal threshold
                    },
                    "asset_class_modifiers": {
                        "cryptocurrency": 1.5,  # 50% higher thresholds for crypto
                        "forex": 0.8,           # 20% lower thresholds for forex
                        "options": 1.2          # 20% higher thresholds for options
                    },
                    "cool_down_minutes": {
                        "extreme": 90,      # 90 min cool-down after extreme volatility (increased from 60 min)
                        "high": 45,         # 45 min cool-down after high volatility (increased from 30 min)
                        "normal": 20,       # 20 min cool-down after normal volatility (increased from 15 min)
                        "low": 0            # No cool-down for low volatility
                    },
                    "hysteresis": {
                        "samples": 20,      # Number of samples to track for hysteresis (increased from 15 to 20)
                        "threshold": 0.85   # 85% of samples must be in new regime (increased from 80% to 85%)
                    }
                },
                "daily_loss": {
                    "portfolio_pct": 0.03,     # 3% daily portfolio loss limit
                    "graduated": {
                        "warning": 0.02,       # 2% triggers warning and position sizing
                        "restricted": 0.025,   # 2.5% triggers restricted trading
                        "halt": 0.03           # 3% triggers full trading halt
                    },
                    "position_sizing": {
                        "warning": 0.75,       # 75% of normal position size
                        "restricted": 0.50,    # 50% of normal position size
                        "halt": 0.0            # 0% of normal position size (halted)
                    },
                    "reset_after_minutes": 0   # Do not auto-reset (until next trading day)
                },
                "execution": {
                    "fail_rate_threshold": 0.3,  # 30% of orders failing
                    "graduated": {
                        "warning": 0.15,        # 15% failure rate triggers warning
                        "restricted": 0.25,     # 25% failure rate triggers restrictions
                        "halt": 0.3             # 30% failure rate triggers halt
                    },
                    "reset_after_minutes": 15    # Auto-reset after 15 minutes
                },
                "api_failure": {
                    "consecutive_failures": 3,    # 3 consecutive API failures
                    "reset_after_minutes": 5      # Auto-reset after 5 minutes
                },
                "correlation": {
                    "threshold": 0.85,           # 85% correlation threshold
                    "graduated": {
                        "warning": 0.75,         # 75% correlation triggers warning
                        "restricted": 0.80,      # 80% correlation triggers restrictions
                        "halt": 0.85             # 85% correlation triggers halt
                    },
                    "reset_after_minutes": 60    # Auto-reset after 60 minutes
                },
                "system": {
                    "reset_after_minutes": 0     # Do not auto-reset system breakers
                }
            }
            
        # Initialize status store for persistence
        self.status_file = "circuit_breaker_status.json"
        self._load_status()

    def _load_config(self, config_path: str) -> None:
        """Load circuit breaker configuration from file"""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded circuit breaker configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading circuit breaker configuration: {str(e)}")
            # Use default configuration
            self.config = {}

    def _load_status(self) -> None:
        """Load the status of all circuit breakers from file"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                    self.circuit_breakers = status_data
                logger.info(f"Loaded circuit breaker status from {self.status_file}")
        except Exception as e:
            logger.error(f"Error loading circuit breaker status: {str(e)}")
            
    def _save_status(self) -> None:
        """Save the current status of all circuit breakers to file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.circuit_breakers, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving circuit breaker status: {str(e)}")
            
    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state"""
        with self.lock:
            self.circuit_breakers = {}
            self._save_status()
        logger.warning("All circuit breakers have been reset")
    
    def process_volatility(
        self, 
        volatility_level: VolatilityLevel,
        volatility_value: float,
        symbol: Optional[str] = None,
        asset_class: Optional[str] = None
    ) -> Tuple[bool, CircuitBreakerStatus, float]:
        """
        Process volatility data and determine appropriate circuit breaker status
        
        Args:
            volatility_level: Enum indicating volatility regime
            volatility_value: Actual volatility value
            symbol: Optional symbol for symbol-specific thresholds
            asset_class: Optional asset class for specific thresholds
            
        Returns:
            Tuple of (breaker_tripped, status, position_size_multiplier)
        """
        with self.lock:
            # Apply hysteresis to avoid rapid switching between regimes
            if symbol in self.volatility_history:
                # Add current reading to history
                self.volatility_history[symbol].append(volatility_level)
                # Keep only the most recent samples
                samples = self.config["volatility"]["hysteresis"]["samples"]
                self.volatility_history[symbol] = self.volatility_history[symbol][-samples:]
                
                # Check if we have enough samples in the new regime to switch
                current_samples = self.volatility_history[symbol]
                threshold = self.config["volatility"]["hysteresis"]["threshold"]
                
                # Count occurrences of each volatility level
                level_counts = {}
                for level in current_samples:
                    level_counts[level] = level_counts.get(level, 0) + 1
                
                # Find the dominant level
                dominant_level = max(level_counts, key=level_counts.get)
                dominant_ratio = level_counts[dominant_level] / len(current_samples)
                
                # Only use the dominant level if it exceeds the threshold
                if dominant_ratio >= threshold:
                    volatility_level = dominant_level
            else:
                # Initialize history for this symbol
                self.volatility_history[symbol] = [volatility_level]
            
            # Get thresholds based on symbol or asset class
            thresholds = self.config["volatility"]["market_wide"]
            position_sizing = thresholds["position_sizing"]
            
            # Apply asset class specific modifiers if available
            modifier = 1.0
            if asset_class and asset_class in self.config["volatility"]["asset_class_modifiers"]:
                modifier = self.config["volatility"]["asset_class_modifiers"][asset_class]
            
            # Determine circuit breaker status based on volatility level
            if volatility_level == VolatilityLevel.EXTREME:
                # Trip the circuit breaker for extreme volatility
                status = CircuitBreakerStatus.OPEN
                position_multiplier = position_sizing["extreme"]
                reset_after = self.config["volatility"]["cool_down_minutes"]["extreme"]
                self.trip(
                    CircuitBreakerType.VOLATILITY,
                    f"Extreme volatility detected: {volatility_value:.2f}%",
                    scope=symbol,
                    reset_after=reset_after,
                    status=status
                )
                return True, status, position_multiplier
                
            elif volatility_level == VolatilityLevel.HIGH:
                # Restricted trading for high volatility
                status = CircuitBreakerStatus.RESTRICTED
                position_multiplier = position_sizing["high"]
                reset_after = self.config["volatility"]["cool_down_minutes"]["high"]
                self.trip(
                    CircuitBreakerType.VOLATILITY,
                    f"High volatility detected: {volatility_value:.2f}%",
                    scope=symbol,
                    reset_after=reset_after,
                    status=status
                )
                return True, status, position_multiplier
                
            elif volatility_level == VolatilityLevel.NORMAL:
                # Cautious trading for normal volatility
                status = CircuitBreakerStatus.CAUTIOUS
                position_multiplier = position_sizing["normal"]
                reset_after = self.config["volatility"]["cool_down_minutes"]["normal"]
                self.trip(
                    CircuitBreakerType.VOLATILITY,
                    f"Normal volatility detected: {volatility_value:.2f}%",
                    scope=symbol,
                    reset_after=reset_after,
                    status=status
                )
                return True, status, position_multiplier
            
            else:  # LOW volatility
                # Normal trading for low volatility
                status = CircuitBreakerStatus.CLOSED
                position_multiplier = position_sizing["low"]
                # Reset any existing volatility circuit breakers
                key = self._get_key(CircuitBreakerType.VOLATILITY, symbol)
                if key in self.circuit_breakers:
                    self.reset(CircuitBreakerType.VOLATILITY, symbol)
                return False, status, position_multiplier
    
    def trip(
        self, 
        breaker_type: CircuitBreakerType,
        reason: str,
        scope: Optional[str] = None,
        reset_after: Optional[int] = None,
        status: CircuitBreakerStatus = CircuitBreakerStatus.OPEN
    ) -> None:
        """
        Trip a circuit breaker to halt or restrict trading
        
        Args:
            breaker_type: Type of circuit breaker
            reason: Human-readable reason for tripping
            scope: Optional scope (e.g., strategy name, symbol)
            reset_after: Minutes until auto-reset (overrides config)
            status: Status to set the circuit breaker to (default: OPEN)
        """
        with self.lock:
            key = self._get_key(breaker_type, scope)
            
            # Use provided reset_after or get from config
            if reset_after is None:
                config_key = breaker_type.value
                if config_key in self.config:
                    reset_after = self.config[config_key].get("reset_after_minutes", 0)
                else:
                    reset_after = 0
            
            # Calculate auto-reset time if applicable
            auto_reset = None
            if reset_after > 0:
                auto_reset = (datetime.now() + timedelta(minutes=reset_after)).isoformat()
            
            # Record the circuit breaker
            self.circuit_breakers[key] = {
                "type": breaker_type.value,
                "scope": scope,
                "status": status.value,
                "reason": reason,
                "tripped_at": datetime.now().isoformat(),
                "auto_reset_at": auto_reset
            }
            
            self._save_status()
            
        logger.warning(
            f"Circuit breaker triggered - Type: {breaker_type.value}, "
            f"Status: {status.value}, Scope: {scope or 'global'}, Reason: {reason}"
        )
    
    def reset(self, breaker_type: CircuitBreakerType, scope: Optional[str] = None) -> bool:
        """
        Manually reset a circuit breaker
        
        Args:
            breaker_type: Type of circuit breaker
            scope: Optional scope (e.g., strategy name, symbol)
            
        Returns:
            bool: True if a breaker was reset, False if not found
        """
        with self.lock:
            key = self._get_key(breaker_type, scope)
            
            if key in self.circuit_breakers:
                # Check current status to determine next state
                current_status = self.circuit_breakers[key]["status"]
                
                if current_status == CircuitBreakerStatus.OPEN.value:
                    # Move from OPEN to RESTRICTED
                    self.circuit_breakers[key]["status"] = CircuitBreakerStatus.RESTRICTED.value
                    self.circuit_breakers[key]["reset_attempted_at"] = datetime.utcnow().isoformat()
                    self._save_status()
                    logger.info(
                        f"Circuit breaker eased from OPEN to RESTRICTED - Type: {breaker_type.value}, "
                        f"Scope: {scope or 'global'}"
                    )
                    return True
                    
                elif current_status == CircuitBreakerStatus.RESTRICTED.value:
                    # Move from RESTRICTED to CAUTIOUS
                    self.circuit_breakers[key]["status"] = CircuitBreakerStatus.CAUTIOUS.value
                    self.circuit_breakers[key]["reset_attempted_at"] = datetime.utcnow().isoformat()
                    self._save_status()
                    logger.info(
                        f"Circuit breaker eased from RESTRICTED to CAUTIOUS - Type: {breaker_type.value}, "
                        f"Scope: {scope or 'global'}"
                    )
                    return True
                    
                elif current_status == CircuitBreakerStatus.CAUTIOUS.value:
                    # Move from CAUTIOUS to CLOSED (fully reset)
                    del self.circuit_breakers[key]
                    self._save_status()
                    logger.info(
                        f"Circuit breaker fully closed - Type: {breaker_type.value}, "
                        f"Scope: {scope or 'global'}"
                    )
                    return True
                    
                elif current_status == CircuitBreakerStatus.HALF_OPEN.value:
                    # Move from HALF_OPEN to CLOSED
                    del self.circuit_breakers[key]
                    self._save_status()
                    logger.info(
                        f"Circuit breaker closed - Type: {breaker_type.value}, "
                        f"Scope: {scope or 'global'}"
                    )
                    return True
            return False
    
    def get_position_sizing(self, breaker_type: Optional[CircuitBreakerType] = None, scope: Optional[str] = None) -> float:
        """
        Return position sizing multiplier based on current state.
        
        Modified in Phase 2 to implement more graduated position sizing
        for different volatility regimes and circuit breaker states.
        
        Args:
            breaker_type: Optional specific type to check
            scope: Optional specific scope to check
            
        Returns:
            Position sizing multiplier (0.0-1.0)
        """
        # Get the circuit breaker status
        allowed, status = self.check(breaker_type, scope) if breaker_type else (True, CircuitBreakerStatus.CLOSED)
        
        # Default regime is normal if we have no history
        current_regime = VolatilityLevel.NORMAL
        if scope and scope in self.volatility_history and self.volatility_history[scope]:
            # Use the most recent volatility level
            current_regime = self.volatility_history[scope][-1]
        
        if status == CircuitBreakerStatus.OPEN:
            return 0.0
        elif status == CircuitBreakerStatus.RESTRICTED:
            if current_regime == VolatilityLevel.EXTREME:
                return 0.03  # Further reduced from 0.05
            elif current_regime == VolatilityLevel.HIGH:
                return 0.10  # Further reduced from 0.15
            elif current_regime == VolatilityLevel.NORMAL:
                return 0.40  # Further reduced from 0.5
            else:
                return 0.60  # Reduced for LOW regime
        elif status == CircuitBreakerStatus.CAUTIOUS:
            if current_regime == VolatilityLevel.EXTREME:
                return 0.05  # Further reduced from 0.07
            elif current_regime == VolatilityLevel.HIGH:
                return 0.15  # Further reduced from 0.20
            elif current_regime == VolatilityLevel.NORMAL:
                return 0.65  # Further reduced from 0.75
            else:
                return 0.85  # Reduced for LOW regime
        else:  # CLOSED
            if current_regime == VolatilityLevel.EXTREME:
                return 0.03  # Further reduced from 0.05
            elif current_regime == VolatilityLevel.HIGH:
                return 0.10  # Further reduced from 0.15
            elif current_regime == VolatilityLevel.NORMAL:
                return 0.90  # Slightly reduced from 1.0
            else:
                return 1.0   # Full size for LOW volatility
    
    def _get_volatility_level_from_status(self, status: str) -> str:
        """Map circuit breaker status to volatility level"""
        if status == CircuitBreakerStatus.OPEN.value:
            return VolatilityLevel.EXTREME.value
        elif status == CircuitBreakerStatus.RESTRICTED.value:
            return VolatilityLevel.HIGH.value
        elif status == CircuitBreakerStatus.CAUTIOUS.value:
            return VolatilityLevel.NORMAL.value
        else:
            return VolatilityLevel.LOW.value
            
    def _get_daily_loss_level_from_status(self, status: str) -> str:
        """Map circuit breaker status to daily loss level"""
        if status == CircuitBreakerStatus.OPEN.value:
            return "halt"
        elif status == CircuitBreakerStatus.RESTRICTED.value:
            return "restricted"
        elif status == CircuitBreakerStatus.CAUTIOUS.value:
            return "warning"
        else:
            return "normal"
    
    def check(
        self,
        breaker_type: Optional[CircuitBreakerType] = None,
        scope: Optional[str] = None
    ) -> Tuple[bool, CircuitBreakerStatus]:
        """
        Check if trading is allowed based on circuit breakers
        
        Args:
            breaker_type: Optional specific type to check
            scope: Optional specific scope to check
            
        Returns:
            Tuple of (is_trading_allowed, circuit_breaker_status)
        """
        with self.lock:
            # Process any auto-resets first
            self._process_auto_resets()
            
            # If specific type and scope provided, check only that breaker
            if breaker_type is not None:
                key = self._get_key(breaker_type, scope)
                allowed, status = self._check_single_breaker(key)
                return allowed, status
            
            # System-wide check
            system_key = self._get_key(CircuitBreakerType.SYSTEM, None)
            if system_key in self.circuit_breakers:
                status = self.circuit_breakers[system_key]["status"]
                if status == CircuitBreakerStatus.OPEN.value:
                    return False, CircuitBreakerStatus.OPEN
            
            # Check if there's a scope-specific breaker for any type
            if scope:
                most_restrictive_status = CircuitBreakerStatus.CLOSED
                
                for breaker_type in CircuitBreakerType:
                    key = self._get_key(breaker_type, scope)
                    allowed, status = self._check_single_breaker(key)
                    
                    # Update most restrictive status
                    if not allowed:
                        return False, status
                    
                    # Track the most restrictive non-blocking status
                    if self._is_more_restrictive(status, most_restrictive_status):
                        most_restrictive_status = status
                
                # Return the most restrictive status that still allows trading
                return True, most_restrictive_status
            
            # All checks passed, trading fully allowed
            return True, CircuitBreakerStatus.CLOSED
    
    def _is_more_restrictive(self, status1: CircuitBreakerStatus, status2: CircuitBreakerStatus) -> bool:
        """Determine if status1 is more restrictive than status2"""
        restriction_level = {
            CircuitBreakerStatus.OPEN: 4,
            CircuitBreakerStatus.RESTRICTED: 3,
            CircuitBreakerStatus.CAUTIOUS: 2,
            CircuitBreakerStatus.HALF_OPEN: 1,
            CircuitBreakerStatus.CLOSED: 0
        }
        
        return restriction_level.get(status1, 0) > restriction_level.get(status2, 0)
    
    def _check_single_breaker(self, key: str) -> Tuple[bool, CircuitBreakerStatus]:
        """Check if a specific breaker allows trading"""
        if key in self.circuit_breakers:
            status_str = self.circuit_breakers[key]["status"]
            status = CircuitBreakerStatus(status_str)
            
            if status == CircuitBreakerStatus.OPEN:
                return False, status
            elif status == CircuitBreakerStatus.RESTRICTED:
                return True, status  # Trading allowed but restricted
            elif status == CircuitBreakerStatus.CAUTIOUS:
                return True, status  # Trading allowed but with caution
            elif status == CircuitBreakerStatus.HALF_OPEN:
                # In half-open state, randomly allow some trades to test if conditions improved
                # Allow 1 in 10 trades at half normal size
                if random.random() > 0.9:
                    return True, status
                else:
                    return False, status
        
        # No breaker or closed breaker
        return True, CircuitBreakerStatus.CLOSED
    
    def _process_auto_resets(self) -> None:
        """Process any circuit breakers that should be auto-reset"""
        now = datetime.now()
        keys_to_update = []
        
        for key, breaker in self.circuit_breakers.items():
            if breaker["status"] != CircuitBreakerStatus.CLOSED.value and breaker.get("auto_reset_at"):
                auto_reset_time = datetime.fromisoformat(breaker["auto_reset_at"])
                if now >= auto_reset_time:
                    keys_to_update.append(key)
        
        for key in keys_to_update:
            breaker_type = self.circuit_breakers[key]["type"]
            scope = self.circuit_breakers[key]["scope"]
            current_status = self.circuit_breakers[key]["status"]
            
            # Implement graduated auto-reset (one level at a time)
            if current_status == CircuitBreakerStatus.OPEN.value:
                new_status = CircuitBreakerStatus.RESTRICTED.value
            elif current_status == CircuitBreakerStatus.RESTRICTED.value:
                new_status = CircuitBreakerStatus.CAUTIOUS.value
            elif current_status == CircuitBreakerStatus.CAUTIOUS.value:
                new_status = CircuitBreakerStatus.CLOSED.value
                # Remove breaker entirely if it's fully closed
                del self.circuit_breakers[key]
                logger.info(
                    f"Auto-closing circuit breaker - Type: {breaker_type}, "
                    f"Scope: {scope or 'global'}"
                )
                continue
            else:
                # Default to half-open for other statuses
                new_status = CircuitBreakerStatus.HALF_OPEN.value
            
            # Update the status if the breaker still exists
            if key in self.circuit_breakers:
                logger.info(
                    f"Auto-easing circuit breaker from {current_status} to {new_status} - Type: {breaker_type}, "
                    f"Scope: {scope or 'global'}"
                )
                
                self.circuit_breakers[key]["status"] = new_status
                self.circuit_breakers[key]["reset_attempted_at"] = now.isoformat()
                
                # Set a new auto-reset time based on the breaker type
                if breaker_type == CircuitBreakerType.VOLATILITY.value:
                    # Get reset time from volatility cool-down config
                    level = self._get_volatility_level_from_status(new_status)
                    minutes = self.config["volatility"]["cool_down_minutes"].get(level, 30)
                    self.circuit_breakers[key]["auto_reset_at"] = (now + timedelta(minutes=minutes)).isoformat()
                else:
                    # For other breaker types, use default reset time from config
                    config_key = breaker_type
                    if config_key in self.config:
                        minutes = self.config[config_key].get("reset_after_minutes", 30)
                        if minutes > 0:
                            self.circuit_breakers[key]["auto_reset_at"] = (now + timedelta(minutes=minutes)).isoformat()
        
        if keys_to_update:
            self._save_status()
    
    def _get_key(self, breaker_type: CircuitBreakerType, scope: Optional[str]) -> str:
        """Generate a unique key for a circuit breaker"""
        if scope:
            return f"{breaker_type.value}:{scope}"
        return breaker_type.value
    
    def get_status(
        self,
        breaker_type: Optional[CircuitBreakerType] = None,
        scope: Optional[str] = None
    ) -> Dict:
        """
        Get the status of all circuit breakers or specific ones
        
        Args:
            breaker_type: Optional specific type to check
            scope: Optional specific scope to check
            
        Returns:
            Dict with circuit breaker statuses
        """
        with self.lock:
            # Process any auto-resets first
            self._process_auto_resets()
            
            if breaker_type and scope:
                key = self._get_key(breaker_type, scope)
                if key in self.circuit_breakers:
                    return {key: self.circuit_breakers[key]}
                return {}
            
            if breaker_type:
                # Return all breakers of this type
                return {k: v for k, v in self.circuit_breakers.items() 
                        if k.startswith(breaker_type.value)}
            
            if scope:
                # Return all breakers for this scope
                return {k: v for k, v in self.circuit_breakers.items() 
                        if v.get("scope") == scope}
            
            # Return all breakers
            return self.circuit_breakers

    def get_active_breakers_count(self) -> Dict[str, int]:
        """
        Get count of active breakers by type and status
        
        Returns:
            Dict with counts by type and status
        """
        counts = {
            "total": 0,
            "by_type": {},
            "by_status": {}
        }
        
        for key, breaker in self.circuit_breakers.items():
            counts["total"] += 1
            
            # Count by type
            breaker_type = breaker["type"]
            counts["by_type"][breaker_type] = counts["by_type"].get(breaker_type, 0) + 1
            
            # Count by status
            status = breaker["status"]
            counts["by_status"][status] = counts["by_status"].get(status, 0) + 1
        
        return counts


# Singleton instance
_circuit_breaker_instance = None

def get_circuit_breaker(config_path: Optional[str] = None) -> CircuitBreaker:
    """Get the global circuit breaker instance"""
    global _circuit_breaker_instance
    if _circuit_breaker_instance is None:
        _circuit_breaker_instance = CircuitBreaker(config_path)
    return _circuit_breaker_instance