"""Market data simulation service.

This module provides realistic market data simulation for paper trading,
including price movements, bid-ask spreads, and volume variations.
"""

import logging
import random
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from fastapi import HTTPException, status

from app.core.config import settings
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class MarketSimulationService:
    """Service for simulating realistic market data."""

    def __init__(self, market_data_service: Optional[MarketDataService] = None):
        """Initialize with optional real market data service for seeding."""
        self.market_data = market_data_service
        self.simulated_prices = {}  # Cache for simulated prices
        self.last_update_time = {}  # Track when each symbol was last updated
        self.volatility_by_symbol = {}  # Simulated volatility by symbol

        # Simulation parameters
        self.update_interval_seconds = 5
        self.bid_ask_spread_pct = Decimal("0.0005")  # 0.05% spread
        self.default_volatility = Decimal("0.0015")  # 0.15% per interval
        self.max_gap_pct = Decimal("0.02")  # 2% max random gap

    def get_current_price(self, symbol: str) -> float:
        """Get current simulated price for a symbol."""
        # Check if we need to initialize or update the simulated price
        current_time = time.time()

        if (
            symbol not in self.simulated_prices
            or (current_time - self.last_update_time.get(symbol, 0))
            > self.update_interval_seconds
        ):
            self._update_simulated_price(symbol)

        # Return the mid price
        return float(self.simulated_prices[symbol]["mid"])

    def get_bid_ask(self, symbol: str) -> Tuple[float, float]:
        """Get simulated bid-ask prices for a symbol."""
        # Ensure price is updated
        self.get_current_price(symbol)

        # Return bid and ask
        return (
            float(self.simulated_prices[symbol]["bid"]),
            float(self.simulated_prices[symbol]["ask"]),
        )

    def get_price_history(
        self, symbol: str, days: int = 30, interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """Get simulated price history for a symbol."""
        try:
            # If we have a real market data service, use that for historical data
            if self.market_data:
                return self.market_data.get_price_history(symbol, days, interval)

            # Otherwise, generate synthetic data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get current price as a baseline
            current_price = self.get_current_price(symbol)

            # Use a random walk with drift to generate historical prices
            volatility = self.volatility_by_symbol.get(symbol, self.default_volatility)
            daily_drift = Decimal("0.0002")  # Slight upward bias

            # Generate daily returns (days - 1 because we start with current price)
            np.random.seed(hash(symbol) % 10000)  # Deterministic seed based on symbol
            returns = np.random.normal(
                float(daily_drift),
                float(volatility) * 3,  # Higher volatility for daily returns
                days - 1,
            )

            # Calculate prices working backwards from current price
            price = Decimal(str(current_price))
            prices = [price]

            for ret in returns:
                # Apply return in reverse order
                price = price / (Decimal(str(1 + ret)))
                prices.append(price)

            # Reverse to get chronological order
            prices.reverse()

            # Generate price history with OHLCV data
            history = []
            current_date = start_date

            for i, price in enumerate(prices):
                # Calculate high and low with some randomness
                daily_volatility = float(volatility) * 2
                high = float(price) * (1 + random.uniform(0, daily_volatility))
                low = float(price) * (1 - random.uniform(0, daily_volatility))

                # Ensure open and close are between high and low
                if i > 0:
                    prev_close = float(prices[i - 1])
                    open_price = prev_close
                else:
                    open_price = float(price) * (
                        1 - random.uniform(-daily_volatility / 2, daily_volatility / 2)
                    )

                close = float(price)

                # Ensure high is the highest, low is the lowest
                high = max(high, open_price, close)
                low = min(low, open_price, close)

                # Generate volume with some randomness
                base_volume = 100000 * (1 + abs(close - open_price) / close * 10)
                volume = int(base_volume * random.uniform(0.5, 1.5))

                history.append(
                    {
                        "timestamp": current_date.isoformat(),
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": volume,
                    }
                )

                current_date += timedelta(days=1)

            return history

        except Exception as e:
            logger.error(f"Error generating price history for {symbol}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to get price history: {str(e)}",
            )

    def get_market_depth(
        self, symbol: str, levels: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get simulated market depth (order book) for a symbol."""
        try:
            # Ensure price is updated
            current_price = self.get_current_price(symbol)
            bid, ask = self.get_bid_ask(symbol)

            # Initialize order book
            bids = []
            asks = []

            # Generate simulated bids
            bid_price = Decimal(str(bid))
            for i in range(levels):
                # Price decreases as we go down the book
                level_price = bid_price * (Decimal("1") - Decimal(str(i * 0.0005)))
                level_price = level_price.quantize(Decimal("0.00000001"))

                # Volume tends to be higher at prices further from the middle
                base_volume = 100 * (i + 1) ** 1.5
                volume = base_volume * random.uniform(0.8, 1.2)

                bids.append({"price": float(level_price), "quantity": round(volume, 2)})

            # Generate simulated asks
            ask_price = Decimal(str(ask))
            for i in range(levels):
                # Price increases as we go up the book
                level_price = ask_price * (Decimal("1") + Decimal(str(i * 0.0005)))
                level_price = level_price.quantize(Decimal("0.00000001"))

                # Volume tends to be higher at prices further from the middle
                base_volume = 100 * (i + 1) ** 1.5
                volume = base_volume * random.uniform(0.8, 1.2)

                asks.append({"price": float(level_price), "quantity": round(volume, 2)})

            return {"bids": bids, "asks": asks, "timestamp": datetime.now().isoformat()}

        except Exception as e:
            logger.error(f"Error generating market depth for {symbol}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to get market depth: {str(e)}",
            )

    def _update_simulated_price(self, symbol: str) -> None:
        """Update the simulated price for a symbol."""
        try:
            current_time = time.time()

            # If this is the first update, initialize with real data if available
            if symbol not in self.simulated_prices:
                if self.market_data:
                    try:
                        seed_price = Decimal(
                            str(self.market_data.get_current_price(symbol))
                        )
                        self._initialize_simulated_price(symbol, seed_price)
                    except Exception as e:
                        logger.warning(f"Failed to get real price for {symbol}: {e}")
                        self._initialize_simulated_price(symbol)
                else:
                    self._initialize_simulated_price(symbol)
            else:
                # Update existing price with random walk
                self._update_with_random_walk(symbol)

            # Update the last update time
            self.last_update_time[symbol] = current_time

        except Exception as e:
            logger.error(f"Error updating simulated price for {symbol}: {e}")
            # Initialize with a default price on error
            self._initialize_simulated_price(symbol)

    def _initialize_simulated_price(
        self, symbol: str, seed_price: Optional[Decimal] = None
    ) -> None:
        """Initialize the simulated price for a symbol."""
        # Use seed price if provided, otherwise use a symbol-based default
        if seed_price is None:
            # Generate a predictable but somewhat unique price based on symbol
            symbol_sum = sum(ord(c) for c in symbol)
            base_price = Decimal(str(50 + (symbol_sum % 450)))
            seed_price = base_price + Decimal(str(random.uniform(-5, 5)))

        # Set a symbol-specific volatility based on the symbol
        symbol_volatility = self.default_volatility * (
            1 + Decimal(str(random.uniform(-0.5, 1.0)))
        )
        self.volatility_by_symbol[symbol] = symbol_volatility

        # Set mid price
        mid_price = seed_price

        # Calculate bid and ask with a spread
        spread = mid_price * self.bid_ask_spread_pct
        bid_price = mid_price - spread
        ask_price = mid_price + spread

        # Store the prices
        self.simulated_prices[symbol] = {
            "mid": mid_price,
            "bid": bid_price,
            "ask": ask_price,
        }

    def _update_with_random_walk(self, symbol: str) -> None:
        """Update price using a random walk model."""
        # Get current mid price
        mid_price = self.simulated_prices[symbol]["mid"]

        # Get volatility for this symbol
        volatility = self.volatility_by_symbol.get(symbol, self.default_volatility)

        # Calculate random price change
        seconds_since_update = time.time() - self.last_update_time.get(
            symbol, time.time()
        )
        time_factor = Decimal(str(seconds_since_update / self.update_interval_seconds))

        # Add occasional price gaps for realism (more likely with longer time between updates)
        gap_probability = min(0.05 * time_factor, 0.2)  # 5% per interval, max 20%

        if random.random() < gap_probability:
            # Create a price gap
            gap_size = (
                volatility * Decimal(str(random.uniform(-2, 2))) * self.max_gap_pct
            )
            mid_price = mid_price * (Decimal("1") + gap_size)
        else:
            # Normal random walk
            random_change = (
                volatility * Decimal(str(random.uniform(-1, 1))) * time_factor
            )
            mid_price = mid_price * (Decimal("1") + random_change)

        # Ensure price doesn't go negative or too small
        mid_price = max(mid_price, Decimal("0.01"))

        # Calculate bid and ask with a spread
        spread = mid_price * self.bid_ask_spread_pct
        bid_price = mid_price - spread
        ask_price = mid_price + spread

        # Store the updated prices
        self.simulated_prices[symbol] = {
            "mid": mid_price,
            "bid": bid_price,
            "ask": ask_price,
        }
