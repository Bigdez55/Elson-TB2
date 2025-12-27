"""Base broker interface for trading.

This module defines the abstract base class for all broker implementations,
allowing the application to seamlessly switch between different broker APIs
and paper trading.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.models.trade import Trade

logger = logging.getLogger(__name__)


class BaseBroker(ABC):
    """Abstract base class for broker implementations."""

    @abstractmethod
    def execute_trade(self, trade: Trade) -> Dict[str, Any]:
        """Execute a trade and return execution details."""
        pass

    @abstractmethod
    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """Get account information."""
        pass

    @abstractmethod
    def get_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get current positions for an account."""
        pass

    @abstractmethod
    def get_trade_status(self, broker_order_id: str) -> Dict[str, Any]:
        """Get the current status of a trade."""
        pass

    @abstractmethod
    def cancel_trade(self, broker_order_id: str) -> bool:
        """Cancel a pending trade."""
        pass

    @abstractmethod
    def get_order_history(
        self,
        account_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get order history for an account."""
        pass

    @abstractmethod
    def get_trade_execution(self, broker_order_id: str) -> Dict[str, Any]:
        """Get detailed execution information for a completed trade."""
        pass

    # Optional methods that may not be supported by all brokers

    def get_market_hours(self, market: str) -> Dict[str, Any]:
        """Get market hours information."""
        raise NotImplementedError("Market hours not supported by this broker")

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get a quote for a symbol."""
        raise NotImplementedError("Quotes not supported by this broker")

    def place_bracket_order(
        self, trade: Trade, take_profit_price: float, stop_loss_price: float
    ) -> Dict[str, Any]:
        """Place a bracket order (entry + take profit + stop loss)."""
        raise NotImplementedError("Bracket orders not supported by this broker")

    def place_trailing_stop(
        self, trade: Trade, trail_amount: float, trail_type: str = "percent"
    ) -> Dict[str, Any]:
        """Place a trailing stop order."""
        raise NotImplementedError("Trailing stops not supported by this broker")

    def place_conditional_order(
        self,
        trade: Trade,
        condition_type: str,
        condition_symbol: str,
        condition_price: float,
    ) -> Dict[str, Any]:
        """Place a conditional order based on another symbol's price."""
        raise NotImplementedError("Conditional orders not supported by this broker")


class BrokerError(Exception):
    """Exception for broker-related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        broker_response: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with error details.

        Args:
            message: Error message
            error_code: Error code from broker
            broker_response: Full response from broker
            metadata: Additional metadata about the error (retry info, etc.)
        """
        self.message = message
        self.error_code = error_code
        self.broker_response = broker_response
        self.metadata = metadata or {}
        super().__init__(self.message)
