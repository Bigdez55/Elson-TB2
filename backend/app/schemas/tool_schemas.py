"""
Tool Schemas for OpenBB and FinanceToolkit Integration

These schemas define the input/output contracts for tool calls,
enabling the model to make auditable, grounded financial queries.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .base import BaseSchema

# =============================================================================
# ENUMS
# =============================================================================


class TimeframeEnum(str, Enum):
    """Supported timeframes for historical data"""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class RatioCategoryEnum(str, Enum):
    """FinanceToolkit ratio categories"""

    PROFITABILITY = "profitability"
    LIQUIDITY = "liquidity"
    SOLVENCY = "solvency"
    VALUATION = "valuation"
    GROWTH = "growth"
    EFFICIENCY = "efficiency"
    ALL = "all"


class MacroSeriesEnum(str, Enum):
    """Supported macroeconomic data series"""

    GDP = "gdp"
    INFLATION = "inflation"
    UNEMPLOYMENT = "unemployment"
    INTEREST_RATES = "interest_rates"
    CONSUMER_SENTIMENT = "consumer_sentiment"
    HOUSING_STARTS = "housing_starts"
    RETAIL_SALES = "retail_sales"
    INDUSTRIAL_PRODUCTION = "industrial_production"


# =============================================================================
# OPENBB TOOL SCHEMAS
# =============================================================================


class QuoteRequest(BaseSchema):
    """Request schema for real-time quote"""

    symbol: str = Field(..., description="Ticker symbol (e.g., AAPL, MSFT)")


class QuoteResponse(BaseSchema):
    """Response schema for real-time quote"""

    symbol: str
    price: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    change: Decimal
    change_percent: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    fifty_two_week_high: Optional[Decimal] = None
    fifty_two_week_low: Optional[Decimal] = None
    avg_volume: Optional[int] = None
    timestamp: datetime
    source: str = "openbb"


class OHLCVRequest(BaseSchema):
    """Request schema for historical OHLCV data"""

    symbol: str = Field(..., description="Ticker symbol")
    start_date: Optional[date] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End date (YYYY-MM-DD)")
    timeframe: TimeframeEnum = Field(TimeframeEnum.DAY_1, description="Data timeframe")
    limit: int = Field(100, ge=1, le=1000, description="Number of bars to return")


class OHLCVBar(BaseSchema):
    """Single OHLCV bar"""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    vwap: Optional[Decimal] = None


class OHLCVResponse(BaseSchema):
    """Response schema for historical OHLCV data"""

    symbol: str
    timeframe: str
    bars: List[OHLCVBar]
    start_date: datetime
    end_date: datetime
    total_bars: int
    source: str = "openbb"


class FundamentalsRequest(BaseSchema):
    """Request schema for company fundamentals"""

    symbol: str = Field(..., description="Ticker symbol")


class FundamentalsResponse(BaseSchema):
    """Response schema for company fundamentals overview"""

    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    ceo: Optional[str] = None
    employees: Optional[int] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    # Valuation
    market_cap: Optional[Decimal] = None
    enterprise_value: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    forward_pe: Optional[Decimal] = None
    peg_ratio: Optional[Decimal] = None
    price_to_book: Optional[Decimal] = None
    price_to_sales: Optional[Decimal] = None
    ev_to_ebitda: Optional[Decimal] = None
    # Financials
    revenue_ttm: Optional[Decimal] = None
    gross_profit_ttm: Optional[Decimal] = None
    ebitda_ttm: Optional[Decimal] = None
    net_income_ttm: Optional[Decimal] = None
    eps_ttm: Optional[Decimal] = None
    # Margins
    profit_margin: Optional[Decimal] = None
    operating_margin: Optional[Decimal] = None
    gross_margin: Optional[Decimal] = None
    # Dividends
    dividend_yield: Optional[Decimal] = None
    dividend_per_share: Optional[Decimal] = None
    payout_ratio: Optional[Decimal] = None
    ex_dividend_date: Optional[date] = None
    # Balance sheet highlights
    total_cash: Optional[Decimal] = None
    total_debt: Optional[Decimal] = None
    debt_to_equity: Optional[Decimal] = None
    current_ratio: Optional[Decimal] = None
    # Metadata
    fiscal_year_end: Optional[str] = None
    last_updated: datetime
    source: str = "openbb"


class NewsRequest(BaseSchema):
    """Request schema for company news"""

    symbol: str = Field(..., description="Ticker symbol")
    limit: int = Field(10, ge=1, le=50, description="Number of headlines")


class NewsItem(BaseSchema):
    """Single news item"""

    title: str
    url: str
    source: str
    published_at: datetime
    summary: Optional[str] = None
    sentiment: Optional[Literal["positive", "negative", "neutral"]] = None


class NewsResponse(BaseSchema):
    """Response schema for company news"""

    symbol: str
    headlines: List[NewsItem]
    total_results: int
    source: str = "openbb"


class MacroRequest(BaseSchema):
    """Request schema for macroeconomic data"""

    series: MacroSeriesEnum = Field(..., description="Economic data series")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    country: str = Field("US", description="Country code")


class MacroDataPoint(BaseSchema):
    """Single macro data point"""

    date: date
    value: Decimal
    period: Optional[str] = None  # e.g., "Q1 2026", "Jan 2026"


class MacroResponse(BaseSchema):
    """Response schema for macroeconomic data"""

    series: str
    country: str
    unit: str  # e.g., "percent", "billions USD"
    frequency: str  # e.g., "monthly", "quarterly"
    data: List[MacroDataPoint]
    last_updated: datetime
    source: str = "openbb"


# =============================================================================
# FINANCETOOLKIT SCHEMAS
# =============================================================================


class FinancialStatementsRequest(BaseSchema):
    """Request schema for financial statements"""

    symbol: str = Field(..., description="Ticker symbol")
    period: Literal["annual", "quarterly"] = Field("annual")
    limit: int = Field(5, ge=1, le=10, description="Number of periods")


class IncomeStatement(BaseSchema):
    """Income statement data"""

    period_end: date
    revenue: Decimal
    cost_of_revenue: Decimal
    gross_profit: Decimal
    operating_expenses: Decimal
    operating_income: Decimal
    interest_expense: Optional[Decimal] = None
    income_before_tax: Decimal
    income_tax_expense: Decimal
    net_income: Decimal
    eps_basic: Decimal
    eps_diluted: Decimal
    shares_outstanding: int


class BalanceSheet(BaseSchema):
    """Balance sheet data"""

    period_end: date
    # Assets
    cash_and_equivalents: Decimal
    short_term_investments: Optional[Decimal] = None
    accounts_receivable: Decimal
    inventory: Optional[Decimal] = None
    total_current_assets: Decimal
    property_plant_equipment: Decimal
    goodwill: Optional[Decimal] = None
    intangible_assets: Optional[Decimal] = None
    total_assets: Decimal
    # Liabilities
    accounts_payable: Decimal
    short_term_debt: Optional[Decimal] = None
    total_current_liabilities: Decimal
    long_term_debt: Optional[Decimal] = None
    total_liabilities: Decimal
    # Equity
    common_stock: Decimal
    retained_earnings: Decimal
    total_equity: Decimal


class CashFlowStatement(BaseSchema):
    """Cash flow statement data"""

    period_end: date
    # Operating
    net_income: Decimal
    depreciation_amortization: Decimal
    stock_based_compensation: Optional[Decimal] = None
    change_in_working_capital: Decimal
    cash_from_operations: Decimal
    # Investing
    capital_expenditures: Decimal
    acquisitions: Optional[Decimal] = None
    purchases_of_investments: Optional[Decimal] = None
    sales_of_investments: Optional[Decimal] = None
    cash_from_investing: Decimal
    # Financing
    debt_repayment: Optional[Decimal] = None
    common_stock_issued: Optional[Decimal] = None
    common_stock_repurchased: Optional[Decimal] = None
    dividends_paid: Optional[Decimal] = None
    cash_from_financing: Decimal
    # Net change
    net_change_in_cash: Decimal
    free_cash_flow: Decimal


class FinancialStatementsResponse(BaseSchema):
    """Response schema for financial statements"""

    symbol: str
    period: str
    income_statements: List[IncomeStatement]
    balance_sheets: List[BalanceSheet]
    cash_flow_statements: List[CashFlowStatement]
    currency: str = "USD"
    source: str = "financetoolkit"


class RatioSummaryRequest(BaseSchema):
    """Request schema for ratio summary"""

    symbol: str = Field(..., description="Ticker symbol")
    period: Literal["annual", "quarterly"] = Field("annual")


class RatioValue(BaseSchema):
    """Single ratio with metadata"""

    name: str
    value: Decimal
    formula: str
    interpretation: str  # e.g., "Higher is better", "Lower is better"
    benchmark: Optional[Decimal] = None  # Industry average


class RatioCategory(BaseSchema):
    """Category of ratios"""

    category: RatioCategoryEnum
    ratios: List[RatioValue]


class RatioSummaryResponse(BaseSchema):
    """Response schema for ratio summary"""

    symbol: str
    period: str
    period_end: date
    categories: List[RatioCategory]
    source: str = "financetoolkit"


class RatioCategoryRequest(BaseSchema):
    """Request schema for single ratio category"""

    symbol: str = Field(..., description="Ticker symbol")
    category: RatioCategoryEnum = Field(..., description="Ratio category")
    period: Literal["annual", "quarterly"] = Field("annual")
    periods: int = Field(5, ge=1, le=10, description="Number of periods for trend")


class RatioCategoryResponse(BaseSchema):
    """Response schema for ratio category detail with trends"""

    symbol: str
    category: RatioCategoryEnum
    periods: List[date]
    ratios: Dict[str, List[Optional[Decimal]]]  # ratio_name -> [values by period]
    formulas: Dict[str, str]
    source: str = "financetoolkit"


class RatioCompareRequest(BaseSchema):
    """Request schema for multi-ticker comparison"""

    symbols: List[str] = Field(..., min_length=2, max_length=10)
    category: RatioCategoryEnum = Field(RatioCategoryEnum.ALL)
    period: Literal["annual", "quarterly"] = Field("annual")


class RatioCompareResponse(BaseSchema):
    """Response schema for multi-ticker ratio comparison"""

    symbols: List[str]
    category: str
    period_end: date
    comparison: Dict[str, Dict[str, Optional[Decimal]]]  # symbol -> {ratio: value}
    rankings: Dict[str, List[str]]  # ratio -> [symbols ranked best to worst]
    source: str = "financetoolkit"


# =============================================================================
# TOOL CALL WRAPPER (for model output)
# =============================================================================


class ToolCall(BaseSchema):
    """Schema for model-generated tool calls"""

    tool: Literal[
        "openbb_quote",
        "openbb_ohlcv",
        "openbb_fundamentals",
        "openbb_news",
        "openbb_macro",
        "financetoolkit_statements",
        "financetoolkit_ratios",
        "financetoolkit_category",
        "financetoolkit_compare",
    ]
    params: Dict[str, Any]


class ToolResponse(BaseSchema):
    """Wrapper for tool responses with provenance"""

    tool: str
    request_params: Dict[str, Any]
    response: Dict[str, Any]
    cached: bool = False
    cache_ttl_remaining: Optional[int] = None  # seconds
    latency_ms: int
    timestamp: datetime
