"""
Strategy Registry - Factory pattern for managing all trading strategies.

Provides centralized registration, instantiation, and management of trading strategies.
"""

import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from .base import TradingStrategy

logger = logging.getLogger(__name__)


class StrategyCategory(str, Enum):
    """Categories for organizing trading strategies"""

    TECHNICAL = "technical"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    BREAKOUT = "breakout"
    ML = "ml"
    SENTIMENT = "sentiment"
    PORTFOLIO = "portfolio"
    EXECUTION = "execution"
    GRID = "grid"
    OPTIONS = "options"


class StrategyInfo:
    """Metadata about a registered strategy"""

    def __init__(
        self,
        name: str,
        strategy_class: Type[TradingStrategy],
        category: StrategyCategory,
        description: str,
        default_parameters: Dict[str, Any],
        required_data: List[str],
        timeframes: List[str],
        risk_level: str = "medium",
    ):
        self.name = name
        self.strategy_class = strategy_class
        self.category = category
        self.description = description
        self.default_parameters = default_parameters
        self.required_data = required_data
        self.timeframes = timeframes
        self.risk_level = risk_level


class StrategyRegistry:
    """
    Central registry for all trading strategies.

    Implements the factory pattern to create strategy instances
    and provides metadata about available strategies.
    """

    _instance = None
    _strategies: Dict[str, StrategyInfo] = {}

    def __new__(cls):
        """Singleton pattern to ensure one registry instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._strategies = {}
        return cls._instance

    @classmethod
    def register(
        cls,
        name: str,
        category: StrategyCategory,
        description: str = "",
        default_parameters: Optional[Dict[str, Any]] = None,
        required_data: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        risk_level: str = "medium",
    ) -> Callable:
        """
        Decorator to register a strategy class.

        Usage:
            @StrategyRegistry.register(
                name="rsi_strategy",
                category=StrategyCategory.TECHNICAL,
                description="RSI-based trading strategy"
            )
            class RSIStrategy(TradingStrategy):
                ...
        """

        def decorator(strategy_class: Type[TradingStrategy]) -> Type[TradingStrategy]:
            cls._strategies[name] = StrategyInfo(
                name=name,
                strategy_class=strategy_class,
                category=category,
                description=description,
                default_parameters=default_parameters or {},
                required_data=required_data or ["close"],
                timeframes=timeframes or ["1d"],
                risk_level=risk_level,
            )
            logger.info(f"Registered strategy: {name} in category: {category}")
            return strategy_class

        return decorator

    @classmethod
    def create(
        cls, name: str, symbol: str, market_data_service: Any = None, **kwargs
    ) -> Optional[TradingStrategy]:
        """
        Create an instance of a registered strategy.

        Args:
            name: Name of the registered strategy
            symbol: Trading symbol
            market_data_service: Market data service instance
            **kwargs: Additional parameters to pass to strategy constructor

        Returns:
            Strategy instance or None if not found
        """
        if name not in cls._strategies:
            logger.error(f"Strategy not found: {name}")
            return None

        info = cls._strategies[name]

        # Merge default parameters with provided kwargs
        parameters = {**info.default_parameters, **kwargs}

        try:
            strategy = info.strategy_class(
                symbol=symbol, market_data_service=market_data_service, **parameters
            )
            logger.info(f"Created strategy instance: {name} for {symbol}")
            return strategy
        except Exception as e:
            logger.error(f"Error creating strategy {name}: {str(e)}")
            return None

    @classmethod
    def get_info(cls, name: str) -> Optional[StrategyInfo]:
        """Get metadata about a registered strategy"""
        return cls._strategies.get(name)

    @classmethod
    def list_strategies(cls, category: Optional[StrategyCategory] = None) -> List[str]:
        """List all registered strategies, optionally filtered by category"""
        if category is None:
            return list(cls._strategies.keys())
        return [
            name for name, info in cls._strategies.items() if info.category == category
        ]

    @classmethod
    def list_categories(cls) -> List[StrategyCategory]:
        """List all strategy categories"""
        return list(StrategyCategory)

    @classmethod
    def get_all_info(cls) -> Dict[str, Dict[str, Any]]:
        """Get metadata about all registered strategies"""
        return {
            name: {
                "name": info.name,
                "category": info.category.value,
                "description": info.description,
                "default_parameters": info.default_parameters,
                "required_data": info.required_data,
                "timeframes": info.timeframes,
                "risk_level": info.risk_level,
            }
            for name, info in cls._strategies.items()
        }

    @classmethod
    def get_strategies_by_risk(cls, risk_level: str) -> List[str]:
        """Get strategies filtered by risk level"""
        return [
            name
            for name, info in cls._strategies.items()
            if info.risk_level == risk_level
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered strategies (mainly for testing)"""
        cls._strategies.clear()
        logger.info("Cleared strategy registry")


# Convenience function for creating strategies
def create_strategy(
    name: str, symbol: str, market_data_service: Any = None, **kwargs
) -> Optional[TradingStrategy]:
    """Convenience function to create a strategy instance"""
    return StrategyRegistry.create(name, symbol, market_data_service, **kwargs)


def list_available_strategies(category: Optional[str] = None) -> List[str]:
    """List available strategies, optionally by category"""
    if category:
        try:
            cat = StrategyCategory(category)
            return StrategyRegistry.list_strategies(cat)
        except ValueError:
            return []
    return StrategyRegistry.list_strategies()
