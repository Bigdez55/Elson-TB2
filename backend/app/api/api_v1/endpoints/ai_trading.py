"""
AI Trading API endpoints for personal trading platform.
"""

from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.base import get_db
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.ai_trading import personal_trading_ai

logger = structlog.get_logger()

router = APIRouter()


@router.get("/portfolio-risk/{portfolio_id}")
async def analyze_portfolio_risk(
    portfolio_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Analyze portfolio risk and get AI-driven recommendations.

    Returns risk score, risk factors, and personalized recommendations.
    """
    # Get portfolio and verify ownership
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.owner_id == current_user.id)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="Portfolio not found or access denied"
        )

    try:
        risk_analysis = await personal_trading_ai.analyze_portfolio_risk(portfolio, db)

        logger.info(
            "Portfolio risk analysis completed",
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            risk_score=risk_analysis.get("risk_score"),
        )

        return risk_analysis

    except Exception as e:
        logger.error(
            "Error in portfolio risk analysis",
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to analyze portfolio risk")


@router.get("/trading-signals")
async def get_trading_signals(
    symbols: str = Query(..., description="Comma-separated list of symbols (max 10)"),
    current_user: User = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """
    Get AI-generated trading signals for specified symbols.

    Returns signals with confidence scores and reasoning.
    """
    try:
        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",")]

        if len(symbol_list) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 symbols allowed per request",
            )

        # Generate signals
        signals = await personal_trading_ai.generate_trading_signals(
            symbol_list, current_user
        )

        logger.info(
            "Trading signals generated",
            user_id=current_user.id,
            symbols=symbol_list,
            signals_count=len(signals),
        )

        return signals

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Error generating trading signals",
            user_id=current_user.id,
            symbols=symbols,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to generate trading signals"
        )


@router.post("/portfolio-optimization/{portfolio_id}")
async def optimize_portfolio(
    portfolio_id: int,
    target_allocations: Dict[str, float],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get portfolio optimization recommendations.

    Analyzes current allocation vs target and provides rebalancing guidance.
    """
    # Verify portfolio ownership
    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.id == portfolio_id, Portfolio.owner_id == current_user.id)
        .first()
    )

    if not portfolio:
        raise HTTPException(
            status_code=404, detail="Portfolio not found or access denied"
        )

    # Validate target allocations
    total_allocation = sum(target_allocations.values())
    if not (0.95 <= total_allocation <= 1.05):  # Allow 5% tolerance
        raise HTTPException(
            status_code=400,
            detail="Target allocations must sum to approximately 100%",
        )

    try:
        optimization = await personal_trading_ai.optimize_portfolio_allocation(
            portfolio, target_allocations
        )

        logger.info(
            "Portfolio optimization completed",
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            rebalancing_needed=optimization.get("rebalancing_needed", False),
        )

        return optimization

    except Exception as e:
        logger.error(
            "Error in portfolio optimization",
            user_id=current_user.id,
            portfolio_id=portfolio_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to optimize portfolio")


@router.get("/market-sentiment/{symbol}")
async def get_market_sentiment(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get AI-analyzed market sentiment for a symbol.

    Provides sentiment analysis based on available data:
    - Price momentum analysis (available)
    - Volatility assessment (available via trading-engine)
    - News/social sentiment (beta - coming soon)
    """
    from datetime import datetime, timedelta

    try:
        symbol = symbol.upper().strip()

        # Get real market data for momentum-based sentiment
        from app.services.market_data import market_data_service

        quote = await market_data_service.get_quote(symbol)
        historical_data = await market_data_service.get_historical_data(
            symbol,
            start_date=(datetime.utcnow() - timedelta(days=30)).isoformat(),
            end_date=datetime.utcnow().isoformat(),
        )

        # Calculate momentum-based sentiment from actual price data
        sentiment_score = 0.5  # Neutral default
        sentiment_label = "Neutral"
        confidence = 50.0
        key_factors = []

        # Use real price change if available
        if quote:
            change_percent = quote.get("change_percent", 0)

            # Convert price momentum to sentiment (simple but real)
            if change_percent > 3:
                sentiment_score = 0.8
                sentiment_label = "Very Positive"
                key_factors.append(f"Strong positive momentum: +{change_percent:.2f}%")
            elif change_percent > 1:
                sentiment_score = 0.65
                sentiment_label = "Positive"
                key_factors.append(f"Positive price action: +{change_percent:.2f}%")
            elif change_percent > -1:
                sentiment_score = 0.5
                sentiment_label = "Neutral"
                key_factors.append(f"Stable price action: {change_percent:+.2f}%")
            elif change_percent > -3:
                sentiment_score = 0.35
                sentiment_label = "Negative"
                key_factors.append(f"Negative price pressure: {change_percent:.2f}%")
            else:
                sentiment_score = 0.2
                sentiment_label = "Very Negative"
                key_factors.append(f"Strong selling pressure: {change_percent:.2f}%")

            confidence = min(85.0, 50.0 + abs(change_percent) * 5)

        # Try to get volatility data from trading-engine
        volatility_regime = None
        try:
            import pandas as pd

            from app.trading_engine.ml_models.volatility_regime import (
                VolatilityDetector,
                VolatilityRegime,
            )

            if historical_data:
                df = pd.DataFrame(historical_data)
                if "close" not in df.columns and "price" in df.columns:
                    df["close"] = df["price"]

                if "close" in df.columns and len(df) >= 5:
                    detector = VolatilityDetector()
                    regime, vol_value = detector.detect_regime(df)
                    volatility_regime = regime.name

                    if regime == VolatilityRegime.LOW:
                        key_factors.append("Low volatility - stable market conditions")
                    elif regime == VolatilityRegime.HIGH:
                        key_factors.append("High volatility - increased uncertainty")
                        confidence = max(30.0, confidence - 15)
                    elif regime == VolatilityRegime.EXTREME:
                        key_factors.append("Extreme volatility - exercise caution")
                        confidence = max(20.0, confidence - 25)

        except ImportError:
            pass
        except Exception as vol_error:
            logger.debug(f"Volatility analysis unavailable: {vol_error}")

        sentiment_data = {
            "symbol": symbol,
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_label": sentiment_label,
            "confidence": round(confidence, 1),
            "key_factors": (
                key_factors if key_factors else ["Analyzing market conditions..."]
            ),
            "data_sources": {
                "price_momentum": "available",
                "volatility_analysis": (
                    "available" if volatility_regime else "unavailable"
                ),
                "news_sentiment": "beta",
                "social_sentiment": "coming_soon",
            },
            "volatility_regime": volatility_regime,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "feature_status": "beta",
            "note": "Sentiment is currently based on price momentum and volatility analysis. "
            "Full NLP-based news and social media sentiment analysis is in development.",
        }

        logger.info(
            "Market sentiment analysis requested",
            user_id=current_user.id,
            symbol=symbol,
        )

        return sentiment_data

    except Exception as e:
        logger.error(
            "Error in market sentiment analysis",
            user_id=current_user.id,
            symbol=symbol,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to analyze market sentiment"
        )


@router.get("/personal-insights")
async def get_personal_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get personalized trading insights based on user's portfolio and preferences.

    Returns customized recommendations, alerts, and opportunities.
    """
    try:
        # Get user's active portfolios
        portfolios = (
            db.query(Portfolio)
            .filter(
                Portfolio.owner_id == current_user.id,
                Portfolio.is_active.is_(True),
            )
            .all()
        )

        insights: Dict[str, Any] = {
            "user_risk_profile": current_user.risk_tolerance,
            "trading_style": current_user.trading_style,
            "total_portfolios": len(portfolios),
            "insights": [],
            "opportunities": [],
            "alerts": [],
            "generated_at": "2025-07-12T03:45:00Z",
        }
        insights_list: List[Dict[str, Any]] = insights["insights"]
        opportunities_list: List[Dict[str, Any]] = insights["opportunities"]
        alerts_list: List[Dict[str, Any]] = insights["alerts"]

        if not portfolios:
            insights_list.append(
                {
                    "type": "setup",
                    "message": "Create your first portfolio to start receiving "
                    "personalized insights",
                    "priority": "high",
                }
            )
            return insights

        # Analyze each portfolio for insights
        for portfolio in portfolios:
            if portfolio.holdings:
                # total_value = sum(h.market_value for h in portfolio.holdings)  # Unused

                # Cash allocation insight
                cash_ratio = portfolio.cash_balance / portfolio.total_value
                if cash_ratio > 0.20:
                    opportunities_list.append(
                        {
                            "type": "cash_deployment",
                            "portfolio": portfolio.name,
                            "message": f"High cash allocation ({cash_ratio:.1%}) "
                            "in {portfolio.name} - consider investing",
                            "priority": "medium",
                        }
                    )

                # Diversification insight
                if len(portfolio.holdings) < 5:
                    insights_list.append(
                        {
                            "type": "diversification",
                            "portfolio": portfolio.name,
                            "message": f"{portfolio.name} has limited holdings "
                            "({len(portfolio.holdings)}) - "
                            "consider diversifying",
                            "priority": "medium",
                        }
                    )

        # Risk tolerance insights
        if current_user.risk_tolerance == "conservative":
            insights_list.append(
                {
                    "type": "risk_management",
                    "message": "Based on your conservative risk profile, "
                    "consider focusing on dividend stocks and bonds",
                    "priority": "low",
                }
            )
        elif current_user.risk_tolerance == "aggressive":
            alerts_list.append(
                {
                    "type": "risk_warning",
                    "message": "Aggressive risk profile detected - "
                    "ensure proper risk management is in place",
                    "priority": "high",
                }
            )

        logger.info(
            "Personal insights generated",
            user_id=current_user.id,
            portfolios_count=len(portfolios),
        )

        return insights

    except Exception as e:
        logger.error(
            "Error generating personal insights",
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Failed to generate personal insights"
        )
