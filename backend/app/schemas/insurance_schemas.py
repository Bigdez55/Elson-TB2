"""
Insurance Workflow Schemas for Elson Financial AI

These schemas define the structured outputs for insurance-related workflows,
enabling suitability assessments, policy comparisons, and needs analysis.

WARNING: These tools assist in understanding insurance concepts.
They do not replace licensed insurance professionals or constitute advice.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .base import BaseSchema

# =============================================================================
# ENUMS
# =============================================================================


class InsuranceTypeEnum(str, Enum):
    """Types of insurance coverage"""

    # Life Insurance
    TERM_LIFE = "term_life"
    WHOLE_LIFE = "whole_life"
    UNIVERSAL_LIFE = "universal_life"
    VARIABLE_LIFE = "variable_life"
    INDEXED_UNIVERSAL_LIFE = "indexed_universal_life"
    FINAL_EXPENSE = "final_expense"

    # Health Insurance
    HEALTH_PPO = "health_ppo"
    HEALTH_HMO = "health_hmo"
    HEALTH_HDHP = "health_hdhp"
    MEDICARE = "medicare"
    MEDICARE_SUPPLEMENT = "medicare_supplement"
    MEDICARE_ADVANTAGE = "medicare_advantage"
    MEDICAID = "medicaid"

    # Disability
    SHORT_TERM_DISABILITY = "short_term_disability"
    LONG_TERM_DISABILITY = "long_term_disability"

    # Long-Term Care
    TRADITIONAL_LTC = "traditional_ltc"
    HYBRID_LTC = "hybrid_ltc"

    # Annuities
    FIXED_ANNUITY = "fixed_annuity"
    VARIABLE_ANNUITY = "variable_annuity"
    INDEXED_ANNUITY = "indexed_annuity"
    IMMEDIATE_ANNUITY = "immediate_annuity"
    DEFERRED_ANNUITY = "deferred_annuity"

    # Property & Casualty
    AUTO = "auto"
    HOMEOWNERS = "homeowners"
    RENTERS = "renters"
    UMBRELLA = "umbrella"
    LIABILITY = "liability"


class InsurancePurposeEnum(str, Enum):
    """Primary purpose of insurance"""

    INCOME_REPLACEMENT = "income_replacement"
    DEBT_COVERAGE = "debt_coverage"
    FINAL_EXPENSES = "final_expenses"
    ESTATE_PLANNING = "estate_planning"
    BUSINESS_CONTINUATION = "business_continuation"
    WEALTH_TRANSFER = "wealth_transfer"
    CASH_ACCUMULATION = "cash_accumulation"
    RETIREMENT_INCOME = "retirement_income"
    HEALTHCARE_COSTS = "healthcare_costs"
    ASSET_PROTECTION = "asset_protection"
    LIABILITY_PROTECTION = "liability_protection"


class RiskClassEnum(str, Enum):
    """Insurance underwriting risk classes"""

    PREFERRED_PLUS = "preferred_plus"
    PREFERRED = "preferred"
    STANDARD_PLUS = "standard_plus"
    STANDARD = "standard"
    SUBSTANDARD = "substandard"
    DECLINE = "decline"


class SuitabilityStatusEnum(str, Enum):
    """Suitability determination status"""

    SUITABLE = "suitable"
    POTENTIALLY_SUITABLE = "potentially_suitable"
    NOT_SUITABLE = "not_suitable"
    REQUIRES_REVIEW = "requires_review"
    INSUFFICIENT_INFORMATION = "insufficient_information"


# =============================================================================
# SCHEMA 1: POLICY COMPARISON
# =============================================================================


class PolicyFeature(BaseSchema):
    """Individual policy feature for comparison"""

    feature_name: str
    policy_a_value: str
    policy_b_value: str
    advantage: Literal["policy_a", "policy_b", "equal", "context_dependent"]
    notes: Optional[str] = None


class PremiumComparison(BaseSchema):
    """Premium comparison between policies"""

    policy_a_premium: Decimal
    policy_b_premium: Decimal
    premium_frequency: Literal["monthly", "quarterly", "semi_annual", "annual"]
    policy_a_total_cost: Decimal  # Over comparison period
    policy_b_total_cost: Decimal
    comparison_period_years: int


class PolicyComparison(BaseSchema):
    """
    Schema 1: Side-by-side Policy Comparison

    Used for: Comparing two insurance policies
    Compliance: Must not recommend; only present facts
    """

    # Metadata
    comparison_id: str
    created_at: datetime
    comparison_type: InsuranceTypeEnum

    # Policies being compared
    policy_a_name: str
    policy_a_carrier: str
    policy_b_name: str
    policy_b_carrier: str

    # Coverage comparison
    policy_a_coverage: Decimal
    policy_b_coverage: Decimal
    coverage_unit: str  # e.g., "death benefit", "daily benefit", "liability limit"

    # Premium comparison
    premium_comparison: PremiumComparison

    # Feature comparison
    features: List[PolicyFeature]

    # Key differences
    policy_a_advantages: List[str]
    policy_b_advantages: List[str]

    # Considerations (not recommendations)
    considerations: List[str]

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This comparison is for educational purposes only.",
            "Policy features and premiums may vary; verify with carrier.",
            "This does not constitute a recommendation to purchase any policy.",
            "Consult a licensed insurance professional for personalized advice.",
        ]
    )


# =============================================================================
# SCHEMA 2: SUITABILITY ASSESSMENT
# =============================================================================


class ClientInsuranceProfile(BaseSchema):
    """Client profile for suitability assessment"""

    age: int
    gender: Optional[Literal["male", "female"]] = None
    health_status: Literal["excellent", "good", "fair", "poor"]
    smoker: bool
    occupation: str
    annual_income: Decimal
    net_worth: Decimal
    dependents: int
    existing_coverage: Dict[str, Decimal]  # type -> amount
    risk_tolerance: Literal["conservative", "moderate", "aggressive"]


class SuitabilityFactor(BaseSchema):
    """Individual suitability factor"""

    factor_name: str
    status: Literal["favorable", "neutral", "unfavorable", "disqualifying"]
    weight: Decimal  # 0-1
    explanation: str


class SuitabilityAssessment(BaseSchema):
    """
    Schema 2: Insurance Suitability Assessment

    Used for: Determining if a product type is suitable for a client
    Compliance: Must follow NAIC suitability guidelines
    """

    # Metadata
    assessment_id: str
    created_at: datetime
    product_type: InsuranceTypeEnum
    product_name: Optional[str] = None

    # Client profile
    client_profile: ClientInsuranceProfile

    # Suitability determination
    overall_status: SuitabilityStatusEnum
    confidence_level: Literal["high", "medium", "low"]

    # Suitability factors
    factors: List[SuitabilityFactor]
    favorable_factors: int
    unfavorable_factors: int

    # Financial suitability
    premium_affordability: Literal["affordable", "stretch", "unaffordable"]
    premium_to_income_ratio: Decimal
    recommended_max_premium: Decimal

    # Needs alignment
    stated_needs: List[InsurancePurposeEnum]
    product_addresses_needs: List[InsurancePurposeEnum]
    unaddressed_needs: List[InsurancePurposeEnum]

    # Alternative considerations
    alternative_products: List[str]

    # Compliance flags
    replacement_involved: bool
    replacement_warnings: List[str] = []
    state_specific_requirements: List[str] = []

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This assessment is for educational purposes only.",
            "Suitability determinations require licensed professional review.",
            "Individual circumstances may vary from this analysis.",
            "This does not constitute a recommendation to purchase.",
        ]
    )


# =============================================================================
# SCHEMA 3: NEEDS ANALYSIS
# =============================================================================


class CoverageGap(BaseSchema):
    """Identified coverage gap"""

    gap_type: InsurancePurposeEnum
    current_coverage: Decimal
    recommended_coverage: Decimal
    gap_amount: Decimal
    priority: Literal["critical", "high", "medium", "low"]
    rationale: str


class IncomeReplacementCalculation(BaseSchema):
    """Income replacement needs calculation"""

    annual_income: Decimal
    replacement_ratio: Decimal  # Typically 60-80%
    years_needed: int
    discount_rate: Decimal
    present_value_needed: Decimal
    existing_coverage: Decimal
    gap: Decimal


class NeedsAnalysis(BaseSchema):
    """
    Schema 3: Insurance Needs Analysis

    Used for: Identifying coverage gaps and needs
    Compliance: Educational only; not a recommendation
    """

    # Metadata
    analysis_id: str
    client_id: str
    created_at: datetime

    # Client situation
    age: int
    annual_income: Decimal
    total_debt: Decimal
    dependents: int
    years_until_retirement: int
    spouse_income: Optional[Decimal] = None

    # Current coverage
    existing_life_coverage: Decimal
    existing_disability_coverage: Decimal
    existing_ltc_coverage: bool
    existing_health_coverage: bool

    # Needs calculations
    income_replacement: IncomeReplacementCalculation

    # Life insurance needs (DIME method or similar)
    debt_coverage_needed: Decimal
    income_replacement_needed: Decimal
    mortgage_balance: Decimal
    education_funding_needed: Decimal
    final_expenses_estimate: Decimal
    total_life_insurance_need: Decimal
    life_insurance_gap: Decimal

    # Disability insurance needs
    monthly_expenses: Decimal
    disability_benefit_needed: Decimal
    disability_gap: Decimal

    # LTC needs
    ltc_recommended: bool
    ltc_rationale: str

    # Coverage gaps
    gaps: List[CoverageGap]
    critical_gaps: int
    high_priority_gaps: int

    # Action items (educational)
    suggested_actions: List[str]

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This needs analysis is for educational purposes only.",
            "Actual needs may differ based on individual circumstances.",
            "Consult a licensed insurance professional for personalized recommendations.",
            "Coverage amounts are estimates and should be verified.",
        ]
    )


# =============================================================================
# SCHEMA 4: PREMIUM ILLUSTRATION SUMMARY
# =============================================================================


class IllustrationYear(BaseSchema):
    """Single year of illustration projection"""

    year: int
    age: int
    premium: Decimal
    cash_value_guaranteed: Decimal
    cash_value_non_guaranteed: Decimal
    death_benefit: Decimal
    surrender_value: Decimal


class PremiumIllustrationSummary(BaseSchema):
    """
    Schema 4: Premium Illustration Summary

    Used for: Summarizing policy projections
    Compliance: Must distinguish guaranteed vs non-guaranteed
    """

    # Metadata
    illustration_id: str
    created_at: datetime
    carrier: str
    product_name: str
    product_type: InsuranceTypeEnum

    # Policy basics
    face_amount: Decimal
    premium_amount: Decimal
    premium_frequency: Literal["monthly", "quarterly", "semi_annual", "annual"]
    payment_period_years: int

    # Insured information
    insured_age: int
    risk_class: RiskClassEnum

    # Assumptions (CRITICAL for compliance)
    assumed_interest_rate: Decimal
    guaranteed_interest_rate: Decimal
    assumed_dividend_rate: Optional[Decimal] = None
    illustration_date: date

    # Projections
    projections: List[IllustrationYear]

    # Key milestones
    breakeven_year: Optional[int] = None  # When cash value > premiums paid
    maturity_age: int

    # Summary values at key ages
    values_at_age_65: Optional[IllustrationYear] = None
    values_at_age_75: Optional[IllustrationYear] = None
    values_at_age_85: Optional[IllustrationYear] = None

    # Warnings (REQUIRED)
    warnings: List[str] = Field(
        default=[
            "Non-guaranteed values are NOT guaranteed and may be higher or lower.",
            "Actual results will vary based on policy performance.",
            "Dividends are not guaranteed and are subject to change.",
            "This summary does not replace the full policy illustration.",
        ]
    )

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This is a summary only; review the full illustration for complete details.",
            "Illustrations are hypothetical and not guarantees of future performance.",
            "Policy loans and withdrawals will reduce values and death benefits.",
            "Consult a licensed insurance professional before purchasing.",
        ]
    )


# =============================================================================
# SCHEMA 5: CLAIMS SCENARIO CHECKLIST
# =============================================================================


class ClaimStep(BaseSchema):
    """Individual claim process step"""

    step_number: int
    action: str
    responsible_party: Literal["policyholder", "beneficiary", "carrier", "agent"]
    typical_timeframe: str
    documents_needed: List[str]
    tips: List[str]


class ClaimsScenarioChecklist(BaseSchema):
    """
    Schema 5: Claims Scenario Checklist

    Used for: Guiding through potential claims scenarios
    Compliance: Educational; refer to carrier for actual claims
    """

    # Metadata
    checklist_id: str
    created_at: datetime
    claim_type: InsuranceTypeEnum
    scenario_description: str

    # Claim basics
    typical_claim_triggers: List[str]
    documentation_required: List[str]
    typical_processing_time: str

    # Step-by-step process
    steps: List[ClaimStep]

    # Common issues
    common_denial_reasons: List[str]
    how_to_avoid_delays: List[str]

    # Contestability
    contestability_period_applies: bool
    contestability_notes: Optional[str] = None

    # Tax implications
    tax_treatment: str
    tax_notes: List[str]

    # Appeals process
    appeal_available: bool
    appeal_timeframe: Optional[str] = None
    appeal_steps: List[str] = []

    # Important contacts
    carrier_claims_contact: str = "Contact carrier directly"
    state_insurance_department: str = "Contact state insurance department if needed"

    # Disclaimers (REQUIRED)
    disclaimers: List[str] = Field(
        default=[
            "This checklist is for educational purposes only.",
            "Actual claims processes vary by carrier and policy.",
            "Contact your insurance carrier for specific claims procedures.",
            "Deadlines and requirements may differ from this general guidance.",
        ]
    )
