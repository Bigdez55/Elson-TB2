"""Broker package for trading execution.

This package provides broker implementations for paper trading and real broker APIs.
It includes a factory pattern for creating broker instances based on configuration.
"""

from app.services.broker.base import BaseBroker, BrokerError
from app.services.broker.paper import PaperBroker
from app.services.broker.factory import get_broker, BrokerType, broker_factory

__all__ = [
    'BaseBroker',
    'BrokerError',
    'PaperBroker',
    'get_broker',
    'BrokerType',
    'broker_factory',
]