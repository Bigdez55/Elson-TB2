"""
Query Router for Intent Classification

Layer 1 of the 5-layer hybrid architecture for Elson Financial AI.

Responsibilities:
1. Classify user queries into 1 of 8 advisory modes
2. Determine service tier based on user profile
3. Identify required professional roles
4. Route to appropriate knowledge domains

This router ensures queries are handled by the right combination of:
- RAG knowledge bases
- Compliance rules
- Professional expertise
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class AdvisoryMode(str, Enum):
    """Advisory modes for specialized wealth management guidance."""

    GENERAL = "general"
    ESTATE_PLANNING = "estate_planning"
    INVESTMENT_ADVISORY = "investment_advisory"
    TAX_OPTIMIZATION = "tax_optimization"
    SUCCESSION_PLANNING = "succession_planning"
    FAMILY_GOVERNANCE = "family_governance"
    TRUST_ADMINISTRATION = "trust_administration"
    CREDIT_FINANCING = "credit_financing"
    COMPLIANCE_OPERATIONS = "compliance_operations"
    FINANCIAL_LITERACY = "financial_literacy"


class ServiceTier(str, Enum):
    """
    Democratized service tiers aligned with US average salary ($66,622/year).

    Philosophy: Same quality advice for everyone - only complexity differs by tier.
    """

    FOUNDATION = "foundation"  # $0-10K - Full CFP access, financial literacy
    BUILDER = "builder"  # $10K-75K - Tax optimization, retirement accounts
    GROWTH = "growth"  # $75K-500K - Portfolio construction, CFA access
    AFFLUENT = "affluent"  # $500K-5M - Full team, trust structures
    HNW_UHNW = "hnw_uhnw"  # $5M+ - Family office, specialists


class DecisionAuthority(str, Enum):
    """Decision authority levels for professional roles."""

    BINDING = "binding"
    SENIOR_ADVISORY = "senior"
    ADVISORY = "advisory"
    SUPPORT_ROLE = "support"


@dataclass
class UserProfile:
    """User profile for tier and role determination."""

    aum: float = 0.0  # Assets Under Management
    income: float = 0.0
    age: int = 0
    has_business: bool = False
    has_trust: bool = False
    has_real_estate: bool = False
    family_members: int = 0
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    existing_relationships: list[str] = field(default_factory=list)  # existing advisors


@dataclass
class RoutingResult:
    """Result of query routing."""

    advisory_mode: AdvisoryMode
    service_tier: ServiceTier
    confidence: float
    required_roles: list[str]
    knowledge_domains: list[str]
    requires_compliance_check: bool
    binding_authorities: list[str]
    reasoning: str


class QueryRouter:
    """
    Intent classification and routing for wealth management queries.

    Implements Layer 1 of the 5-layer hybrid architecture.
    """

    # Advisory mode keywords mapping
    MODE_KEYWORDS = {
        AdvisoryMode.ESTATE_PLANNING: [
            "estate",
            "will",
            "trust",
            "inheritance",
            "probate",
            "beneficiary",
            "heir",
            "legacy",
            "succession",
            "power of attorney",
            "poa",
            "healthcare directive",
            "living will",
            "death",
            "passing",
        ],
        AdvisoryMode.INVESTMENT_ADVISORY: [
            "invest",
            "portfolio",
            "stock",
            "bond",
            "etf",
            "mutual fund",
            "asset allocation",
            "diversification",
            "return",
            "risk",
            "market",
            "securities",
            "equity",
            "fixed income",
        ],
        AdvisoryMode.TAX_OPTIMIZATION: [
            "tax",
            "deduction",
            "credit",
            "irs",
            "form",
            "filing",
            "income tax",
            "capital gains",
            "estate tax",
            "gift tax",
            "1031",
            "roth conversion",
            "tax loss harvesting",
        ],
        AdvisoryMode.SUCCESSION_PLANNING: [
            "business succession",
            "exit strategy",
            "sell business",
            "business transfer",
            "buy-sell agreement",
            "valuation",
            "m&a",
            "merger",
            "acquisition",
            "ownership transfer",
        ],
        AdvisoryMode.FAMILY_GOVERNANCE: [
            "family meeting",
            "family council",
            "governance",
            "family office",
            "family mission",
            "family values",
            "next generation",
            "family education",
            "family constitution",
        ],
        AdvisoryMode.TRUST_ADMINISTRATION: [
            "trustee",
            "trust protector",
            "beneficiary distribution",
            "fiduciary",
            "trust accounting",
            "form 1041",
            "k-1",
            "decanting",
            "trust situs",
            "trustee duties",
        ],
        AdvisoryMode.CREDIT_FINANCING: [
            "credit",
            "loan",
            "mortgage",
            "financing",
            "borrow",
            "business credit",
            "line of credit",
            "sba loan",
            "venture debt",
            "invoice factoring",
        ],
        AdvisoryMode.COMPLIANCE_OPERATIONS: [
            "compliance",
            "aml",
            "kyc",
            "regulatory",
            "audit",
            "sar",
            "ctr",
            "reporting",
            "risk management",
        ],
        AdvisoryMode.FINANCIAL_LITERACY: [
            "budget",
            "save",
            "emergency fund",
            "debt",
            "credit score",
            "beginner",
            "basics",
            "learn",
            "understand",
            "how does",
            "what is",
            "explain",
            "starter",
        ],
    }

    # Roles by service tier
    TIER_ROLES = {
        ServiceTier.FOUNDATION: ["CFP", "Financial Coach"],
        ServiceTier.BUILDER: ["CFP", "CPA", "Insurance Advisor"],
        ServiceTier.GROWTH: ["CFP", "CFA", "CPA", "Estate Planning Attorney"],
        ServiceTier.AFFLUENT: [
            "CFP",
            "CFA",
            "CPA",
            "CPWA",
            "Estate Planning Attorney",
            "Trust Administration Attorney",
            "Insurance Specialist",
        ],
        ServiceTier.HNW_UHNW: [
            "CPWA",
            "CFA",
            "CPA",
            "Family Office CEO",
            "CIO",
            "CFO",
            "Estate Planning Attorney",
            "Trust Administration Attorney",
            "International Tax Attorney",
            "Trust Protector",
            "Philanthropic Advisor",
            "Business Valuation Expert",
        ],
    }

    # Knowledge domains by advisory mode
    MODE_DOMAINS = {
        AdvisoryMode.GENERAL: [
            "family_office",
            "professional_roles",
            "certifications",
            "financial_advisors",
            "financial_literacy",
        ],
        AdvisoryMode.ESTATE_PLANNING: [
            "estate_planning",
            "trust_administration",
            "generational_wealth",
            "professional_roles",
        ],
        AdvisoryMode.INVESTMENT_ADVISORY: [
            "financial_advisors",
            "governance",
            "certifications",
        ],
        AdvisoryMode.TAX_OPTIMIZATION: [
            "estate_planning",
            "succession_planning",
            "compliance_operations",
        ],
        AdvisoryMode.SUCCESSION_PLANNING: [
            "succession_planning",
            "professional_roles",
            "family_office",
        ],
        AdvisoryMode.FAMILY_GOVERNANCE: [
            "governance",
            "family_office",
            "generational_wealth",
        ],
        AdvisoryMode.TRUST_ADMINISTRATION: [
            "trust_administration",
            "estate_planning",
            "professional_roles",
        ],
        AdvisoryMode.CREDIT_FINANCING: ["credit_financing", "treasury_banking"],
        AdvisoryMode.COMPLIANCE_OPERATIONS: ["compliance_operations", "governance"],
        AdvisoryMode.FINANCIAL_LITERACY: ["financial_literacy"],
    }

    # Binding authorities by mode (roles with BINDING decision authority)
    MODE_BINDING_AUTHORITIES = {
        AdvisoryMode.TAX_OPTIMIZATION: ["TAX_MANAGER", "CPA"],
        AdvisoryMode.TRUST_ADMINISTRATION: [
            "TRUSTEE",
            "TRUST_PROTECTOR",
            "GENERAL_COUNSEL",
        ],
        AdvisoryMode.COMPLIANCE_OPERATIONS: ["CCO", "GENERAL_COUNSEL"],
        AdvisoryMode.ESTATE_PLANNING: ["GENERAL_COUNSEL"],
        AdvisoryMode.SUCCESSION_PLANNING: ["TAX_MANAGER", "GENERAL_COUNSEL"],
    }

    def __init__(self):
        """Initialize the query router."""
        logger.info("QueryRouter initialized")

    def determine_service_tier(self, profile: UserProfile) -> ServiceTier:
        """
        Determine service tier based on user profile.

        Democratized tiers aligned with $66,622 US average salary:
        - Foundation: $0-10K
        - Builder: $10K-75K
        - Growth: $75K-500K
        - Affluent: $500K-5M
        - HNW/UHNW: $5M+

        Args:
            profile: User profile with AUM and other factors

        Returns:
            Appropriate service tier
        """
        aum = profile.aum

        if aum >= 5_000_000:
            return ServiceTier.HNW_UHNW
        elif aum >= 500_000:
            return ServiceTier.AFFLUENT
        elif aum >= 75_000:
            return ServiceTier.GROWTH
        elif aum >= 10_000:
            return ServiceTier.BUILDER
        else:
            return ServiceTier.FOUNDATION

    def classify_advisory_mode(self, query: str) -> tuple[AdvisoryMode, float]:
        """
        Classify the query into an advisory mode.

        Args:
            query: User's query text

        Returns:
            Tuple of (AdvisoryMode, confidence score)
        """
        query_lower = query.lower()
        mode_scores = {}

        for mode, keywords in self.MODE_KEYWORDS.items():
            score = 0
            matches = 0
            for keyword in keywords:
                if keyword in query_lower:
                    matches += 1
                    # Boost for exact phrase matches
                    if f" {keyword} " in f" {query_lower} ":
                        score += 2
                    else:
                        score += 1

            if matches > 0:
                mode_scores[mode] = score / len(keywords) * min(matches, 5)

        if not mode_scores:
            return AdvisoryMode.GENERAL, 0.3

        best_mode = max(mode_scores, key=mode_scores.get)
        best_score = mode_scores[best_mode]

        # Normalize confidence to 0-1 range
        confidence = min(best_score / 2.0, 1.0)

        return best_mode, confidence

    def identify_required_roles(
        self, mode: AdvisoryMode, tier: ServiceTier, query: str
    ) -> list[str]:
        """
        Identify professional roles required for the query.

        Args:
            mode: Classified advisory mode
            tier: User's service tier
            query: Original query text

        Returns:
            List of required professional roles
        """
        # Base roles from tier
        roles = list(self.TIER_ROLES.get(tier, []))

        # Add mode-specific roles
        query_lower = query.lower()

        # Estate planning specific
        if mode == AdvisoryMode.ESTATE_PLANNING:
            if "trust" in query_lower:
                if "Trust Administration Attorney" not in roles:
                    roles.append("Trust Administration Attorney")
            if "international" in query_lower or "foreign" in query_lower:
                roles.append("International Tax Attorney")

        # Succession planning specific
        if mode == AdvisoryMode.SUCCESSION_PLANNING:
            roles.append("Business Valuation Expert")
            roles.append("M&A Attorney")

        # Trust administration specific
        if mode == AdvisoryMode.TRUST_ADMINISTRATION:
            if tier in [ServiceTier.HNW_UHNW, ServiceTier.AFFLUENT]:
                if "Trust Protector" not in roles:
                    roles.append("Trust Protector")

        # Family governance specific
        if mode == AdvisoryMode.FAMILY_GOVERNANCE:
            roles.append("Family Enterprise Advisor")

        return list(set(roles))  # Remove duplicates

    def requires_compliance_check(self, mode: AdvisoryMode, query: str) -> bool:
        """
        Determine if the query requires compliance rule checks.

        Args:
            mode: Classified advisory mode
            query: Original query text

        Returns:
            True if compliance check is required
        """
        # Always check compliance for these modes
        compliance_modes = {
            AdvisoryMode.TAX_OPTIMIZATION,
            AdvisoryMode.TRUST_ADMINISTRATION,
            AdvisoryMode.COMPLIANCE_OPERATIONS,
            AdvisoryMode.ESTATE_PLANNING,
            AdvisoryMode.SUCCESSION_PLANNING,
        }

        if mode in compliance_modes:
            return True

        # Check for compliance-related keywords
        compliance_keywords = [
            "tax",
            "irs",
            "filing",
            "report",
            "compliance",
            "aml",
            "kyc",
            "fiduciary",
            "beneficiary",
            "distribution",
            "gift",
            "estate",
            "trust",
            "form",
            "deadline",
        ]

        query_lower = query.lower()
        return any(kw in query_lower for kw in compliance_keywords)

    def get_binding_authorities(self, mode: AdvisoryMode) -> list[str]:
        """
        Get list of authorities with BINDING decision power for this mode.

        Args:
            mode: Advisory mode

        Returns:
            List of binding authority identifiers
        """
        return self.MODE_BINDING_AUTHORITIES.get(mode, [])

    def route_query(
        self, query: str, profile: Optional[UserProfile] = None
    ) -> RoutingResult:
        """
        Main routing method - classifies and routes a query.

        Args:
            query: User's query text
            profile: Optional user profile for tier determination

        Returns:
            RoutingResult with all routing information
        """
        # Use default profile if not provided
        if profile is None:
            profile = UserProfile()

        # Determine service tier
        tier = self.determine_service_tier(profile)

        # Classify advisory mode
        mode, confidence = self.classify_advisory_mode(query)

        # Get knowledge domains
        domains = self.MODE_DOMAINS.get(mode, self.MODE_DOMAINS[AdvisoryMode.GENERAL])

        # Identify required roles
        roles = self.identify_required_roles(mode, tier, query)

        # Check if compliance rules apply
        needs_compliance = self.requires_compliance_check(mode, query)

        # Get binding authorities
        binding = self.get_binding_authorities(mode)

        # Generate reasoning
        reasoning = self._generate_reasoning(query, mode, tier, confidence)

        result = RoutingResult(
            advisory_mode=mode,
            service_tier=tier,
            confidence=confidence,
            required_roles=roles,
            knowledge_domains=domains,
            requires_compliance_check=needs_compliance,
            binding_authorities=binding,
            reasoning=reasoning,
        )

        logger.info(
            f"Query routed: mode={mode.value}, tier={tier.value}, "
            f"confidence={confidence:.2f}, compliance={needs_compliance}"
        )

        return result

    def _generate_reasoning(
        self, query: str, mode: AdvisoryMode, tier: ServiceTier, confidence: float
    ) -> str:
        """Generate human-readable reasoning for the routing decision."""
        parts = []

        parts.append(
            f"Query classified as {mode.value.replace('_', ' ')} (confidence: {confidence:.0%})."
        )

        if tier == ServiceTier.FOUNDATION:
            parts.append(
                "Service tier: Foundation ($0-10K) - Full CFP-level guidance available."
            )
        elif tier == ServiceTier.BUILDER:
            parts.append(
                "Service tier: Builder ($10K-75K) - CFP + CPA expertise engaged."
            )
        elif tier == ServiceTier.GROWTH:
            parts.append(
                "Service tier: Growth ($75K-500K) - CFA investment expertise added."
            )
        elif tier == ServiceTier.AFFLUENT:
            parts.append(
                "Service tier: Affluent ($500K-5M) - Full advisory team available."
            )
        else:
            parts.append(
                "Service tier: HNW/UHNW ($5M+) - Family office resources engaged."
            )

        return " ".join(parts)


# Singleton instance
_router: Optional[QueryRouter] = None


def get_query_router() -> QueryRouter:
    """Get or create the singleton query router."""
    global _router
    if _router is None:
        _router = QueryRouter()
    return _router
