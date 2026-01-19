"""
Accounting Compliance Rules Engine for Elson Financial AI

Implements rules to ensure the AI provides helpful financial guidance
while staying within appropriate boundaries.

Key Principle: The AI helps with organization, categorization, and education.
It does NOT perform actual tax calculations, filing, or professional accounting.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
import re


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

class AccountingAuthority(str, Enum):
    """Decision authority for accounting compliance"""
    COMPLIANCE = "compliance"  # Binding
    EDUCATION = "education"  # Advisory
    TAX_PROFESSIONAL = "tax_professional"  # Requires CPA/EA


class AccountingRuleAction(str, Enum):
    """Actions when rule triggers"""
    BLOCK_RESPONSE = "block_response"
    ADD_DISCLAIMER = "add_disclaimer"
    ADD_WARNING = "add_warning"
    REDIRECT_TO_PROFESSIONAL = "redirect_to_professional"
    LOG_FOR_REVIEW = "log_for_review"


class AccountingRuleSeverity(str, Enum):
    """Rule severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# CONTEXT OBJECTS
# =============================================================================

@dataclass
class AccountingRequestContext:
    """Context for accounting-related requests"""
    request_type: str  # categorize, budget, forecast, kpi, tax_question
    involves_tax_filing: bool = False
    involves_tax_calculation: bool = False
    involves_business_accounting: bool = False
    involves_audit: bool = False
    is_historical: bool = True  # vs real-time decisions
    amount_threshold: Decimal = Decimal("0")


@dataclass
class AccountingResponseContext:
    """Context for checking AI responses"""
    response_text: str
    includes_tax_advice: bool = False
    includes_specific_numbers: bool = False
    includes_filing_instructions: bool = False


# =============================================================================
# COMPLIANCE RULES
# =============================================================================

@dataclass
class AccountingRule:
    """Definition of an accounting compliance rule"""
    rule_id: str
    name: str
    description: str
    authority: AccountingAuthority
    severity: AccountingRuleSeverity
    action: AccountingRuleAction
    category: str
    check_function: str


# Registry of accounting compliance rules
ACCOUNTING_RULES: List[AccountingRule] = [
    # ==========================================================================
    # TAX BOUNDARY RULES
    # ==========================================================================
    AccountingRule(
        rule_id="ACCT_TAX_001",
        name="No Tax Filing Instructions",
        description="Cannot provide specific tax filing instructions",
        authority=AccountingAuthority.COMPLIANCE,
        severity=AccountingRuleSeverity.CRITICAL,
        action=AccountingRuleAction.BLOCK_RESPONSE,
        category="tax_boundary",
        check_function="check_no_tax_filing_instructions"
    ),
    AccountingRule(
        rule_id="ACCT_TAX_002",
        name="No Specific Tax Calculations",
        description="Cannot calculate specific tax liability",
        authority=AccountingAuthority.TAX_PROFESSIONAL,
        severity=AccountingRuleSeverity.CRITICAL,
        action=AccountingRuleAction.REDIRECT_TO_PROFESSIONAL,
        category="tax_boundary",
        check_function="check_no_specific_tax_calculations"
    ),
    AccountingRule(
        rule_id="ACCT_TAX_003",
        name="No Tax Evasion Assistance",
        description="Cannot help with tax evasion or illegal schemes",
        authority=AccountingAuthority.COMPLIANCE,
        severity=AccountingRuleSeverity.CRITICAL,
        action=AccountingRuleAction.BLOCK_RESPONSE,
        category="tax_boundary",
        check_function="check_no_tax_evasion"
    ),
    AccountingRule(
        rule_id="ACCT_TAX_004",
        name="Tax Year Disclaimer",
        description="Tax information may be outdated; verify current rules",
        authority=AccountingAuthority.EDUCATION,
        severity=AccountingRuleSeverity.MEDIUM,
        action=AccountingRuleAction.ADD_DISCLAIMER,
        category="tax_boundary",
        check_function="check_tax_year_disclaimer"
    ),

    # ==========================================================================
    # PROFESSIONAL BOUNDARY RULES
    # ==========================================================================
    AccountingRule(
        rule_id="ACCT_PROF_001",
        name="CPA Referral for Complex Matters",
        description="Complex accounting requires professional guidance",
        authority=AccountingAuthority.TAX_PROFESSIONAL,
        severity=AccountingRuleSeverity.HIGH,
        action=AccountingRuleAction.REDIRECT_TO_PROFESSIONAL,
        category="professional_boundary",
        check_function="check_cpa_referral_needed"
    ),
    AccountingRule(
        rule_id="ACCT_PROF_002",
        name="Audit Assistance Limitation",
        description="Cannot represent in audits or provide audit defense",
        authority=AccountingAuthority.TAX_PROFESSIONAL,
        severity=AccountingRuleSeverity.CRITICAL,
        action=AccountingRuleAction.REDIRECT_TO_PROFESSIONAL,
        category="professional_boundary",
        check_function="check_audit_limitation"
    ),
    AccountingRule(
        rule_id="ACCT_PROF_003",
        name="Business Entity Advice Limitation",
        description="Entity structure advice requires professional consultation",
        authority=AccountingAuthority.TAX_PROFESSIONAL,
        severity=AccountingRuleSeverity.HIGH,
        action=AccountingRuleAction.ADD_WARNING,
        category="professional_boundary",
        check_function="check_entity_advice_limitation"
    ),

    # ==========================================================================
    # DATA INTEGRITY RULES
    # ==========================================================================
    AccountingRule(
        rule_id="ACCT_DATA_001",
        name="Verify Categorization",
        description="User should verify AI-suggested categorizations",
        authority=AccountingAuthority.EDUCATION,
        severity=AccountingRuleSeverity.MEDIUM,
        action=AccountingRuleAction.ADD_DISCLAIMER,
        category="data_integrity",
        check_function="check_categorization_disclaimer"
    ),
    AccountingRule(
        rule_id="ACCT_DATA_002",
        name="Projection Uncertainty",
        description="Forecasts and projections are estimates only",
        authority=AccountingAuthority.EDUCATION,
        severity=AccountingRuleSeverity.MEDIUM,
        action=AccountingRuleAction.ADD_DISCLAIMER,
        category="data_integrity",
        check_function="check_projection_disclaimer"
    ),

    # ==========================================================================
    # PERSONAL/BUSINESS SEPARATION
    # ==========================================================================
    AccountingRule(
        rule_id="ACCT_SEP_001",
        name="Personal/Business Separation Warning",
        description="Warn about mixing personal and business finances",
        authority=AccountingAuthority.EDUCATION,
        severity=AccountingRuleSeverity.MEDIUM,
        action=AccountingRuleAction.ADD_WARNING,
        category="separation",
        check_function="check_separation_warning"
    ),
]


# =============================================================================
# RULE CHECK FUNCTIONS
# =============================================================================

def check_no_tax_filing_instructions(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Block responses with specific tax filing instructions"""
    filing_patterns = [
        r"file\s+(your|the)\s+(tax|1040|schedule)",
        r"enter\s+(this|the)\s+amount\s+on\s+(line|form)",
        r"report\s+(this|it)\s+on\s+(schedule|form)\s+\w+",
        r"fill\s+out\s+(form|schedule)\s+\d+",
        r"submit\s+(to|with)\s+the\s+irs",
        r"mail\s+(your|the)\s+(return|form)\s+to",
        r"e-file\s+(your|the)",
    ]

    for pattern in filing_patterns:
        if re.search(pattern, response.response_text.lower()):
            return False, (
                "BLOCKED: Cannot provide specific tax filing instructions. "
                "For filing guidance, please consult a tax professional (CPA or EA) "
                "or use IRS-approved tax preparation software."
            )

    return True, ""


def check_no_specific_tax_calculations(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Block specific tax liability calculations"""
    calculation_patterns = [
        r"your\s+tax\s+(liability|owed|due)\s+(is|will be|equals?)\s*\$?\d+",
        r"you\s+(owe|will owe)\s+\$?\d+\s+(in|to)\s+tax",
        r"your\s+refund\s+(is|will be)\s+\$?\d+",
        r"total\s+tax\s*[:=]\s*\$?\d+",
        r"tax\s+due\s*[:=]\s*\$?\d+",
    ]

    for pattern in calculation_patterns:
        if re.search(pattern, response.response_text.lower()):
            return False, (
                "TAX PROFESSIONAL NEEDED: Specific tax calculations require a "
                "qualified tax professional. The AI can explain concepts and "
                "general rules, but cannot determine your specific tax liability. "
                "Please consult a CPA or EA for accurate calculations."
            )

    return True, ""


def check_no_tax_evasion(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Block any tax evasion assistance"""
    evasion_patterns = [
        r"(hide|conceal)\s+(income|money|assets)",
        r"(avoid|evade)\s+(reporting|taxes)",
        r"(don't|do not)\s+report",
        r"(offshore|foreign)\s+(account|shell)",
        r"(launder|laundering)",
        r"(under|mis)report",
        r"cash\s+(only|basis)\s+(to avoid|so they)",
    ]

    for pattern in evasion_patterns:
        if re.search(pattern, response.response_text.lower()):
            return False, (
                "BLOCKED: Cannot assist with tax evasion or illegal schemes. "
                "Tax evasion is a federal crime. For legitimate tax planning "
                "and optimization strategies, consult a licensed tax professional."
            )

    return True, ""


def check_tax_year_disclaimer(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Add disclaimer about tax information currency"""
    tax_terms = [
        "tax bracket",
        "standard deduction",
        "contribution limit",
        "tax rate",
        "exemption",
        "tax credit",
        "deduction limit",
    ]

    if any(term in response.response_text.lower() for term in tax_terms):
        return True, (
            "Note: Tax rules, rates, and limits change annually. "
            "Verify current figures with IRS publications or a tax professional."
        )

    return True, ""


def check_cpa_referral_needed(
    request: AccountingRequestContext
) -> tuple[bool, str]:
    """Determine if CPA referral is needed"""
    complex_indicators = [
        request.involves_business_accounting,
        request.involves_audit,
        request.amount_threshold > Decimal("100000"),
    ]

    if any(complex_indicators):
        return True, (
            "PROFESSIONAL RECOMMENDED: Given the complexity of this matter, "
            "we recommend consulting a Certified Public Accountant (CPA) or "
            "Enrolled Agent (EA) who can provide personalized guidance."
        )

    return True, ""


def check_audit_limitation(
    request: AccountingRequestContext
) -> tuple[bool, str]:
    """Cannot assist with audits"""
    if request.involves_audit:
        return False, (
            "AUDIT ASSISTANCE LIMITATION: The AI cannot represent you in an "
            "IRS audit or provide audit defense. Only qualified professionals "
            "(CPAs, EAs, or tax attorneys) can represent taxpayers before the IRS. "
            "Please seek professional representation immediately."
        )

    return True, ""


def check_entity_advice_limitation(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Warn about business entity advice"""
    entity_terms = [
        "should form an llc",
        "incorporate as",
        "s-corp election",
        "convert to",
        "best entity type",
        "you should be a",
    ]

    if any(term in response.response_text.lower() for term in entity_terms):
        return True, (
            "PROFESSIONAL CONSULTATION ADVISED: Business entity decisions have "
            "significant legal and tax implications. Consult a CPA and/or attorney "
            "before forming or changing your business structure."
        )

    return True, ""


def check_categorization_disclaimer(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Add disclaimer for categorization suggestions"""
    categorization_terms = [
        "categorize",
        "category",
        "classify",
        "should be recorded as",
        "belongs in",
    ]

    if any(term in response.response_text.lower() for term in categorization_terms):
        return True, (
            "Note: AI-suggested categories are for organizational purposes. "
            "Verify categorizations before using for tax or financial reporting."
        )

    return True, ""


def check_projection_disclaimer(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Add disclaimer for projections and forecasts"""
    projection_terms = [
        "forecast",
        "projection",
        "estimate",
        "predict",
        "expected",
        "anticipated",
    ]

    if any(term in response.response_text.lower() for term in projection_terms):
        return True, (
            "Note: Projections are estimates based on current information and "
            "assumptions. Actual results will vary. Review and update regularly."
        )

    return True, ""


def check_separation_warning(
    response: AccountingResponseContext
) -> tuple[bool, str]:
    """Warn about personal/business separation"""
    separation_concerns = [
        "personal expense",
        "business expense",
        "mixed use",
        "personal account",
        "business account",
    ]

    text_lower = response.response_text.lower()
    if any(term in text_lower for term in separation_concerns):
        if "separate" not in text_lower:
            return True, (
                "Reminder: Keep personal and business finances separate. "
                "Mixing funds can create liability issues and tax complications."
            )

    return True, ""


# =============================================================================
# TRANSACTION CATEGORIZATION RULES
# =============================================================================

# Common transaction categorization patterns
CATEGORIZATION_PATTERNS = {
    # Income patterns
    "income_salary": [
        r"payroll",
        r"salary",
        r"direct deposit",
        r"wages",
        r"paycheck",
    ],
    "income_business": [
        r"invoice payment",
        r"client payment",
        r"stripe",
        r"square",
        r"paypal.*received",
    ],
    "income_investment": [
        r"dividend",
        r"interest.*earned",
        r"capital gain",
        r"distribution",
    ],

    # Expense patterns
    "expense_housing": [
        r"rent",
        r"mortgage",
        r"hoa",
        r"property tax",
        r"home insurance",
    ],
    "expense_utilities": [
        r"electric",
        r"gas.*company",
        r"water.*utility",
        r"internet",
        r"cable",
        r"phone",
    ],
    "expense_food": [
        r"grocery",
        r"safeway",
        r"kroger",
        r"whole foods",
        r"trader joe",
        r"costco",
        r"restaurant",
        r"doordash",
        r"ubereats",
        r"grubhub",
    ],
    "expense_transportation": [
        r"gas\s+station",
        r"shell",
        r"chevron",
        r"exxon",
        r"uber(?!eats)",
        r"lyft",
        r"parking",
        r"toll",
        r"car wash",
        r"auto insurance",
    ],
    "expense_healthcare": [
        r"pharmacy",
        r"cvs",
        r"walgreens",
        r"doctor",
        r"medical",
        r"hospital",
        r"dental",
        r"vision",
        r"health insurance",
    ],
    "expense_entertainment": [
        r"netflix",
        r"spotify",
        r"hulu",
        r"disney\+",
        r"movie",
        r"theater",
        r"concert",
        r"gaming",
    ],
    "expense_shopping": [
        r"amazon",
        r"target",
        r"walmart",
        r"best buy",
        r"clothing",
        r"department store",
    ],
}


def suggest_category(description: str) -> tuple[Optional[str], Decimal]:
    """
    Suggest a category for a transaction based on description.
    Returns (category, confidence).
    """
    description_lower = description.lower()

    for category, patterns in CATEGORIZATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, description_lower):
                return category, Decimal("0.85")

    return None, Decimal("0")


# =============================================================================
# MAIN COMPLIANCE CHECK FUNCTION
# =============================================================================

class AccountingComplianceResult:
    """Result of accounting compliance check"""

    def __init__(self):
        self.passed = True
        self.blocked = False
        self.warnings: List[str] = []
        self.disclaimers: List[str] = []
        self.professional_referrals: List[str] = []
        self.triggered_rules: List[str] = []

    def add_warning(self, rule_id: str, message: str):
        self.warnings.append(f"[{rule_id}] {message}")
        self.triggered_rules.append(rule_id)

    def add_disclaimer(self, rule_id: str, message: str):
        self.disclaimers.append(message)
        self.triggered_rules.append(rule_id)

    def add_referral(self, rule_id: str, message: str):
        self.professional_referrals.append(f"[{rule_id}] {message}")
        self.triggered_rules.append(rule_id)

    def block(self, rule_id: str, message: str):
        self.blocked = True
        self.passed = False
        self.warnings.append(f"[{rule_id}] BLOCKED: {message}")
        self.triggered_rules.append(rule_id)


def check_accounting_compliance(
    request: Optional[AccountingRequestContext] = None,
    response: Optional[AccountingResponseContext] = None,
) -> AccountingComplianceResult:
    """
    Run all applicable accounting compliance rules.
    """
    result = AccountingComplianceResult()

    # Check functions that need request context
    if request:
        if request.involves_audit:
            passed, msg = check_audit_limitation(request)
            if not passed:
                result.add_referral("ACCT_PROF_002", msg)

        passed, msg = check_cpa_referral_needed(request)
        if msg:
            result.add_referral("ACCT_PROF_001", msg)

    # Check functions that need response context
    if response:
        # Critical checks (can block)
        passed, msg = check_no_tax_filing_instructions(response)
        if not passed:
            result.block("ACCT_TAX_001", msg)
            return result  # Stop checking if blocked

        passed, msg = check_no_specific_tax_calculations(response)
        if not passed:
            result.add_referral("ACCT_TAX_002", msg)

        passed, msg = check_no_tax_evasion(response)
        if not passed:
            result.block("ACCT_TAX_003", msg)
            return result

        # Advisory checks
        passed, msg = check_tax_year_disclaimer(response)
        if msg:
            result.add_disclaimer("ACCT_TAX_004", msg)

        passed, msg = check_entity_advice_limitation(response)
        if msg:
            result.add_warning("ACCT_PROF_003", msg)

        passed, msg = check_categorization_disclaimer(response)
        if msg:
            result.add_disclaimer("ACCT_DATA_001", msg)

        passed, msg = check_projection_disclaimer(response)
        if msg:
            result.add_disclaimer("ACCT_DATA_002", msg)

        passed, msg = check_separation_warning(response)
        if msg:
            result.add_warning("ACCT_SEP_001", msg)

    return result
