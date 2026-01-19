"""
Elson Financial AI - API Schemas

Pydantic models for request/response validation across all API endpoints.
"""

# Tool Schemas (OpenBB, FinanceToolkit)
from .tool_schemas import (
    # Enums
    TimeframeEnum,
    RatioCategoryEnum,
    MacroSeriesEnum,
    # OpenBB schemas
    QuoteRequest,
    QuoteResponse,
    OHLCVRequest,
    OHLCVBar,
    OHLCVResponse,
    FundamentalsRequest,
    FundamentalsResponse,
    NewsRequest,
    NewsItem,
    NewsResponse,
    MacroRequest,
    MacroDataPoint,
    MacroResponse,
    # FinanceToolkit schemas
    FinancialStatementsRequest,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    FinancialStatementsResponse,
    RatioSummaryRequest,
    RatioValue,
    RatioCategory,
    RatioSummaryResponse,
    RatioCategoryRequest,
    RatioCategoryResponse,
    RatioCompareRequest,
    RatioCompareResponse,
    # Tool call wrappers
    ToolCall,
    ToolResponse,
)

# Structured Output Schemas (7 core)
from .output_schemas import (
    # Enums
    RiskToleranceEnum,
    TimeHorizonEnum,
    TaxFilingStatusEnum,
    AccountTypeEnum,
    AssetClassEnum,
    ComplianceStatusEnum,
    # Schema 1: Financial Plan
    FinancialGoal,
    CashFlowProjection,
    DebtItem,
    InsuranceCoverage,
    FinancialPlan,
    # Schema 2: Portfolio Policy Statement
    AssetAllocation,
    InvestmentRestriction,
    PortfolioPolicyStatement,
    # Schema 3: Trade Plan
    TradeOrder,
    TradePlan,
    # Schema 4: Tax Scenario Summary
    TaxBracketImpact,
    TaxScenario,
    TaxScenarioSummary,
    # Schema 5: Compliance Checklist
    ComplianceCheckItem,
    ComplianceChecklist,
    # Schema 6: Market Data Request
    MarketDataRequest,
    # Schema 7: Fundamental Analysis Report
    ValuationAssessment,
    FinancialHealthIndicator,
    FundamentalAnalysisReport,
)

# Wealth Advisory Schemas
from .wealth_advisory import (
    # Enums
    AdvisoryMode,
    WealthTier,
    CredentialType,
    ProfessionalRoleType,
    # Base models
    Citation,
    ProfessionalRecommendation,
    ActionItem,
    # Request models
    WealthAdvisoryRequest,
    EstatePlanningRequest,
    SuccessionPlanningRequest,
    TeamCoordinationRequest,
    FinancialLiteracyRequest,
    CredentialInfoRequest,
    RoleInfoRequest,
    # Response models
    WealthAdvisoryResponse,
    EstatePlanningResponse,
    SuccessionPlanningResponse,
    TeamCoordinationResponse,
    FinancialLiteracyResponse,
    CredentialInfoResponse,
    RoleInfoResponse,
    KnowledgeBaseStatsResponse,
)

__all__ = [
    # Tool Schemas
    "TimeframeEnum",
    "RatioCategoryEnum",
    "MacroSeriesEnum",
    "QuoteRequest",
    "QuoteResponse",
    "OHLCVRequest",
    "OHLCVBar",
    "OHLCVResponse",
    "FundamentalsRequest",
    "FundamentalsResponse",
    "NewsRequest",
    "NewsItem",
    "NewsResponse",
    "MacroRequest",
    "MacroDataPoint",
    "MacroResponse",
    "FinancialStatementsRequest",
    "IncomeStatement",
    "BalanceSheet",
    "CashFlowStatement",
    "FinancialStatementsResponse",
    "RatioSummaryRequest",
    "RatioValue",
    "RatioCategory",
    "RatioSummaryResponse",
    "RatioCategoryRequest",
    "RatioCategoryResponse",
    "RatioCompareRequest",
    "RatioCompareResponse",
    "ToolCall",
    "ToolResponse",
    # Structured Output Schemas
    "RiskToleranceEnum",
    "TimeHorizonEnum",
    "TaxFilingStatusEnum",
    "AccountTypeEnum",
    "AssetClassEnum",
    "ComplianceStatusEnum",
    "FinancialGoal",
    "CashFlowProjection",
    "DebtItem",
    "InsuranceCoverage",
    "FinancialPlan",
    "AssetAllocation",
    "InvestmentRestriction",
    "PortfolioPolicyStatement",
    "TradeOrder",
    "TradePlan",
    "TaxBracketImpact",
    "TaxScenario",
    "TaxScenarioSummary",
    "ComplianceCheckItem",
    "ComplianceChecklist",
    "MarketDataRequest",
    "ValuationAssessment",
    "FinancialHealthIndicator",
    "FundamentalAnalysisReport",
    # Wealth Advisory
    "AdvisoryMode",
    "WealthTier",
    "CredentialType",
    "ProfessionalRoleType",
    "Citation",
    "ProfessionalRecommendation",
    "ActionItem",
    "WealthAdvisoryRequest",
    "EstatePlanningRequest",
    "SuccessionPlanningRequest",
    "TeamCoordinationRequest",
    "FinancialLiteracyRequest",
    "CredentialInfoRequest",
    "RoleInfoRequest",
    "WealthAdvisoryResponse",
    "EstatePlanningResponse",
    "SuccessionPlanningResponse",
    "TeamCoordinationResponse",
    "FinancialLiteracyResponse",
    "CredentialInfoResponse",
    "RoleInfoResponse",
    "KnowledgeBaseStatsResponse",
]
