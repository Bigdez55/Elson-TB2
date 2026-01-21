"""
yfinance Tool Endpoints

Provides free market data tools for the Elson Financial AI model.
Uses yfinance for data - convenient but NOT an official data feed.

IMPORTANT: All data is labeled as "market data estimate" - not authoritative exchange feed.
This is acceptable for educational/institutional-style answers but should be disclosed.

Tool-First Architecture:
- Model MUST call these tools for current pricing/market data
- All responses include timestamps and source attribution
- Return null for unavailable data - NEVER hallucinate
"""

import hashlib
import json
import logging
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools/yfinance", tags=["Tools - yfinance"])


# =============================================================================
# RESPONSE MODELS
# =============================================================================


class YFinanceToolResponse(BaseModel):
    """Standard response wrapper for yfinance tools"""

    tool: str
    request_params: Dict[str, Any]
    response: Dict[str, Any]
    cached: bool = False
    cache_ttl_remaining: Optional[int] = None
    latency_ms: int
    timestamp: datetime
    data_disclaimer: str = (
        "Market data estimate from yfinance. Not an authoritative exchange feed. Data may be delayed or incomplete."
    )


class QuoteData(BaseModel):
    """Quote response data"""

    symbol: str
    price: Optional[str] = Field(None, description="Current/last price")
    previous_close: Optional[str] = None
    open: Optional[str] = None
    day_high: Optional[str] = None
    day_low: Optional[str] = None
    volume: Optional[int] = None
    market_cap: Optional[str] = None
    timestamp: str
    source: str = "yfinance"


class OHLCVBar(BaseModel):
    """Single OHLCV bar"""

    timestamp: str
    open: str
    high: str
    low: str
    close: str
    volume: int


class FundamentalsData(BaseModel):
    """Company fundamentals"""

    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    employees: Optional[int] = None
    market_cap: Optional[str] = None
    enterprise_value: Optional[str] = None
    trailing_pe: Optional[str] = None
    forward_pe: Optional[str] = None
    price_to_book: Optional[str] = None
    dividend_yield: Optional[str] = None
    revenue: Optional[str] = None
    gross_profit: Optional[str] = None
    ebitda: Optional[str] = None
    net_income: Optional[str] = None
    total_cash: Optional[str] = None
    total_debt: Optional[str] = None
    timestamp: str
    source: str = "yfinance"


class ComputedRatios(BaseModel):
    """Computed financial ratios - null for unavailable"""

    symbol: str
    pe_ratio: Optional[str] = Field(None, description="Price to Earnings (trailing)")
    forward_pe: Optional[str] = Field(None, description="Forward P/E")
    price_to_book: Optional[str] = Field(None, description="Price to Book")
    debt_to_equity: Optional[str] = Field(None, description="Debt to Equity")
    current_ratio: Optional[str] = Field(None, description="Current Ratio")
    gross_margin: Optional[str] = Field(None, description="Gross Margin %")
    operating_margin: Optional[str] = Field(None, description="Operating Margin %")
    roe: Optional[str] = Field(None, description="Return on Equity %")
    roa: Optional[str] = Field(None, description="Return on Assets %")
    unavailable_ratios: List[str] = Field(
        default_factory=list,
        description="Ratios that could not be computed from available data",
    )
    timestamp: str
    source: str = "yfinance"
    note: str = (
        "Ratios computed from yfinance data. Null values indicate data unavailable from free data source."
    )


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

_cache: dict = {}

CACHE_TTL = {
    "quote": 60,  # 1 minute
    "history": 300,  # 5 minutes
    "fundamentals": 86400,  # 24 hours
    "ratios": 3600,  # 1 hour
}


def _cache_key(endpoint: str, params: dict) -> str:
    """Generate cache key from endpoint and params"""
    param_str = json.dumps(params, sort_keys=True, default=str)
    return f"yfinance:{endpoint}:{hashlib.md5(param_str.encode()).hexdigest()}"


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
# YFINANCE WRAPPER
# =============================================================================


def _get_yfinance_ticker(symbol: str):
    """
    Get yfinance Ticker object.
    Returns None if yfinance not installed.
    """
    try:
        import yfinance as yf

        return yf.Ticker(symbol)
    except ImportError:
        logger.warning("yfinance not installed - returning mock data")
        return None


def _safe_get(data: dict, key: str, default=None):
    """Safely get value from dict, returning None for missing/invalid"""
    try:
        val = data.get(key, default)
        if val is None or (isinstance(val, float) and (val != val)):  # NaN check
            return None
        return val
    except Exception:
        return None


def _to_str(value) -> Optional[str]:
    """Convert value to string, returning None for invalid values"""
    if value is None:
        return None
    if isinstance(value, float) and (value != value):  # NaN check
        return None
    try:
        return str(value)
    except Exception:
        return None


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/quote/{ticker}", response_model=YFinanceToolResponse)
async def get_quote(ticker: str) -> YFinanceToolResponse:
    """
    Get real-time quote for a ticker.

    Tool: yfinance_quote

    Returns: price, previous_close, open, day_high, day_low, volume, market_cap

    Use when user asks about:
    - Current stock price
    - Today's price movement
    - Market cap
    """
    start_time = time.time()
    ticker = ticker.upper()

    cache_key = _cache_key("quote", {"ticker": ticker})
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return YFinanceToolResponse(
            tool="yfinance_quote",
            request_params={"ticker": ticker},
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    yf_ticker = _get_yfinance_ticker(ticker)

    if yf_ticker:
        try:
            info = yf_ticker.info
            fast_info = yf_ticker.fast_info if hasattr(yf_ticker, "fast_info") else {}

            quote_data = {
                "symbol": ticker,
                "price": _to_str(
                    _safe_get(info, "currentPrice")
                    or _safe_get(info, "regularMarketPrice")
                ),
                "previous_close": _to_str(
                    _safe_get(info, "previousClose")
                    or _safe_get(info, "regularMarketPreviousClose")
                ),
                "open": _to_str(
                    _safe_get(info, "open") or _safe_get(info, "regularMarketOpen")
                ),
                "day_high": _to_str(
                    _safe_get(info, "dayHigh")
                    or _safe_get(info, "regularMarketDayHigh")
                ),
                "day_low": _to_str(
                    _safe_get(info, "dayLow") or _safe_get(info, "regularMarketDayLow")
                ),
                "volume": _safe_get(info, "volume")
                or _safe_get(info, "regularMarketVolume"),
                "market_cap": _to_str(_safe_get(info, "marketCap")),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "yfinance",
            }
        except Exception as e:
            logger.error(f"yfinance quote error for {ticker}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {e}")
    else:
        # Mock data for development
        quote_data = {
            "symbol": ticker,
            "price": "150.25",
            "previous_close": "149.75",
            "open": "149.50",
            "day_high": "151.00",
            "day_low": "149.00",
            "volume": 45000000,
            "market_cap": "2500000000000",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "yfinance_mock",
        }

    _set_cached(cache_key, quote_data, CACHE_TTL["quote"])

    latency_ms = int((time.time() - start_time) * 1000)

    return YFinanceToolResponse(
        tool="yfinance_quote",
        request_params={"ticker": ticker},
        response=quote_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@router.get("/history/{ticker}", response_model=YFinanceToolResponse)
async def get_history(
    ticker: str,
    period: str = Query(
        "1mo",
        description="Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max",
    ),
    interval: str = Query(
        "1d",
        description="Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo",
    ),
) -> YFinanceToolResponse:
    """
    Get historical OHLCV data.

    Tool: yfinance_history

    Returns: OHLCV series for the specified period and interval

    Use when user asks about:
    - Historical price data
    - Price charts or trends
    - Technical analysis inputs
    - Performance over a period
    """
    start_time = time.time()
    ticker = ticker.upper()

    cache_key = _cache_key(
        "history", {"ticker": ticker, "period": period, "interval": interval}
    )
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return YFinanceToolResponse(
            tool="yfinance_history",
            request_params={"ticker": ticker, "period": period, "interval": interval},
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    yf_ticker = _get_yfinance_ticker(ticker)

    if yf_ticker:
        try:
            hist = yf_ticker.history(period=period, interval=interval)

            bars = []
            for idx, row in hist.iterrows():
                bars.append(
                    {
                        "timestamp": (
                            idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
                        ),
                        "open": _to_str(row.get("Open")),
                        "high": _to_str(row.get("High")),
                        "low": _to_str(row.get("Low")),
                        "close": _to_str(row.get("Close")),
                        "volume": int(row.get("Volume", 0)) if row.get("Volume") else 0,
                    }
                )

            history_data = {
                "symbol": ticker,
                "period": period,
                "interval": interval,
                "bars": bars,
                "total_bars": len(bars),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "yfinance",
            }
        except Exception as e:
            logger.error(f"yfinance history error for {ticker}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")
    else:
        # Mock data
        bars = []
        base_price = 150.0
        for i in range(30):
            bars.append(
                {
                    "timestamp": (
                        datetime.utcnow() - timedelta(days=30 - i)
                    ).isoformat(),
                    "open": str(round(base_price + i * 0.5, 2)),
                    "high": str(round(base_price + i * 0.5 + 2, 2)),
                    "low": str(round(base_price + i * 0.5 - 1, 2)),
                    "close": str(round(base_price + i * 0.5 + 1, 2)),
                    "volume": 50000000 + i * 100000,
                }
            )

        history_data = {
            "symbol": ticker,
            "period": period,
            "interval": interval,
            "bars": bars,
            "total_bars": len(bars),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "yfinance_mock",
        }

    _set_cached(cache_key, history_data, CACHE_TTL["history"])

    latency_ms = int((time.time() - start_time) * 1000)

    return YFinanceToolResponse(
        tool="yfinance_history",
        request_params={"ticker": ticker, "period": period, "interval": interval},
        response=history_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@router.get("/fundamentals/{ticker}", response_model=YFinanceToolResponse)
async def get_fundamentals(ticker: str) -> YFinanceToolResponse:
    """
    Get basic company info and key financial fields.

    Tool: yfinance_fundamentals

    Returns: Company info plus key financial statement fields available through yfinance

    Use when user asks about:
    - Company information
    - Revenue, earnings
    - Company description
    """
    start_time = time.time()
    ticker = ticker.upper()

    cache_key = _cache_key("fundamentals", {"ticker": ticker})
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return YFinanceToolResponse(
            tool="yfinance_fundamentals",
            request_params={"ticker": ticker},
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    yf_ticker = _get_yfinance_ticker(ticker)

    if yf_ticker:
        try:
            info = yf_ticker.info

            fundamentals_data = {
                "symbol": ticker,
                "name": _safe_get(info, "longName") or _safe_get(info, "shortName"),
                "sector": _safe_get(info, "sector"),
                "industry": _safe_get(info, "industry"),
                "website": _safe_get(info, "website"),
                "description": _safe_get(info, "longBusinessSummary"),
                "employees": _safe_get(info, "fullTimeEmployees"),
                "market_cap": _to_str(_safe_get(info, "marketCap")),
                "enterprise_value": _to_str(_safe_get(info, "enterpriseValue")),
                "trailing_pe": _to_str(_safe_get(info, "trailingPE")),
                "forward_pe": _to_str(_safe_get(info, "forwardPE")),
                "price_to_book": _to_str(_safe_get(info, "priceToBook")),
                "dividend_yield": _to_str(_safe_get(info, "dividendYield")),
                "revenue": _to_str(_safe_get(info, "totalRevenue")),
                "gross_profit": _to_str(_safe_get(info, "grossProfits")),
                "ebitda": _to_str(_safe_get(info, "ebitda")),
                "net_income": _to_str(_safe_get(info, "netIncomeToCommon")),
                "total_cash": _to_str(_safe_get(info, "totalCash")),
                "total_debt": _to_str(_safe_get(info, "totalDebt")),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "yfinance",
            }
        except Exception as e:
            logger.error(f"yfinance fundamentals error for {ticker}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch fundamentals: {e}"
            )
    else:
        # Mock data
        fundamentals_data = {
            "symbol": ticker,
            "name": f"{ticker} Inc.",
            "sector": "Technology",
            "industry": "Software",
            "website": f"https://www.{ticker.lower()}.com",
            "description": f"Mock description for {ticker}",
            "employees": 50000,
            "market_cap": "500000000000",
            "enterprise_value": "520000000000",
            "trailing_pe": "25.5",
            "forward_pe": "22.0",
            "price_to_book": "10.5",
            "dividend_yield": "0.015",
            "revenue": "100000000000",
            "gross_profit": "40000000000",
            "ebitda": "30000000000",
            "net_income": "20000000000",
            "total_cash": "15000000000",
            "total_debt": "10000000000",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "yfinance_mock",
        }

    _set_cached(cache_key, fundamentals_data, CACHE_TTL["fundamentals"])

    latency_ms = int((time.time() - start_time) * 1000)

    return YFinanceToolResponse(
        tool="yfinance_fundamentals",
        request_params={"ticker": ticker},
        response=fundamentals_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


@router.get("/ratios/{ticker}", response_model=YFinanceToolResponse)
async def compute_ratios(ticker: str) -> YFinanceToolResponse:
    """
    Compute financial ratios from available yfinance data.

    Tool: yfinance_ratios

    Computes:
    - PE (trailing)
    - Forward PE
    - Price to Book
    - Debt to Equity
    - Current Ratio
    - Gross Margin
    - Operating Margin
    - ROE (Return on Equity)
    - ROA (Return on Assets)

    IMPORTANT: Returns null for any ratio that cannot be computed from available data.
    NEVER hallucinate values. If data is unavailable, respond with
    "unavailable from free data" and suggest what data source would provide it.

    Use when user asks about:
    - Financial ratios
    - Valuation metrics
    - Profitability analysis
    """
    start_time = time.time()
    ticker = ticker.upper()

    cache_key = _cache_key("ratios", {"ticker": ticker})
    cached = _get_cached(cache_key)

    if cached:
        latency_ms = int((time.time() - start_time) * 1000)
        return YFinanceToolResponse(
            tool="yfinance_ratios",
            request_params={"ticker": ticker},
            response=cached,
            cached=True,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow(),
        )

    yf_ticker = _get_yfinance_ticker(ticker)
    unavailable = []

    if yf_ticker:
        try:
            info = yf_ticker.info

            # Extract ratios - return null for missing
            pe_ratio = _to_str(_safe_get(info, "trailingPE"))
            if not pe_ratio:
                unavailable.append("pe_ratio")

            forward_pe = _to_str(_safe_get(info, "forwardPE"))
            if not forward_pe:
                unavailable.append("forward_pe")

            price_to_book = _to_str(_safe_get(info, "priceToBook"))
            if not price_to_book:
                unavailable.append("price_to_book")

            debt_to_equity = _to_str(_safe_get(info, "debtToEquity"))
            if not debt_to_equity:
                unavailable.append("debt_to_equity")

            current_ratio = _to_str(_safe_get(info, "currentRatio"))
            if not current_ratio:
                unavailable.append("current_ratio")

            gross_margin = _to_str(_safe_get(info, "grossMargins"))
            if not gross_margin:
                unavailable.append("gross_margin")

            operating_margin = _to_str(_safe_get(info, "operatingMargins"))
            if not operating_margin:
                unavailable.append("operating_margin")

            roe = _to_str(_safe_get(info, "returnOnEquity"))
            if not roe:
                unavailable.append("roe")

            roa = _to_str(_safe_get(info, "returnOnAssets"))
            if not roa:
                unavailable.append("roa")

            ratios_data = {
                "symbol": ticker,
                "pe_ratio": pe_ratio,
                "forward_pe": forward_pe,
                "price_to_book": price_to_book,
                "debt_to_equity": debt_to_equity,
                "current_ratio": current_ratio,
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "roe": roe,
                "roa": roa,
                "unavailable_ratios": unavailable,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "yfinance",
                "note": "Ratios computed from yfinance data. Null values indicate data unavailable from free data source. For comprehensive data, consider premium providers like Bloomberg or FactSet.",
            }
        except Exception as e:
            logger.error(f"yfinance ratios error for {ticker}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to compute ratios: {e}"
            )
    else:
        # Mock data
        ratios_data = {
            "symbol": ticker,
            "pe_ratio": "25.5",
            "forward_pe": "22.0",
            "price_to_book": "10.5",
            "debt_to_equity": "0.8",
            "current_ratio": "1.5",
            "gross_margin": "0.40",
            "operating_margin": "0.25",
            "roe": "0.35",
            "roa": "0.15",
            "unavailable_ratios": [],
            "timestamp": datetime.utcnow().isoformat(),
            "source": "yfinance_mock",
            "note": "Mock data for development. In production, returns actual yfinance data.",
        }

    _set_cached(cache_key, ratios_data, CACHE_TTL["ratios"])

    latency_ms = int((time.time() - start_time) * 1000)

    return YFinanceToolResponse(
        tool="yfinance_ratios",
        request_params={"ticker": ticker},
        response=ratios_data,
        cached=False,
        latency_ms=latency_ms,
        timestamp=datetime.utcnow(),
    )


# =============================================================================
# HEALTH CHECK
# =============================================================================


@router.get("/health")
async def health_check():
    """Check yfinance tool service health"""
    try:
        import yfinance

        yf_available = True
        yf_version = yfinance.__version__
    except ImportError:
        yf_available = False
        yf_version = None

    return {
        "status": "healthy",
        "yfinance_available": yf_available,
        "yfinance_version": yf_version,
        "cache_entries": len(_cache),
        "timestamp": datetime.utcnow().isoformat(),
        "disclaimer": "yfinance provides market data estimates, not authoritative exchange feeds",
    }
