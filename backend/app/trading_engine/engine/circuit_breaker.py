import json
import logging
import os
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class CircuitBreakerType(str, Enum):
    """Types of circuit breakers that can be triggered"""

    SYSTEM = "system"
    VOLATILITY = "volatility"
    DAILY_LOSS = "daily_loss"
    PER_STRATEGY = "per_strategy"
    CORRELATION = "correlation"
    API_FAILURE = "api_failure"
    LIQUIDITY = "liquidity"
    EXECUTION = "execution"
    MANUAL = "manual"


class CircuitBreakerStatus(str, Enum):
    """Status of the circuit breaker"""

    OPEN = "open"  # Trading suspended
    RESTRICTED = "restricted"  # Limited trading allowed
    CAUTIOUS = "cautious"  # Trading allowed with additional risk controls
    CLOSED = "closed"  # Trading allowed normally
    HALF_OPEN = "half_open"  # Testing if it's safe to re-enable trading


class VolatilityLevel(str, Enum):
    """Volatility levels corresponding to the volatility regimes"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class CircuitBreaker:
    """
    Implements a circuit breaker pattern to halt trading when risk thresholds
    are exceeded or system issues are detected.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the circuit breaker system"""
        self.circuit_breakers: Dict[str, Dict] = {}
        self.lock = threading.RLock()
        self.volatility_history = {}

        # Default configuration
        self.config = {
            "volatility": {
                "market_wide": {
                    "extreme": 0.35,
                    "high": 0.20,
                    "normal": 0.15,
                    "position_sizing": {"extreme": 0.03, "high": 0.10, "normal": 0.90, "low": 1.0},
                },
                "cool_down_minutes": {"extreme": 90, "high": 45, "normal": 20, "low": 0},
            },
            "daily_loss": {
                "portfolio_pct": 0.03,
                "graduated": {"warning": 0.02, "restricted": 0.025, "halt": 0.03},
                "position_sizing": {"warning": 0.75, "restricted": 0.50, "halt": 0.0},
                "reset_after_minutes": 0,
            },
            "execution": {"fail_rate_threshold": 0.3, "reset_after_minutes": 15},
            "api_failure": {"consecutive_failures": 3, "reset_after_minutes": 5},
            "system": {"reset_after_minutes": 0},
        }

        # Initialize status store for persistence
        self.status_file = "circuit_breaker_status.json"
        self._load_status()

    def _load_status(self) -> None:
        """Load the status of all circuit breakers from file"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, "r") as f:
                    status_data = json.load(f)
                    self.circuit_breakers = status_data
        except Exception as e:
            logger.error(f"Error loading circuit breaker status: {str(e)}")

    def _save_status(self) -> None:
        """Save the current status of all circuit breakers to file"""
        try:
            with open(self.status_file, "w") as f:
                json.dump(self.circuit_breakers, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving circuit breaker status: {str(e)}")

    def reset_all(self) -> None:
        """Reset all circuit breakers to closed state"""
        with self.lock:
            self.circuit_breakers = {}
            self._save_status()
        logger.warning("All circuit breakers have been reset")

    def trip(
        self,
        breaker_type: CircuitBreakerType,
        reason: str,
        scope: Optional[str] = None,
        reset_after: Optional[int] = None,
        status: CircuitBreakerStatus = CircuitBreakerStatus.OPEN,
    ) -> None:
        """
        Trip a circuit breaker to halt or restrict trading
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
                "auto_reset_at": auto_reset,
            }

            self._save_status()

        logger.warning(
            f"Circuit breaker triggered - Type: {breaker_type.value}, "
            f"Status: {status.value}, Scope: {scope or 'global'}, Reason: {reason}"
        )

    def reset(self, breaker_type: CircuitBreakerType, scope: Optional[str] = None) -> bool:
        """
        Manually reset a circuit breaker
        """
        with self.lock:
            key = self._get_key(breaker_type, scope)

            if key in self.circuit_breakers:
                current_status = self.circuit_breakers[key]["status"]

                if current_status == CircuitBreakerStatus.OPEN.value:
                    self.circuit_breakers[key]["status"] = CircuitBreakerStatus.RESTRICTED.value
                    self.circuit_breakers[key]["reset_attempted_at"] = datetime.utcnow().isoformat()
                    self._save_status()
                    logger.info(f"Circuit breaker eased from OPEN to RESTRICTED - Type: {breaker_type.value}")
                    return True
                elif current_status == CircuitBreakerStatus.RESTRICTED.value:
                    self.circuit_breakers[key]["status"] = CircuitBreakerStatus.CAUTIOUS.value
                    self.circuit_breakers[key]["reset_attempted_at"] = datetime.utcnow().isoformat()
                    self._save_status()
                    logger.info(f"Circuit breaker eased from RESTRICTED to CAUTIOUS - Type: {breaker_type.value}")
                    return True
                elif current_status == CircuitBreakerStatus.CAUTIOUS.value:
                    del self.circuit_breakers[key]
                    self._save_status()
                    logger.info(f"Circuit breaker fully closed - Type: {breaker_type.value}")
                    return True
            return False

    def check(
        self, breaker_type: Optional[CircuitBreakerType] = None, scope: Optional[str] = None
    ) -> Tuple[bool, CircuitBreakerStatus]:
        """
        Check if trading is allowed based on circuit breakers
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
            CircuitBreakerStatus.CLOSED: 0,
        }

        return restriction_level.get(status1, 0) > restriction_level.get(status2, 0)

    def _check_single_breaker(self, key: str) -> Tuple[bool, CircuitBreakerStatus]:
        """Check if a specific breaker allows trading"""
        if key in self.circuit_breakers:
            status_str = self.circuit_breakers[key]["status"]
            status = CircuitBreakerStatus(status_str)

            if status == CircuitBreakerStatus.OPEN:
                return False, status
            elif status in [CircuitBreakerStatus.RESTRICTED, CircuitBreakerStatus.CAUTIOUS]:
                return True, status  # Trading allowed but restricted/cautious
            elif status == CircuitBreakerStatus.HALF_OPEN:
                # In half-open state, allow limited testing
                return True, status

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
            current_status = self.circuit_breakers[key]["status"]

            # Implement graduated auto-reset
            if current_status == CircuitBreakerStatus.OPEN.value:
                new_status = CircuitBreakerStatus.RESTRICTED.value
            elif current_status == CircuitBreakerStatus.RESTRICTED.value:
                new_status = CircuitBreakerStatus.CAUTIOUS.value
            elif current_status == CircuitBreakerStatus.CAUTIOUS.value:
                # Remove breaker entirely
                del self.circuit_breakers[key]
                logger.info(f"Auto-closing circuit breaker - Type: {breaker_type}")
                continue
            else:
                new_status = CircuitBreakerStatus.HALF_OPEN.value

            # Update the status
            if key in self.circuit_breakers:
                self.circuit_breakers[key]["status"] = new_status
                self.circuit_breakers[key]["reset_attempted_at"] = now.isoformat()

        if keys_to_update:
            self._save_status()

    def _get_key(self, breaker_type: CircuitBreakerType, scope: Optional[str]) -> str:
        """Generate a unique key for a circuit breaker"""
        if scope:
            return f"{breaker_type.value}:{scope}"
        return breaker_type.value

    def get_status(self, breaker_type: Optional[CircuitBreakerType] = None, scope: Optional[str] = None) -> Dict:
        """
        Get the status of all circuit breakers or specific ones
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
                return {k: v for k, v in self.circuit_breakers.items() if k.startswith(breaker_type.value)}

            if scope:
                # Return all breakers for this scope
                return {k: v for k, v in self.circuit_breakers.items() if v.get("scope") == scope}

            # Return all breakers
            return self.circuit_breakers

    def get_position_sizing(
        self, breaker_type: Optional[CircuitBreakerType] = None, scope: Optional[str] = None
    ) -> float:
        """
        Return position sizing multiplier based on current state.
        """
        # Get the circuit breaker status
        allowed, status = self.check(breaker_type, scope) if breaker_type else (True, CircuitBreakerStatus.CLOSED)

        if status == CircuitBreakerStatus.OPEN:
            return 0.0
        elif status == CircuitBreakerStatus.RESTRICTED:
            return 0.25  # 25% of normal position size
        elif status == CircuitBreakerStatus.CAUTIOUS:
            return 0.75  # 75% of normal position size
        else:  # CLOSED or HALF_OPEN
            return 1.0  # Full position size


# Singleton instance
_circuit_breaker_instance = None


def get_circuit_breaker(config_path: Optional[str] = None) -> CircuitBreaker:
    """Get the global circuit breaker instance"""
    global _circuit_breaker_instance
    if _circuit_breaker_instance is None:
        _circuit_breaker_instance = CircuitBreaker(config_path)
    return _circuit_breaker_instance
