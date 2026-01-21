"""
OpenBB Tool Endpoints

Provides market data tools for the Elson Financial AI model to call.
These endpoints wrap OpenBB SDK calls with caching and normalized outputs.

Tool-First Architecture:
- Model MUST call these tools for current pricing/market data
- All responses include timestamps and source attribution
- Redis caching reduces API calls and improves latency
"""

import hashlib
import json
import logging
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.schemas.tool_schemas import (
    FundamentalsRequest,
    FundamentalsResponse,
    MacroDataPoint,
    MacroRequest,
    MacroResponse,
    MacroSeriesEnum,
    NewsItem,
    NewsRequest,
    NewsResponse,
    OHLCVBar,
    OHLCVRequest,
    OHLCVResponse,
    QuoteRequest,
    QuoteResponse,
    TimeframeEnum,
    ToolResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools/openbb", tags=["Tools - OpenBB"])


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# In-memory cache (replace with Redis in production)
_cache: dict = {}

CACHE_TTL = {
    "quote": 60,  # 1 minute
    "ohlcv": 300,  # 5 minutes
    "fundamentals": 86400,  # 24 hours
    "news": 900,  # 15 minutes
    "macro": 3600,  # 1 hour
}


def _cache_key(endpoint: str, params: dict) -> str:
    """Generate cache key from endpoint and params"""
    param_str = json.dumps(params, sort_keys=True, default=str)
    return f"openbb:{endpoint}:{hashlib.md5(param_str.encode()).hexdigest()}"


def _get_cached(key: str) -> Optional[dict]:
    """Get value from cache if not expired"""
    if key in _cache:
        entry = _cache[key]
        if datetime.utcnow() < entry["expires"]:
            return entry["data"]
        del _cache[key]
    return None


def _set_cached(key: str, data: dict, ttl: int):
    """Set value in cache with TTL"""
    _cache[key] = {"data": data, "expires": datetime.utcnow() + timedelta(seconds=ttl)}


# =============================================================================
# OPENBB SDK WRAPPER
# =============================================================================


def _get_openbb():
    """
    Get OpenBB client instance.

    Returns mock data if OpenBB is not installed.
    In production, this would initialize the actual OpenBB SDK.
    """
    try:
        from openbb import obb

        return obb
    except ImportError:
        logger.warning("OpenBB SDK not installed - returning mock data")
        return None


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/quote/{symbol}", response_model=ToolResponse)
async def get_quote(
    symbol: str,
) -> ToolResponse:
    """
    Get real-time quote for a symbol.

    Tool: openbb_quote
    Cache TTL: 60 seconds

    Use this when the user asks about:
    - Current stock price
    - Today's price movement
    - Bid/ask spread
    - Market cap
    """
    start_time = time.time()
    symbol = symbol.upper()

    cache_key = _cache_key("quote", {"symbol": symbol})
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResponse(
            tool="openbb_quote",
            request_params={"symbol": symbol},
            response=cached,
            cached=True,
            cache_ttl_remaining=int(
                (datetime.utcnow() - _cache[cache_key]["expires"]).total_seconds()
            ),
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    obb = _get_openbb()

    if obb:
        try:
            result = obb.equity.price.quote(symbol=symbol, provider="yfinance")
            data = result.to_dict("records")[0] if result else {}

            quote_data = {
                "symbol": symbol,
                "price": Decimal(str(data.get("last_price", 0))),
                "open": Decimal(str(data.get("open", 0))),
                "high": Decimal(str(data.get("high", 0))),
                "low": Decimal(str(data.get("low", 0))),
                "close": Decimal(str(data.get("previous_close", 0))),
                "volume": int(data.get("volume", 0)),
                "change": Decimal(str(data.get("change", 0))),
                "change_percent": Decimal(str(data.get("change_percent", 0))),
                "bid": Decimal(str(data.get("bid", 0))) if data.get("bid") else None,
                "ask": Decimal(str(data.get("ask", 0))) if data.get("ask") else None,
                "market_cap": (
                    Decimal(str(data.get("market_cap", 0)))
                    if data.get("market_cap")
                    else None
                ),
                "pe_ratio": (
                    Decimal(str(data.get("pe_ratio", 0)))
                    if data.get("pe_ratio")
                    else None
                ),
                "fifty_two_week_high": (
                    Decimal(str(data.get("year_high", 0)))
                    if data.get("year_high")
                    else None
                ),
                "fifty_two_week_low": (
                    Decimal(str(data.get("year_low", 0)))
                    if data.get("year_low")
                    else None
                ),
                "avg_volume": (
                    int(data.get("avg_volume", 0)) if data.get("avg_volume") else None
                ),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "openbb",
            }
        except Exception as e:
            logger.error(f"OpenBB quote error for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {e}")
    else:
        # Mock data for development/testing
        quote_data = {
            "symbol": symbol,
            "price": Decimal("150.25"),
            "open": Decimal("149.50"),
            "high": Decimal("151.00"),
            "low": Decimal("149.00"),
            "close": Decimal("149.75"),
            "volume": 45000000,
            "change": Decimal("0.50"),
            "change_percent": Decimal("0.33"),
            "bid": Decimal("150.20"),
            "ask": Decimal("150.30"),
            "market_cap": Decimal("2500000000000"),
            "pe_ratio": Decimal("28.5"),
            "fifty_two_week_high": Decimal("180.00"),
            "fifty_two_week_low": Decimal("120.00"),
            "avg_volume": 50000000,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "openbb_mock",
        }

    # Convert Decimals to strings for JSON serialization
    quote_data_serializable = {
        k: str(v) if isinstance(v, Decimal) else v for k, v in quote_data.items()
    }

    _set_cached(cache_key, quote_data_serializable, CACHE_TTL["quote"])

    latency_ms = int((time.time() - start_time) * 1000)

    return ToolResponse(
        tool="openbb_quote",
        request_params={"symbol": symbol},
        response=quote_data_serializable,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@router.get("/ohlcv/{symbol}", response_model=ToolResponse)
async def get_ohlcv(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    timeframe: TimeframeEnum = Query(TimeframeEnum.DAY_1, description="Data timeframe"),
    limit: int = Query(100, ge=1, le=1000, description="Number of bars"),
) -> ToolResponse:
    """
    Get historical OHLCV (candlestick) data.

    Tool: openbb_ohlcv
    Cache TTL: 5 minutes

    Use this when the user asks about:
    - Historical price data
    - Price charts or trends
    - Technical analysis inputs
    - Performance over a period
    """
    start_time = time.time()
    symbol = symbol.upper()

    # Default date range
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    cache_key = _cache_key(
        "ohlcv",
        {
            "symbol": symbol,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "timeframe": timeframe.value,
            "limit": limit,
        },
    )
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResponse(
            tool="openbb_ohlcv",
            request_params={
                "symbol": symbol,
                "start_date": str(start_date),
                "end_date": str(end_date),
            },
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    obb = _get_openbb()

    if obb:
        try:
            result = obb.equity.price.historical(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                provider="yfinance",
            )
            df = result.to_df() if result else None

            bars = []
            if df is not None and not df.empty:
                for idx, row in df.tail(limit).iterrows():
                    bars.append(
                        {
                            "timestamp": (
                                idx.isoformat()
                                if hasattr(idx, "isoformat")
                                else str(idx)
                            ),
                            "open": str(row.get("open", 0)),
                            "high": str(row.get("high", 0)),
                            "low": str(row.get("low", 0)),
                            "close": str(row.get("close", 0)),
                            "volume": int(row.get("volume", 0)),
                            "vwap": str(row.get("vwap")) if row.get("vwap") else None,
                        }
                    )

            ohlcv_data = {
                "symbol": symbol,
                "timeframe": timeframe.value,
                "bars": bars,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "total_bars": len(bars),
                "source": "openbb",
            }
        except Exception as e:
            logger.error(f"OpenBB OHLCV error for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch OHLCV: {e}")
    else:
        # Mock data
        bars = []
        current_date = start_date
        base_price = 150.0
        while current_date <= end_date and len(bars) < limit:
            bars.append(
                {
                    "timestamp": datetime.combine(
                        current_date, datetime.min.time()
                    ).isoformat(),
                    "open": str(round(base_price + (len(bars) % 10) * 0.5, 2)),
                    "high": str(round(base_price + (len(bars) % 10) * 0.5 + 2, 2)),
                    "low": str(round(base_price + (len(bars) % 10) * 0.5 - 1, 2)),
                    "close": str(round(base_price + (len(bars) % 10) * 0.5 + 1, 2)),
                    "volume": 50000000 + len(bars) * 100000,
                    "vwap": None,
                }
            )
            current_date += timedelta(days=1)

        ohlcv_data = {
            "symbol": symbol,
            "timeframe": timeframe.value,
            "bars": bars,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_bars": len(bars),
            "source": "openbb_mock",
        }

    _set_cached(cache_key, ohlcv_data, CACHE_TTL["ohlcv"])

    latency_ms = int((time.time() - start_time) * 1000)

    return ToolResponse(
        tool="openbb_ohlcv",
        request_params={
            "symbol": symbol,
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
        response=ohlcv_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@router.get("/fundamentals/{symbol}", response_model=ToolResponse)
async def get_fundamentals(
    symbol: str,
) -> ToolResponse:
    """
    Get company fundamentals overview.

    Tool: openbb_fundamentals
    Cache TTL: 24 hours

    Use this when the user asks about:
    - Company information
    - Revenue, earnings, margins
    - Valuation metrics (P/E, P/B, etc.)
    - Dividend information
    - Balance sheet highlights
    """
    start_time = time.time()
    symbol = symbol.upper()

    cache_key = _cache_key("fundamentals", {"symbol": symbol})
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResponse(
            tool="openbb_fundamentals",
            request_params={"symbol": symbol},
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    obb = _get_openbb()

    if obb:
        try:
            result = obb.equity.fundamental.overview(symbol=symbol, provider="fmp")
            data = result.to_dict("records")[0] if result else {}

            fundamentals_data = {
                "symbol": symbol,
                "name": data.get("company_name", symbol),
                "sector": data.get("sector"),
                "industry": data.get("industry"),
                "description": data.get("description"),
                "ceo": data.get("ceo"),
                "employees": data.get("full_time_employees"),
                "headquarters": data.get("address"),
                "website": data.get("website"),
                "market_cap": (
                    str(data.get("market_cap")) if data.get("market_cap") else None
                ),
                "enterprise_value": (
                    str(data.get("enterprise_value"))
                    if data.get("enterprise_value")
                    else None
                ),
                "pe_ratio": str(data.get("pe_ratio")) if data.get("pe_ratio") else None,
                "forward_pe": (
                    str(data.get("forward_pe")) if data.get("forward_pe") else None
                ),
                "peg_ratio": (
                    str(data.get("peg_ratio")) if data.get("peg_ratio") else None
                ),
                "price_to_book": (
                    str(data.get("price_to_book"))
                    if data.get("price_to_book")
                    else None
                ),
                "price_to_sales": (
                    str(data.get("price_to_sales"))
                    if data.get("price_to_sales")
                    else None
                ),
                "ev_to_ebitda": (
                    str(data.get("ev_to_ebitda")) if data.get("ev_to_ebitda") else None
                ),
                "revenue_ttm": (
                    str(data.get("revenue")) if data.get("revenue") else None
                ),
                "gross_profit_ttm": (
                    str(data.get("gross_profit")) if data.get("gross_profit") else None
                ),
                "ebitda_ttm": str(data.get("ebitda")) if data.get("ebitda") else None,
                "net_income_ttm": (
                    str(data.get("net_income")) if data.get("net_income") else None
                ),
                "eps_ttm": str(data.get("eps")) if data.get("eps") else None,
                "profit_margin": (
                    str(data.get("profit_margin"))
                    if data.get("profit_margin")
                    else None
                ),
                "operating_margin": (
                    str(data.get("operating_margin"))
                    if data.get("operating_margin")
                    else None
                ),
                "gross_margin": (
                    str(data.get("gross_margin")) if data.get("gross_margin") else None
                ),
                "dividend_yield": (
                    str(data.get("dividend_yield"))
                    if data.get("dividend_yield")
                    else None
                ),
                "dividend_per_share": (
                    str(data.get("dividend_per_share"))
                    if data.get("dividend_per_share")
                    else None
                ),
                "total_cash": (
                    str(data.get("total_cash")) if data.get("total_cash") else None
                ),
                "total_debt": (
                    str(data.get("total_debt")) if data.get("total_debt") else None
                ),
                "debt_to_equity": (
                    str(data.get("debt_to_equity"))
                    if data.get("debt_to_equity")
                    else None
                ),
                "current_ratio": (
                    str(data.get("current_ratio"))
                    if data.get("current_ratio")
                    else None
                ),
                "last_updated": datetime.utcnow().isoformat(),
                "source": "openbb",
            }
        except Exception as e:
            logger.error(f"OpenBB fundamentals error for {symbol}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch fundamentals: {e}"
            )
    else:
        # Mock data
        fundamentals_data = {
            "symbol": symbol,
            "name": f"{symbol} Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "description": f"Mock description for {symbol}",
            "ceo": "John Doe",
            "employees": 150000,
            "headquarters": "Cupertino, CA",
            "website": f"https://www.{symbol.lower()}.com",
            "market_cap": "2500000000000",
            "enterprise_value": "2600000000000",
            "pe_ratio": "28.5",
            "forward_pe": "26.2",
            "peg_ratio": "2.1",
            "price_to_book": "35.0",
            "price_to_sales": "7.5",
            "ev_to_ebitda": "20.5",
            "revenue_ttm": "380000000000",
            "gross_profit_ttm": "170000000000",
            "ebitda_ttm": "130000000000",
            "net_income_ttm": "95000000000",
            "eps_ttm": "6.05",
            "profit_margin": "0.25",
            "operating_margin": "0.30",
            "gross_margin": "0.45",
            "dividend_yield": "0.005",
            "dividend_per_share": "0.96",
            "total_cash": "60000000000",
            "total_debt": "120000000000",
            "debt_to_equity": "1.5",
            "current_ratio": "1.1",
            "last_updated": datetime.utcnow().isoformat(),
            "source": "openbb_mock",
        }

    _set_cached(cache_key, fundamentals_data, CACHE_TTL["fundamentals"])

    latency_ms = int((time.time() - start_time) * 1000)

    return ToolResponse(
        tool="openbb_fundamentals",
        request_params={"symbol": symbol},
        response=fundamentals_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@router.get("/news/{symbol}", response_model=ToolResponse)
async def get_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=50, description="Number of headlines"),
) -> ToolResponse:
    """
    Get company news headlines.

    Tool: openbb_news
    Cache TTL: 15 minutes

    Use this when the user asks about:
    - Recent news about a company
    - Market sentiment drivers
    - Catalysts or events
    """
    start_time = time.time()
    symbol = symbol.upper()

    cache_key = _cache_key("news", {"symbol": symbol, "limit": limit})
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResponse(
            tool="openbb_news",
            request_params={"symbol": symbol, "limit": limit},
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    obb = _get_openbb()

    if obb:
        try:
            result = obb.news.company(symbol=symbol, limit=limit, provider="benzinga")
            data = result.to_dict("records") if result else []

            headlines = []
            for item in data[:limit]:
                headlines.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "source": item.get("source", ""),
                        "published_at": (
                            item.get("date", datetime.utcnow()).isoformat()
                            if item.get("date")
                            else datetime.utcnow().isoformat()
                        ),
                        "summary": (
                            item.get("text", "")[:500] if item.get("text") else None
                        ),
                        "sentiment": None,  # Would need sentiment analysis
                    }
                )

            news_data = {
                "symbol": symbol,
                "headlines": headlines,
                "total_results": len(headlines),
                "source": "openbb",
            }
        except Exception as e:
            logger.error(f"OpenBB news error for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch news: {e}")
    else:
        # Mock data
        headlines = []
        for i in range(min(limit, 5)):
            headlines.append(
                {
                    "title": f"Mock headline {i+1} for {symbol}",
                    "url": f"https://example.com/news/{symbol.lower()}/{i+1}",
                    "source": "MockNews",
                    "published_at": (
                        datetime.utcnow() - timedelta(hours=i * 2)
                    ).isoformat(),
                    "summary": f"This is a mock news summary for {symbol} headline {i+1}.",
                    "sentiment": ["positive", "negative", "neutral"][i % 3],
                }
            )

        news_data = {
            "symbol": symbol,
            "headlines": headlines,
            "total_results": len(headlines),
            "source": "openbb_mock",
        }

    _set_cached(cache_key, news_data, CACHE_TTL["news"])

    latency_ms = int((time.time() - start_time) * 1000)

    return ToolResponse(
        tool="openbb_news",
        request_params={"symbol": symbol, "limit": limit},
        response=news_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@router.get("/macro/{series}", response_model=ToolResponse)
async def get_macro(
    series: MacroSeriesEnum,
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    country: str = Query("US", description="Country code"),
) -> ToolResponse:
    """
    Get macroeconomic data series.

    Tool: openbb_macro
    Cache TTL: 1 hour

    Use this when the user asks about:
    - GDP, inflation, unemployment
    - Interest rates
    - Consumer sentiment
    - Economic indicators
    """
    start_time = time.time()

    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365 * 5)  # 5 years default

    cache_key = _cache_key(
        "macro",
        {
            "series": series.value,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "country": country,
        },
    )
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResponse(
            tool="openbb_macro",
            request_params={"series": series.value, "country": country},
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    # Series mapping to OpenBB functions
    series_config = {
        MacroSeriesEnum.GDP: {"unit": "billions USD", "frequency": "quarterly"},
        MacroSeriesEnum.INFLATION: {"unit": "percent", "frequency": "monthly"},
        MacroSeriesEnum.UNEMPLOYMENT: {"unit": "percent", "frequency": "monthly"},
        MacroSeriesEnum.INTEREST_RATES: {"unit": "percent", "frequency": "daily"},
        MacroSeriesEnum.CONSUMER_SENTIMENT: {"unit": "index", "frequency": "monthly"},
        MacroSeriesEnum.HOUSING_STARTS: {"unit": "thousands", "frequency": "monthly"},
        MacroSeriesEnum.RETAIL_SALES: {"unit": "billions USD", "frequency": "monthly"},
        MacroSeriesEnum.INDUSTRIAL_PRODUCTION: {
            "unit": "index",
            "frequency": "monthly",
        },
    }

    config = series_config.get(series, {"unit": "unknown", "frequency": "unknown"})

    obb = _get_openbb()

    if obb:
        try:
            # Map series to OpenBB economy functions
            if series == MacroSeriesEnum.GDP:
                result = obb.economy.gdp.nominal(
                    country=country,
                    start_date=start_date,
                    end_date=end_date,
                    provider="oecd",
                )
            elif series == MacroSeriesEnum.INFLATION:
                result = obb.economy.cpi(
                    country=country,
                    start_date=start_date,
                    end_date=end_date,
                    provider="fred",
                )
            elif series == MacroSeriesEnum.UNEMPLOYMENT:
                result = obb.economy.unemployment(
                    country=country,
                    start_date=start_date,
                    end_date=end_date,
                    provider="oecd",
                )
            elif series == MacroSeriesEnum.INTEREST_RATES:
                result = obb.economy.fred_series(
                    symbol="FEDFUNDS", start_date=start_date, end_date=end_date
                )
            else:
                result = None

            data_points = []
            if result:
                df = result.to_df()
                for idx, row in df.iterrows():
                    data_points.append(
                        {
                            "date": (
                                idx.strftime("%Y-%m-%d")
                                if hasattr(idx, "strftime")
                                else str(idx)
                            ),
                            "value": str(row.iloc[0]) if len(row) > 0 else "0",
                            "period": None,
                        }
                    )

            macro_data = {
                "series": series.value,
                "country": country,
                "unit": config["unit"],
                "frequency": config["frequency"],
                "data": data_points[-100:],  # Limit to last 100 points
                "last_updated": datetime.utcnow().isoformat(),
                "source": "openbb",
            }
        except Exception as e:
            logger.error(f"OpenBB macro error for {series.value}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch macro data: {e}"
            )
    else:
        # Mock data
        data_points = []
        current_date = start_date
        base_value = 100.0
        while current_date <= end_date and len(data_points) < 60:
            data_points.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "value": str(round(base_value + len(data_points) * 0.5, 2)),
                    "period": f"Q{(current_date.month - 1) // 3 + 1} {current_date.year}",
                }
            )
            current_date += timedelta(days=30)

        macro_data = {
            "series": series.value,
            "country": country,
            "unit": config["unit"],
            "frequency": config["frequency"],
            "data": data_points,
            "last_updated": datetime.utcnow().isoformat(),
            "source": "openbb_mock",
        }

    _set_cached(cache_key, macro_data, CACHE_TTL["macro"])

    latency_ms = int((time.time() - start_time) * 1000)

    return ToolResponse(
        tool="openbb_macro",
        request_params={"series": series.value, "country": country},
        response=macro_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


# =============================================================================
# HEALTH CHECK
# =============================================================================


@router.get("/health")
async def health_check():
    """Check OpenBB tool service health"""
    obb = _get_openbb()
    return {
        "status": "healthy",
        "openbb_available": obb is not None,
        "cache_entries": len(_cache),
        "timestamp": datetime.utcnow().isoformat(),
    }
