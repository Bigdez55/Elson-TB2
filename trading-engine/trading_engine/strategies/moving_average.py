import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

# Trade models imported but not used in current implementation
from app.services.market_data import MarketDataService

from .base import TradingStrategy

logger = logging.getLogger(__name__)


class MovingAverageStrategy(TradingStrategy):
    """
    Moving Average Crossover Strategy with RSI and Volume confirmation

    This strategy generates buy/sell signals based on:
    - Short-term and long-term moving average crossovers
    - RSI overbought/oversold levels
    - Volume confirmation
    - MACD trend confirmation
    """

    def __init__(
        self,
        symbol: str,
        market_data_service: MarketDataService,
        short_window: int = 20,
        long_window: int = 50,
        rsi_period: int = 14,
        rsi_overbought: int = 70,
        rsi_oversold: int = 30,
        volume_factor: float = 1.5,
        **kwargs,
    ):
        """
        Initialize the Moving Average Strategy

        Args:
            symbol: Trading symbol
            market_data_service: Market data service instance
            short_window: Short-term moving average period
            long_window: Long-term moving average period
            rsi_period: RSI calculation period
            rsi_overbought: RSI overbought threshold
            rsi_oversold: RSI oversold threshold
            volume_factor: Volume confirmation factor
        """
        super().__init__(
            symbol=symbol,
            name="Moving Average Crossover",
            description="Moving average crossover strategy with RSI and volume confirmation",
            parameters={
                "short_window": short_window,
                "long_window": long_window,
                "rsi_period": rsi_period,
                "rsi_overbought": rsi_overbought,
                "rsi_oversold": rsi_oversold,
                "volume_factor": volume_factor,
                "max_position_pct": kwargs.get("max_position_pct", 0.05),
                "base_position_pct": kwargs.get("base_position_pct", 0.02),
                "confidence_multiplier": kwargs.get("confidence_multiplier", 1.5),
                "min_confidence": kwargs.get("min_confidence", 0.6),
            },
        )
        self.market_data_service = market_data_service
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volume_factor = volume_factor

        # Strategy state
        self.last_crossover = None
        self.last_indicators = {}

    async def generate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a trading signal based on market data
        """
        try:
            # Get historical data for indicator calculations
            df = await self._get_historical_data()

            if df is None or len(df) < self.long_window:
                logger.warning(f"Insufficient data for {self.symbol}")
                return {
                    "action": "hold",
                    "confidence": 0.0,
                    "price": market_data.get("price", 0.0),
                    "reason": "Insufficient historical data",
                }

            # Calculate indicators
            df_with_indicators = self._calculate_indicators(df)

            # Generate trading decision
            signal = self._generate_trading_decision(df_with_indicators)

            # Update last signal time
            self.last_signal_time = datetime.utcnow()

            return signal

        except Exception as e:
            logger.error(f"Error generating signal for {self.symbol}: {str(e)}")
            return {
                "action": "hold",
                "confidence": 0.0,
                "price": market_data.get("price", 0.0),
                "reason": f"Error: {str(e)}",
            }

    async def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """
        Update strategy parameters
        """
        try:
            for key, value in new_parameters.items():
                if key in self.parameters:
                    self.parameters[key] = value
                    # Update instance variables
                    if hasattr(self, key):
                        setattr(self, key, value)

            logger.info(f"Updated parameters for {self.name}: {new_parameters}")
            return True
        except Exception as e:
            logger.error(f"Error updating parameters: {str(e)}")
            return False

    async def _get_historical_data(self) -> Optional[pd.DataFrame]:
        """Get historical market data for analysis"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(
                days=100
            )  # Get enough data for indicators

            # Get historical data from market data service
            data = await self.market_data_service.get_historical_data(
                self.symbol, start_date.isoformat(), end_date.isoformat()
            )

            if not data:
                return None

            # Convert to DataFrame if it's not already
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = data

            # Ensure required columns exist
            required_columns = ["timestamp", "close", "volume"]
            for col in required_columns:
                if col not in df.columns and col.lower() in df.columns:
                    df[col] = df[col.lower()]
                elif col not in df.columns and col.capitalize() in df.columns:
                    df[col] = df[col.capitalize()]

            if not all(col in df.columns for col in required_columns):
                logger.warning(f"Missing required columns in data for {self.symbol}")
                return None

            # Sort by timestamp
            df = df.sort_values("timestamp")
            df = df.reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        try:
            # Ensure we have numeric columns
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

            # Calculate moving averages
            df["sma_short"] = df["close"].rolling(window=self.short_window).mean()
            df["sma_long"] = df["close"].rolling(window=self.long_window).mean()

            # Calculate RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            # Calculate volume moving average
            df["volume_ma"] = df["volume"].rolling(window=20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_ma"]

            # Calculate MACD
            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            df["macd"] = exp1 - exp2
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

            # Generate crossover signals
            df["signal"] = 0
            df.loc[df["sma_short"] > df["sma_long"], "signal"] = 1
            df.loc[df["sma_short"] < df["sma_long"], "signal"] = -1

            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return df

    def _generate_trading_decision(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading decision based on signals"""
        try:
            if len(df) < 2:
                return {
                    "action": "hold",
                    "confidence": 0.0,
                    "price": float(df.iloc[-1]["close"]) if len(df) > 0 else 0.0,
                    "reason": "Insufficient data for decision",
                }

            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            # Check for missing values
            if pd.isna(last_row["signal"]) or pd.isna(prev_row["signal"]):
                return {
                    "action": "hold",
                    "confidence": 0.0,
                    "price": float(last_row["close"]),
                    "reason": "Incomplete indicator calculations",
                }

            signal_action = "hold"
            confidence = 0.0

            # Detect crossover
            if prev_row["signal"] != last_row["signal"]:
                if last_row["signal"] == 1:  # Bullish crossover
                    signal_action = "buy"
                    self.last_crossover = "bullish"
                elif last_row["signal"] == -1:  # Bearish crossover
                    signal_action = "sell"
                    self.last_crossover = "bearish"

                # Calculate confidence for the crossover signal
                confidence = self._calculate_signal_confidence(last_row)

            # Store last indicators for debugging
            self.last_indicators = {
                "rsi": float(last_row.get("rsi", 0))
                if not pd.isna(last_row.get("rsi", np.nan))
                else 0,
                "macd": float(last_row.get("macd", 0))
                if not pd.isna(last_row.get("macd", np.nan))
                else 0,
                "volume_ratio": float(last_row.get("volume_ratio", 0))
                if not pd.isna(last_row.get("volume_ratio", np.nan))
                else 0,
                "sma_short": float(last_row.get("sma_short", 0))
                if not pd.isna(last_row.get("sma_short", np.nan))
                else 0,
                "sma_long": float(last_row.get("sma_long", 0))
                if not pd.isna(last_row.get("sma_long", np.nan))
                else 0,
            }

            # Create signal dictionary
            signal = {
                "action": signal_action,
                "confidence": confidence,
                "price": float(last_row["close"]),
                "timestamp": datetime.utcnow().isoformat(),
                "indicators": self.last_indicators,
                "reason": f"Moving average crossover: {self.last_crossover}"
                if self.last_crossover
                else "No crossover detected",
            }

            # Add stop loss and take profit if it's a buy/sell signal
            if signal_action in ["buy", "sell"]:
                signal.update(
                    self._calculate_stop_loss_take_profit(last_row, signal_action)
                )

            return signal

        except Exception as e:
            logger.error(f"Error generating trading decision: {str(e)}")
            return {
                "action": "hold",
                "confidence": 0.0,
                "price": 0.0,
                "reason": f"Error: {str(e)}",
            }

    def _calculate_signal_confidence(self, row: pd.Series) -> float:
        """Calculate confidence score for signal"""
        try:
            confidence = 0.0
            weights = {"crossover": 0.4, "rsi": 0.2, "volume": 0.2, "macd": 0.2}

            # Crossover confidence (base signal)
            if self.last_crossover in ["bullish", "bearish"]:
                confidence += weights["crossover"]

            # RSI confirmation
            rsi = row.get("rsi", 50)
            if not pd.isna(rsi):
                if self.last_crossover == "bullish" and rsi < self.rsi_oversold:
                    confidence += weights["rsi"]
                elif self.last_crossover == "bearish" and rsi > self.rsi_overbought:
                    confidence += weights["rsi"]
                elif self.rsi_oversold < rsi < self.rsi_overbought:
                    confidence += (
                        weights["rsi"] * 0.5
                    )  # Neutral RSI gets partial credit

            # Volume confirmation
            volume_ratio = row.get("volume_ratio", 1.0)
            if not pd.isna(volume_ratio) and volume_ratio > self.volume_factor:
                confidence += weights["volume"]

            # MACD confirmation
            macd = row.get("macd", 0)
            macd_signal = row.get("macd_signal", 0)
            if not pd.isna(macd) and not pd.isna(macd_signal):
                if (self.last_crossover == "bullish" and macd > macd_signal) or (
                    self.last_crossover == "bearish" and macd < macd_signal
                ):
                    confidence += weights["macd"]

            return min(confidence, 1.0)  # Cap at 1.0

        except Exception as e:
            logger.error(f"Error calculating signal confidence: {str(e)}")
            return 0.0

    def _calculate_stop_loss_take_profit(
        self, row: pd.Series, action: str
    ) -> Dict[str, float]:
        """Calculate stop loss and take profit levels"""
        try:
            current_price = float(row["close"])

            if action == "buy":
                # For buy orders: stop loss below, take profit above
                stop_loss = current_price * 0.98  # 2% stop loss
                take_profit = current_price * 1.06  # 6% take profit
            else:  # sell
                # For sell orders: stop loss above, take profit below
                stop_loss = current_price * 1.02  # 2% stop loss
                take_profit = current_price * 0.94  # 6% take profit

            return {"stop_loss": stop_loss, "take_profit": take_profit}

        except Exception as e:
            logger.error(f"Error calculating stop loss/take profit: {str(e)}")
            return {}

    async def _custom_validation(
        self, signal: Dict[str, Any], market_data: Dict[str, Any]
    ) -> bool:
        """
        Custom validation for moving average strategy
        """
        try:
            # Check if we have recent crossover
            if signal["action"] != "hold" and not self.last_crossover:
                logger.debug("No crossover detected, signal invalid")
                return False

            # Check minimum confidence for this strategy
            min_confidence = self.parameters.get("min_confidence", 0.6)
            if signal["confidence"] < min_confidence:
                logger.debug(
                    f"Signal confidence {signal['confidence']:.2f} below strategy minimum {min_confidence:.2f}"
                )
                return False

            # Check if indicators are reasonable
            indicators = signal.get("indicators", {})
            rsi = indicators.get("rsi", 50)

            # RSI should be in valid range
            if not 0 <= rsi <= 100:
                logger.warning(f"Invalid RSI value: {rsi}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error in custom validation: {str(e)}")
            return False
