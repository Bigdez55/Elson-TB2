"""
AI/ML Trading Service for Personal Trading Platform

This module provides AI-driven trading insights, portfolio optimization,
and market analysis specifically designed for personal use.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import structlog
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from xgboost import XGBRegressor

from app.models.portfolio import Holding, Portfolio
from app.models.user import User
from app.services.market_data import market_data_service

logger = structlog.get_logger()


class PersonalTradingAI:
    """
    AI service for personal trading optimization and market analysis.
    Designed for single-user scenarios with focus on practical insights.
    """

    def __init__(self):
        self.volatility_model = XGBRegressor(n_estimators=100, random_state=42)
        self.sentiment_model = RandomForestRegressor(
            n_estimators=50, random_state=42
        )
        self.scaler = StandardScaler()
        self._models_trained = False

    async def analyze_portfolio_risk(
        self, portfolio: Portfolio, db: Session
    ) -> Dict[str, Any]:
        """
        Analyze portfolio risk profile and provide recommendations.

        Args:
            portfolio: Portfolio to analyze
            db: Database session

        Returns:
            Risk analysis with recommendations
        """
        try:
            holdings = portfolio.holdings
            if not holdings:
                return {
                    "risk_score": 0,
                    "risk_level": "No holdings",
                    "recommendations": [
                        "Add diversified holdings to start analysis"
                    ],
                }

            # Calculate portfolio metrics
            total_value = sum(h.market_value for h in holdings)
            allocations = [h.market_value / total_value for h in holdings]

            # Concentration risk
            max_allocation = max(allocations)
            concentration_risk = (
                max_allocation > 0.25
            )  # More than 25% in one asset

            # Sector/asset type diversification
            asset_types = {}
            for holding in holdings:
                asset_type = holding.asset_type
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1

            diversification_score = len(asset_types) / len(holdings)

            # Calculate risk score (0-100)
            risk_score = 0
            risk_factors = []

            if concentration_risk:
                risk_score += 30
                risk_factors.append(
                    f"High concentration: {max_allocation:.1%} in single asset"
                )

            if diversification_score < 0.5:
                risk_score += 20
                risk_factors.append("Limited asset type diversification")

            if len(holdings) < 5:
                risk_score += 15
                risk_factors.append("Portfolio has fewer than 5 holdings")

            # Get volatility data for major holdings
            volatility_risk = await self._calculate_volatility_risk(holdings)
            risk_score += volatility_risk

            # Determine risk level
            if risk_score < 20:
                risk_level = "Conservative"
            elif risk_score < 40:
                risk_level = "Moderate"
            elif risk_score < 60:
                risk_level = "Aggressive"
            else:
                risk_level = "High Risk"

            recommendations = await self._generate_risk_recommendations(
                portfolio, risk_factors, db
            )

            return {
                "risk_score": min(risk_score, 100),
                "risk_level": risk_level,
                "concentration_risk": concentration_risk,
                "diversification_score": diversification_score,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "analysis_date": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error in portfolio risk analysis", error=str(e))
            return {
                "error": "Failed to analyze portfolio risk",
                "risk_score": 50,
                "risk_level": "Unknown",
            }

    async def generate_trading_signals(
        self, symbols: List[str], user: User
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-driven trading signals for given symbols.

        Args:
            symbols: List of symbols to analyze
            user: User for personalized signals

        Returns:
            List of trading signals with confidence scores
        """
        signals = []

        for symbol in symbols[:10]:  # Limit to 10 symbols for performance
            try:
                signal = await self._analyze_symbol_signal(symbol, user)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.warning(
                    "Failed to generate signal for symbol",
                    symbol=symbol,
                    error=str(e),
                )

        return sorted(
            signals, key=lambda x: x.get("confidence", 0), reverse=True
        )

    async def _analyze_symbol_signal(
        self, symbol: str, user: User
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single symbol for trading signals."""
        try:
            # Get historical data
            historical_data = await market_data_service.get_historical_data(
                symbol, period="3mo"
            )

            if not historical_data or len(historical_data) < 20:
                return None

            df = pd.DataFrame(historical_data)

            # Calculate technical indicators
            df["sma_20"] = df["close"].rolling(window=20).mean()
            df["sma_50"] = df["close"].rolling(window=50).mean()
            df["rsi"] = self._calculate_rsi(df["close"])
            df["volatility"] = df["close"].pct_change().rolling(20).std()

            current_price = df["close"].iloc[-1]
            sma_20 = df["sma_20"].iloc[-1]
            sma_50 = df["sma_50"].iloc[-1]
            rsi = df["rsi"].iloc[-1]
            volatility = df["volatility"].iloc[-1]

            # Generate signal based on technical analysis
            signal_strength = 0
            reasons = []

            # Moving average signals
            if current_price > sma_20 > sma_50:
                signal_strength += 0.3
                reasons.append("Price above both moving averages (bullish)")
            elif current_price < sma_20 < sma_50:
                signal_strength -= 0.3
                reasons.append("Price below both moving averages (bearish)")

            # RSI signals
            if rsi < 30:
                signal_strength += 0.2
                reasons.append("RSI indicates oversold condition")
            elif rsi > 70:
                signal_strength -= 0.2
                reasons.append("RSI indicates overbought condition")

            # Volatility consideration
            if volatility > 0.05:  # High volatility
                signal_strength *= 0.8  # Reduce confidence
                reasons.append("High volatility detected")

            # Personal risk tolerance adjustment
            if user.risk_tolerance == "conservative":
                signal_strength *= 0.7
            elif user.risk_tolerance == "aggressive":
                signal_strength *= 1.2

            # Determine action
            if signal_strength > 0.3:
                action = "BUY"
            elif signal_strength < -0.3:
                action = "SELL"
            else:
                action = "HOLD"

            confidence = min(abs(signal_strength) * 100, 95)

            return {
                "symbol": symbol,
                "action": action,
                "confidence": round(confidence, 1),
                "current_price": current_price,
                "target_price": self._calculate_target_price(
                    current_price, signal_strength
                ),
                "reasons": reasons,
                "technical_indicators": {
                    "rsi": round(rsi, 2),
                    "sma_20": round(sma_20, 2),
                    "sma_50": round(sma_50, 2),
                    "volatility": round(volatility * 100, 2),
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                "Error analyzing symbol signal", symbol=symbol, error=str(e)
            )
            return None

    def _calculate_rsi(
        self, prices: pd.Series, periods: int = 14
    ) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_target_price(
        self, current_price: float, signal_strength: float
    ) -> float:
        """Calculate target price based on signal strength."""
        if signal_strength > 0:
            # Bullish target (3-8% upside)
            return current_price * (1 + 0.03 + signal_strength * 0.05)
        else:
            # Bearish target (3-8% downside)
            return current_price * (1 + 0.03 + signal_strength * 0.05)

    async def _calculate_volatility_risk(self, holdings: List[Holding]) -> int:
        """Calculate volatility-based risk score."""
        try:
            volatility_scores = []

            for holding in holdings[:5]:  # Check top 5 holdings
                historical_data = (
                    await market_data_service.get_historical_data(
                        holding.symbol, period="1mo"
                    )
                )

                if historical_data:
                    prices = [float(d["close"]) for d in historical_data]
                    returns = pd.Series(prices).pct_change().dropna()
                    volatility = returns.std() * np.sqrt(
                        252
                    )  # Annualized volatility

                    # Convert volatility to risk score (0-30)
                    vol_score = min(volatility * 100, 30)
                    volatility_scores.append(vol_score)

            return int(np.mean(volatility_scores)) if volatility_scores else 0

        except Exception as e:
            logger.warning("Error calculating volatility risk", error=str(e))
            return 15  # Default moderate risk

    async def _generate_risk_recommendations(
        self, portfolio: Portfolio, risk_factors: List[str], db: Session
    ) -> List[str]:
        """Generate personalized risk management recommendations."""
        recommendations = []

        holdings = portfolio.holdings
        total_value = sum(h.market_value for h in holdings)

        # Diversification recommendations
        if len(holdings) < 5:
            recommendations.append(
                "Consider adding more holdings to improve diversification"
            )

        # Rebalancing recommendations
        if portfolio.auto_rebalance:
            recommendations.append(
                "Auto-rebalancing is enabled - review thresholds regularly"
            )
        else:
            recommendations.append(
                "Consider enabling auto-rebalancing for better risk management"
            )

        # Concentration risk
        for holding in holdings:
            allocation = holding.market_value / total_value
            if allocation > 0.25:
                recommendations.append(
                    f"Consider reducing {holding.symbol} position "
                    f"({allocation:.1%} of portfolio)"
                )

        # Cash allocation
        cash_percentage = portfolio.cash_balance / portfolio.total_value
        if cash_percentage < 0.05:
            recommendations.append(
                "Consider maintaining 5-10% cash for opportunities"
            )
        elif cash_percentage > 0.20:
            recommendations.append(
                "High cash allocation - consider deploying excess cash"
            )

        return recommendations

    async def optimize_portfolio_allocation(
        self, portfolio: Portfolio, target_allocations: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Optimize portfolio allocation using modern portfolio theory principles.

        Args:
            portfolio: Portfolio to optimize
            target_allocations: Target allocation percentages by asset/sector

        Returns:
            Optimization recommendations
        """
        try:
            holdings = portfolio.holdings
            if not holdings:
                return {"error": "No holdings to optimize"}

            current_allocations = {}
            total_value = sum(h.market_value for h in holdings)

            for holding in holdings:
                current_allocations[holding.symbol] = (
                    holding.market_value / total_value
                )

            # Calculate rebalancing needs
            rebalancing_actions = []

            for symbol, current_alloc in current_allocations.items():
                target_alloc = target_allocations.get(symbol, 0)
                difference = target_alloc - current_alloc

                if abs(difference) > 0.02:  # 2% threshold
                    action_type = "INCREASE" if difference > 0 else "DECREASE"
                    amount = abs(difference) * total_value

                    rebalancing_actions.append(
                        {
                            "symbol": symbol,
                            "action": action_type,
                            "current_allocation": round(
                                current_alloc * 100, 1
                            ),
                            "target_allocation": round(target_alloc * 100, 1),
                            "amount_needed": round(amount, 2),
                            "difference_pct": round(difference * 100, 1),
                        }
                    )

            return {
                "total_portfolio_value": total_value,
                "current_allocations": {
                    k: round(v * 100, 1)
                    for k, v in current_allocations.items()
                },
                "target_allocations": {
                    k: round(v * 100, 1) for k, v in target_allocations.items()
                },
                "rebalancing_actions": rebalancing_actions,
                "rebalancing_needed": len(rebalancing_actions) > 0,
                "optimization_date": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Error in portfolio optimization", error=str(e))
            return {"error": "Failed to optimize portfolio allocation"}


# Singleton instance
personal_trading_ai = PersonalTradingAI()
