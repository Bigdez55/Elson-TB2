"""
Structured Output Schemas for Elson Financial AI

These 7 core schemas define the structured outputs the model should produce
for downstream tools, compliance checking, and institutional-grade documentation.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Literal
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from .base import BaseSchema


# =============================================================================
# ENUMS
# =============================================================================

class RiskToleranceEnum(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATELY_CONSERVATIVE = "moderately_conservative"
    MODERATE = "moderate"
    MODERATELY_AGGRESSIVE = "moderately_aggressive"
    AGGRESSIVE = "aggressive"


class TimeHorizonEnum(str, Enum):
    SHORT = "short"  # < 3 years
    MEDIUM = "medium"  # 3-10 years
    LONG = "long"  # 10-20 years
    VERY_LONG = "very_long"  # 20+ years


class TaxFilingStatusEnum(str, Enum):
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"
    QUALIFYING_WIDOW = "qualifying_widow"


class AccountTypeEnum(str, Enum):
    TAXABLE = "taxable"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_IRA = "roth_ira"
    TRADITIONAL_401K = "traditional_401k"
    ROTH_401K = "roth_401k"
    SEP_IRA = "sep_ira"
    SIMPLE_IRA = "simple_ira"
    HSA = "hsa"
    FIVE_TWENTY_NINE = "529"
    TRUST = "trust"
    ESTATE = "estate"


class AssetClassEnum(str, Enum):
    US_EQUITY_LARGE_CAP = "us_equity_large_cap"
    US_EQUITY_MID_CAP = "us_equity_mid_cap"
    US_EQUITY_SMALL_CAP = "us_equity_small_cap"
    INTERNATIONAL_DEVELOPED = "international_developed"
    EMERGING_MARKETS = "emerging_markets"
    US_BONDS_GOVERNMENT = "us_bonds_government"
    US_BONDS_CORPORATE = "us_bonds_corporate"
    US_BONDS_MUNICIPAL = "us_bonds_municipal"
    INTERNATIONAL_BONDS = "international_bonds"
    HIGH_YIELD_BONDS = "high_yield_bonds"
    TIPS = "tips"
    REAL_ESTATE = "real_estate"
    COMMODITIES = "commodities"
    CASH_EQUIVALENTS = "cash_equivalents"
    ALTERNATIVES = "alternatives"
    CRYPTO = "crypto"


class ComplianceStatusEnum(str, Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    REQUIRES_REVIEW = "requires_review"


# =============================================================================
# SCHEMA 1: FINANCIAL PLAN
# =============================================================================

class FinancialGoal(BaseSchema):
    """Individual financial goal"""
    goal_id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: date
    priority: Literal["essential", "important", "aspirational"]
    monthly_contribution_needed: Decimal
    probability_of_success: Optional[Decimal] = None  # 0-100%
    notes: Optional[str] = None


class CashFlowProjection(BaseSchema):
    """Monthly cash flow breakdown"""
    gross_income: Decimal
    taxes: Decimal
    net_income: Decimal
    fixed_expenses: Decimal
    variable_expenses: Decimal
    debt_payments: Decimal
    savings_investments: Decimal
    discretionary: Decimal


class DebtItem(BaseSchema):
    """Individual debt item"""
    name: str
    balance: Decimal
    interest_rate: Decimal
    minimum_payment: Decimal
    debt_type: Literal["mortgage", "auto", "student", "credit_card", "personal", "other"]
    payoff_date: Optional[date] = None


class InsuranceCoverage(BaseSchema):
    """Insurance coverage summary"""
    coverage_type: Literal["life", "disability", "health", "auto", "home", "umbrella", "ltc"]
    provider: Optional[str] = None
    coverage_amount: Optional[Decimal] = None
    premium_annual: Decimal
    is_adequate: bool
    recommendation: Optional[str] = None


class FinancialPlan(BaseSchema):
    """
    Schema 1: Comprehensive Financial Plan

    Used for: Generating complete financial plans for clients
    Compliance: Must include disclaimers, no guaranteed returns
    """
    # Metadata
    plan_id: str
    client_id: str
    created_at: datetime
    valid_until: date
    advisor_notes: Optional[str] = None

    # Client Profile
    age: int
    retirement_age: int
    life_expectancy: int
    risk_tolerance: RiskToleranceEnum
    time_horizon: TimeHorizonEnum
    filing_status: TaxFilingStatusEnum
    state_of_residence: str
    dependents: int

    # Net Worth
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    liquid_net_worth: Decimal

    # Cash Flow
    monthly_cash_flow: CashFlowProjection
    emergency_fund_months: Decimal
    emergency_fund_target_months: int = 6

    # Goals
    goals: List[FinancialGoal]

    # Debt
    debts: List[DebtItem]
    debt_to_income_ratio: Decimal
    recommended_payoff_strategy: Literal["avalanche", "snowball", "hybrid"]

    # Insurance
    insurance_coverages: List[InsuranceCoverage]

    # Recommendations (prioritized)
    recommendations: List[str]

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This plan is for educational purposes and does not constitute financial advice.",
            "Past performance does not guarantee future results.",
            "Consult a qualified financial professional before making investment decisions.",
            "Projections are estimates and actual results may vary significantly."
        ]
    )


# =============================================================================
# SCHEMA 2: PORTFOLIO POLICY STATEMENT (IPS)
# =============================================================================

class AssetAllocation(BaseSchema):
    """Target allocation for an asset class"""
    asset_class: AssetClassEnum
    target_percent: Decimal = Field(..., ge=0, le=100)
    min_percent: Decimal = Field(..., ge=0, le=100)
    max_percent: Decimal = Field(..., ge=0, le=100)
    current_percent: Optional[Decimal] = None
    rebalance_trigger: Decimal = Field(default=Decimal("5.0"))  # % deviation


class InvestmentRestriction(BaseSchema):
    """Investment restriction or prohibition"""
    restriction_type: Literal["prohibited", "limited", "esg_exclusion", "concentration"]
    description: str
    applies_to: List[str]  # Tickers, sectors, or asset classes
    reason: str


class PortfolioPolicyStatement(BaseSchema):
    """
    Schema 2: Investment Policy Statement

    Used for: Documenting investment guidelines and constraints
    Compliance: Must be reviewed by compliance before trading
    """
    # Metadata
    ips_id: str
    client_id: str
    effective_date: date
    review_date: date
    version: str

    # Investment Objectives
    primary_objective: Literal["growth", "income", "preservation", "balanced"]
    secondary_objective: Optional[str] = None
    return_target_annual: Decimal  # Expected return %
    max_drawdown_tolerance: Decimal  # Maximum acceptable loss %

    # Risk Parameters
    risk_tolerance: RiskToleranceEnum
    time_horizon: TimeHorizonEnum
    liquidity_needs: Literal["high", "medium", "low"]
    liquidity_reserve_percent: Decimal

    # Asset Allocation
    strategic_allocation: List[AssetAllocation]
    rebalancing_frequency: Literal["monthly", "quarterly", "semi_annual", "annual", "threshold_only"]
    tax_loss_harvesting_enabled: bool

    # Restrictions
    restrictions: List[InvestmentRestriction]

    # Benchmark
    benchmark: str  # e.g., "60/40 US Equity/Bond"
    benchmark_components: Dict[str, Decimal]  # {"SPY": 60, "AGG": 40}

    # Governance
    decision_authority: Literal["discretionary", "non_discretionary"]
    requires_client_approval: List[str]  # Actions requiring approval

    # Signatures (for compliance)
    client_acknowledged: bool
    client_acknowledged_date: Optional[datetime] = None
    advisor_approved: bool
    advisor_approved_date: Optional[datetime] = None
    compliance_reviewed: bool
    compliance_reviewed_date: Optional[datetime] = None


# =============================================================================
# SCHEMA 3: TRADE PLAN
# =============================================================================

class TradeOrder(BaseSchema):
    """Individual trade order"""
    order_id: str
    symbol: str
    action: Literal["buy", "sell", "sell_short", "buy_to_cover"]
    quantity: int
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    account_type: AccountTypeEnum
    estimated_cost_basis: Optional[Decimal] = None
    estimated_proceeds: Optional[Decimal] = None
    tax_lot_method: Optional[Literal["fifo", "lifo", "hifo", "specific"]] = None


class TradePlan(BaseSchema):
    """
    Schema 3: Trade Plan with Sizing and Rationale

    Used for: Documenting and executing trade decisions
    Compliance: Cannot include "buy" or "sell" recommendations without context
    """
    # Metadata
    plan_id: str
    client_id: str
    created_at: datetime
    expires_at: datetime
    status: Literal["draft", "pending_approval", "approved", "executed", "cancelled"]

    # Market Context (from tools)
    market_data_timestamp: datetime
    relevant_prices: Dict[str, Decimal]  # symbol -> price
    market_conditions: str  # Brief summary

    # Rationale
    investment_thesis: str
    catalyst: Optional[str] = None
    risks: List[str]

    # Position Sizing
    portfolio_value: Decimal
    max_position_size_percent: Decimal
    position_size_dollars: Decimal
    position_size_shares: int

    # Risk Management
    stop_loss_price: Optional[Decimal] = None
    stop_loss_percent: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None
    take_profit_percent: Optional[Decimal] = None
    max_loss_dollars: Decimal
    risk_reward_ratio: Optional[Decimal] = None

    # Orders
    orders: List[TradeOrder]

    # Tax Considerations
    estimated_tax_impact: Optional[Decimal] = None
    holding_period: Optional[Literal["short_term", "long_term"]] = None
    wash_sale_warning: bool = False

    # Compliance
    ips_compliant: bool
    compliance_notes: Optional[str] = None
    requires_approval: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Disclaimers
    disclaimers: List[str] = Field(
        default=[
            "This trade plan is based on current market conditions which may change.",
            "Past performance does not guarantee future results.",
            "Consult your financial advisor before executing trades."
        ]
    )


# =============================================================================
# SCHEMA 4: TAX SCENARIO SUMMARY
# =============================================================================

class TaxBracketImpact(BaseSchema):
    """Impact on tax brackets"""
    bracket_rate: Decimal
    income_in_bracket: Decimal
    tax_in_bracket: Decimal


class TaxScenario(BaseSchema):
    """Single tax scenario for comparison"""
    scenario_name: str
    description: str
    # Income
    ordinary_income: Decimal
    qualified_dividends: Decimal
    short_term_gains: Decimal
    long_term_gains: Decimal
    tax_exempt_income: Decimal
    # Deductions
    standard_deduction: Decimal
    itemized_deductions: Optional[Decimal] = None
    above_line_deductions: Decimal
    # Taxable income
    agi: Decimal
    taxable_income: Decimal
    # Tax calculation
    federal_tax: Decimal
    state_tax: Decimal
    fica_tax: Decimal
    niit_tax: Decimal  # Net Investment Income Tax
    amt_exposure: Decimal
    total_tax: Decimal
    effective_rate: Decimal
    marginal_rate: Decimal
    # Bracket breakdown
    bracket_impacts: List[TaxBracketImpact]


class TaxScenarioSummary(BaseSchema):
    """
    Schema 4: Tax Scenario Analysis

    Used for: Comparing tax optimization strategies
    Compliance: Cannot provide specific tax filing instructions
    """
    # Metadata
    analysis_id: str
    client_id: str
    tax_year: int
    created_at: datetime
    filing_status: TaxFilingStatusEnum
    state: str

    # Scenarios
    baseline_scenario: TaxScenario
    alternative_scenarios: List[TaxScenario]

    # Comparison
    recommended_scenario: str
    tax_savings_vs_baseline: Decimal

    # Strategies evaluated
    strategies_considered: List[str]

    # Action items (educational, not filing instructions)
    suggested_actions: List[str]

    # Important dates
    important_deadlines: Dict[str, date]

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This analysis is for educational purposes only and does not constitute tax advice.",
            "Consult a qualified tax professional (CPA or EA) before making tax decisions.",
            "Tax laws change frequently; verify current rates and rules.",
            "State tax implications vary; this analysis may not cover all state-specific rules."
        ]
    )


# =============================================================================
# SCHEMA 5: COMPLIANCE CHECKLIST
# =============================================================================

class ComplianceCheckItem(BaseSchema):
    """Individual compliance check"""
    check_id: str
    category: str
    description: str
    status: ComplianceStatusEnum
    rule_reference: Optional[str] = None  # e.g., "AML_CASH_REPORTING"
    details: Optional[str] = None
    action_required: Optional[str] = None
    due_date: Optional[date] = None
    responsible_party: Optional[str] = None


class ComplianceChecklist(BaseSchema):
    """
    Schema 5: Compliance Checklist

    Used for: Ensuring regulatory compliance before actions
    Compliance: This IS the compliance check
    """
    # Metadata
    checklist_id: str
    context_type: Literal["transaction", "account_opening", "trade", "gift", "fiduciary"]
    context_id: str
    created_at: datetime

    # Overall status
    overall_status: ComplianceStatusEnum
    blocking_issues: int
    warnings: int
    passed_checks: int

    # Checks by category
    aml_kyc_checks: List[ComplianceCheckItem]
    fiduciary_checks: List[ComplianceCheckItem]
    tax_compliance_checks: List[ComplianceCheckItem]
    investment_policy_checks: List[ComplianceCheckItem]
    privacy_security_checks: List[ComplianceCheckItem]

    # Required actions
    required_filings: List[str]
    required_disclosures: List[str]
    escalation_needed: bool
    escalation_contacts: List[str]

    # Sign-off
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved: bool = False


# =============================================================================
# SCHEMA 6: MARKET DATA REQUEST (Tool Call Schema)
# =============================================================================

class MarketDataRequest(BaseSchema):
    """
    Schema 6: Structured Market Data Request

    Used for: Model requesting data from OpenBB
    """
    request_id: str
    request_type: Literal["quote", "ohlcv", "fundamentals", "news", "macro"]
    symbols: List[str]

    # Time parameters (for historical)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timeframe: Optional[str] = None

    # Filters
    limit: int = 10

    # Context
    purpose: str  # Why is this data needed
    will_cite_in_response: bool = True


# =============================================================================
# SCHEMA 7: FUNDAMENTAL ANALYSIS REPORT
# =============================================================================

class ValuationAssessment(BaseSchema):
    """Valuation analysis"""
    metric: str
    current_value: Decimal
    historical_avg: Optional[Decimal] = None
    sector_avg: Optional[Decimal] = None
    assessment: Literal["undervalued", "fairly_valued", "overvalued"]
    confidence: Literal["low", "medium", "high"]


class FinancialHealthIndicator(BaseSchema):
    """Financial health metric"""
    indicator: str
    value: Decimal
    trend: Literal["improving", "stable", "declining"]
    assessment: Literal["strong", "adequate", "weak", "critical"]


class FundamentalAnalysisReport(BaseSchema):
    """
    Schema 7: Fundamental Analysis Report

    Used for: Comprehensive company analysis grounded in tool data
    Compliance: Must cite data sources, no price targets
    """
    # Metadata
    report_id: str
    symbol: str
    company_name: str
    sector: str
    industry: str
    created_at: datetime
    data_as_of: datetime

    # Data sources (REQUIRED for grounding)
    data_sources: List[str]  # e.g., ["openbb_fundamentals", "financetoolkit_ratios"]

    # Executive summary
    investment_thesis: str
    key_strengths: List[str]
    key_risks: List[str]

    # Valuation
    valuation_assessments: List[ValuationAssessment]
    overall_valuation: Literal["undervalued", "fairly_valued", "overvalued"]

    # Financial health
    profitability_indicators: List[FinancialHealthIndicator]
    liquidity_indicators: List[FinancialHealthIndicator]
    solvency_indicators: List[FinancialHealthIndicator]
    growth_indicators: List[FinancialHealthIndicator]

    # Competitive position
    competitive_advantages: List[str]
    competitive_threats: List[str]
    market_share_trend: Optional[Literal["gaining", "stable", "losing"]] = None

    # Management assessment
    management_quality: Optional[Literal["excellent", "good", "adequate", "poor"]] = None
    capital_allocation_history: Optional[str] = None

    # Catalysts
    potential_catalysts: List[str]
    potential_headwinds: List[str]

    # NOT included (compliance)
    # - Price targets
    # - Buy/sell recommendations
    # - Guaranteed returns

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This analysis is for educational purposes only.",
            "All data sourced from third-party providers; verify independently.",
            "This does not constitute a buy, sell, or hold recommendation.",
            "Past performance does not guarantee future results."
        ]
    )
