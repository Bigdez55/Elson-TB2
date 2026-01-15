"""
Wealth Advisory Request/Response Schemas

Pydantic models for the wealth management advisory API endpoints.
Supports all wealth tiers from $0 to $1B+ with specialized advisory modes.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

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


class WealthTier(str, Enum):
    """
    Democratized service tiers aligned with US average salary ($66,622/year).

    Philosophy: Same quality advice for everyone - only complexity differs by tier.
    Financial literacy is the foundation of generational wealth.
    """
    FOUNDATION = "foundation"      # $0-10K - Full CFP access, financial literacy
    BUILDER = "builder"            # $10K-75K - Tax optimization, retirement accounts
    GROWTH = "growth"              # $75K-500K - Portfolio construction, CFA access
    AFFLUENT = "affluent"          # $500K-5M - Full team, trust structures
    HNW_UHNW = "hnw_uhnw"          # $5M+ - Family office, specialists


class CredentialType(str, Enum):
    """Professional certification types."""
    CFP = "CFP"  # Certified Financial Planner
    CFA = "CFA"  # Chartered Financial Analyst
    CPA = "CPA"  # Certified Public Accountant
    CPWA = "CPWA"  # Certified Private Wealth Advisor
    CHFC = "ChFC"  # Chartered Financial Consultant
    CIMA = "CIMA"  # Certified Investment Management Analyst
    CVA = "CVA"  # Certified Valuation Analyst
    ASA = "ASA"  # Accredited Senior Appraiser
    FEA = "FEA"  # Family Enterprise Advisor
    CLU = "CLU"  # Chartered Life Underwriter


class ProfessionalRoleType(str, Enum):
    """Professional role types in wealth management."""
    ESTATE_PLANNING_ATTORNEY = "estate_planning_attorney"
    PROBATE_ATTORNEY = "probate_attorney"
    TRUST_ATTORNEY = "trust_attorney"
    INTERNATIONAL_TAX_ATTORNEY = "international_tax_attorney"
    FINANCIAL_PLANNER = "financial_planner"
    INVESTMENT_ANALYST = "investment_analyst"
    TAX_ACCOUNTANT = "tax_accountant"
    WEALTH_MANAGER = "wealth_manager"
    VALUATION_EXPERT = "valuation_expert"
    INSURANCE_ADVISOR = "insurance_advisor"
    FAMILY_GOVERNANCE_OFFICER = "family_governance_officer"
    TRUSTEE = "trustee"
    TRUST_PROTECTOR = "trust_protector"


# =============================================================================
# BASE MODELS
# =============================================================================

class Citation(BaseModel):
    """Citation from the knowledge base."""
    source: str = Field(..., description="Source document or category")
    content: str = Field(..., description="Relevant excerpt")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score 0-1")


class ProfessionalRecommendation(BaseModel):
    """Recommended professional for a specific need."""
    role: str = Field(..., description="Professional role title")
    credentials: list[str] = Field(default_factory=list, description="Relevant credentials")
    responsibilities: list[str] = Field(default_factory=list, description="Key responsibilities")
    why_recommended: str = Field(..., description="Why this professional is recommended")
    priority: int = Field(default=1, ge=1, le=5, description="Priority level 1-5")


class ActionItem(BaseModel):
    """Recommended next step or action."""
    action: str = Field(..., description="The action to take")
    category: str = Field(..., description="Category of action")
    priority: str = Field(default="medium", description="Priority: high, medium, low")
    professional_needed: Optional[str] = Field(None, description="Professional to consult")


# =============================================================================
# REQUEST MODELS
# =============================================================================

class WealthAdvisoryRequest(BaseModel):
    """General wealth management advisory query request."""
    query: str = Field(..., min_length=5, max_length=2000, description="The advisory question")
    advisory_mode: AdvisoryMode = Field(
        default=AdvisoryMode.GENERAL,
        description="Advisory mode for specialized guidance"
    )
    wealth_tier: Optional[WealthTier] = Field(
        None,
        description="Client's wealth tier for context-appropriate advice"
    )
    include_citations: bool = Field(
        default=True,
        description="Include knowledge base citations"
    )
    include_professionals: bool = Field(
        default=True,
        description="Include professional recommendations"
    )
    family_context: Optional[dict[str, Any]] = Field(
        None,
        description="Additional family or situation context"
    )


class EstatePlanningRequest(BaseModel):
    """Estate planning specific advisory request."""
    situation: str = Field(..., min_length=10, description="Description of estate planning needs")
    estimated_estate_value: Optional[float] = Field(None, ge=0, description="Estimated estate value")
    family_members: Optional[int] = Field(None, ge=1, description="Number of family members")
    has_business: bool = Field(default=False, description="Whether client owns a business")
    charitable_intent: bool = Field(default=False, description="Charitable giving interest")
    state_of_residence: Optional[str] = Field(None, description="State for jurisdiction-specific advice")
    existing_documents: Optional[list[str]] = Field(
        None,
        description="List of existing estate documents"
    )


class SuccessionPlanningRequest(BaseModel):
    """Business succession planning request."""
    business_type: str = Field(..., description="Type of business")
    business_name: Optional[str] = Field(None, description="Business name")
    estimated_value: Optional[float] = Field(None, ge=0, description="Estimated business value")
    owner_age: Optional[int] = Field(None, ge=18, le=120, description="Business owner's age")
    years_until_exit: Optional[int] = Field(None, ge=0, description="Target years until exit")
    potential_successors: Optional[list[str]] = Field(
        None,
        description="Potential successor types (family, employee, external)"
    )
    exit_preferences: Optional[list[str]] = Field(
        None,
        description="Preferred exit options"
    )
    annual_revenue: Optional[float] = Field(None, ge=0, description="Annual revenue")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees")


class TeamCoordinationRequest(BaseModel):
    """Professional team coordination recommendations request."""
    situation_type: str = Field(
        ...,
        description="Type of situation requiring team coordination"
    )
    situation_details: str = Field(..., min_length=20, description="Details of the situation")
    wealth_tier: WealthTier = Field(..., description="Client's wealth tier")
    existing_advisors: Optional[list[str]] = Field(
        None,
        description="List of existing advisor types"
    )
    budget_constraints: Optional[str] = Field(
        None,
        description="Any budget constraints for advisory team"
    )


class FinancialLiteracyRequest(BaseModel):
    """Financial literacy educational content request."""
    topic: str = Field(..., description="Financial topic to learn about")
    current_knowledge_level: str = Field(
        default="beginner",
        description="Current knowledge level: beginner, intermediate, advanced"
    )
    specific_questions: Optional[list[str]] = Field(
        None,
        description="Specific questions about the topic"
    )
    current_financial_situation: Optional[str] = Field(
        None,
        description="Brief description of current financial situation"
    )
    learning_goals: Optional[list[str]] = Field(
        None,
        description="What the user wants to achieve"
    )


class CredentialInfoRequest(BaseModel):
    """Request for credential/certification information."""
    credential_type: CredentialType = Field(..., description="The credential to learn about")
    include_study_resources: bool = Field(
        default=True,
        description="Include study provider information"
    )
    include_career_path: bool = Field(
        default=True,
        description="Include career path information"
    )


class RoleInfoRequest(BaseModel):
    """Request for professional role information."""
    role_type: ProfessionalRoleType = Field(..., description="The professional role")
    wealth_tier_context: Optional[WealthTier] = Field(
        None,
        description="Wealth tier for context-specific information"
    )


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class WealthAdvisoryResponse(BaseModel):
    """General wealth management advisory response."""
    response: str = Field(..., description="The advisory response")
    advisory_mode: AdvisoryMode = Field(..., description="The advisory mode used")
    wealth_tier: Optional[WealthTier] = Field(None, description="The wealth tier context")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Knowledge base citations"
    )
    recommended_professionals: list[ProfessionalRecommendation] = Field(
        default_factory=list,
        description="Recommended professionals to consult"
    )
    next_steps: list[ActionItem] = Field(
        default_factory=list,
        description="Recommended next steps"
    )
    confidence: float = Field(
        default=0.85,
        ge=0,
        le=1,
        description="Confidence score 0-1"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class EstatePlanningResponse(BaseModel):
    """Estate planning advisory response."""
    summary: str = Field(..., description="Summary of recommendations")
    recommended_structures: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recommended trust and estate structures"
    )
    tax_strategies: list[str] = Field(
        default_factory=list,
        description="Tax minimization strategies"
    )
    document_checklist: list[str] = Field(
        default_factory=list,
        description="Required estate planning documents"
    )
    professional_team: list[ProfessionalRecommendation] = Field(
        default_factory=list,
        description="Professional team recommendations"
    )
    citations: list[Citation] = Field(default_factory=list)
    timeline_recommendation: Optional[str] = Field(None, description="Suggested timeline")


class SuccessionPlanningResponse(BaseModel):
    """Business succession planning response."""
    summary: str = Field(..., description="Succession planning summary")
    recommended_exit_options: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ranked exit options with pros/cons"
    )
    dream_team_structure: list[ProfessionalRecommendation] = Field(
        default_factory=list,
        description="Dream Team professional coordination"
    )
    valuation_considerations: list[str] = Field(
        default_factory=list,
        description="Business valuation factors"
    )
    tax_strategies: list[str] = Field(
        default_factory=list,
        description="Tax optimization strategies"
    )
    timeline_phases: list[dict[str, str]] = Field(
        default_factory=list,
        description="Succession timeline phases"
    )
    citations: list[Citation] = Field(default_factory=list)


class TeamCoordinationResponse(BaseModel):
    """Professional team coordination response."""
    recommended_team: list[ProfessionalRecommendation] = Field(
        default_factory=list,
        description="Recommended professional team"
    )
    coordination_framework: str = Field(
        ...,
        description="How the team should coordinate"
    )
    communication_protocol: str = Field(
        ...,
        description="Recommended communication approach"
    )
    quarterly_review_agenda: list[str] = Field(
        default_factory=list,
        description="Quarterly review meeting agenda items"
    )
    citations: list[Citation] = Field(default_factory=list)


class FinancialLiteracyResponse(BaseModel):
    """Financial literacy educational response."""
    topic: str = Field(..., description="The topic explained")
    explanation: str = Field(..., description="Clear explanation of the topic")
    key_concepts: list[str] = Field(
        default_factory=list,
        description="Key concepts to understand"
    )
    practical_steps: list[str] = Field(
        default_factory=list,
        description="Practical steps to take"
    )
    common_mistakes: list[str] = Field(
        default_factory=list,
        description="Common mistakes to avoid"
    )
    resources: list[str] = Field(
        default_factory=list,
        description="Additional learning resources"
    )
    next_topics: list[str] = Field(
        default_factory=list,
        description="Suggested next topics to learn"
    )
    citations: list[Citation] = Field(default_factory=list)


class CredentialInfoResponse(BaseModel):
    """Credential/certification information response."""
    credential_type: str = Field(..., description="The credential type")
    full_name: str = Field(..., description="Full name of the credential")
    issuing_organization: str = Field(..., description="Organization that issues credential")
    requirements: dict[str, Any] = Field(
        default_factory=dict,
        description="Requirements to obtain"
    )
    study_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Study hours, materials, costs"
    )
    study_providers: Optional[list[dict[str, Any]]] = Field(
        None,
        description="Study material providers"
    )
    career_applications: list[str] = Field(
        default_factory=list,
        description="Career applications"
    )
    related_credentials: list[str] = Field(
        default_factory=list,
        description="Related credentials"
    )
    citations: list[Citation] = Field(default_factory=list)


class RoleInfoResponse(BaseModel):
    """Professional role information response."""
    role_type: str = Field(..., description="The role type")
    title: str = Field(..., description="Role title")
    description: str = Field(..., description="Role description")
    typical_credentials: list[str] = Field(
        default_factory=list,
        description="Typical credentials held"
    )
    key_responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities"
    )
    reports_to: Optional[str] = Field(None, description="Typical reporting structure")
    works_with: list[str] = Field(
        default_factory=list,
        description="Other roles this professional works with"
    )
    when_to_engage: list[str] = Field(
        default_factory=list,
        description="Situations when to engage this professional"
    )
    citations: list[Citation] = Field(default_factory=list)


class KnowledgeBaseStatsResponse(BaseModel):
    """Knowledge base statistics response."""
    total_documents: int = Field(..., description="Total documents indexed")
    collection_name: str = Field(..., description="Vector collection name")
    embedding_model: str = Field(..., description="Embedding model used")
    categories: list[str] = Field(default_factory=list, description="Available categories")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
