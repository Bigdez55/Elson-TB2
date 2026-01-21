"""
Core JSON Output Schemas for Elson Financial AI

These 5 schemas cover 80% of workflows and enable machine-readable plans
that can be executed, stored, compared, and audited.

Schema 1: FinancialPlan - Goals, timeline, income, expenses, debt plan, savings
Schema 2: PortfolioPolicy - IPS-style allocation, constraints, rebalancing
Schema 3: ScenarioAnalysis - Best/base/worst cases, key risks, assumptions
Schema 4: TradePlan - Educational trade template (no buy/sell calls)
Schema 5: ComplianceCheck - Triggered rules, allowed responses, disclaimers

All responses in STANDARD or DEEP_DIVE mode should output one of these schemas.
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# =============================================================================
# COMMON ENUMS
# =============================================================================


class TimeHorizon(str, Enum):
    """Investment time horizons"""

    SHORT = "short_term"  # < 3 years
    MEDIUM = "medium_term"  # 3-10 years
    LONG = "long_term"  # 10+ years
    VERY_LONG = "very_long"  # 20+ years


class RiskTolerance(str, Enum):
    """Risk tolerance levels"""

    CONSERVATIVE = "conservative"
    MODERATELY_CONSERVATIVE = "moderately_conservative"
    MODERATE = "moderate"
    MODERATELY_AGGRESSIVE = "moderately_aggressive"
    AGGRESSIVE = "aggressive"


class AssetClass(str, Enum):
    """Major asset classes"""

    US_EQUITY = "us_equity"
    INTL_EQUITY = "international_equity"
    EMERGING_EQUITY = "emerging_markets_equity"
    US_BONDS = "us_bonds"
    INTL_BONDS = "international_bonds"
    TIPS = "tips"
    REITS = "reits"
    COMMODITIES = "commodities"
    CASH = "cash_equivalents"
    ALTERNATIVES = "alternatives"
    CRYPTO = "cryptocurrency"


class GoalType(str, Enum):
    """Types of financial goals"""

    RETIREMENT = "retirement"
    EMERGENCY_FUND = "emergency_fund"
    HOME_PURCHASE = "home_purchase"
    EDUCATION = "education"
    DEBT_PAYOFF = "debt_payoff"
    MAJOR_PURCHASE = "major_purchase"
    WEALTH_BUILDING = "wealth_building"
    INCOME_GENERATION = "income_generation"
    LEGACY = "legacy_planning"
    OTHER = "other"


class DebtType(str, Enum):
    """Types of debt"""

    MORTGAGE = "mortgage"
    STUDENT_LOAN = "student_loan"
    AUTO_LOAN = "auto_loan"
    CREDIT_CARD = "credit_card"
    PERSONAL_LOAN = "personal_loan"
    HELOC = "heloc"
    MEDICAL = "medical"
    OTHER = "other"


# =============================================================================
# SCHEMA 1: FINANCIAL PLAN
# =============================================================================


class FinancialGoal(BaseModel):
    """A single financial goal within a plan"""

    goal_id: str = Field(..., description="Unique identifier for the goal")
    goal_type: GoalType
    description: str = Field(..., description="Human-readable goal description")
    target_amount: Decimal = Field(..., description="Target amount in USD")
    current_amount: Decimal = Field(
        default=Decimal("0"), description="Current progress"
    )
    target_date: Optional[date] = Field(None, description="Target completion date")
    priority: int = Field(..., ge=1, le=10, description="Priority 1-10, 1 is highest")
    monthly_contribution: Optional[Decimal] = Field(
        None, description="Suggested monthly contribution"
    )
    on_track: Optional[bool] = Field(None, description="Whether goal is on track")
    notes: Optional[str] = None


class IncomeSource(BaseModel):
    """An income source"""

    source_name: str
    amount: Decimal = Field(..., description="Monthly amount")
    frequency: Literal["monthly", "biweekly", "weekly", "annual", "irregular"]
    is_taxable: bool = True
    is_reliable: bool = True
    notes: Optional[str] = None


class ExpenseCategory(BaseModel):
    """An expense category"""

    category: str
    monthly_amount: Decimal
    is_essential: bool = Field(..., description="Needs vs Wants")
    is_fixed: bool = Field(..., description="Fixed vs Variable")
    reduction_potential: Optional[Decimal] = Field(
        None, description="Possible monthly savings"
    )


class DebtItem(BaseModel):
    """A debt item for payoff planning"""

    debt_name: str
    debt_type: DebtType
    balance: Decimal
    interest_rate: Decimal = Field(..., description="Annual interest rate as decimal")
    minimum_payment: Decimal
    recommended_payment: Optional[Decimal] = None
    payoff_date: Optional[date] = None
    priority_rank: int = Field(..., ge=1, description="Payoff priority")


class NextAction(BaseModel):
    """An actionable next step"""

    action_id: str
    description: str
    priority: Literal["high", "medium", "low"]
    deadline: Optional[str] = None
    category: str = "general"


class FinancialPlan(BaseModel):
    """
    Schema 1: Comprehensive Financial Plan

    Used for: Budgeting, savings, goal planning, debt management
    Covers both citizen-friendly and institutional-depth needs
    """

    # Metadata
    plan_id: str = Field(..., description="Unique plan identifier")
    created_date: date = Field(default_factory=date.today)
    client_summary: str = Field(..., description="Brief client situation summary")

    # Time context
    time_horizon: TimeHorizon
    planning_period_months: int = Field(
        default=12, description="Planning period in months"
    )

    # Income
    total_monthly_income: Decimal
    income_sources: List[IncomeSource] = Field(default_factory=list)

    # Expenses
    total_monthly_expenses: Decimal
    essential_expenses: Decimal = Field(..., description="Needs category total")
    discretionary_expenses: Decimal = Field(..., description="Wants category total")
    expense_categories: List[ExpenseCategory] = Field(default_factory=list)

    # Budget metrics (50/30/20 framework)
    needs_percent: Decimal = Field(..., description="Essential expenses as % of income")
    wants_percent: Decimal = Field(..., description="Discretionary as % of income")
    savings_percent: Decimal = Field(..., description="Savings/debt as % of income")
    budget_health: Literal["healthy", "needs_attention", "critical"]

    # Savings
    monthly_savings_target: Decimal
    emergency_fund_target: Decimal
    emergency_fund_current: Decimal
    emergency_fund_months: Decimal = Field(
        ..., description="Months of expenses covered"
    )

    # Debt
    total_debt: Decimal
    monthly_debt_payments: Decimal
    debt_items: List[DebtItem] = Field(default_factory=list)
    debt_payoff_strategy: Literal["avalanche", "snowball", "hybrid", "minimum_only"]

    # Goals
    financial_goals: List[FinancialGoal] = Field(default_factory=list)
    goals_on_track: int = Field(default=0)
    goals_at_risk: int = Field(default=0)

    # Next actions
    next_actions: List[NextAction] = Field(default_factory=list)

    # Summary
    key_insights: List[str] = Field(..., description="3-5 key takeaways")
    biggest_opportunity: str = Field(..., description="Primary improvement area")
    biggest_risk: str = Field(..., description="Primary risk to address")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "FP-2026-001",
                "client_summary": "35-year-old professional, dual income household, saving for home down payment",
                "time_horizon": "medium_term",
                "total_monthly_income": "8500.00",
                "total_monthly_expenses": "6200.00",
                "budget_health": "needs_attention",
            }
        }


# =============================================================================
# SCHEMA 2: PORTFOLIO POLICY (IPS-STYLE)
# =============================================================================


class AllocationTarget(BaseModel):
    """Target allocation for an asset class"""

    asset_class: AssetClass
    target_percent: Decimal = Field(..., ge=0, le=100)
    min_percent: Decimal = Field(
        ..., ge=0, le=100, description="Rebalancing lower bound"
    )
    max_percent: Decimal = Field(
        ..., ge=0, le=100, description="Rebalancing upper bound"
    )
    current_percent: Optional[Decimal] = None
    implementation_notes: Optional[str] = None


class InvestmentConstraint(BaseModel):
    """A constraint on the portfolio"""

    constraint_type: Literal["prohibited", "limited", "required", "preference"]
    description: str
    reason: str
    applies_to: Optional[str] = None  # Specific securities or asset classes


class RebalancingRule(BaseModel):
    """Rules for portfolio rebalancing"""

    trigger_type: Literal["calendar", "threshold", "both"]
    calendar_frequency: Optional[
        Literal["monthly", "quarterly", "semi_annual", "annual"]
    ] = None
    threshold_percent: Optional[Decimal] = Field(
        None, description="Drift threshold to trigger"
    )
    tax_aware: bool = True
    notes: Optional[str] = None


class LiquidityBucket(BaseModel):
    """Bucket for liquidity management"""

    bucket_name: str
    purpose: str
    target_amount: Decimal
    current_amount: Optional[Decimal] = None
    replenishment_rule: Optional[str] = None


class PortfolioPolicy(BaseModel):
    """
    Schema 2: Portfolio Policy Statement (IPS-Style)

    Used for: Portfolio construction, asset allocation, rebalancing
    Provides institutional-grade investment policy documentation
    """

    # Metadata
    policy_id: str = Field(..., description="Unique policy identifier")
    created_date: date = Field(default_factory=date.today)
    review_date: date = Field(..., description="Next review date")
    client_summary: str

    # Risk profile
    risk_tolerance: RiskTolerance
    risk_capacity: Literal["low", "medium", "high"] = Field(
        ..., description="Ability to take risk"
    )
    time_horizon: TimeHorizon

    # Investment objectives
    primary_objective: Literal["growth", "income", "preservation", "balanced"]
    return_target: Optional[str] = Field(
        None, description="Target return description, not guarantee"
    )
    income_requirement: Optional[Decimal] = Field(
        None, description="Annual income need"
    )

    # Strategic asset allocation
    target_allocation: List[AllocationTarget] = Field(default_factory=list)
    total_equity_target: Decimal = Field(..., description="Total equity allocation %")
    total_fixed_income_target: Decimal = Field(..., description="Total fixed income %")
    total_alternatives_target: Decimal = Field(default=Decimal("0"))

    # Constraints
    constraints: List[InvestmentConstraint] = Field(default_factory=list)
    prohibited_investments: List[str] = Field(default_factory=list)
    concentration_limits: Dict[str, Decimal] = Field(
        default_factory=dict, description="Max allocation to any single security/sector"
    )

    # Rebalancing
    rebalancing_rule: RebalancingRule

    # Liquidity
    liquidity_buckets: List[LiquidityBucket] = Field(default_factory=list)
    minimum_cash_reserve: Decimal = Field(..., description="Minimum cash to maintain")

    # Implementation
    preferred_vehicles: List[str] = Field(
        default_factory=list,
        description="Preferred investment vehicles (ETF, mutual fund, etc.)",
    )
    tax_considerations: List[str] = Field(default_factory=list)

    # Governance
    decision_authority: str = Field(..., description="Who makes investment decisions")
    review_frequency: Literal["quarterly", "semi_annual", "annual"]

    class Config:
        json_schema_extra = {
            "example": {
                "policy_id": "IPS-2026-001",
                "risk_tolerance": "moderate",
                "primary_objective": "growth",
                "total_equity_target": "60.00",
                "total_fixed_income_target": "35.00",
            }
        }


# =============================================================================
# SCHEMA 3: SCENARIO ANALYSIS
# =============================================================================


class Assumption(BaseModel):
    """An assumption underlying the analysis"""

    assumption_id: str
    category: str
    description: str
    value: Optional[str] = None
    source: Optional[str] = None
    confidence: Literal["high", "medium", "low"]


class ScenarioCase(BaseModel):
    """A scenario case (best, base, worst)"""

    case_type: Literal["best", "base", "worst", "alternative"]
    description: str
    probability: Optional[Decimal] = Field(
        None, ge=0, le=100, description="Probability %"
    )
    key_assumptions: List[str] = Field(default_factory=list)
    projected_outcome: str
    projected_value: Optional[Decimal] = None
    timeline: Optional[str] = None


class KeyRisk(BaseModel):
    """A key risk identified in the analysis"""

    risk_id: str
    risk_category: str
    description: str
    likelihood: Literal["low", "medium", "high"]
    impact: Literal["low", "medium", "high"]
    mitigation: Optional[str] = None


class SensitivityFactor(BaseModel):
    """A factor the analysis is sensitive to"""

    factor: str
    current_value: str
    impact_if_changed: str
    breakeven_value: Optional[str] = None


class ScenarioAnalysis(BaseModel):
    """
    Schema 3: Scenario Analysis

    Used for: What-if analysis, projections, risk assessment
    Provides structured best/base/worst case analysis
    """

    # Metadata
    analysis_id: str = Field(..., description="Unique analysis identifier")
    created_date: date = Field(default_factory=date.today)
    analysis_subject: str = Field(..., description="What is being analyzed")

    # Question being answered
    primary_question: str = Field(..., description="The question this analysis answers")
    analysis_type: Literal[
        "projection", "comparison", "risk_assessment", "optimization"
    ]

    # Assumptions
    assumptions: List[Assumption] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)

    # Scenarios
    best_case: ScenarioCase
    base_case: ScenarioCase
    worst_case: ScenarioCase
    alternative_cases: List[ScenarioCase] = Field(default_factory=list)

    # Risk identification
    key_risks: List[KeyRisk] = Field(default_factory=list)
    risk_mitigation_options: List[str] = Field(default_factory=list)

    # Sensitivity
    sensitivity_factors: List[SensitivityFactor] = Field(default_factory=list)

    # Conclusion
    recommendation: str = Field(..., description="Summary recommendation")
    confidence_level: Literal["high", "medium", "low"]
    what_changes_conclusion: List[str] = Field(
        ..., description="Factors that would change the recommendation"
    )
    next_steps: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "SA-2026-001",
                "analysis_subject": "Retirement at age 60 vs 65",
                "primary_question": "Can I afford to retire 5 years early?",
                "confidence_level": "medium",
            }
        }


# =============================================================================
# SCHEMA 4: TRADE PLAN (EDUCATIONAL)
# =============================================================================


class EntryLogic(BaseModel):
    """Educational entry logic description"""

    setup_description: str = Field(
        ..., description="What conditions trigger entry consideration"
    )
    technical_factors: List[str] = Field(default_factory=list)
    fundamental_factors: List[str] = Field(default_factory=list)
    confirmation_signals: List[str] = Field(default_factory=list)


class RiskParameters(BaseModel):
    """Risk management parameters"""

    max_position_size_percent: Decimal = Field(..., description="Max % of portfolio")
    max_loss_per_trade_percent: Decimal = Field(..., description="Max % loss per trade")
    risk_reward_ratio: str = Field(..., description="Target R:R ratio")
    correlation_consideration: Optional[str] = None


class ExitStrategy(BaseModel):
    """Exit strategy description"""

    stop_loss_logic: str = Field(..., description="How stop loss is determined")
    profit_target_logic: str = Field(..., description="How profit target is determined")
    trailing_stop_logic: Optional[str] = None
    time_based_exit: Optional[str] = None


class InvalidationCondition(BaseModel):
    """Conditions that invalidate the trade thesis"""

    condition: str
    action_if_triggered: str


class TradePlan(BaseModel):
    """
    Schema 4: Trade Plan (Educational Template)

    Used for: Educational trade analysis, position sizing examples
    IMPORTANT: This is educational only - no specific buy/sell recommendations
    """

    # Metadata
    plan_id: str = Field(..., description="Unique plan identifier")
    created_date: date = Field(default_factory=date.today)

    # Disclaimers (required)
    educational_disclaimer: str = Field(
        default="This is an educational template only. It does not constitute investment advice "
        "or a recommendation to buy or sell any security. Past performance does not "
        "guarantee future results. Consult a qualified financial advisor before trading.",
        description="Required educational disclaimer",
    )

    # Trade thesis
    thesis_summary: str = Field(..., description="Brief description of the trade idea")
    instrument_type: str = Field(
        ..., description="Type of instrument (stock, ETF, etc.)"
    )
    direction: Literal["long_educational", "short_educational", "neutral_educational"]
    time_frame: str = Field(..., description="Intended holding period")

    # Entry logic (educational)
    entry_logic: EntryLogic

    # Risk management (educational)
    risk_parameters: RiskParameters
    position_sizing_method: str = Field(
        ..., description="How position size is calculated"
    )
    position_sizing_example: str = Field(..., description="Example calculation")

    # Exit strategy (educational)
    exit_strategy: ExitStrategy

    # Invalidation
    invalidation_conditions: List[InvalidationCondition] = Field(default_factory=list)

    # Execution notes (educational)
    execution_considerations: List[str] = Field(
        default_factory=list,
        description="Things to consider when executing (liquidity, timing, etc.)",
    )

    # Record keeping
    review_criteria: List[str] = Field(
        default_factory=list, description="How to review the trade after completion"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "TP-EDU-001",
                "thesis_summary": "Educational example of momentum trade setup",
                "direction": "long_educational",
                "time_frame": "2-4 weeks swing trade example",
            }
        }


# =============================================================================
# SCHEMA 5: COMPLIANCE CHECK
# =============================================================================


class TriggeredRule(BaseModel):
    """A compliance rule that was triggered"""

    rule_id: str
    rule_name: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    description: str
    action_required: str
    resolved: bool = False


class RequiredDisclaimer(BaseModel):
    """A required disclaimer"""

    disclaimer_type: str
    text: str
    placement: Literal["beginning", "end", "inline"]


class MissingInformation(BaseModel):
    """Information needed to provide a complete response"""

    information_type: str
    question_to_ask: str
    why_needed: str
    priority: Literal["required", "recommended", "optional"]


class ComplianceCheck(BaseModel):
    """
    Schema 5: Compliance Check

    Used for: Compliance verification, required disclaimers, missing info
    Ensures responses meet regulatory and ethical standards
    """

    # Metadata
    check_id: str = Field(..., description="Unique check identifier")
    timestamp: str = Field(..., description="When the check was performed")
    request_summary: str = Field(
        ..., description="Summary of the request being checked"
    )

    # Overall status
    overall_status: Literal[
        "approved", "approved_with_conditions", "blocked", "needs_review"
    ]
    confidence: Decimal = Field(..., ge=0, le=1, description="Confidence in the check")

    # Triggered rules
    triggered_rules: List[TriggeredRule] = Field(default_factory=list)
    critical_violations: int = Field(default=0)
    warnings: int = Field(default=0)

    # Allowed response types
    allowed_response_types: List[str] = Field(
        default_factory=list, description="Types of responses allowed given the request"
    )
    prohibited_content: List[str] = Field(
        default_factory=list, description="Content that must not be included"
    )

    # Required disclaimers
    required_disclaimers: List[RequiredDisclaimer] = Field(default_factory=list)

    # Missing information
    missing_information: List[MissingInformation] = Field(default_factory=list)
    can_proceed_without_missing: bool = Field(
        ..., description="Whether response can be given without missing info"
    )

    # Professional referral
    requires_professional_referral: bool = False
    professional_type: Optional[str] = Field(
        None, description="Type of professional to refer to (CPA, attorney, CFP, etc.)"
    )
    referral_reason: Optional[str] = None

    # Response modifications
    tone_guidance: Optional[str] = Field(
        None, description="Guidance on appropriate tone for response"
    )
    depth_limit: Optional[str] = Field(
        None, description="Limit on response depth for compliance"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "check_id": "CC-2026-001",
                "overall_status": "approved_with_conditions",
                "critical_violations": 0,
                "warnings": 2,
                "requires_professional_referral": False,
            }
        }


# =============================================================================
# SCHEMA REGISTRY
# =============================================================================

CORE_SCHEMAS = {
    "FinancialPlan": FinancialPlan,
    "PortfolioPolicy": PortfolioPolicy,
    "ScenarioAnalysis": ScenarioAnalysis,
    "TradePlan": TradePlan,
    "ComplianceCheck": ComplianceCheck,
}


def get_schema(schema_name: str) -> type:
    """Get a schema class by name"""
    if schema_name not in CORE_SCHEMAS:
        raise ValueError(
            f"Unknown schema: {schema_name}. Available: {list(CORE_SCHEMAS.keys())}"
        )
    return CORE_SCHEMAS[schema_name]


def get_schema_json(schema_name: str) -> dict:
    """Get the JSON schema for a given schema name"""
    schema_class = get_schema(schema_name)
    return schema_class.model_json_schema()
