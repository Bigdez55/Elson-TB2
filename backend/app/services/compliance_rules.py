"""
Neuro-Symbolic Compliance Rules Engine

Handles BINDING decision authority roles (CCO, General Counsel, Tax Manager) with
deterministic rules that cannot be overridden by LLM reasoning.

This engine ensures compliance even if the LLM hallucinates or provides incorrect
advice. All BINDING rules are checked:
1. Pre-generation: Before the LLM generates a response
2. Post-generation: After the LLM generates to validate compliance

Decision Authority Levels:
- BINDING: Deterministic rules, must be followed - LLM cannot override
- SENIOR_ADVISORY: High-weight recommendations, near-binding
- ADVISORY: Standard recommendations, user decides
- SUPPORT_ROLE: Informational only, background context
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class RuleAuthority(str, Enum):
    """Authority responsible for the compliance rule."""
    CCO = "CCO"  # Chief Compliance Officer
    TAX_MANAGER = "TAX_MANAGER"
    GENERAL_COUNSEL = "GENERAL_COUNSEL"
    CIO = "CIO"  # Chief Investment Officer
    CRO = "CRO"  # Chief Risk Officer
    CFO = "CFO"  # Chief Financial Officer


class RuleAction(str, Enum):
    """Actions to take when a rule is triggered."""
    BLOCK_RESPONSE = "block_response"  # Stop and require human review
    REQUIRE_DISCLOSURE = "require_disclosure"  # Add mandatory disclosure
    REQUIRE_FILING = "require_filing"  # Require regulatory filing
    ADD_WARNING = "add_warning"  # Add warning to response
    ESCALATE = "escalate"  # Escalate to human professional
    MODIFY_RESPONSE = "modify_response"  # Modify the response content


class RuleSeverity(str, Enum):
    """Severity level of the rule."""
    CRITICAL = "critical"  # Must block/escalate
    HIGH = "high"  # Serious compliance concern
    MEDIUM = "medium"  # Standard compliance requirement
    LOW = "low"  # Informational/best practice


@dataclass
class RuleResult:
    """Result of a rule check."""
    rule_id: str
    rule_name: str
    triggered: bool
    action: RuleAction
    severity: RuleSeverity
    authority: RuleAuthority
    message: str
    details: dict = field(default_factory=dict)
    required_disclosures: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of response validation."""
    is_valid: bool
    violations: list[RuleResult] = field(default_factory=list)
    warnings: list[RuleResult] = field(default_factory=list)
    required_disclosures: list[str] = field(default_factory=list)
    modified_response: Optional[str] = None


@dataclass
class TransactionContext:
    """Context for transaction-related rule checks."""
    amount: Decimal = Decimal("0")
    transaction_type: str = ""
    currency: str = "USD"
    parties: list[str] = field(default_factory=list)
    is_international: bool = False
    is_cash: bool = False
    source_of_funds: str = ""
    beneficiary: str = ""


@dataclass
class GiftContext:
    """Context for gift/transfer-related rule checks."""
    amount: Decimal = Decimal("0")
    recipient: str = ""
    relationship: str = ""  # spouse, child, grandchild, unrelated
    gift_type: str = ""  # cash, securities, real_estate
    is_split_gift: bool = False  # Joint gift with spouse
    year: int = field(default_factory=lambda: datetime.now().year)


@dataclass
class InvestmentContext:
    """Context for investment-related rule checks."""
    asset_class: str = ""
    allocation_percentage: Decimal = Decimal("0")
    is_concentrated: bool = False
    risk_level: str = ""  # low, medium, high, speculative
    conflicts_with_ips: bool = False
    is_prohibited_investment: bool = False


class ComplianceRulesEngine:
    """
    Neuro-symbolic rules engine for BINDING decisions.

    Implements deterministic rules from:
    - CCO: AML/KYC compliance, regulatory monitoring
    - Tax Manager: Tax thresholds, filing deadlines
    - General Counsel: Fiduciary duties, legal compliance
    - CIO: Investment policy compliance
    """

    # 2024/2025 Tax Thresholds (Updated annually)
    GIFT_TAX_ANNUAL_EXCLUSION = Decimal("18000")  # 2024 limit
    GIFT_TAX_LIFETIME_EXCLUSION = Decimal("13610000")  # 2024 limit
    AML_CASH_REPORTING_THRESHOLD = Decimal("10000")
    SAR_THRESHOLD = Decimal("5000")  # Suspicious activity threshold
    ESTATE_TAX_EXEMPTION = Decimal("13610000")  # 2024 limit
    GST_TAX_EXEMPTION = Decimal("13610000")  # 2024 limit

    def __init__(self):
        """Initialize the compliance rules engine."""
        self.rules = self._initialize_rules()
        logger.info(f"ComplianceRulesEngine initialized with {len(self.rules)} rules")

    def _initialize_rules(self) -> dict[str, dict]:
        """Initialize all compliance rules."""
        return {
            # AML/KYC Rules (CCO Authority)
            "AML_CASH_REPORTING": {
                "name": "Currency Transaction Report (CTR) Requirement",
                "authority": RuleAuthority.CCO,
                "severity": RuleSeverity.CRITICAL,
                "description": "Cash transactions of $10,000 or more require CTR filing",
                "threshold": self.AML_CASH_REPORTING_THRESHOLD,
                "action": RuleAction.REQUIRE_FILING,
            },
            "AML_STRUCTURING_DETECTION": {
                "name": "Structuring Detection",
                "authority": RuleAuthority.CCO,
                "severity": RuleSeverity.CRITICAL,
                "description": "Multiple transactions designed to avoid reporting thresholds",
                "action": RuleAction.BLOCK_RESPONSE,
            },
            "AML_SAR_THRESHOLD": {
                "name": "Suspicious Activity Report Threshold",
                "authority": RuleAuthority.CCO,
                "severity": RuleSeverity.HIGH,
                "description": "Suspicious transactions of $5,000+ require SAR consideration",
                "threshold": self.SAR_THRESHOLD,
                "action": RuleAction.ESCALATE,
            },
            "AML_PEP_SCREENING": {
                "name": "Politically Exposed Person Screening",
                "authority": RuleAuthority.CCO,
                "severity": RuleSeverity.HIGH,
                "description": "Enhanced due diligence required for PEPs",
                "action": RuleAction.REQUIRE_DISCLOSURE,
            },

            # Tax Compliance Rules (Tax Manager Authority)
            "TAX_GIFT_ANNUAL_EXCLUSION": {
                "name": "Gift Tax Annual Exclusion",
                "authority": RuleAuthority.TAX_MANAGER,
                "severity": RuleSeverity.MEDIUM,
                "description": f"Gifts over ${self.GIFT_TAX_ANNUAL_EXCLUSION:,} require gift tax return",
                "threshold": self.GIFT_TAX_ANNUAL_EXCLUSION,
                "action": RuleAction.REQUIRE_DISCLOSURE,
            },
            "TAX_GIFT_LIFETIME_EXCLUSION": {
                "name": "Lifetime Gift Tax Exclusion",
                "authority": RuleAuthority.TAX_MANAGER,
                "severity": RuleSeverity.HIGH,
                "description": "Approaching lifetime gift tax exclusion limit",
                "threshold": self.GIFT_TAX_LIFETIME_EXCLUSION,
                "action": RuleAction.ADD_WARNING,
            },
            "TAX_ESTIMATED_PAYMENT": {
                "name": "Estimated Tax Payment Deadlines",
                "authority": RuleAuthority.TAX_MANAGER,
                "severity": RuleSeverity.MEDIUM,
                "description": "Quarterly estimated tax payments required",
                "action": RuleAction.REQUIRE_DISCLOSURE,
            },
            "TAX_FORM_1041_DEADLINE": {
                "name": "Form 1041 Trust Tax Return",
                "authority": RuleAuthority.TAX_MANAGER,
                "severity": RuleSeverity.HIGH,
                "description": "Trust tax returns due April 15 (or extended deadline)",
                "action": RuleAction.REQUIRE_DISCLOSURE,
            },

            # Fiduciary Duty Rules (General Counsel Authority)
            "FIDUCIARY_DUTY_OF_CARE": {
                "name": "Fiduciary Duty of Care",
                "authority": RuleAuthority.GENERAL_COUNSEL,
                "severity": RuleSeverity.CRITICAL,
                "description": "Actions must meet prudent person standard",
                "action": RuleAction.BLOCK_RESPONSE,
            },
            "FIDUCIARY_DUTY_OF_LOYALTY": {
                "name": "Fiduciary Duty of Loyalty",
                "authority": RuleAuthority.GENERAL_COUNSEL,
                "severity": RuleSeverity.CRITICAL,
                "description": "Must act solely in beneficiary's interest",
                "action": RuleAction.BLOCK_RESPONSE,
            },
            "FIDUCIARY_CONFLICT_OF_INTEREST": {
                "name": "Conflict of Interest Detection",
                "authority": RuleAuthority.GENERAL_COUNSEL,
                "severity": RuleSeverity.CRITICAL,
                "description": "Self-dealing or conflicts must be disclosed/avoided",
                "action": RuleAction.ESCALATE,
            },
            "FIDUCIARY_IMPARTIALITY": {
                "name": "Duty of Impartiality",
                "authority": RuleAuthority.GENERAL_COUNSEL,
                "severity": RuleSeverity.HIGH,
                "description": "Balance interests of current and remainder beneficiaries",
                "action": RuleAction.ADD_WARNING,
            },

            # Investment Policy Rules (CIO Authority)
            "IPS_COMPLIANCE": {
                "name": "Investment Policy Statement Compliance",
                "authority": RuleAuthority.CIO,
                "severity": RuleSeverity.HIGH,
                "description": "Investment recommendations must comply with IPS",
                "action": RuleAction.BLOCK_RESPONSE,
            },
            "IPS_CONCENTRATION_LIMIT": {
                "name": "Concentration Risk Limit",
                "authority": RuleAuthority.CIO,
                "severity": RuleSeverity.MEDIUM,
                "description": "Single position should not exceed policy limits",
                "action": RuleAction.ADD_WARNING,
            },
            "IPS_PROHIBITED_INVESTMENTS": {
                "name": "Prohibited Investments",
                "authority": RuleAuthority.CIO,
                "severity": RuleSeverity.CRITICAL,
                "description": "Certain investments prohibited by policy",
                "action": RuleAction.BLOCK_RESPONSE,
            },

            # Privacy/Security Rules (CCO Authority)
            "PRIVACY_PII_PROTECTION": {
                "name": "PII Protection",
                "authority": RuleAuthority.CCO,
                "severity": RuleSeverity.CRITICAL,
                "description": "Personal identifiable information must be protected",
                "action": RuleAction.BLOCK_RESPONSE,
            },
            "PRIVACY_CONSENT_REQUIRED": {
                "name": "Consent Required for Data Sharing",
                "authority": RuleAuthority.CCO,
                "severity": RuleSeverity.HIGH,
                "description": "Client consent required before sharing information",
                "action": RuleAction.REQUIRE_DISCLOSURE,
            },
        }

    def check_transaction(self, context: TransactionContext) -> list[RuleResult]:
        """
        Check transaction-related compliance rules.

        Args:
            context: Transaction context with amount, type, parties, etc.

        Returns:
            List of triggered rule results
        """
        results = []

        # AML Cash Reporting Threshold
        if context.is_cash and context.amount >= self.AML_CASH_REPORTING_THRESHOLD:
            rule = self.rules["AML_CASH_REPORTING"]
            results.append(RuleResult(
                rule_id="AML_CASH_REPORTING",
                rule_name=rule["name"],
                triggered=True,
                action=rule["action"],
                severity=rule["severity"],
                authority=rule["authority"],
                message=f"Cash transaction of ${context.amount:,.2f} requires Currency Transaction Report (CTR) filing with FinCEN within 15 days.",
                details={"amount": str(context.amount), "threshold": str(self.AML_CASH_REPORTING_THRESHOLD)},
                required_disclosures=[
                    "This transaction requires filing a Currency Transaction Report (CTR) with FinCEN.",
                    "Financial institutions must file CTR within 15 days of the transaction."
                ]
            ))

        # SAR Threshold for suspicious activity
        if context.amount >= self.SAR_THRESHOLD:
            # Check for suspicious patterns
            suspicious_indicators = []
            if context.is_international and not context.source_of_funds:
                suspicious_indicators.append("International transaction without documented source of funds")
            if context.amount == Decimal("9999") or context.amount == Decimal("9900"):
                suspicious_indicators.append("Amount appears structured to avoid reporting threshold")

            if suspicious_indicators:
                rule = self.rules["AML_SAR_THRESHOLD"]
                results.append(RuleResult(
                    rule_id="AML_SAR_THRESHOLD",
                    rule_name=rule["name"],
                    triggered=True,
                    action=rule["action"],
                    severity=rule["severity"],
                    authority=rule["authority"],
                    message="Transaction exhibits suspicious indicators. Consider Suspicious Activity Report (SAR) filing.",
                    details={"indicators": suspicious_indicators, "amount": str(context.amount)},
                    required_disclosures=[
                        "This transaction may require a Suspicious Activity Report (SAR) to be filed.",
                        "Please consult with the Chief Compliance Officer before proceeding."
                    ]
                ))

        logger.info(f"Transaction check: {len(results)} rules triggered for ${context.amount:,.2f}")
        return results

    def check_gift(self, context: GiftContext) -> list[RuleResult]:
        """
        Check gift/transfer-related compliance rules.

        Args:
            context: Gift context with amount, recipient, relationship, etc.

        Returns:
            List of triggered rule results
        """
        results = []

        # Gift Tax Annual Exclusion
        annual_limit = self.GIFT_TAX_ANNUAL_EXCLUSION
        if context.is_split_gift:
            annual_limit *= 2  # $36,000 for split gifts in 2024

        if context.amount > annual_limit:
            rule = self.rules["TAX_GIFT_ANNUAL_EXCLUSION"]
            excess = context.amount - annual_limit
            results.append(RuleResult(
                rule_id="TAX_GIFT_ANNUAL_EXCLUSION",
                rule_name=rule["name"],
                triggered=True,
                action=rule["action"],
                severity=rule["severity"],
                authority=rule["authority"],
                message=f"Gift of ${context.amount:,.2f} exceeds {context.year} annual exclusion of ${annual_limit:,.2f}. Form 709 (Gift Tax Return) required.",
                details={
                    "gift_amount": str(context.amount),
                    "annual_exclusion": str(annual_limit),
                    "excess_amount": str(excess),
                    "split_gift": context.is_split_gift
                },
                required_disclosures=[
                    f"A gift tax return (Form 709) is required for gifts exceeding the ${annual_limit:,.0f} annual exclusion.",
                    f"The excess of ${excess:,.2f} will be applied against the lifetime gift tax exemption.",
                    "Form 709 is due April 15 of the year following the gift."
                ]
            ))

        # Spouse exception (unlimited marital deduction)
        if context.relationship == "spouse" and context.amount > annual_limit:
            # Modify the result - unlimited marital deduction applies
            for result in results:
                if result.rule_id == "TAX_GIFT_ANNUAL_EXCLUSION":
                    result.message += " Note: If recipient is a US citizen spouse, the unlimited marital deduction may apply."
                    result.required_disclosures.append(
                        "Gifts to US citizen spouses qualify for unlimited marital deduction - no gift tax return required."
                    )

        logger.info(f"Gift check: {len(results)} rules triggered for ${context.amount:,.2f} gift")
        return results

    def check_investment(self, context: InvestmentContext) -> list[RuleResult]:
        """
        Check investment-related compliance rules.

        Args:
            context: Investment context with asset class, allocation, etc.

        Returns:
            List of triggered rule results
        """
        results = []

        # IPS Compliance
        if context.conflicts_with_ips:
            rule = self.rules["IPS_COMPLIANCE"]
            results.append(RuleResult(
                rule_id="IPS_COMPLIANCE",
                rule_name=rule["name"],
                triggered=True,
                action=rule["action"],
                severity=rule["severity"],
                authority=rule["authority"],
                message="This investment recommendation conflicts with the client's Investment Policy Statement (IPS).",
                details={"asset_class": context.asset_class, "conflicts_with_ips": True},
                required_disclosures=[
                    "This recommendation does not comply with the established Investment Policy Statement.",
                    "Please review the IPS before proceeding or seek committee approval for deviation."
                ]
            ))

        # Concentration Limit (typically 10-15% single position)
        if context.is_concentrated or context.allocation_percentage > Decimal("15"):
            rule = self.rules["IPS_CONCENTRATION_LIMIT"]
            results.append(RuleResult(
                rule_id="IPS_CONCENTRATION_LIMIT",
                rule_name=rule["name"],
                triggered=True,
                action=rule["action"],
                severity=rule["severity"],
                authority=rule["authority"],
                message=f"Position concentration of {context.allocation_percentage}% exceeds typical policy limits.",
                details={"allocation": str(context.allocation_percentage), "asset_class": context.asset_class},
                required_disclosures=[
                    "Concentrated positions increase portfolio risk.",
                    "Consider diversification strategies or document the rationale for deviation."
                ]
            ))

        # Prohibited Investments
        if context.is_prohibited_investment:
            rule = self.rules["IPS_PROHIBITED_INVESTMENTS"]
            results.append(RuleResult(
                rule_id="IPS_PROHIBITED_INVESTMENTS",
                rule_name=rule["name"],
                triggered=True,
                action=rule["action"],
                severity=rule["severity"],
                authority=rule["authority"],
                message=f"Investment in {context.asset_class} is prohibited by policy.",
                details={"asset_class": context.asset_class, "prohibited": True},
                required_disclosures=[
                    "This investment type is prohibited under the current Investment Policy Statement.",
                    "This recommendation cannot proceed without policy amendment."
                ]
            ))

        logger.info(f"Investment check: {len(results)} rules triggered")
        return results

    def check_fiduciary_duties(
        self,
        action_description: str,
        beneficiary_impact: str,
        has_conflict: bool = False,
        favors_current_beneficiary: Optional[bool] = None
    ) -> list[RuleResult]:
        """
        Check fiduciary duty compliance.

        Args:
            action_description: Description of the proposed action
            beneficiary_impact: How the action impacts beneficiaries
            has_conflict: Whether there's a conflict of interest
            favors_current_beneficiary: If action favors current over remainder beneficiaries

        Returns:
            List of triggered rule results
        """
        results = []

        # Conflict of Interest
        if has_conflict:
            rule = self.rules["FIDUCIARY_CONFLICT_OF_INTEREST"]
            results.append(RuleResult(
                rule_id="FIDUCIARY_CONFLICT_OF_INTEREST",
                rule_name=rule["name"],
                triggered=True,
                action=rule["action"],
                severity=rule["severity"],
                authority=rule["authority"],
                message="A potential conflict of interest has been identified. This matter must be escalated for review.",
                details={"action": action_description, "has_conflict": True},
                required_disclosures=[
                    "A conflict of interest has been identified.",
                    "This matter requires review by the General Counsel or Trust Protector.",
                    "The fiduciary must recuse themselves from this decision if the conflict cannot be resolved."
                ]
            ))

        # Duty of Impartiality (current vs remainder beneficiaries)
        if favors_current_beneficiary is not None:
            rule = self.rules["FIDUCIARY_IMPARTIALITY"]
            direction = "current" if favors_current_beneficiary else "remainder"
            results.append(RuleResult(
                rule_id="FIDUCIARY_IMPARTIALITY",
                rule_name=rule["name"],
                triggered=True,
                action=rule["action"],
                severity=rule["severity"],
                authority=rule["authority"],
                message=f"This action may disproportionately favor {direction} beneficiaries. Balance of interests required.",
                details={
                    "action": action_description,
                    "favors": direction,
                    "beneficiary_impact": beneficiary_impact
                },
                required_disclosures=[
                    "Trustees must balance the interests of current income beneficiaries and remainder beneficiaries.",
                    "Document the rationale for any distribution decisions that may affect this balance."
                ]
            ))

        logger.info(f"Fiduciary check: {len(results)} rules triggered")
        return results

    def check_all_rules(self, context: dict) -> list[RuleResult]:
        """
        Check all applicable rules based on context.

        This is the main pre-generation check method.

        Args:
            context: Dictionary containing various context types

        Returns:
            List of all triggered rule results
        """
        results = []

        # Transaction rules
        if "transaction" in context:
            tx_context = TransactionContext(**context["transaction"])
            results.extend(self.check_transaction(tx_context))

        # Gift rules
        if "gift" in context:
            gift_context = GiftContext(**context["gift"])
            results.extend(self.check_gift(gift_context))

        # Investment rules
        if "investment" in context:
            inv_context = InvestmentContext(**context["investment"])
            results.extend(self.check_investment(inv_context))

        # Fiduciary duty rules
        if "fiduciary" in context:
            results.extend(self.check_fiduciary_duties(**context["fiduciary"]))

        # Sort by severity (critical first)
        severity_order = {
            RuleSeverity.CRITICAL: 0,
            RuleSeverity.HIGH: 1,
            RuleSeverity.MEDIUM: 2,
            RuleSeverity.LOW: 3
        }
        results.sort(key=lambda r: severity_order.get(r.severity, 99))

        logger.info(f"Total rules checked: {len(results)} triggered")
        return results

    def validate_response(
        self,
        response: str,
        context: dict,
        include_disclosures: bool = True
    ) -> ValidationResult:
        """
        Post-generation validation of LLM response.

        Args:
            response: The generated response to validate
            context: Context for rule checks
            include_disclosures: Whether to add required disclosures

        Returns:
            ValidationResult with validity status and any modifications
        """
        # Run all rule checks
        rule_results = self.check_all_rules(context)

        violations = [r for r in rule_results if r.severity == RuleSeverity.CRITICAL]
        warnings = [r for r in rule_results if r.severity != RuleSeverity.CRITICAL]

        # Collect all required disclosures
        all_disclosures = []
        for result in rule_results:
            all_disclosures.extend(result.required_disclosures)

        # Check if response is valid (no critical violations)
        is_valid = len(violations) == 0

        # Modify response to add disclosures if needed
        modified_response = response
        if include_disclosures and all_disclosures:
            disclosure_text = "\n\n---\n**Important Compliance Disclosures:**\n"
            for i, disclosure in enumerate(all_disclosures, 1):
                disclosure_text += f"{i}. {disclosure}\n"
            modified_response = response + disclosure_text

        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            required_disclosures=all_disclosures,
            modified_response=modified_response if all_disclosures else None
        )

    def should_block_response(self, rule_results: list[RuleResult]) -> bool:
        """
        Determine if the response should be blocked based on rule results.

        Args:
            rule_results: List of rule check results

        Returns:
            True if response should be blocked
        """
        for result in rule_results:
            if result.triggered and result.action == RuleAction.BLOCK_RESPONSE:
                return True
            if result.triggered and result.severity == RuleSeverity.CRITICAL:
                return True
        return False

    def get_escalation_contacts(self, rule_results: list[RuleResult]) -> dict[str, list[str]]:
        """
        Get contact information for escalation based on triggered rules.

        Args:
            rule_results: List of triggered rule results

        Returns:
            Dictionary mapping authority to required actions
        """
        escalations = {}
        for result in rule_results:
            if result.triggered and result.action in [RuleAction.ESCALATE, RuleAction.BLOCK_RESPONSE]:
                authority = result.authority.value
                if authority not in escalations:
                    escalations[authority] = []
                escalations[authority].append(f"{result.rule_name}: {result.message}")

        return escalations


# Singleton instance
_rules_engine: Optional[ComplianceRulesEngine] = None


def get_compliance_engine() -> ComplianceRulesEngine:
    """Get or create the singleton compliance rules engine."""
    global _rules_engine
    if _rules_engine is None:
        _rules_engine = ComplianceRulesEngine()
    return _rules_engine
