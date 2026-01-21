"""
Mode Router for Elson Financial AI

Implements automatic depth switching with user override capability.
Every prompt is classified into: Mode, Task Type, Risk Level

This enables one model to serve both citizen-friendly (Goal A) and
institutional-depth (Goal B) use cases through routing, not mixing.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# ENUMS
# =============================================================================


class ResponseMode(str, Enum):
    """Response depth modes"""

    SIMPLE = "simple"  # Citizen-friendly, 2-6 sentences
    STANDARD = "standard"  # Balanced depth, typical use case
    DEEP_DIVE = "deep_dive"  # Institutional depth, full analysis


class TaskType(str, Enum):
    """Classification of financial tasks"""

    # Goal A - Citizen/Personal Finance
    BUDGETING = "budgeting"
    SAVINGS = "savings"
    DEBT_MANAGEMENT = "debt_management"
    RETIREMENT_BASIC = "retirement_basic"
    INSURANCE_BASICS = "insurance_basics"
    TAX_EDUCATION = "tax_education"
    GOAL_PLANNING = "goal_planning"

    # Goal B - Institutional/Advanced
    PORTFOLIO_CONSTRUCTION = "portfolio_construction"
    RISK_ANALYSIS = "risk_analysis"
    TAX_OPTIMIZATION = "tax_optimization"
    ESTATE_PLANNING = "estate_planning"
    COMPLIANCE_CHECK = "compliance_check"
    TRADE_ANALYSIS = "trade_analysis"
    SCENARIO_MODELING = "scenario_modeling"

    # Shared
    MARKET_DATA = "market_data"
    PRODUCT_EXPLANATION = "product_explanation"
    GENERAL_QUESTION = "general_question"


class RiskLevel(str, Enum):
    """Risk level of the request - determines required depth"""

    LOW = "low"  # General education, no action implications
    MEDIUM = "medium"  # Planning context, some action implications
    HIGH = "high"  # Specific advice context, significant implications
    CRITICAL = "critical"  # Tax, legal, compliance - requires maximum rigor


# =============================================================================
# CLASSIFICATION PATTERNS
# =============================================================================

# Keywords that indicate higher risk/depth requirements
HIGH_RISK_PATTERNS = [
    r"\b(should i|is it safe|recommend|best|optimal)\b.*\b(invest|buy|sell|trade)\b",
    r"\b(tax|irs|audit|compliance|legal|fiduciary)\b",
    r"\b(estate|inheritance|trust|beneficiary)\b",
    r"\b(margin|leverage|options|derivatives|short)\b",
    r"\b(specific|exact|precise)\s+(amount|number|calculation)\b",
    r"\b(guaranteed|certain|always|never)\b.*\b(return|profit|gain)\b",
]

MEDIUM_RISK_PATTERNS = [
    r"\b(plan|strategy|approach|method)\b.*\b(retire|save|invest)\b",
    r"\b(portfolio|allocation|diversif|rebalance)\b",
    r"\b(how much|when should|how long)\b.*\b(save|invest|retire)\b",
    r"\b(compare|versus|vs|better)\b.*\b(fund|etf|stock|bond)\b",
]

LOW_RISK_PATTERNS = [
    r"\b(what is|explain|define|meaning of)\b",
    r"\b(how does|how do)\b.*\b(work|function)\b",
    r"\b(example|instance|illustration)\b",
    r"\b(history|background|overview)\b",
]

# Task type classification patterns
TASK_PATTERNS: Dict[TaskType, List[str]] = {
    TaskType.BUDGETING: [
        r"\bbudget\b",
        r"\bspending\b",
        r"\bexpense\b",
        r"\b50.?30.?20\b",
        r"\btrack\b.*\b(money|spend)\b",
        r"\bmonthly\b.*\b(plan|limit)\b",
    ],
    TaskType.SAVINGS: [
        r"\b(save|saving|savings)\b",
        r"\bemergency fund\b",
        r"\bhigh.?yield\b",
        r"\bsinking fund\b",
    ],
    TaskType.DEBT_MANAGEMENT: [
        r"\bdebt\b",
        r"\bloan\b",
        r"\bcredit card\b",
        r"\bmortgage\b",
        r"\b(pay off|payoff|snowball|avalanche)\b",
    ],
    TaskType.RETIREMENT_BASIC: [
        r"\bretire\b",
        r"\b401k\b",
        r"\bira\b",
        r"\broth\b",
        r"\bpension\b",
        r"\bsocial security\b",
    ],
    TaskType.INSURANCE_BASICS: [
        r"\binsurance\b",
        r"\bpolicy\b",
        r"\bpremium\b",
        r"\bcoverage\b",
        r"\bdeductible\b",
        r"\bbeneficiary\b",
    ],
    TaskType.TAX_EDUCATION: [
        r"\btax\b",
        r"\birs\b",
        r"\bdeduction\b",
        r"\bcredit\b",
        r"\bwithholding\b",
        r"\bfiling\b",
    ],
    TaskType.PORTFOLIO_CONSTRUCTION: [
        r"\bportfolio\b",
        r"\ballocation\b",
        r"\bdiversif\b",
        r"\brebalance\b",
        r"\basset class\b",
    ],
    TaskType.RISK_ANALYSIS: [
        r"\brisk\b.*\b(assess|analyz|measur)\b",
        r"\bvolatility\b",
        r"\bsharpe\b",
        r"\bbeta\b",
        r"\bdrawdown\b",
        r"\bvar\b",
    ],
    TaskType.TAX_OPTIMIZATION: [
        r"\btax.?(loss|gain)\s*harvest\b",
        r"\btax.?efficient\b",
        r"\basset location\b",
        r"\btax.?advantaged\b",
    ],
    TaskType.ESTATE_PLANNING: [
        r"\bestate\b",
        r"\binheritance\b",
        r"\btrust\b",
        r"\bwill\b",
        r"\bprobate\b",
        r"\bbeneficiary\b.*\bdesignation\b",
    ],
    TaskType.COMPLIANCE_CHECK: [
        r"\bcompliance\b",
        r"\bregulation\b",
        r"\bfiduciary\b",
        r"\bsuitability\b",
        r"\bdisclosure\b",
    ],
    TaskType.TRADE_ANALYSIS: [
        r"\btrade\b",
        r"\bentry\b",
        r"\bexit\b",
        r"\bposition\b",
        r"\bstop.?loss\b",
        r"\btarget\b",
    ],
    TaskType.SCENARIO_MODELING: [
        r"\bscenario\b",
        r"\bwhat if\b",
        r"\bsimulat\b",
        r"\bproject\b",
        r"\bforecast\b",
    ],
    TaskType.MARKET_DATA: [
        r"\bprice\b",
        r"\bquote\b",
        r"\bcurrent\b.*\bmarket\b",
        r"\bpe ratio\b",
        r"\beps\b",
        r"\bdividend yield\b",
    ],
    TaskType.PRODUCT_EXPLANATION: [
        r"\b(what is|explain)\b.*\b(etf|fund|bond|stock|option)\b",
        r"\bhow does\b.*\b(work|function)\b",
    ],
}


# =============================================================================
# ROUTER CONTEXT
# =============================================================================


@dataclass
class UserContext:
    """User profile for routing decisions"""

    user_id: Optional[str] = None
    wealth_tier: str = "mass_market"  # mass_market, affluent, hnw, uhnw, institutional
    is_professional: bool = False
    preferred_mode: Optional[ResponseMode] = None  # User override
    risk_tolerance: str = "moderate"
    experience_level: str = "beginner"  # beginner, intermediate, advanced, expert


@dataclass
class RoutingDecision:
    """Output of the mode router"""

    mode: ResponseMode
    task_type: TaskType
    risk_level: RiskLevel
    confidence: float
    reasoning: str
    required_schemas: List[str] = field(default_factory=list)
    required_disclaimers: List[str] = field(default_factory=list)
    requires_tool_call: bool = False
    requires_retrieval: bool = False


# =============================================================================
# MODE ROUTER
# =============================================================================


class ModeRouter:
    """
    Routes prompts to appropriate response mode based on:
    1. Automatic classification of task type and risk level
    2. User context (wealth tier, experience, preferences)
    3. User override (Simple vs Deep Dive toggle)
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        self.high_risk_compiled = [
            re.compile(p, re.IGNORECASE) for p in HIGH_RISK_PATTERNS
        ]
        self.medium_risk_compiled = [
            re.compile(p, re.IGNORECASE) for p in MEDIUM_RISK_PATTERNS
        ]
        self.low_risk_compiled = [
            re.compile(p, re.IGNORECASE) for p in LOW_RISK_PATTERNS
        ]

        self.task_compiled: Dict[TaskType, List[re.Pattern]] = {}
        for task, patterns in TASK_PATTERNS.items():
            self.task_compiled[task] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def classify_task(self, prompt: str) -> Tuple[TaskType, float]:
        """Classify the task type of a prompt"""
        best_match = TaskType.GENERAL_QUESTION
        best_score = 0.0

        for task, patterns in self.task_compiled.items():
            matches = sum(1 for p in patterns if p.search(prompt))
            score = matches / len(patterns) if patterns else 0
            if score > best_score:
                best_score = score
                best_match = task

        # Minimum confidence threshold
        if best_score < 0.1:
            return TaskType.GENERAL_QUESTION, 0.5

        return best_match, min(best_score * 2, 1.0)  # Scale confidence

    def assess_risk(self, prompt: str, task_type: TaskType) -> RiskLevel:
        """Assess the risk level of a prompt"""
        # Check for high risk patterns
        high_matches = sum(1 for p in self.high_risk_compiled if p.search(prompt))
        if high_matches >= 2:
            return RiskLevel.CRITICAL
        if high_matches >= 1:
            return RiskLevel.HIGH

        # Check for medium risk patterns
        medium_matches = sum(1 for p in self.medium_risk_compiled if p.search(prompt))
        if medium_matches >= 2:
            return RiskLevel.HIGH
        if medium_matches >= 1:
            return RiskLevel.MEDIUM

        # Task-based risk defaults
        high_risk_tasks = {
            TaskType.TAX_OPTIMIZATION,
            TaskType.ESTATE_PLANNING,
            TaskType.COMPLIANCE_CHECK,
            TaskType.TRADE_ANALYSIS,
        }
        medium_risk_tasks = {
            TaskType.PORTFOLIO_CONSTRUCTION,
            TaskType.RISK_ANALYSIS,
            TaskType.SCENARIO_MODELING,
            TaskType.RETIREMENT_BASIC,
        }

        if task_type in high_risk_tasks:
            return RiskLevel.HIGH
        if task_type in medium_risk_tasks:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def determine_mode(
        self,
        risk_level: RiskLevel,
        task_type: TaskType,
        user_context: Optional[UserContext] = None,
    ) -> ResponseMode:
        """Determine response mode based on risk and context"""
        # User override takes precedence
        if user_context and user_context.preferred_mode:
            return user_context.preferred_mode

        # Critical risk always requires deep dive
        if risk_level == RiskLevel.CRITICAL:
            return ResponseMode.DEEP_DIVE

        # High risk defaults to deep dive unless simple context
        if risk_level == RiskLevel.HIGH:
            if user_context and user_context.experience_level == "beginner":
                return ResponseMode.STANDARD  # Don't overwhelm beginners
            return ResponseMode.DEEP_DIVE

        # Medium risk uses standard
        if risk_level == RiskLevel.MEDIUM:
            return ResponseMode.STANDARD

        # Low risk uses simple
        return ResponseMode.SIMPLE

    def get_required_schemas(
        self, task_type: TaskType, mode: ResponseMode
    ) -> List[str]:
        """Determine which JSON schemas are required for this task"""
        schemas = []

        if mode == ResponseMode.SIMPLE:
            return []  # Simple mode doesn't require structured output

        schema_mapping = {
            TaskType.BUDGETING: ["FinancialPlan"],
            TaskType.SAVINGS: ["FinancialPlan"],
            TaskType.GOAL_PLANNING: ["FinancialPlan"],
            TaskType.RETIREMENT_BASIC: ["FinancialPlan", "ScenarioAnalysis"],
            TaskType.PORTFOLIO_CONSTRUCTION: ["PortfolioPolicy"],
            TaskType.RISK_ANALYSIS: ["PortfolioPolicy", "ScenarioAnalysis"],
            TaskType.SCENARIO_MODELING: ["ScenarioAnalysis"],
            TaskType.TRADE_ANALYSIS: ["TradePlan"],
            TaskType.COMPLIANCE_CHECK: ["ComplianceCheck"],
            TaskType.TAX_OPTIMIZATION: ["ScenarioAnalysis", "ComplianceCheck"],
            TaskType.ESTATE_PLANNING: ["FinancialPlan", "ComplianceCheck"],
        }

        return schema_mapping.get(task_type, [])

    def get_required_disclaimers(
        self, task_type: TaskType, risk_level: RiskLevel
    ) -> List[str]:
        """Determine which disclaimers are required"""
        disclaimers = []

        # Universal disclaimer for financial content
        disclaimers.append("GENERAL_FINANCIAL")

        # Task-specific disclaimers
        if task_type in {TaskType.TAX_EDUCATION, TaskType.TAX_OPTIMIZATION}:
            disclaimers.append("TAX_PROFESSIONAL")

        if task_type in {TaskType.ESTATE_PLANNING}:
            disclaimers.append("LEGAL_PROFESSIONAL")

        if task_type in {TaskType.TRADE_ANALYSIS}:
            disclaimers.append("EDUCATIONAL_ONLY")

        if task_type in {TaskType.INSURANCE_BASICS}:
            disclaimers.append("INSURANCE_DISCLAIMER")

        # Risk-based disclaimers
        if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            disclaimers.append("PROFESSIONAL_ADVICE")

        return disclaimers

    def requires_tool_call(self, task_type: TaskType, prompt: str) -> bool:
        """Determine if the task requires calling external tools"""
        # Market data always requires tools
        if task_type == TaskType.MARKET_DATA:
            return True

        # Check for specific data requests
        tool_indicators = [
            r"\bcurrent\b.*\b(price|quote|rate)\b",
            r"\btoday\b.*\b(market|stock|fund)\b",
            r"\b(pe|p/e|eps|dividend)\b.*\bratio\b",
            r"\bfundamental\b.*\bdata\b",
        ]

        for pattern in tool_indicators:
            if re.search(pattern, prompt, re.IGNORECASE):
                return True

        return False

    def requires_retrieval(self, task_type: TaskType, risk_level: RiskLevel) -> bool:
        """Determine if retrieval is required for grounded answers"""
        # High risk tasks require retrieval for grounding
        if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            return True

        # Compliance and tax always need retrieval
        if task_type in {
            TaskType.COMPLIANCE_CHECK,
            TaskType.TAX_OPTIMIZATION,
            TaskType.TAX_EDUCATION,
            TaskType.ESTATE_PLANNING,
        }:
            return True

        return False

    def route(
        self, prompt: str, user_context: Optional[UserContext] = None
    ) -> RoutingDecision:
        """
        Main routing function - classifies prompt and returns routing decision.

        Args:
            prompt: The user's input prompt
            user_context: Optional user profile for personalization

        Returns:
            RoutingDecision with mode, task, risk, and requirements
        """
        # 1. Classify task type
        task_type, task_confidence = self.classify_task(prompt)

        # 2. Assess risk level
        risk_level = self.assess_risk(prompt, task_type)

        # 3. Determine response mode
        mode = self.determine_mode(risk_level, task_type, user_context)

        # 4. Get requirements
        required_schemas = self.get_required_schemas(task_type, mode)
        required_disclaimers = self.get_required_disclaimers(task_type, risk_level)
        requires_tool = self.requires_tool_call(task_type, prompt)
        requires_retrieval = self.requires_retrieval(task_type, risk_level)

        # 5. Build reasoning
        reasoning = self._build_reasoning(
            task_type, risk_level, mode, user_context, requires_tool, requires_retrieval
        )

        return RoutingDecision(
            mode=mode,
            task_type=task_type,
            risk_level=risk_level,
            confidence=task_confidence,
            reasoning=reasoning,
            required_schemas=required_schemas,
            required_disclaimers=required_disclaimers,
            requires_tool_call=requires_tool,
            requires_retrieval=requires_retrieval,
        )

    def _build_reasoning(
        self,
        task_type: TaskType,
        risk_level: RiskLevel,
        mode: ResponseMode,
        user_context: Optional[UserContext],
        requires_tool: bool,
        requires_retrieval: bool,
    ) -> str:
        """Build human-readable reasoning for the routing decision"""
        parts = []

        parts.append(f"Task classified as {task_type.value}")
        parts.append(f"Risk level: {risk_level.value}")

        if user_context and user_context.preferred_mode:
            parts.append(f"User override: {user_context.preferred_mode.value}")
        else:
            parts.append(f"Auto-selected mode: {mode.value}")

        if requires_tool:
            parts.append("Tool call required for live data")

        if requires_retrieval:
            parts.append("Retrieval required for grounded response")

        return "; ".join(parts)


# =============================================================================
# ANSWER CONTRACT
# =============================================================================


@dataclass
class AnswerContract:
    """
    Defines the structure of responses based on routing decision.

    Section 1: Plain English summary (2-6 sentences, citizen-friendly)
    Section 2: Professional detail (if risk >= medium or mode == deep_dive)
    Section 3: Next actions (checklist or JSON schema)
    Section 4: Compliance note (short, only when relevant)
    """

    mode: ResponseMode
    risk_level: RiskLevel

    # Section toggles
    include_summary: bool = True  # Always true
    include_detail: bool = False  # Based on mode/risk
    include_actions: bool = True  # Usually true
    include_compliance: bool = False  # Only when disclaimers needed

    # Output format
    output_schema: Optional[str] = None  # JSON schema to use
    max_summary_sentences: int = 6
    max_detail_paragraphs: int = 4

    @classmethod
    def from_routing(cls, decision: RoutingDecision) -> "AnswerContract":
        """Create answer contract from routing decision"""
        include_detail = (
            decision.mode == ResponseMode.DEEP_DIVE
            or decision.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
        )

        include_compliance = len(decision.required_disclaimers) > 0

        output_schema = (
            decision.required_schemas[0] if decision.required_schemas else None
        )

        # Adjust summary length based on mode
        if decision.mode == ResponseMode.SIMPLE:
            max_summary = 3
        elif decision.mode == ResponseMode.STANDARD:
            max_summary = 5
        else:
            max_summary = 6

        return cls(
            mode=decision.mode,
            risk_level=decision.risk_level,
            include_summary=True,
            include_detail=include_detail,
            include_actions=True,
            include_compliance=include_compliance,
            output_schema=output_schema,
            max_summary_sentences=max_summary,
        )

    def get_system_prompt_additions(self) -> str:
        """Generate system prompt additions based on contract"""
        parts = []

        # Mode-specific instructions
        if self.mode == ResponseMode.SIMPLE:
            parts.append(
                "Respond in plain English that a financial beginner would understand. "
                "Keep explanations to 2-4 sentences. Avoid jargon."
            )
        elif self.mode == ResponseMode.STANDARD:
            parts.append(
                "Provide a balanced response with clear explanations. "
                "Include relevant context but avoid overwhelming detail."
            )
        else:  # DEEP_DIVE
            parts.append(
                "Provide comprehensive institutional-depth analysis. "
                "Include assumptions, edge cases, calculations where relevant."
            )

        # Structure requirements
        parts.append("\nStructure your response with these sections:")
        parts.append("1. **Summary**: Brief plain-English overview")

        if self.include_detail:
            parts.append(
                "2. **Analysis**: Detailed examination with assumptions and constraints"
            )

        if self.include_actions:
            parts.append(f"3. **Next Steps**: Actionable checklist")

        if self.include_compliance:
            parts.append("4. **Important Notes**: Brief compliance/disclaimer notes")

        if self.output_schema:
            parts.append(
                f"\nProvide structured output using the {self.output_schema} schema."
            )

        return "\n".join(parts)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global router instance
_router: Optional[ModeRouter] = None


def get_router() -> ModeRouter:
    """Get or create the global router instance"""
    global _router
    if _router is None:
        _router = ModeRouter()
    return _router


def route_prompt(
    prompt: str, user_context: Optional[UserContext] = None
) -> RoutingDecision:
    """Convenience function to route a prompt"""
    return get_router().route(prompt, user_context)


def get_answer_contract(
    prompt: str, user_context: Optional[UserContext] = None
) -> AnswerContract:
    """Get the answer contract for a prompt"""
    decision = route_prompt(prompt, user_context)
    return AnswerContract.from_routing(decision)
