"""Broker services package.

This package provides interfaces and implementations for various broker APIs,
enabling the trading platform to execute trades through different brokerages.
"""

from .base import BaseBroker, BrokerError
from .alpaca import AlpacaBroker
from .factory import BrokerFactory, get_broker, get_paper_broker, get_live_broker

__all__ = [
    "BaseBroker",
    "BrokerError",
    "AlpacaBroker",
    "BrokerFactory",
    "get_broker",
    "get_paper_broker",
    "get_live_broker",
]
