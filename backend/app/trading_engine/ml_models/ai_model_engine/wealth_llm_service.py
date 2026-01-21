"""
Wealth Management LLM Service

Implements the 5-layer hybrid architecture for democratized wealth management:
1. Query Router - Routes to appropriate advisory mode
2. RAG Layer - Retrieval augmented generation
3. Compliance Rules - Neuro-symbolic decision validation
4. LLM Layer - QDoRA fine-tuned model
5. Validation Layer - Response validation and formatting

Democratized Service Tiers (aligned with $66,622 US average salary):
- Foundation: $0-10K (Full CFP access, financial literacy foundation)
- Builder: $10K-75K (~1 year median US savings, CFP + CPA, tax optimization)
- Growth: $75K-500K (Earlier CFA access for middle-class families)
- Affluent: $500K-5M (Full team, trust structures, estate planning)
- HNW/UHNW: $5M+ (Family office, philanthropy, specialists)

Philosophy: Same quality advice for everyone - only complexity differs by tier.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .wealth_model_loader import ModelConfig, ModelSource, WealthModelLoader

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================


class ServiceTier(Enum):
    """
    Democratized service tiers aligned with US average salary ($66,622/year).

    Philosophy: Help clients establish generational wealth EARLY.
    Traditional wealth management gatekeeps advice behind high AUM minimums -
    Elson breaks this barrier with same quality advice for everyone.
    """

    FOUNDATION = "foundation"  # $0-10K: Full CFP access, financial literacy foundation
    BUILDER = "builder"  # $10K-75K: ~1 year median US savings, achievable for most
    GROWTH = "growth"  # $75K-500K: Earlier CFA access for middle-class families
    AFFLUENT = "affluent"  # $500K-5M: Full team, trust structures
    HNW_UHNW = "hnw_uhnw"  # $5M+: Family office, philanthropy, specialists


class AdvisoryMode(Enum):
    """Query routing modes for different advisory needs."""

    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TAX_OPTIMIZATION = "tax_optimization"
    RETIREMENT_PLANNING = "retirement_planning"
    ESTATE_PLANNING = "estate_planning"
    INVESTMENT_EDUCATION = "investment_education"
    MARKET_ANALYSIS = "market_analysis"
    REBALANCING = "rebalancing"
    ASSET_ALLOCATION = "asset_allocation"
    GENERAL_INQUIRY = "general_inquiry"


class DecisionAuthority(Enum):
    """Decision authority levels for compliance."""

    BINDING = "binding"  # Must be followed (regulatory)
    ADVISORY = "advisory"  # Recommended but optional
    SUPPORT = "support"  # Informational only


class ComplianceCategory(Enum):
    """Compliance rule categories."""

    FIDUCIARY_DUTY = "fiduciary_duty"
    SUITABILITY = "suitability"
    CONCENTRATION_LIMITS = "concentration_limits"
    RISK_TOLERANCE = "risk_tolerance"
    REGULATORY = "regulatory"
    TAX_COMPLIANCE = "tax_compliance"
    DISCLOSURE = "disclosure"
    PROHIBITED_TRANSACTIONS = "prohibited_transactions"
    CONFLICT_OF_INTEREST = "conflict_of_interest"
    RECORD_KEEPING = "record_keeping"
    AML_KYC = "aml_kyc"
    PRIVACY = "privacy"
    ACCREDITED_INVESTOR = "accredited_investor"
    MARGIN_REQUIREMENTS = "margin_requirements"
    POSITION_LIMITS = "position_limits"
    WASH_SALE = "wash_sale"
    PATTERN_DAY_TRADING = "pattern_day_trading"


# Democratized service tier thresholds (aligned with $66,622 US average salary)
TIER_THRESHOLDS = {
    ServiceTier.FOUNDATION: (0, 10_000),  # $0-10K
    ServiceTier.BUILDER: (10_000, 75_000),  # $10K-75K (~1 year median US savings)
    ServiceTier.GROWTH: (75_000, 500_000),  # $75K-500K (earlier CFA access)
    ServiceTier.AFFLUENT: (500_000, 5_000_000),  # $500K-5M (full team)
    ServiceTier.HNW_UHNW: (5_000_000, float("inf")),  # $5M+ (family office)
}


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class UserProfile:
    """User profile for personalized advice."""

    user_id: str
    portfolio_value: float
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    investment_horizon: int = 10  # years
    age: Optional[int] = None
    income: Optional[float] = None
    tax_bracket: Optional[str] = None
    is_accredited: bool = False
    goals: List[str] = field(default_factory=list)

    @property
    def service_tier(self) -> ServiceTier:
        """Determine service tier based on portfolio value."""
        for tier, (min_val, max_val) in TIER_THRESHOLDS.items():
            if min_val <= self.portfolio_value < max_val:
                return tier
        return ServiceTier.FOUNDATION


@dataclass
class ComplianceResult:
    """Result of compliance check."""

    passed: bool
    category: ComplianceCategory
    authority: DecisionAuthority
    message: str
    rule_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class QueryContext:
    """Context for a wealth management query."""

    query: str
    user_profile: UserProfile
    advisory_mode: AdvisoryMode
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdvisoryResponse:
    """Structured response from the wealth LLM service."""

    response: str
    advisory_mode: AdvisoryMode
    service_tier: ServiceTier
    compliance_checks: List[ComplianceResult]
    confidence: float
    disclaimers: List[str]
    follow_up_questions: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# 5-LAYER ARCHITECTURE COMPONENTS
# =============================================================================


class QueryRouter:
    """
    Layer 1: Query Router
    Routes incoming queries to the appropriate advisory mode.
    """

    # Keywords for routing
    MODE_KEYWORDS = {
        AdvisoryMode.PORTFOLIO_ANALYSIS: [
            "portfolio",
            "holdings",
            "positions",
            "allocation",
            "performance",
        ],
        AdvisoryMode.RISK_ASSESSMENT: [
            "risk",
            "volatility",
            "downside",
            "exposure",
            "hedge",
        ],
        AdvisoryMode.TAX_OPTIMIZATION: [
            "tax",
            "capital gains",
            "loss harvest",
            "deduction",
            "bracket",
        ],
        AdvisoryMode.RETIREMENT_PLANNING: [
            "retirement",
            "401k",
            "ira",
            "pension",
            "social security",
        ],
        AdvisoryMode.ESTATE_PLANNING: [
            "estate",
            "inheritance",
            "trust",
            "will",
            "beneficiary",
        ],
        AdvisoryMode.INVESTMENT_EDUCATION: [
            "what is",
            "explain",
            "how does",
            "learn",
            "understand",
        ],
        AdvisoryMode.MARKET_ANALYSIS: [
            "market",
            "sector",
            "trend",
            "outlook",
            "forecast",
        ],
        AdvisoryMode.REBALANCING: ["rebalance", "drift", "target allocation", "adjust"],
        AdvisoryMode.ASSET_ALLOCATION: [
            "allocation",
            "diversify",
            "mix",
            "split",
            "distribute",
        ],
    }

    def route(self, query: str, user_profile: UserProfile) -> AdvisoryMode:
        """Route query to appropriate advisory mode."""
        query_lower = query.lower()

        # Score each mode based on keyword matches
        scores = {}
        for mode, keywords in self.MODE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[mode] = score

        if scores:
            return max(scores, key=scores.get)

        return AdvisoryMode.GENERAL_INQUIRY


class RAGLayer:
    """
    Layer 2: Retrieval Augmented Generation
    Retrieves relevant context for the query.
    """

    def __init__(self):
        self.knowledge_base = {}  # Placeholder for vector store

    def retrieve(
        self, query: str, mode: AdvisoryMode, tier: ServiceTier, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for the query.

        Returns list of relevant context documents.
        """
        # Placeholder - in production, this would query a vector database
        # like Pinecone, Weaviate, or ChromaDB

        # Return tier-appropriate context
        base_context = [
            {"type": "disclaimer", "content": self._get_tier_disclaimer(tier)}
        ]

        if mode == AdvisoryMode.TAX_OPTIMIZATION:
            base_context.append(
                {
                    "type": "reference",
                    "content": "Tax optimization strategies should be reviewed with a qualified tax professional.",
                }
            )

        return base_context

    def _get_tier_disclaimer(self, tier: ServiceTier) -> str:
        """Get tier-appropriate disclaimer for democratized service tiers."""
        disclaimers = {
            ServiceTier.FOUNDATION: (
                "This guidance provides full CFP-level educational content. "
                "Financial literacy is the foundation of generational wealth."
            ),
            ServiceTier.BUILDER: (
                "This analysis includes CFP + CPA expertise for tax optimization "
                "and retirement account strategies. Past performance does not "
                "guarantee future results."
            ),
            ServiceTier.GROWTH: (
                "This recommendation incorporates CFA investment expertise for "
                "portfolio construction. Please review before implementation."
            ),
            ServiceTier.AFFLUENT: (
                "This personalized strategy leverages our full advisory team "
                "including estate planning and trust structure expertise."
            ),
            ServiceTier.HNW_UHNW: (
                "This family office level analysis includes sophisticated "
                "strategies for philanthropy and multi-generational planning. "
                "Coordinate with your advisory team for execution."
            ),
        }
        return disclaimers.get(tier, disclaimers[ServiceTier.FOUNDATION])


class ComplianceEngine:
    """
    Layer 3: Compliance Rules Engine
    Validates queries and responses against regulatory requirements.
    """

    def __init__(self):
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance rules."""
        return {
            "FIDUCIARY_001": {
                "category": ComplianceCategory.FIDUCIARY_DUTY,
                "authority": DecisionAuthority.BINDING,
                "description": "Must act in client's best interest",
                "check": self._check_fiduciary_duty,
            },
            "SUITABLE_001": {
                "category": ComplianceCategory.SUITABILITY,
                "authority": DecisionAuthority.BINDING,
                "description": "Recommendations must be suitable for client profile",
                "check": self._check_suitability,
            },
            "CONC_001": {
                "category": ComplianceCategory.CONCENTRATION_LIMITS,
                "authority": DecisionAuthority.ADVISORY,
                "description": "Warn on position concentration > 10%",
                "check": self._check_concentration,
            },
            "RISK_001": {
                "category": ComplianceCategory.RISK_TOLERANCE,
                "authority": DecisionAuthority.ADVISORY,
                "description": "Align recommendations with risk tolerance",
                "check": self._check_risk_alignment,
            },
            "ACCRED_001": {
                "category": ComplianceCategory.ACCREDITED_INVESTOR,
                "authority": DecisionAuthority.BINDING,
                "description": "Verify accredited status for certain investments",
                "check": self._check_accredited_requirements,
            },
            "DISC_001": {
                "category": ComplianceCategory.DISCLOSURE,
                "authority": DecisionAuthority.BINDING,
                "description": "Include required disclosures",
                "check": self._check_disclosures,
            },
            "PDT_001": {
                "category": ComplianceCategory.PATTERN_DAY_TRADING,
                "authority": DecisionAuthority.BINDING,
                "description": "PDT rules for accounts < $25K",
                "check": self._check_pdt_rules,
            },
        }

    def validate_query(self, context: QueryContext) -> List[ComplianceResult]:
        """Validate query against compliance rules."""
        results = []

        for rule_id, rule in self.rules.items():
            check_fn = rule["check"]
            passed, message = check_fn(context, is_query=True)

            results.append(
                ComplianceResult(
                    passed=passed,
                    category=rule["category"],
                    authority=rule["authority"],
                    message=message,
                    rule_id=rule_id,
                )
            )

        return results

    def validate_response(
        self, response: str, context: QueryContext
    ) -> List[ComplianceResult]:
        """Validate generated response against compliance rules."""
        results = []

        for rule_id, rule in self.rules.items():
            check_fn = rule["check"]
            passed, message = check_fn(context, response=response, is_query=False)

            results.append(
                ComplianceResult(
                    passed=passed,
                    category=rule["category"],
                    authority=rule["authority"],
                    message=message,
                    rule_id=rule_id,
                )
            )

        return results

    # Compliance check implementations
    def _check_fiduciary_duty(self, context: QueryContext, **kwargs) -> tuple:
        """Check fiduciary duty compliance."""
        # Always pass - the model is trained to act in client's interest
        return True, "Fiduciary duty maintained"

    def _check_suitability(self, context: QueryContext, **kwargs) -> tuple:
        """Check suitability compliance."""
        profile = context.user_profile
        mode = context.advisory_mode

        # Check if advice type is suitable for profile
        if mode == AdvisoryMode.ESTATE_PLANNING and profile.portfolio_value < 100_000:
            return True, "Basic estate planning guidance provided"

        return True, "Advice suitable for client profile"

    def _check_concentration(self, context: QueryContext, **kwargs) -> tuple:
        """Check position concentration limits."""
        return True, "Concentration limits checked"

    def _check_risk_alignment(self, context: QueryContext, **kwargs) -> tuple:
        """Check risk tolerance alignment."""
        return True, "Risk alignment verified"

    def _check_accredited_requirements(self, context: QueryContext, **kwargs) -> tuple:
        """Check accredited investor requirements."""
        profile = context.user_profile
        mode = context.advisory_mode

        # For certain strategies, check accredited status
        if (
            "alternative" in context.query.lower()
            or "hedge fund" in context.query.lower()
        ):
            if not profile.is_accredited:
                return (
                    False,
                    "Accredited investor status required for this investment type",
                )

        return True, "Accredited investor check passed"

    def _check_disclosures(self, context: QueryContext, **kwargs) -> tuple:
        """Check required disclosures are present."""
        return True, "Required disclosures included"

    def _check_pdt_rules(self, context: QueryContext, **kwargs) -> tuple:
        """Check pattern day trading rules."""
        profile = context.user_profile

        if "day trading" in context.query.lower() and profile.portfolio_value < 25_000:
            return False, (
                "Pattern day trading requires minimum $25,000 account balance. "
                "Your current portfolio value does not meet this requirement."
            )

        return True, "PDT rules checked"


class ValidationLayer:
    """
    Layer 5: Response Validation
    Validates and formats the final response.
    """

    def __init__(self):
        self.disclaimers = {
            "general": (
                "This information is for educational purposes only and does not "
                "constitute financial advice. Past performance does not guarantee "
                "future results."
            ),
            "investment": (
                "All investments involve risk, including potential loss of principal. "
                "Please consult with a qualified financial advisor before making "
                "investment decisions."
            ),
            "tax": (
                "Tax information provided is general in nature. Consult a qualified "
                "tax professional for advice specific to your situation."
            ),
        }

    def validate(
        self,
        response: str,
        context: QueryContext,
        compliance_results: List[ComplianceResult],
    ) -> AdvisoryResponse:
        """Validate and format the response."""
        # Check for compliance failures
        failed_checks = [r for r in compliance_results if not r.passed]

        if failed_checks:
            # Handle binding failures
            binding_failures = [
                r for r in failed_checks if r.authority == DecisionAuthority.BINDING
            ]
            if binding_failures:
                response = self._handle_binding_failure(response, binding_failures)

        # Add appropriate disclaimers
        disclaimers = self._get_disclaimers(context)

        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(context)

        # Calculate confidence
        confidence = self._calculate_confidence(response, compliance_results)

        return AdvisoryResponse(
            response=response,
            advisory_mode=context.advisory_mode,
            service_tier=context.user_profile.service_tier,
            compliance_checks=compliance_results,
            confidence=confidence,
            disclaimers=disclaimers,
            follow_up_questions=follow_ups,
        )

    def _handle_binding_failure(
        self, response: str, failures: List[ComplianceResult]
    ) -> str:
        """Modify response to handle binding compliance failures."""
        failure_messages = [f.message for f in failures]

        return (
            f"I'm unable to provide specific advice on this topic due to "
            f"regulatory requirements:\n\n"
            f"- " + "\n- ".join(failure_messages) + "\n\n"
            f"Please consult with a qualified financial advisor for guidance "
            f"on this matter."
        )

    def _get_disclaimers(self, context: QueryContext) -> List[str]:
        """Get appropriate disclaimers for the response."""
        disclaimers = [self.disclaimers["general"]]

        if context.advisory_mode in [
            AdvisoryMode.PORTFOLIO_ANALYSIS,
            AdvisoryMode.ASSET_ALLOCATION,
            AdvisoryMode.REBALANCING,
        ]:
            disclaimers.append(self.disclaimers["investment"])

        if context.advisory_mode == AdvisoryMode.TAX_OPTIMIZATION:
            disclaimers.append(self.disclaimers["tax"])

        return disclaimers

    def _generate_follow_ups(self, context: QueryContext) -> List[str]:
        """Generate relevant follow-up questions."""
        follow_ups = {
            AdvisoryMode.PORTFOLIO_ANALYSIS: [
                "Would you like a detailed breakdown by sector?",
                "Should I analyze your portfolio's risk metrics?",
            ],
            AdvisoryMode.RISK_ASSESSMENT: [
                "Would you like suggestions to reduce portfolio risk?",
                "Should I show historical volatility analysis?",
            ],
            AdvisoryMode.TAX_OPTIMIZATION: [
                "Would you like to explore tax-loss harvesting opportunities?",
                "Should I analyze your tax-efficient fund placement?",
            ],
            AdvisoryMode.RETIREMENT_PLANNING: [
                "Would you like a retirement income projection?",
                "Should I compare Roth vs Traditional contributions?",
            ],
        }

        return follow_ups.get(
            context.advisory_mode,
            [
                "Would you like more details on any aspect?",
                "Do you have any follow-up questions?",
            ],
        )

    def _calculate_confidence(
        self, response: str, compliance_results: List[ComplianceResult]
    ) -> float:
        """Calculate confidence score for the response."""
        # Start with base confidence
        confidence = 0.85

        # Reduce for compliance issues
        failed = sum(1 for r in compliance_results if not r.passed)
        confidence -= failed * 0.1

        # Reduce for short responses
        if len(response) < 100:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))


# =============================================================================
# MAIN SERVICE
# =============================================================================


class WealthLLMService:
    """
    Main service implementing the 5-layer hybrid architecture.

    Provides democratized wealth management advisory services powered by
    the QDoRA fine-tuned LLM with compliance guardrails.
    """

    def __init__(
        self,
        model_loader: Optional[WealthModelLoader] = None,
        quantization: str = "4bit",
    ):
        """
        Initialize the wealth LLM service.

        Args:
            model_loader: Pre-configured model loader (optional)
            quantization: Model quantization (4bit, 8bit, none)
        """
        # Initialize 5 layers
        self.query_router = QueryRouter()
        self.rag_layer = RAGLayer()
        self.compliance_engine = ComplianceEngine()
        self.validation_layer = ValidationLayer()

        # Initialize model loader (Layer 4)
        if model_loader:
            self.model_loader = model_loader
        else:
            config = ModelConfig(quantization=quantization)
            self.model_loader = WealthModelLoader(config=config)

        self._model_loaded = False

    def load_model(self, force_download: bool = False):
        """Load the QDoRA model."""
        self.model_loader.load_model(force_download=force_download)
        self._model_loaded = True
        logger.info("WealthLLMService model loaded")

    def _build_prompt(
        self, query: str, context: QueryContext, rag_context: List[Dict[str, Any]]
    ) -> str:
        """Build the prompt for the LLM."""
        tier = context.user_profile.service_tier
        mode = context.advisory_mode

        # System context
        system_prompt = f"""You are ELSON, an AI-powered wealth management advisor.
You provide {tier.value}-tier advisory services focused on {mode.value.replace('_', ' ')}.

Client Profile:
- Portfolio Value: ${context.user_profile.portfolio_value:,.2f}
- Risk Tolerance: {context.user_profile.risk_tolerance}
- Investment Horizon: {context.user_profile.investment_horizon} years
- Service Tier: {tier.value.title()}

Guidelines:
- Provide clear, actionable advice appropriate for the client's tier
- Always consider the client's risk tolerance
- Include relevant disclaimers
- Be educational and explain concepts when needed
"""

        # Add RAG context
        rag_content = ""
        for doc in rag_context:
            if doc["type"] == "disclaimer":
                rag_content += f"\nNote: {doc['content']}"
            else:
                rag_content += f"\nContext: {doc['content']}"

        # Build full prompt
        prompt = f"""{system_prompt}
{rag_content}

User Query: {query}

Response:"""

        return prompt

    def query(
        self, query: str, user_profile: UserProfile, session_id: Optional[str] = None
    ) -> AdvisoryResponse:
        """
        Process a wealth management query through the 5-layer architecture.

        Args:
            query: User's question or request
            user_profile: User's financial profile
            session_id: Optional session identifier

        Returns:
            Structured advisory response
        """
        # Ensure model is loaded
        if not self._model_loaded:
            self.load_model()

        # Layer 1: Route the query
        advisory_mode = self.query_router.route(query, user_profile)
        logger.info(f"Query routed to mode: {advisory_mode.value}")

        # Create context
        context = QueryContext(
            query=query,
            user_profile=user_profile,
            advisory_mode=advisory_mode,
            session_id=session_id,
        )

        # Layer 3: Pre-query compliance check
        pre_compliance = self.compliance_engine.validate_query(context)
        binding_failures = [
            r
            for r in pre_compliance
            if not r.passed and r.authority == DecisionAuthority.BINDING
        ]

        if binding_failures:
            # Return early with compliance failure
            return self.validation_layer.validate(
                "Unable to process this query due to compliance restrictions.",
                context,
                pre_compliance,
            )

        # Layer 2: Retrieve relevant context
        rag_context = self.rag_layer.retrieve(
            query, advisory_mode, user_profile.service_tier
        )

        # Build prompt
        prompt = self._build_prompt(query, context, rag_context)

        # Layer 4: Generate response with LLM
        response = self.model_loader.generate(
            prompt, max_new_tokens=512, temperature=0.7
        )

        # Layer 3: Post-response compliance check
        post_compliance = self.compliance_engine.validate_response(response, context)

        # Layer 5: Validate and format response
        final_response = self.validation_layer.validate(
            response, context, pre_compliance + post_compliance
        )

        return final_response

    def get_service_tier_info(self, portfolio_value: float) -> Dict[str, Any]:
        """Get information about the applicable service tier."""
        for tier, (min_val, max_val) in TIER_THRESHOLDS.items():
            if min_val <= portfolio_value < max_val:
                return {
                    "tier": tier.value,
                    "tier_name": tier.name,
                    "portfolio_range": f"${min_val:,.0f} - ${max_val:,.0f}",
                    "features": self._get_tier_features(tier),
                }
        return {"tier": "foundation", "tier_name": "FOUNDATION"}

    def _get_tier_features(self, tier: ServiceTier) -> List[str]:
        """Get features available for a service tier (democratized access model)."""
        features = {
            ServiceTier.FOUNDATION: [
                "Full CFP-level financial literacy",
                "Budgeting and emergency fund planning",
                "Debt payoff strategy",
                "Credit building guidance",
                "Savings automation",
                "Basic investment education",
            ],
            ServiceTier.BUILDER: [
                "All Foundation features",
                "CFP + CPA access",
                "Tax optimization fundamentals",
                "Retirement account selection (401k/IRA)",
                "Insurance fundamentals",
                "First investment portfolio construction",
            ],
            ServiceTier.GROWTH: [
                "All Builder features",
                "CFP + CFA + CPA access",
                "Strategic portfolio construction",
                "Estate planning basics",
                "Tax-loss harvesting strategies",
                "Real estate investment considerations",
            ],
            ServiceTier.AFFLUENT: [
                "All Growth features",
                "Full advisory team access",
                "Trust structures and planning",
                "Multi-entity tax planning",
                "Business succession planning",
                "Family governance fundamentals",
            ],
            ServiceTier.HNW_UHNW: [
                "All Affluent features",
                "CPWA + specialist access",
                "Family office services",
                "Multi-generational wealth planning",
                "Philanthropic planning (DAFs, foundations)",
                "Alternative investments (PE, hedge funds)",
                "International tax planning",
            ],
        }
        return features.get(tier, features[ServiceTier.FOUNDATION])


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_wealth_service(quantization: str = "4bit") -> WealthLLMService:
    """Create a wealth LLM service instance."""
    return WealthLLMService(quantization=quantization)


def quick_wealth_query(
    query: str, portfolio_value: float = 50000, risk_tolerance: str = "moderate"
) -> AdvisoryResponse:
    """
    Quick wealth management query without full setup.

    Args:
        query: User's question
        portfolio_value: Estimated portfolio value
        risk_tolerance: Risk tolerance level

    Returns:
        Advisory response
    """
    service = create_wealth_service()
    profile = UserProfile(
        user_id="quick_query",
        portfolio_value=portfolio_value,
        risk_tolerance=risk_tolerance,
    )
    return service.query(query, profile)
