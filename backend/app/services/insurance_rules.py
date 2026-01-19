"""
Insurance Compliance Rules Engine for Elson Financial AI

Implements neuro-symbolic deterministic rules for insurance compliance,
following NAIC guidelines and state-specific requirements.

These rules ensure the AI:
1. Never provides unsuitable recommendations
2. Flags replacement transactions for review
3. Requires proper disclosures
4. Blocks prohibited language (guaranteed returns, etc.)
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
import re


# =============================================================================
# AUTHORITY LEVELS
# =============================================================================

class InsuranceAuthority(str, Enum):
    """Decision authority for insurance compliance"""
    COMPLIANCE_OFFICER = "compliance_officer"  # Binding decisions
    LICENSED_AGENT = "licensed_agent"  # Advisory
    GENERAL_COUNSEL = "general_counsel"  # Legal matters
    UNDERWRITING = "underwriting"  # Risk classification


class RuleAction(str, Enum):
    """Actions to take when a rule triggers"""
    BLOCK_RESPONSE = "block_response"
    REQUIRE_DISCLOSURE = "require_disclosure"
    ADD_WARNING = "add_warning"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    LOG_FOR_REVIEW = "log_for_review"
    MODIFY_RESPONSE = "modify_response"


class RuleSeverity(str, Enum):
    """Severity of rule violation"""
    CRITICAL = "critical"  # Must block
    HIGH = "high"  # Must escalate or add strong warning
    MEDIUM = "medium"  # Add warning
    LOW = "low"  # Log for review


# =============================================================================
# CONTEXT OBJECTS
# =============================================================================

@dataclass
class InsuranceClientContext:
    """Client context for suitability rules"""
    age: int
    annual_income: Decimal
    net_worth: Decimal
    liquid_assets: Decimal
    risk_tolerance: str  # conservative, moderate, aggressive
    existing_coverage: Dict[str, Decimal] = field(default_factory=dict)
    health_status: str = "good"
    dependents: int = 0
    is_senior: bool = False  # 65+
    state: str = "CA"


@dataclass
class InsuranceProductContext:
    """Product context for suitability rules"""
    product_type: str
    carrier: str
    annual_premium: Decimal
    death_benefit: Optional[Decimal] = None
    cash_value: Optional[Decimal] = None
    surrender_period_years: Optional[int] = None
    has_market_risk: bool = False
    is_replacement: bool = False
    existing_policy_carrier: Optional[str] = None


@dataclass
class InsuranceResponseContext:
    """Context for checking AI response content"""
    response_text: str
    intent: str  # quote, comparison, recommendation, education
    product_mentioned: Optional[str] = None
    includes_projection: bool = False


# =============================================================================
# COMPLIANCE RULES
# =============================================================================

@dataclass
class InsuranceRule:
    """Definition of an insurance compliance rule"""
    rule_id: str
    name: str
    description: str
    authority: InsuranceAuthority
    severity: RuleSeverity
    action: RuleAction
    category: str
    check_function: str  # Name of function to call


# Registry of all insurance compliance rules
INSURANCE_RULES: List[InsuranceRule] = [
    # ==========================================================================
    # SUITABILITY RULES
    # ==========================================================================
    InsuranceRule(
        rule_id="INS_SUIT_001",
        name="Senior Annuity Suitability",
        description="Enhanced suitability review for annuity sales to seniors (65+)",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.HIGH,
        action=RuleAction.REQUIRE_DISCLOSURE,
        category="suitability",
        check_function="check_senior_annuity_suitability"
    ),
    InsuranceRule(
        rule_id="INS_SUIT_002",
        name="Premium Affordability",
        description="Premium should not exceed 10% of annual income for most products",
        authority=InsuranceAuthority.LICENSED_AGENT,
        severity=RuleSeverity.MEDIUM,
        action=RuleAction.ADD_WARNING,
        category="suitability",
        check_function="check_premium_affordability"
    ),
    InsuranceRule(
        rule_id="INS_SUIT_003",
        name="Surrender Period Suitability",
        description="Long surrender periods may be unsuitable for seniors or those needing liquidity",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.HIGH,
        action=RuleAction.ADD_WARNING,
        category="suitability",
        check_function="check_surrender_period_suitability"
    ),
    InsuranceRule(
        rule_id="INS_SUIT_004",
        name="Risk Tolerance Alignment",
        description="Variable products require appropriate risk tolerance",
        authority=InsuranceAuthority.LICENSED_AGENT,
        severity=RuleSeverity.MEDIUM,
        action=RuleAction.ADD_WARNING,
        category="suitability",
        check_function="check_risk_tolerance_alignment"
    ),

    # ==========================================================================
    # REPLACEMENT RULES (NAIC Model Regulation)
    # ==========================================================================
    InsuranceRule(
        rule_id="INS_REPL_001",
        name="Replacement Transaction Disclosure",
        description="1035 exchanges and replacements require specific disclosures",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.CRITICAL,
        action=RuleAction.REQUIRE_DISCLOSURE,
        category="replacement",
        check_function="check_replacement_disclosure"
    ),
    InsuranceRule(
        rule_id="INS_REPL_002",
        name="Replacement Comparison Required",
        description="Replacements must include comparison of old vs new policy",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.HIGH,
        action=RuleAction.REQUIRE_DISCLOSURE,
        category="replacement",
        check_function="check_replacement_comparison"
    ),
    InsuranceRule(
        rule_id="INS_REPL_003",
        name="Surrender Charge Warning",
        description="Warn about surrender charges on replaced policy",
        authority=InsuranceAuthority.LICENSED_AGENT,
        severity=RuleSeverity.HIGH,
        action=RuleAction.ADD_WARNING,
        category="replacement",
        check_function="check_surrender_charge_warning"
    ),

    # ==========================================================================
    # PROHIBITED CONTENT RULES
    # ==========================================================================
    InsuranceRule(
        rule_id="INS_PROH_001",
        name="No Guaranteed Returns Language",
        description="Cannot guarantee returns on variable or indexed products",
        authority=InsuranceAuthority.GENERAL_COUNSEL,
        severity=RuleSeverity.CRITICAL,
        action=RuleAction.BLOCK_RESPONSE,
        category="prohibited_content",
        check_function="check_no_guaranteed_returns"
    ),
    InsuranceRule(
        rule_id="INS_PROH_002",
        name="No Investment Advice for Insurance",
        description="Insurance products are not investments; avoid investment language",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.MEDIUM,
        action=RuleAction.MODIFY_RESPONSE,
        category="prohibited_content",
        check_function="check_no_investment_language"
    ),
    InsuranceRule(
        rule_id="INS_PROH_003",
        name="No Specific Carrier Recommendations",
        description="Cannot recommend specific carriers without proper licensing",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.HIGH,
        action=RuleAction.MODIFY_RESPONSE,
        category="prohibited_content",
        check_function="check_no_carrier_recommendations"
    ),
    InsuranceRule(
        rule_id="INS_PROH_004",
        name="No Medical Advice",
        description="Cannot provide advice on health conditions for underwriting",
        authority=InsuranceAuthority.GENERAL_COUNSEL,
        severity=RuleSeverity.CRITICAL,
        action=RuleAction.BLOCK_RESPONSE,
        category="prohibited_content",
        check_function="check_no_medical_advice"
    ),

    # ==========================================================================
    # DISCLOSURE RULES
    # ==========================================================================
    InsuranceRule(
        rule_id="INS_DISC_001",
        name="Illustration Disclaimer Required",
        description="All projections must include non-guarantee disclaimer",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.CRITICAL,
        action=RuleAction.REQUIRE_DISCLOSURE,
        category="disclosure",
        check_function="check_illustration_disclaimer"
    ),
    InsuranceRule(
        rule_id="INS_DISC_002",
        name="Not a Recommendation Disclaimer",
        description="Must clarify that information is educational, not a recommendation",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.HIGH,
        action=RuleAction.REQUIRE_DISCLOSURE,
        category="disclosure",
        check_function="check_recommendation_disclaimer"
    ),
    InsuranceRule(
        rule_id="INS_DISC_003",
        name="Tax Implications Disclosure",
        description="Must note tax implications when discussing cash value or annuities",
        authority=InsuranceAuthority.LICENSED_AGENT,
        severity=RuleSeverity.MEDIUM,
        action=RuleAction.ADD_WARNING,
        category="disclosure",
        check_function="check_tax_disclosure"
    ),

    # ==========================================================================
    # STATE-SPECIFIC RULES
    # ==========================================================================
    InsuranceRule(
        rule_id="INS_STATE_001",
        name="California Annuity Training",
        description="CA requires specific training for annuity sales to seniors",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.HIGH,
        action=RuleAction.ADD_WARNING,
        category="state_specific",
        check_function="check_california_annuity_rules"
    ),
    InsuranceRule(
        rule_id="INS_STATE_002",
        name="New York Best Interest Standard",
        description="NY Regulation 187 requires best interest standard",
        authority=InsuranceAuthority.COMPLIANCE_OFFICER,
        severity=RuleSeverity.HIGH,
        action=RuleAction.REQUIRE_DISCLOSURE,
        category="state_specific",
        check_function="check_new_york_best_interest"
    ),
]


# =============================================================================
# RULE CHECK FUNCTIONS
# =============================================================================

def check_senior_annuity_suitability(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """Check suitability of annuity products for seniors"""
    if client.age < 65:
        return True, ""

    if product and "annuity" in product.product_type.lower():
        # Check surrender period
        if product.surrender_period_years and product.surrender_period_years > 5:
            return False, (
                f"SUITABILITY WARNING: Client is {client.age} years old. "
                f"A {product.surrender_period_years}-year surrender period may limit "
                f"access to funds during retirement. Consider shorter surrender periods "
                f"or products with better liquidity features."
            )

        # Check premium as % of liquid assets
        if client.liquid_assets > 0:
            premium_ratio = product.annual_premium / client.liquid_assets
            if premium_ratio > Decimal("0.25"):
                return False, (
                    f"SUITABILITY WARNING: Premium represents {premium_ratio:.0%} of "
                    f"liquid assets. For clients 65+, tying up significant assets "
                    f"in products with surrender periods requires careful consideration."
                )

    return True, ""


def check_premium_affordability(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """Check if premium is affordable relative to income"""
    if not product:
        return True, ""

    premium_ratio = product.annual_premium / client.annual_income

    if premium_ratio > Decimal("0.15"):
        return False, (
            f"AFFORDABILITY WARNING: Annual premium of ${product.annual_premium:,.0f} "
            f"represents {premium_ratio:.0%} of annual income. Premiums exceeding "
            f"10-15% of income may strain household finances and increase lapse risk."
        )
    elif premium_ratio > Decimal("0.10"):
        return True, (
            f"Note: Premium represents {premium_ratio:.0%} of income. "
            f"Ensure client can sustain this payment long-term."
        )

    return True, ""


def check_surrender_period_suitability(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """Check if surrender period is appropriate for client"""
    if not product or not product.surrender_period_years:
        return True, ""

    # Seniors need liquidity
    if client.age >= 60 and product.surrender_period_years > 7:
        return False, (
            f"LIQUIDITY WARNING: {product.surrender_period_years}-year surrender period "
            f"means client (age {client.age}) may face penalties accessing funds "
            f"until age {client.age + product.surrender_period_years}. "
            f"Consider products with shorter surrender periods."
        )

    # Check liquidity ratio
    if client.liquid_assets > 0 and product.annual_premium > 0:
        years_of_premium = client.liquid_assets / product.annual_premium
        if years_of_premium < product.surrender_period_years:
            return False, (
                f"LIQUIDITY WARNING: Client's liquid assets would be depleted before "
                f"surrender period ends. This may create financial hardship."
            )

    return True, ""


def check_risk_tolerance_alignment(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """Check if product risk matches client tolerance"""
    if not product:
        return True, ""

    if product.has_market_risk and client.risk_tolerance == "conservative":
        return False, (
            f"RISK ALIGNMENT WARNING: {product.product_type} has market risk exposure, "
            f"but client has indicated conservative risk tolerance. "
            f"Consider fixed alternatives or ensure client understands market risks."
        )

    return True, ""


def check_replacement_disclosure(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """Check if replacement disclosures are needed"""
    if not product or not product.is_replacement:
        return True, ""

    return False, (
        "REPLACEMENT DISCLOSURE REQUIRED: This transaction involves replacing "
        "an existing policy. Per NAIC Model Regulation, the following must be provided:\n"
        "1. Notice Regarding Replacement of Life Insurance or Annuity\n"
        "2. Comparison of existing vs proposed policy\n"
        "3. Illustration of proposed policy\n"
        "4. Copy of any proposals presented\n\n"
        "The existing insurer must be notified within specified timeframes."
    )


def check_replacement_comparison(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """Ensure replacement includes proper comparison"""
    if not product or not product.is_replacement:
        return True, ""

    warnings = []

    if product.existing_policy_carrier:
        warnings.append(
            f"When replacing a policy from {product.existing_policy_carrier}, compare:\n"
            f"- Death benefits (existing vs proposed)\n"
            f"- Cash values (existing vs proposed)\n"
            f"- Premium amounts and payment period\n"
            f"- Surrender charges on existing policy\n"
            f"- New contestability period on proposed policy\n"
            f"- Any riders or benefits that may be lost"
        )

    return True, "\n".join(warnings) if warnings else ""


def check_surrender_charge_warning(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """Warn about surrender charges on replacement"""
    if not product or not product.is_replacement:
        return True, ""

    return True, (
        "SURRENDER CHARGE WARNING: Replacing an existing policy may result in:\n"
        "- Surrender charges on the existing policy\n"
        "- Loss of accumulated benefits or bonus credits\n"
        "- New contestability period (typically 2 years)\n"
        "- New suicide exclusion period\n"
        "Carefully evaluate whether replacement is in client's best interest."
    )


def check_no_guaranteed_returns(
    response: InsuranceResponseContext
) -> tuple[bool, str]:
    """Block responses that guarantee returns"""
    prohibited_patterns = [
        r"guarantee[ds]?\s+(a\s+)?return",
        r"guaranteed\s+\d+%",
        r"will\s+earn\s+\d+%",
        r"certain\s+to\s+(earn|grow|increase)",
        r"risk[- ]free\s+(return|investment|growth)",
        r"cannot\s+lose\s+(money|value|principal)",
    ]

    for pattern in prohibited_patterns:
        if re.search(pattern, response.response_text.lower()):
            return False, (
                "BLOCKED: Response contains prohibited guaranteed return language. "
                "Variable and indexed products do not guarantee returns. "
                "Rephrase to indicate that values are not guaranteed and may vary."
            )

    return True, ""


def check_no_investment_language(
    response: InsuranceResponseContext
) -> tuple[bool, str]:
    """Avoid treating insurance as investment"""
    investment_terms = [
        "invest in this policy",
        "portfolio of insurance",
        "insurance investment",
        "return on your insurance",
    ]

    text_lower = response.response_text.lower()
    for term in investment_terms:
        if term in text_lower:
            return True, (
                f"Note: Consider rephrasing '{term}'. Insurance products provide "
                f"protection and may have cash value accumulation features, "
                f"but are not investments in the traditional sense."
            )

    return True, ""


def check_no_carrier_recommendations(
    response: InsuranceResponseContext
) -> tuple[bool, str]:
    """Don't recommend specific carriers"""
    recommendation_patterns = [
        r"(you should|I recommend|best choice is)\s+[A-Z][a-z]+\s+(Life|Insurance)",
        r"go with\s+[A-Z][a-z]+",
        r"buy from\s+[A-Z][a-z]+",
    ]

    for pattern in recommendation_patterns:
        if re.search(pattern, response.response_text):
            return True, (
                "Note: Specific carrier recommendations require proper licensing "
                "and suitability analysis. Consider rephrasing to present options "
                "rather than recommendations."
            )

    return True, ""


def check_no_medical_advice(
    response: InsuranceResponseContext
) -> tuple[bool, str]:
    """Block medical advice for underwriting"""
    medical_advice_patterns = [
        r"(don't|do not)\s+(disclose|mention|tell them about)",
        r"hide\s+(your|the)\s+(condition|diagnosis|medication)",
        r"(you can|should)\s+(lie|omit|leave out)",
    ]

    for pattern in medical_advice_patterns:
        if re.search(pattern, response.response_text.lower()):
            return False, (
                "BLOCKED: Response may encourage non-disclosure of medical information. "
                "All applications require truthful and complete disclosure. "
                "Material misrepresentation can void policies."
            )

    return True, ""


def check_illustration_disclaimer(
    response: InsuranceResponseContext
) -> tuple[bool, str]:
    """Require disclaimer for projections"""
    if not response.includes_projection:
        return True, ""

    projection_indicators = [
        "will grow to",
        "projected value",
        "at age",
        "in 20 years",
        "cash value of",
    ]

    needs_disclaimer = any(
        ind in response.response_text.lower()
        for ind in projection_indicators
    )

    if needs_disclaimer:
        return False, (
            "DISCLAIMER REQUIRED: Projections must include:\n"
            "- 'Non-guaranteed values are NOT guaranteed and may be higher or lower.'\n"
            "- 'Illustrations are hypothetical and not guarantees of future performance.'\n"
            "- 'Actual results depend on factors not shown in this projection.'"
        )

    return True, ""


def check_recommendation_disclaimer(
    response: InsuranceResponseContext
) -> tuple[bool, str]:
    """Ensure educational disclaimer is present"""
    if response.intent in ["recommendation", "comparison", "quote"]:
        disclaimer_phrases = [
            "for educational purposes",
            "not a recommendation",
            "consult a licensed",
            "does not constitute advice",
        ]

        has_disclaimer = any(
            phrase in response.response_text.lower()
            for phrase in disclaimer_phrases
        )

        if not has_disclaimer:
            return False, (
                "DISCLAIMER REQUIRED: Add educational disclaimer such as:\n"
                "'This information is for educational purposes only and does not "
                "constitute a recommendation. Consult a licensed insurance "
                "professional for personalized advice.'"
            )

    return True, ""


def check_tax_disclosure(
    response: InsuranceResponseContext
) -> tuple[bool, str]:
    """Add tax implications when relevant"""
    tax_relevant_terms = [
        "cash value",
        "surrender",
        "withdrawal",
        "annuity payment",
        "1035 exchange",
        "death benefit",
    ]

    text_lower = response.response_text.lower()
    if any(term in text_lower for term in tax_relevant_terms):
        tax_phrases = [
            "tax",
            "irs",
            "taxable",
            "income tax",
        ]

        if not any(phrase in text_lower for phrase in tax_phrases):
            return True, (
                "Consider adding tax note: Withdrawals, surrenders, and certain "
                "transactions may have tax implications. Consult a tax professional."
            )

    return True, ""


def check_california_annuity_rules(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """California-specific annuity rules"""
    if client.state != "CA":
        return True, ""

    if product and "annuity" in product.product_type.lower() and client.age >= 65:
        return True, (
            "CALIFORNIA NOTICE: California requires specific annuity training "
            "for sales to seniors. Ensure proper documentation of:\n"
            "- Suitability analysis\n"
            "- Reason for recommendation\n"
            "- Alternatives considered\n"
            "- Client's stated financial objectives"
        )

    return True, ""


def check_new_york_best_interest(
    client: InsuranceClientContext,
    product: Optional[InsuranceProductContext] = None
) -> tuple[bool, str]:
    """New York Regulation 187 best interest standard"""
    if client.state != "NY":
        return True, ""

    return True, (
        "NEW YORK NOTICE: Under Regulation 187, recommendations must be in the "
        "client's best interest. Documentation required:\n"
        "- Care obligation: Reasonable basis for recommendation\n"
        "- Disclosure obligation: Material conflicts of interest\n"
        "- The basis for the determination that the recommendation is suitable"
    )


# =============================================================================
# MAIN COMPLIANCE CHECK FUNCTION
# =============================================================================

class InsuranceComplianceResult:
    """Result of compliance check"""

    def __init__(self):
        self.passed = True
        self.blocked = False
        self.warnings: List[str] = []
        self.required_disclosures: List[str] = []
        self.triggered_rules: List[str] = []

    def add_warning(self, rule_id: str, message: str):
        self.warnings.append(f"[{rule_id}] {message}")
        self.triggered_rules.append(rule_id)

    def add_disclosure(self, rule_id: str, message: str):
        self.required_disclosures.append(f"[{rule_id}] {message}")
        self.triggered_rules.append(rule_id)

    def block(self, rule_id: str, message: str):
        self.blocked = True
        self.passed = False
        self.warnings.append(f"[{rule_id}] BLOCKED: {message}")
        self.triggered_rules.append(rule_id)


def check_insurance_compliance(
    client: Optional[InsuranceClientContext] = None,
    product: Optional[InsuranceProductContext] = None,
    response: Optional[InsuranceResponseContext] = None,
) -> InsuranceComplianceResult:
    """
    Run all applicable insurance compliance rules.

    Returns a result object with warnings, required disclosures, and block status.
    """
    result = InsuranceComplianceResult()

    # Check function registry
    check_functions = {
        "check_senior_annuity_suitability": check_senior_annuity_suitability,
        "check_premium_affordability": check_premium_affordability,
        "check_surrender_period_suitability": check_surrender_period_suitability,
        "check_risk_tolerance_alignment": check_risk_tolerance_alignment,
        "check_replacement_disclosure": check_replacement_disclosure,
        "check_replacement_comparison": check_replacement_comparison,
        "check_surrender_charge_warning": check_surrender_charge_warning,
        "check_no_guaranteed_returns": check_no_guaranteed_returns,
        "check_no_investment_language": check_no_investment_language,
        "check_no_carrier_recommendations": check_no_carrier_recommendations,
        "check_no_medical_advice": check_no_medical_advice,
        "check_illustration_disclaimer": check_illustration_disclaimer,
        "check_recommendation_disclaimer": check_recommendation_disclaimer,
        "check_tax_disclosure": check_tax_disclosure,
        "check_california_annuity_rules": check_california_annuity_rules,
        "check_new_york_best_interest": check_new_york_best_interest,
    }

    for rule in INSURANCE_RULES:
        check_fn = check_functions.get(rule.check_function)
        if not check_fn:
            continue

        # Determine which context to pass
        try:
            if rule.category in ["prohibited_content", "disclosure"]:
                if response:
                    passed, message = check_fn(response)
                else:
                    continue
            else:
                if client:
                    passed, message = check_fn(client, product)
                else:
                    continue

            if not passed or message:
                if rule.action == RuleAction.BLOCK_RESPONSE:
                    result.block(rule.rule_id, message)
                elif rule.action == RuleAction.REQUIRE_DISCLOSURE:
                    result.add_disclosure(rule.rule_id, message)
                elif rule.action in [RuleAction.ADD_WARNING, RuleAction.MODIFY_RESPONSE]:
                    if message:
                        result.add_warning(rule.rule_id, message)

        except Exception as e:
            result.add_warning(rule.rule_id, f"Rule check error: {str(e)}")

    return result
