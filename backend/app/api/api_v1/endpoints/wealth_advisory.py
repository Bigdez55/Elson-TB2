"""
Wealth Advisory API Endpoints

Comprehensive wealth management advisory endpoints supporting all wealth tiers
from $0 to $1B+ with specialized advisory modes and knowledge retrieval.

Endpoints:
- POST /advisory/query - General wealth management advisory
- POST /advisory/estate-planning - Estate planning guidance
- POST /advisory/succession - Business succession planning
- POST /advisory/team-coordination - Professional team recommendations
- POST /advisory/financial-literacy - Financial education content
- GET /knowledge/roles/{role_type} - Professional role information
- GET /knowledge/certifications/{cert_type} - Certification information
- GET /knowledge/stats - Knowledge base statistics
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.wealth_advisory import (
    # Enums
    AdvisoryMode,
    WealthTier,
    CredentialType,
    ProfessionalRoleType,
    # Request models
    WealthAdvisoryRequest,
    EstatePlanningRequest,
    SuccessionPlanningRequest,
    TeamCoordinationRequest,
    FinancialLiteracyRequest,
    RetirementPlanningRequest,
    CollegePlanningRequest,
    GoalPlanningRequest,
    # Response models
    WealthAdvisoryResponse,
    EstatePlanningResponse,
    SuccessionPlanningResponse,
    TeamCoordinationResponse,
    FinancialLiteracyResponse,
    CredentialInfoResponse,
    RoleInfoResponse,
    KnowledgeBaseStatsResponse,
    RetirementPlanningResponse,
    CollegePlanningResponse,
    GoalPlanningResponse,
    # Supporting models
    Citation,
    ProfessionalRecommendation,
    ActionItem,
    RetirementMilestone,
    RetirementAccountRecommendation,
    CollegeCostProjection,
    CollegeSavingsStrategy,
    FinancialAidEstimate,
    TierProgressionMilestone,
    AccelerationStrategy,
)
from app.services.knowledge_rag import (
    get_wealth_rag,
    WealthManagementRAG,
    AdvisoryMode as RAGAdvisoryMode,
    WealthTier as RAGWealthTier,
)
from app.trading_engine.ml_models.llm_models.prompts import (
    WealthManagementPromptBuilder,
    create_prompt_builder,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_rag_service() -> WealthManagementRAG:
    """Get the RAG service instance."""
    return get_wealth_rag()


def get_prompt_builder() -> WealthManagementPromptBuilder:
    """Get the prompt builder instance."""
    return create_prompt_builder()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def convert_advisory_mode(mode: AdvisoryMode) -> RAGAdvisoryMode:
    """Convert schema AdvisoryMode to RAG AdvisoryMode."""
    return RAGAdvisoryMode(mode.value)


def convert_wealth_tier(tier: WealthTier) -> RAGWealthTier:
    """Convert schema WealthTier to RAG WealthTier."""
    return RAGWealthTier(tier.value)


def format_citations(rag_results: list[dict]) -> list[Citation]:
    """Convert RAG results to Citation schema objects."""
    return [
        Citation(
            source=result.get("source", "knowledge_base"),
            content=result.get("content", "")[:500],  # Truncate long content
            relevance_score=result.get("relevance_score", 0.0)
        )
        for result in rag_results
    ]


async def generate_advisory_response(
    query: str,
    rag: WealthManagementRAG,
    advisory_mode: AdvisoryMode,
    wealth_tier: WealthTier | None = None,
    n_results: int = 5
) -> tuple[list[dict], list[str]]:
    """
    Generate context from RAG for advisory response.

    Returns:
        Tuple of (RAG results, context strings)
    """
    rag_mode = convert_advisory_mode(advisory_mode)
    rag_tier = convert_wealth_tier(wealth_tier) if wealth_tier else None

    results = await rag.query(
        question=query,
        n_results=n_results,
        advisory_mode=rag_mode,
        wealth_tier=rag_tier
    )

    context = [r.get("content", "") for r in results if r.get("content")]
    return results, context


def extract_professionals_from_context(context: list[str]) -> list[ProfessionalRecommendation]:
    """Extract professional recommendations from context."""
    professionals = []

    # CFP recommendation for general planning
    if any("CFP" in c or "financial planner" in c.lower() for c in context):
        professionals.append(ProfessionalRecommendation(
            role="Certified Financial Planner (CFP®)",
            credentials=["CFP®"],
            responsibilities=["Comprehensive financial planning", "Team coordination"],
            why_recommended="Serves as 'quarterback' for coordinating advisory team",
            priority=1
        ))

    # Estate attorney for estate matters
    if any("estate" in c.lower() or "trust" in c.lower() for c in context):
        professionals.append(ProfessionalRecommendation(
            role="Estate Planning Attorney",
            credentials=["Bar License", "Board Certified in Estate Planning preferred"],
            responsibilities=["Wills", "Trusts", "Asset protection"],
            why_recommended="Essential for legal estate planning documents",
            priority=2
        ))

    # CPA for tax matters
    if any("tax" in c.lower() or "cpa" in c.lower() for c in context):
        professionals.append(ProfessionalRecommendation(
            role="Certified Public Accountant (CPA)",
            credentials=["CPA License"],
            responsibilities=["Tax planning", "Financial statements", "Compliance"],
            why_recommended="Critical for tax optimization and compliance",
            priority=2
        ))

    return professionals


def generate_next_steps(advisory_mode: AdvisoryMode, wealth_tier: WealthTier | None) -> list[ActionItem]:
    """Generate recommended next steps based on context."""
    steps = []

    if advisory_mode == AdvisoryMode.ESTATE_PLANNING:
        steps.extend([
            ActionItem(
                action="Schedule consultation with estate planning attorney",
                category="legal",
                priority="high",
                professional_needed="Estate Planning Attorney"
            ),
            ActionItem(
                action="Gather inventory of all assets and liabilities",
                category="preparation",
                priority="high",
                professional_needed=None
            ),
            ActionItem(
                action="Review current beneficiary designations on all accounts",
                category="review",
                priority="medium",
                professional_needed=None
            )
        ])

    elif advisory_mode == AdvisoryMode.SUCCESSION_PLANNING:
        steps.extend([
            ActionItem(
                action="Obtain business valuation from qualified appraiser",
                category="valuation",
                priority="high",
                professional_needed="Business Valuation Expert (ASA/CVA)"
            ),
            ActionItem(
                action="Assemble 'Dream Team' of advisors",
                category="team",
                priority="high",
                professional_needed="CFP® as coordinator"
            ),
            ActionItem(
                action="Document key processes and reduce owner dependence",
                category="preparation",
                priority="medium",
                professional_needed=None
            )
        ])

    elif advisory_mode == AdvisoryMode.FINANCIAL_LITERACY:
        steps.extend([
            ActionItem(
                action="Create or review monthly budget",
                category="budgeting",
                priority="high",
                professional_needed=None
            ),
            ActionItem(
                action="Build emergency fund (3-6 months expenses)",
                category="savings",
                priority="high",
                professional_needed=None
            )
        ])

    else:
        steps.append(ActionItem(
            action="Consult with qualified financial professional",
            category="general",
            priority="medium",
            professional_needed="CFP® or appropriate specialist"
        ))

    return steps


# =============================================================================
# ADVISORY ENDPOINTS
# =============================================================================

@router.post("/advisory/query", response_model=WealthAdvisoryResponse)
async def wealth_advisory_query(
    request: WealthAdvisoryRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> WealthAdvisoryResponse:
    """
    General wealth management advisory query.

    Provides comprehensive guidance across all wealth management domains
    with knowledge base citations and professional recommendations.
    """
    logger.info(f"Advisory query: {request.query[:50]}... mode={request.advisory_mode}")

    try:
        # Get RAG context
        rag_results, context = await generate_advisory_response(
            query=request.query,
            rag=rag,
            advisory_mode=request.advisory_mode,
            wealth_tier=request.wealth_tier,
            n_results=5
        )

        # Generate response text
        response_text = _generate_response_text(request.query, context, request.advisory_mode)

        # Build response
        citations = format_citations(rag_results) if request.include_citations else []
        professionals = extract_professionals_from_context(context) if request.include_professionals else []
        next_steps = generate_next_steps(request.advisory_mode, request.wealth_tier)

        return WealthAdvisoryResponse(
            response=response_text,
            advisory_mode=request.advisory_mode,
            wealth_tier=request.wealth_tier,
            citations=citations,
            recommended_professionals=professionals,
            next_steps=next_steps,
            confidence=0.85 if rag_results else 0.6
        )

    except Exception as e:
        logger.error(f"Error in advisory query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing advisory query: {str(e)}"
        )


@router.post("/advisory/estate-planning", response_model=EstatePlanningResponse)
async def estate_planning_advisory(
    request: EstatePlanningRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> EstatePlanningResponse:
    """
    Estate planning specific advisory.

    Provides guidance on wills, trusts, tax strategies, and estate documents.
    """
    logger.info(f"Estate planning request: value=${request.estimated_estate_value}")

    try:
        # Build query from request
        query = f"Estate planning guidance: {request.situation}"
        if request.has_business:
            query += " Business owner requiring succession integration."
        if request.charitable_intent:
            query += " Interested in charitable giving strategies."

        # Get RAG context
        rag_results, context = await generate_advisory_response(
            query=query,
            rag=rag,
            advisory_mode=AdvisoryMode.ESTATE_PLANNING,
            n_results=8
        )

        # Generate structured recommendations
        structures = _generate_estate_structures(request)
        tax_strategies = _generate_tax_strategies(request)
        documents = _generate_document_checklist(request)
        team = _generate_estate_team(request)

        return EstatePlanningResponse(
            summary=_generate_estate_summary(request, context),
            recommended_structures=structures,
            tax_strategies=tax_strategies,
            document_checklist=documents,
            professional_team=team,
            citations=format_citations(rag_results),
            timeline_recommendation="Begin with attorney consultation within 30 days"
        )

    except Exception as e:
        logger.error(f"Error in estate planning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing estate planning request: {str(e)}"
        )


@router.post("/advisory/succession", response_model=SuccessionPlanningResponse)
async def succession_planning(
    request: SuccessionPlanningRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> SuccessionPlanningResponse:
    """
    Business succession planning advisory.

    Provides guidance on exit strategies, valuation, and Dream Team coordination.
    """
    logger.info(f"Succession planning: {request.business_type}, value=${request.estimated_value}")

    try:
        # Build query
        query = f"Business succession planning for {request.business_type}"
        if request.estimated_value:
            query += f" valued at approximately ${request.estimated_value:,.0f}"
        if request.years_until_exit:
            query += f" with {request.years_until_exit} year exit horizon"

        # Get RAG context
        rag_results, context = await generate_advisory_response(
            query=query,
            rag=rag,
            advisory_mode=AdvisoryMode.SUCCESSION_PLANNING,
            n_results=8
        )

        # Generate recommendations
        exit_options = _generate_exit_options(request)
        dream_team = _generate_dream_team()
        valuation_considerations = _generate_valuation_considerations(request)
        tax_strategies = _generate_succession_tax_strategies(request)
        timeline = _generate_succession_timeline(request)

        return SuccessionPlanningResponse(
            summary=_generate_succession_summary(request, context),
            recommended_exit_options=exit_options,
            dream_team_structure=dream_team,
            valuation_considerations=valuation_considerations,
            tax_strategies=tax_strategies,
            timeline_phases=timeline,
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error in succession planning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing succession planning: {str(e)}"
        )


@router.post("/advisory/team-coordination", response_model=TeamCoordinationResponse)
async def team_coordination(
    request: TeamCoordinationRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> TeamCoordinationResponse:
    """
    Professional team coordination recommendations.

    Provides guidance on assembling and coordinating an advisory team.
    """
    logger.info(f"Team coordination: {request.situation_type}, tier={request.wealth_tier}")

    try:
        # Get RAG context
        rag_results, context = await generate_advisory_response(
            query=f"Professional team for {request.situation_type}: {request.situation_details}",
            rag=rag,
            advisory_mode=AdvisoryMode.GENERAL,
            wealth_tier=request.wealth_tier,
            n_results=6
        )

        # Generate team recommendations
        team = _generate_coordinated_team(request)
        framework = _generate_coordination_framework(request)
        protocol = _generate_communication_protocol(request)
        agenda = _generate_review_agenda(request)

        return TeamCoordinationResponse(
            recommended_team=team,
            coordination_framework=framework,
            communication_protocol=protocol,
            quarterly_review_agenda=agenda,
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error in team coordination: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing team coordination: {str(e)}"
        )


@router.post("/advisory/financial-literacy", response_model=FinancialLiteracyResponse)
async def financial_literacy_content(
    request: FinancialLiteracyRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> FinancialLiteracyResponse:
    """
    Financial literacy educational content.

    Provides clear, accessible explanations of financial topics for learners.
    """
    logger.info(f"Financial literacy: topic={request.topic}, level={request.current_knowledge_level}")

    try:
        # Get RAG context from financial literacy category
        rag_results = await rag.get_financial_literacy_content(
            topic=request.topic,
            level=request.current_knowledge_level
        )

        context = [r.get("content", "") for r in rag_results]

        # Generate educational content
        explanation = _generate_literacy_explanation(request, context)
        key_concepts = _extract_key_concepts(request.topic, context)
        practical_steps = _generate_practical_steps(request.topic)
        mistakes = _generate_common_mistakes(request.topic)
        resources = _generate_learning_resources(request.topic)
        next_topics = _suggest_next_topics(request.topic)

        return FinancialLiteracyResponse(
            topic=request.topic,
            explanation=explanation,
            key_concepts=key_concepts,
            practical_steps=practical_steps,
            common_mistakes=mistakes,
            resources=resources,
            next_topics=next_topics,
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error in financial literacy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing financial literacy request: {str(e)}"
        )


# =============================================================================
# KNOWLEDGE ENDPOINTS
# =============================================================================

@router.get("/knowledge/roles/{role_type}", response_model=RoleInfoResponse)
async def get_role_info(
    role_type: ProfessionalRoleType,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> RoleInfoResponse:
    """
    Get information about a specific professional role.

    Provides credentials, responsibilities, and engagement guidance.
    """
    logger.info(f"Role info request: {role_type}")

    try:
        # Query RAG for role information
        rag_results = await rag.search_by_category(
            question=f"What are the responsibilities and credentials of a {role_type.value.replace('_', ' ')}?",
            categories=["professional_roles", "certifications"],
            n_results=5
        )

        role_info = _get_role_details(role_type)

        return RoleInfoResponse(
            role_type=role_type.value,
            title=role_info["title"],
            description=role_info["description"],
            typical_credentials=role_info["credentials"],
            key_responsibilities=role_info["responsibilities"],
            reports_to=role_info.get("reports_to"),
            works_with=role_info.get("works_with", []),
            when_to_engage=role_info.get("when_to_engage", []),
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error getting role info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving role information: {str(e)}"
        )


@router.get("/knowledge/certifications/{cert_type}", response_model=CredentialInfoResponse)
async def get_certification_info(
    cert_type: CredentialType,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> CredentialInfoResponse:
    """
    Get information about a specific certification/credential.

    Provides requirements, study details, and career applications.
    """
    logger.info(f"Certification info request: {cert_type}")

    try:
        # Query RAG for certification information
        rag_results = await rag.search_by_category(
            question=f"What are the requirements and study materials for the {cert_type.value} certification?",
            categories=["certifications", "study_materials"],
            n_results=5
        )

        cert_info = _get_certification_details(cert_type)

        return CredentialInfoResponse(
            credential_type=cert_type.value,
            full_name=cert_info["full_name"],
            issuing_organization=cert_info["organization"],
            requirements=cert_info["requirements"],
            study_details=cert_info["study_details"],
            study_providers=cert_info.get("providers"),
            career_applications=cert_info["career_applications"],
            related_credentials=cert_info.get("related", []),
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error getting certification info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving certification information: {str(e)}"
        )


@router.get("/knowledge/stats", response_model=KnowledgeBaseStatsResponse)
async def get_knowledge_stats(
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> KnowledgeBaseStatsResponse:
    """
    Get knowledge base statistics.

    Returns information about indexed documents and categories.
    """
    try:
        stats = rag.get_collection_stats()

        return KnowledgeBaseStatsResponse(
            total_documents=stats.get("total_documents", 0),
            collection_name=stats.get("collection_name", "unknown"),
            embedding_model=stats.get("embedding_model", "unknown"),
            categories=list(rag.category_files.keys()),
            last_updated=None  # Could track this in metadata
        )

    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving knowledge statistics: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS FOR RESPONSE GENERATION
# =============================================================================

def _generate_response_text(query: str, context: list[str], mode: AdvisoryMode) -> str:
    """Generate response text from query and context."""
    if not context:
        return f"Based on your question about {mode.value.replace('_', ' ')}, I recommend consulting with a qualified professional for personalized guidance."

    # Combine context into response
    context_summary = " ".join(context[:3])[:1000]
    return f"Based on the wealth management knowledge base: {context_summary}... Please consult with appropriate professionals for specific advice tailored to your situation."


def _generate_estate_summary(request: EstatePlanningRequest, context: list[str]) -> str:
    """Generate estate planning summary."""
    summary_parts = ["Estate Planning Recommendations:"]

    if request.estimated_estate_value and request.estimated_estate_value > 12920000:  # 2023 exemption
        summary_parts.append("- Your estate may be subject to federal estate tax. Advanced planning strategies recommended.")
    else:
        summary_parts.append("- Focus on asset protection, probate avoidance, and incapacity planning.")

    if request.has_business:
        summary_parts.append("- Business succession planning should be integrated with overall estate plan.")

    if request.charitable_intent:
        summary_parts.append("- Consider charitable remainder trusts, donor-advised funds, or private foundation.")

    return " ".join(summary_parts)


def _generate_estate_structures(request: EstatePlanningRequest) -> list[dict[str, Any]]:
    """Generate recommended estate structures."""
    structures = [
        {"name": "Revocable Living Trust", "purpose": "Probate avoidance, incapacity planning", "recommended": True},
        {"name": "Pour-Over Will", "purpose": "Catch-all for assets not in trust", "recommended": True}
    ]

    if request.estimated_estate_value and request.estimated_estate_value > 1000000:
        structures.append({"name": "Irrevocable Life Insurance Trust (ILIT)", "purpose": "Remove life insurance from taxable estate", "recommended": True})

    if request.charitable_intent:
        structures.append({"name": "Charitable Remainder Trust (CRT)", "purpose": "Income stream with charitable benefit", "recommended": True})

    return structures


def _generate_tax_strategies(request: EstatePlanningRequest) -> list[str]:
    """Generate tax strategies."""
    strategies = ["Annual exclusion gifting ($18,000 per recipient in 2024)"]

    if request.estimated_estate_value and request.estimated_estate_value > 5000000:
        strategies.extend([
            "Consider Grantor Retained Annuity Trust (GRAT) for appreciation transfer",
            "Evaluate Qualified Personal Residence Trust (QPRT) for residence",
            "Review charitable lead/remainder trust options"
        ])

    return strategies


def _generate_document_checklist(request: EstatePlanningRequest) -> list[str]:
    """Generate document checklist."""
    documents = [
        "Last Will and Testament",
        "Revocable Living Trust",
        "Durable Power of Attorney (Financial)",
        "Healthcare Power of Attorney",
        "HIPAA Authorization",
        "Living Will / Advance Directive"
    ]

    if request.has_business:
        documents.extend(["Buy-Sell Agreement", "Business Succession Plan"])

    return documents


def _generate_estate_team(request: EstatePlanningRequest) -> list[ProfessionalRecommendation]:
    """Generate estate planning team recommendations."""
    return [
        ProfessionalRecommendation(
            role="Estate Planning Attorney",
            credentials=["Bar License", "Board Certified preferred"],
            responsibilities=["Document drafting", "Legal strategy", "Trust administration guidance"],
            why_recommended="Essential for legal document preparation and strategy",
            priority=1
        ),
        ProfessionalRecommendation(
            role="CPA with Estate Focus",
            credentials=["CPA License"],
            responsibilities=["Tax planning", "Return preparation", "Asset valuation coordination"],
            why_recommended="Critical for tax optimization and compliance",
            priority=2
        ),
        ProfessionalRecommendation(
            role="CFP® Financial Planner",
            credentials=["CFP®"],
            responsibilities=["Comprehensive planning", "Team coordination", "Goal alignment"],
            why_recommended="Serves as 'quarterback' coordinating all advisors",
            priority=2
        )
    ]


def _generate_exit_options(request: SuccessionPlanningRequest) -> list[dict[str, Any]]:
    """Generate exit options for succession planning."""
    options = []

    if request.potential_successors and "family" in request.potential_successors:
        options.append({
            "option": "Family Transfer",
            "description": "Transfer to next generation family members",
            "pros": ["Preserves family legacy", "Flexible structuring", "Gradual transition possible"],
            "cons": ["Potential family conflict", "May not maximize value", "Financing challenges"],
            "suitable_for": "Families with capable, interested successors"
        })

    if request.potential_successors and "employee" in request.potential_successors:
        options.append({
            "option": "Management Buyout (MBO)",
            "description": "Sale to existing management team",
            "pros": ["Management knows business", "Smoother transition", "Preserves culture"],
            "cons": ["Management may lack capital", "May require seller financing"],
            "suitable_for": "Businesses with strong management team"
        })

    options.append({
        "option": "Third-Party Sale",
        "description": "Sale to strategic or financial buyer",
        "pros": ["Highest potential valuation", "Clean break", "Professional process"],
        "cons": ["Loss of legacy", "Longer process", "Due diligence burden"],
        "suitable_for": "Owners seeking maximum value and clean exit"
    })

    if request.employee_count and request.employee_count >= 20:
        options.append({
            "option": "ESOP",
            "description": "Employee Stock Ownership Plan",
            "pros": ["Tax advantages (Section 1042)", "Employee ownership culture", "Legacy preservation"],
            "cons": ["Complex and expensive", "Ongoing administration", "Repurchase obligation"],
            "suitable_for": "Companies with $5M+ value and 20+ employees"
        })

    return options


def _generate_dream_team() -> list[ProfessionalRecommendation]:
    """Generate Dream Team structure for succession."""
    return [
        ProfessionalRecommendation(
            role="CFP® Financial Planner",
            credentials=["CFP®"],
            responsibilities=["Define personal financial objectives", "Coordinate team", "Post-transaction planning"],
            why_recommended="'Quarterback' ensuring all aspects align with owner's life goals",
            priority=1
        ),
        ProfessionalRecommendation(
            role="M&A Attorney",
            credentials=["Bar License", "M&A experience"],
            responsibilities=["Transaction structure", "Purchase agreements", "Legal due diligence"],
            why_recommended="Essential for legal protection and deal structure",
            priority=1
        ),
        ProfessionalRecommendation(
            role="CPA with Transaction Experience",
            credentials=["CPA License"],
            responsibilities=["Tax-efficient structuring", "Due diligence", "Post-transaction planning"],
            why_recommended="Critical for minimizing tax implications",
            priority=1
        ),
        ProfessionalRecommendation(
            role="Business Valuation Expert",
            credentials=["ASA", "CVA"],
            responsibilities=["Objective valuation", "Defensible pricing", "Tax challenge defense"],
            why_recommended="Establishes fair market value for negotiations",
            priority=2
        ),
        ProfessionalRecommendation(
            role="Estate Planning Attorney",
            credentials=["Bar License", "Estate specialization"],
            responsibilities=["Estate plan updates", "Seller note structuring", "Trust adjustments"],
            why_recommended="Ensures alignment with overall estate plan",
            priority=2
        ),
        ProfessionalRecommendation(
            role="Wealth Manager",
            credentials=["CPWA®", "CFA®", "CFP®"],
            responsibilities=["Post-transaction investment", "Tax optimization", "Retirement income"],
            why_recommended="Manages proceeds for long-term financial security",
            priority=2
        )
    ]


def _generate_valuation_considerations(request: SuccessionPlanningRequest) -> list[str]:
    """Generate valuation considerations."""
    considerations = [
        "Multiple valuation methodologies (DCF, comparable companies, comparable transactions)",
        "Consideration of control premiums or minority discounts",
        "Lack of marketability discount for private company"
    ]

    if request.business_type:
        considerations.append(f"Industry-specific multiples for {request.business_type}")

    considerations.extend([
        "Normalized earnings (add-backs for owner compensation, one-time items)",
        "Working capital requirements",
        "Customer concentration risk assessment"
    ])

    return considerations


def _generate_succession_tax_strategies(request: SuccessionPlanningRequest) -> list[str]:
    """Generate tax strategies for succession."""
    strategies = [
        "Installment sale to spread capital gains over multiple years (Section 453)",
        "Qualified Small Business Stock exclusion if applicable (Section 1202)"
    ]

    if request.estimated_value and request.estimated_value > 10000000:
        strategies.extend([
            "Consider charitable remainder trust for appreciated stock",
            "Opportunity Zone investment for gain deferral",
            "ESOP with Section 1042 rollover potential"
        ])

    return strategies


def _generate_succession_timeline(request: SuccessionPlanningRequest) -> list[dict[str, str]]:
    """Generate succession timeline phases."""
    years = request.years_until_exit or 3

    return [
        {"phase": "Preparation", "duration": f"Years 1-{max(1, years - 2)}", "activities": "Assemble team, valuation, value enhancement"},
        {"phase": "Marketing", "duration": "3-12 months", "activities": "Identify buyers, confidential outreach, evaluate offers"},
        {"phase": "Transaction", "duration": "3-6 months", "activities": "Due diligence, negotiation, closing"},
        {"phase": "Transition", "duration": "6-24 months post-close", "activities": "Knowledge transfer, earnout period"}
    ]


def _generate_succession_summary(request: SuccessionPlanningRequest, context: list[str]) -> str:
    """Generate succession planning summary."""
    parts = [f"Business Succession Plan for {request.business_type}:"]

    if request.estimated_value:
        parts.append(f"Estimated value: ${request.estimated_value:,.0f}")

    if request.years_until_exit:
        parts.append(f"Target exit horizon: {request.years_until_exit} years")

    parts.append("Recommend assembling 'Dream Team' of coordinated professionals.")

    return " ".join(parts)


def _generate_coordinated_team(request: TeamCoordinationRequest) -> list[ProfessionalRecommendation]:
    """Generate coordinated team recommendations."""
    team = [
        ProfessionalRecommendation(
            role="CFP® Financial Planner",
            credentials=["CFP®"],
            responsibilities=["Team coordination", "Comprehensive planning"],
            why_recommended="Central coordinator for advisory team",
            priority=1
        )
    ]

    if request.wealth_tier == WealthTier.HNW_UHNW:
        team.append(ProfessionalRecommendation(
            role="CPWA® Private Wealth Advisor",
            credentials=["CPWA®"],
            responsibilities=["UHNW strategies", "Complex planning", "Family office coordination"],
            why_recommended="Specialized in high-net-worth and ultra-high-net-worth needs",
            priority=1
        ))

    return team


def _generate_coordination_framework(request: TeamCoordinationRequest) -> str:
    """Generate coordination framework."""
    return """Recommended coordination framework:
1. CFP® serves as central quarterback and communication hub
2. Monthly advisor sync meetings
3. Quarterly comprehensive reviews with all key advisors
4. Clear documentation and decision protocols
5. Shared secure document repository"""


def _generate_communication_protocol(request: TeamCoordinationRequest) -> str:
    """Generate communication protocol."""
    return """Communication protocol:
- CFP® coordinates all advisor communications
- Quarterly written status reports from each advisor
- Immediate notification for time-sensitive matters
- Annual comprehensive plan review meeting
- Secure portal for document sharing"""


def _generate_review_agenda(request: TeamCoordinationRequest) -> list[str]:
    """Generate quarterly review agenda."""
    return [
        "Investment performance review and rebalancing needs",
        "Tax planning updates and opportunities",
        "Estate plan review and life changes impact",
        "Risk management and insurance adequacy",
        "Goal progress assessment",
        "Regulatory and legislative updates",
        "Action items for next quarter"
    ]


def _generate_literacy_explanation(request: FinancialLiteracyRequest, context: list[str]) -> str:
    """Generate financial literacy explanation."""
    if context:
        return f"Here's what you need to know about {request.topic}: " + " ".join(context[:2])[:800]
    return f"Understanding {request.topic} is an important step in your financial journey."


def _extract_key_concepts(topic: str, context: list[str]) -> list[str]:
    """Extract key concepts from topic."""
    concepts = {
        "budgeting": ["Income vs expenses", "Fixed vs variable costs", "Tracking spending", "Budget categories"],
        "emergency fund": ["3-6 months expenses", "Liquid savings", "Financial safety net", "High-yield savings"],
        "debt": ["Interest rates", "Principal vs interest", "Debt avalanche", "Debt snowball"],
        "credit": ["Credit score factors", "Payment history", "Credit utilization", "Length of history"],
        "investing": ["Compound interest", "Diversification", "Risk vs return", "Time horizon"],
        "retirement": ["401(k)", "IRA types", "Employer match", "Compound growth"]
    }

    for key, values in concepts.items():
        if key in topic.lower():
            return values

    return ["Understanding basics", "Building good habits", "Long-term thinking", "Consistent action"]


def _generate_practical_steps(topic: str) -> list[str]:
    """Generate practical steps for financial topic."""
    steps = {
        "budgeting": [
            "Track all spending for one month",
            "Categorize expenses into needs, wants, savings",
            "Set spending limits for each category",
            "Review and adjust weekly"
        ],
        "emergency fund": [
            "Calculate monthly essential expenses",
            "Set target of 3-6 months expenses",
            "Open high-yield savings account",
            "Automate regular contributions"
        ],
        "debt": [
            "List all debts with interest rates",
            "Choose strategy (avalanche or snowball)",
            "Make minimum payments on all debts",
            "Put extra money toward target debt"
        ],
        "credit": [
            "Check credit report for free annually",
            "Pay all bills on time",
            "Keep credit utilization under 30%",
            "Avoid opening unnecessary accounts"
        ]
    }

    for key, values in steps.items():
        if key in topic.lower():
            return values

    return ["Start with small, consistent actions", "Track your progress", "Review regularly", "Seek guidance when needed"]


def _generate_common_mistakes(topic: str) -> list[str]:
    """Generate common mistakes for financial topic."""
    mistakes = {
        "budgeting": [
            "Not tracking small purchases",
            "Setting unrealistic limits",
            "Not adjusting for irregular expenses",
            "Giving up after one mistake"
        ],
        "emergency fund": [
            "Keeping emergency fund too accessible",
            "Using it for non-emergencies",
            "Not replenishing after use",
            "Stopping contributions too early"
        ],
        "debt": [
            "Only making minimum payments",
            "Adding new debt while paying off old",
            "Not addressing high-interest debt first",
            "Ignoring the psychological aspect"
        ]
    }

    for key, values in mistakes.items():
        if key in topic.lower():
            return values

    return ["Starting too aggressively", "Not being consistent", "Comparing to others", "Expecting quick results"]


def _generate_learning_resources(topic: str) -> list[str]:
    """Generate learning resources."""
    return [
        "Consumer Financial Protection Bureau (CFPB) educational materials",
        "Federal Reserve educational resources",
        "Your local library financial literacy programs",
        "Reputable personal finance books and podcasts"
    ]


def _suggest_next_topics(topic: str) -> list[str]:
    """Suggest next topics to learn."""
    progression = {
        "budgeting": ["Emergency fund", "Debt management", "Saving strategies"],
        "emergency fund": ["Debt payoff strategies", "Basic investing", "Insurance basics"],
        "debt": ["Credit building", "Saving strategies", "Investment basics"],
        "credit": ["Loan basics", "Major purchases", "Building wealth"],
        "investing": ["Retirement accounts", "Asset allocation", "Tax-advantaged investing"]
    }

    for key, values in progression.items():
        if key in topic.lower():
            return values

    return ["Budgeting basics", "Emergency fund building", "Understanding credit"]


def _get_role_details(role_type: ProfessionalRoleType) -> dict[str, Any]:
    """Get detailed information about a professional role."""
    roles = {
        ProfessionalRoleType.ESTATE_PLANNING_ATTORNEY: {
            "title": "Estate Planning Attorney",
            "description": "Legal specialist in wills, trusts, and estate planning documents",
            "credentials": ["Bar License", "Board Certified in Estate Planning preferred"],
            "responsibilities": ["Draft wills and trusts", "Tax reduction strategies", "Asset protection", "Healthcare directives"],
            "reports_to": "Family/Clients",
            "works_with": ["CPA", "CFP", "Trust Officers"],
            "when_to_engage": ["Creating or updating estate plan", "Major life changes", "Business succession"]
        },
        ProfessionalRoleType.FINANCIAL_PLANNER: {
            "title": "Certified Financial Planner (CFP®)",
            "description": "Comprehensive financial planning professional serving as 'quarterback'",
            "credentials": ["CFP® Certification"],
            "responsibilities": ["Comprehensive planning", "Team coordination", "Investment advice", "Retirement planning"],
            "reports_to": "Clients",
            "works_with": ["CPA", "Attorney", "Insurance Advisor"],
            "when_to_engage": ["Starting financial journey", "Life transitions", "Comprehensive planning needs"]
        },
        ProfessionalRoleType.TRUSTEE: {
            "title": "Trustee",
            "description": "Fiduciary responsible for managing trust assets for beneficiaries",
            "credentials": ["Individual or Corporate Trustee"],
            "responsibilities": ["Asset management", "Distributions", "Tax filings", "Record-keeping"],
            "reports_to": "Beneficiaries/Courts",
            "works_with": ["Trust Attorney", "CPA", "Investment Advisor"],
            "when_to_engage": ["Trust administration", "Fiduciary services needed"]
        }
    }

    return roles.get(role_type, {
        "title": role_type.value.replace("_", " ").title(),
        "description": f"Professional role in {role_type.value.replace('_', ' ')}",
        "credentials": ["Relevant professional credentials"],
        "responsibilities": ["Role-specific responsibilities"],
        "works_with": ["Related professionals"],
        "when_to_engage": ["When expertise in this area is needed"]
    })


def _get_certification_details(cert_type: CredentialType) -> dict[str, Any]:
    """Get detailed information about a certification."""
    certs = {
        CredentialType.CFP: {
            "full_name": "Certified Financial Planner",
            "organization": "CFP Board of Standards",
            "requirements": {
                "education": "Bachelor's degree + CFP Board education requirements",
                "examination": "Comprehensive 170-question exam",
                "experience": "6,000 hours (3 years) or 4,000 hours (2 years apprenticeship)",
                "ethics": "Background check and fiduciary commitment"
            },
            "study_details": {
                "hours": "300+ hours",
                "topics": "70+ integrated financial planning topics",
                "cost": "$4,700 - $6,500"
            },
            "providers": [
                {"name": "Dalton Education", "features": ["Live review", "Practice exams"]},
                {"name": "Kaplan", "features": ["Self-study", "Live online"]}
            ],
            "career_applications": ["Financial planner", "Wealth advisor", "Team coordinator"],
            "related": ["ChFC", "CPWA"]
        },
        CredentialType.CFA: {
            "full_name": "Chartered Financial Analyst",
            "organization": "CFA Institute",
            "requirements": {
                "education": "Bachelor's degree or final year of program",
                "examination": "Three 6-hour exams (Level I, II, III)",
                "experience": "4 years relevant work experience",
                "ethics": "CFA Institute ethical standards"
            },
            "study_details": {
                "hours": "2,000+ total (700-950 per level)",
                "levels": 3,
                "duration": "18-36 months minimum"
            },
            "providers": [
                {"name": "Kaplan Schweser", "features": ["Study notes", "Mock exams"]},
                {"name": "AnalystPrep", "features": ["Practice questions", "Video content"]}
            ],
            "career_applications": ["Portfolio manager", "Investment analyst", "CIO"],
            "related": ["CIMA", "FRM"]
        },
        CredentialType.CPA: {
            "full_name": "Certified Public Accountant",
            "organization": "State Boards of Accountancy",
            "requirements": {
                "education": "150 credit hours",
                "examination": "Four sections (FAR, AUD, REG, BEC)",
                "experience": "State-specific (typically 1-2 years)",
                "ethics": "Ethics exam in most states"
            },
            "study_details": {
                "hours": "200-240 total",
                "sections": "4 exam sections",
                "cost": "$2,499 - $5,999"
            },
            "providers": [
                {"name": "Becker", "features": ["Comprehensive materials", "SkillMaster videos"]},
                {"name": "Surgent", "features": ["Adaptive learning", "Shorter study time"]}
            ],
            "career_applications": ["Tax advisor", "Financial reporting", "Audit"],
            "related": ["PFS", "CFP"]
        }
    }

    return certs.get(cert_type, {
        "full_name": cert_type.value,
        "organization": "Professional certifying body",
        "requirements": {"general": "Varies by credential"},
        "study_details": {"hours": "Varies"},
        "career_applications": ["Relevant professional roles"],
        "related": []
    })


# =============================================================================
# NEW PLANNING ENDPOINTS
# =============================================================================

@router.post("/advisory/retirement-planning", response_model=RetirementPlanningResponse)
async def retirement_planning_advisory(
    request: RetirementPlanningRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> RetirementPlanningResponse:
    """
    Retirement planning advisory.

    Provides comprehensive retirement planning guidance including:
    - Savings trajectory analysis
    - Account recommendations (401k, IRA, Roth, etc.)
    - Social Security optimization strategies
    - Withdrawal strategies (4% rule, bucket strategy, etc.)
    - Tax optimization for retirement
    """
    logger.info(f"Retirement planning: age={request.current_age}, target={request.target_retirement_age}")

    try:
        # Build query for RAG
        query = f"Retirement planning for {request.current_age} year old with ${request.annual_income:,.0f} income"
        if request.has_pension:
            query += " who has a pension"

        # Get RAG context
        rag_results, context = await generate_advisory_response(
            query=query,
            rag=rag,
            advisory_mode=AdvisoryMode.RETIREMENT_PLANNING,
            n_results=8
        )

        # Calculate retirement projections
        years_to_retirement = request.target_retirement_age - request.current_age
        retirement_calcs = _calculate_retirement_projections(request)

        # Generate account recommendations
        account_recs = _generate_retirement_account_recommendations(request)

        # Generate milestones
        milestones = _generate_retirement_milestones(request, retirement_calcs)

        # Determine trajectory
        trajectory = _determine_retirement_trajectory(retirement_calcs)

        # Generate Social Security strategy
        ss_strategy = _generate_social_security_strategy(request)

        # Generate withdrawal strategy
        withdrawal_strategy = _generate_withdrawal_strategy(request)

        # Generate tax strategies
        tax_strategies = _generate_retirement_tax_strategies(request)

        # Generate risk factors
        risk_factors = _generate_retirement_risk_factors(request)

        # Generate professional recommendations
        professionals = _generate_retirement_professionals(request)

        return RetirementPlanningResponse(
            summary=_generate_retirement_summary(request, retirement_calcs, trajectory),
            years_to_retirement=years_to_retirement,
            current_trajectory=trajectory,
            target_retirement_savings=retirement_calcs["target_savings"],
            projected_retirement_savings=retirement_calcs["projected_savings"],
            savings_gap=retirement_calcs["savings_gap"],
            recommended_monthly_savings=retirement_calcs["recommended_monthly"],
            account_recommendations=account_recs,
            social_security_strategy=ss_strategy,
            withdrawal_strategy=withdrawal_strategy,
            milestones=milestones,
            tax_strategies=tax_strategies,
            risk_factors=risk_factors,
            recommended_professionals=professionals,
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error in retirement planning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing retirement planning request: {str(e)}"
        )


@router.post("/advisory/college-planning", response_model=CollegePlanningResponse)
async def college_planning_advisory(
    request: CollegePlanningRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> CollegePlanningResponse:
    """
    College/education planning advisory.

    Provides comprehensive college planning guidance including:
    - Cost projections with inflation
    - 529 plan recommendations
    - Financial aid optimization (FAFSA, CSS Profile)
    - Alternative education funding strategies
    - Tax benefits (AOTC, LLC, etc.)
    """
    logger.info(f"College planning: child_age={request.child_current_age}, school_type={request.target_school_type}")

    try:
        # Build query for RAG
        query = f"College planning for child age {request.child_current_age} targeting {request.target_school_type} school"

        # Get RAG context
        rag_results, context = await generate_advisory_response(
            query=query,
            rag=rag,
            advisory_mode=AdvisoryMode.COLLEGE_PLANNING,
            n_results=8
        )

        # Calculate years until college
        years_until_college = request.target_college_start_age - request.child_current_age

        # Generate cost projection
        cost_projection = _generate_college_cost_projection(request, years_until_college)

        # Calculate savings trajectory
        savings_calcs = _calculate_college_savings(request, years_until_college, cost_projection)

        # Generate savings strategies
        savings_strategies = _generate_college_savings_strategies(request)

        # Generate financial aid estimate if applicable
        financial_aid = None
        if request.interested_in_financial_aid and request.household_income:
            financial_aid = _generate_financial_aid_estimate(request, cost_projection)

        # Generate alternative options
        alternatives = _generate_college_alternatives()

        # Generate tax strategies
        tax_strategies = _generate_college_tax_strategies(request)

        # Generate timeline actions
        timeline_actions = _generate_college_timeline(request, years_until_college)

        # Determine trajectory
        trajectory = _determine_college_trajectory(savings_calcs)

        # Generate professionals
        professionals = _generate_college_professionals()

        return CollegePlanningResponse(
            summary=_generate_college_summary(request, savings_calcs, trajectory),
            years_until_college=years_until_college,
            cost_projection=cost_projection,
            current_savings_trajectory=trajectory,
            projected_savings_at_start=savings_calcs["projected_savings"],
            funding_gap=savings_calcs["funding_gap"],
            savings_strategies=savings_strategies,
            financial_aid_estimate=financial_aid,
            alternative_options=alternatives,
            tax_strategies=tax_strategies,
            timeline_actions=timeline_actions,
            recommended_professionals=professionals,
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error in college planning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing college planning request: {str(e)}"
        )


@router.post("/goals/create-plan", response_model=GoalPlanningResponse)
async def create_goal_plan(
    request: GoalPlanningRequest,
    rag: WealthManagementRAG = Depends(get_rag_service)
) -> GoalPlanningResponse:
    """
    Goal-based tier progression planning.

    Creates a comprehensive roadmap for clients to progress through wealth tiers
    toward their financial goals. Supports planning from Foundation ($0-10K)
    all the way to HNW/UHNW ($5M+) and Family Office ($10M+).

    Example: A 30-year-old making $100K/year wanting to reach Family Office
    status will receive a detailed 20-25 year roadmap with:
    - Year-by-year milestones and actions
    - Required savings rates
    - Acceleration strategies (career, business, tax optimization)
    - Professional advisor recommendations at each stage
    """
    logger.info(f"Goal planning: age={request.current_age}, income=${request.annual_income:,.0f}, target={request.target_tier}")

    try:
        # Build query for RAG
        query = f"Wealth tier progression from ${request.current_assets:,.0f} to {request.target_tier.value} tier"

        # Get RAG context
        rag_results, context = await generate_advisory_response(
            query=query,
            rag=rag,
            advisory_mode=AdvisoryMode.GOAL_PLANNING,
            n_results=10
        )

        # Determine current tier
        current_tier = _determine_wealth_tier(request.current_assets)

        # Calculate target assets based on tier
        target_assets = request.target_assets or _get_tier_minimum(request.target_tier)

        # Calculate projections
        goal_calcs = _calculate_goal_projections(request, target_assets)

        # Determine feasibility
        feasibility = _determine_goal_feasibility(request, goal_calcs)

        # Generate yearly roadmap
        roadmap = _generate_tier_roadmap(request, current_tier, goal_calcs)

        # Generate acceleration strategies
        acceleration = _generate_acceleration_strategies(request)

        # Generate key milestones
        milestones = _generate_key_milestones(current_tier, request.target_tier)

        # Generate risk factors
        risk_factors = _generate_goal_risk_factors(request)

        # Generate advisors by stage
        advisors_by_stage = _generate_advisors_by_stage(current_tier, request.target_tier)

        # Generate current professional recommendations
        professionals = _generate_goal_professionals(current_tier)

        # Generate motivation message
        motivation = _generate_motivation_message(request, feasibility)

        return GoalPlanningResponse(
            summary=_generate_goal_summary(request, goal_calcs, feasibility),
            current_tier=current_tier,
            target_tier=request.target_tier,
            feasibility=feasibility,
            recommended_timeline_years=goal_calcs["recommended_years"],
            required_savings_rate=goal_calcs["required_savings_rate"],
            current_savings_rate=goal_calcs["current_savings_rate"],
            savings_rate_gap=goal_calcs["savings_rate_gap"],
            target_assets=target_assets,
            projected_assets_at_timeline=goal_calcs["projected_assets"],
            yearly_roadmap=roadmap,
            acceleration_strategies=acceleration,
            key_milestones=milestones,
            risk_factors=risk_factors,
            advisors_by_stage=advisors_by_stage,
            recommended_professionals=professionals,
            motivation_message=motivation,
            citations=format_citations(rag_results)
        )

    except Exception as e:
        logger.error(f"Error in goal planning: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing goal planning request: {str(e)}"
        )


# =============================================================================
# RETIREMENT PLANNING HELPERS
# =============================================================================

def _calculate_retirement_projections(request: RetirementPlanningRequest) -> dict[str, float]:
    """Calculate retirement savings projections."""
    years = request.target_retirement_age - request.current_age
    current_savings = request.current_retirement_savings

    # Assume 7% average return
    growth_rate = 0.07

    # Estimate current monthly savings if not provided
    if request.current_contributions:
        annual_contribution = sum(request.current_contributions.values())
    else:
        # Assume 10% savings rate
        annual_contribution = request.annual_income * 0.10

    # Add employer match if provided
    if request.employer_401k_match:
        match_contribution = min(request.annual_income * request.employer_401k_match, request.annual_income * 0.06)
        annual_contribution += match_contribution

    # Project future value
    projected_savings = current_savings * ((1 + growth_rate) ** years)
    for year in range(years):
        projected_savings += annual_contribution * ((1 + growth_rate) ** (years - year - 1))

    # Calculate target (25x desired income or 80% current income)
    desired_income = request.desired_retirement_income or (request.annual_income * 0.80)
    target_savings = desired_income * 25  # 4% rule

    # Calculate gap and recommended monthly
    savings_gap = max(0, target_savings - projected_savings)

    # Calculate what's needed to close gap
    if savings_gap > 0 and years > 0:
        # PMT formula to find annual contribution needed
        monthly_needed = (savings_gap / (((1 + growth_rate) ** years - 1) / growth_rate)) / 12
        recommended_monthly = max(monthly_needed, annual_contribution / 12)
    else:
        recommended_monthly = annual_contribution / 12

    return {
        "target_savings": target_savings,
        "projected_savings": projected_savings,
        "savings_gap": savings_gap,
        "recommended_monthly": recommended_monthly,
        "current_annual_contribution": annual_contribution,
        "desired_retirement_income": desired_income
    }


def _determine_retirement_trajectory(calcs: dict[str, float]) -> str:
    """Determine if on track for retirement."""
    if calcs["projected_savings"] >= calcs["target_savings"] * 0.95:
        return "on_track"
    elif calcs["projected_savings"] >= calcs["target_savings"] * 0.70:
        return "needs_adjustment"
    else:
        return "significant_gap"


def _generate_retirement_account_recommendations(request: RetirementPlanningRequest) -> list[RetirementAccountRecommendation]:
    """Generate retirement account recommendations."""
    recommendations = []

    # 401k with match first
    if request.employer_401k_match:
        match_amount = min(request.annual_income * request.employer_401k_match, request.annual_income * 0.06)
        recommendations.append(RetirementAccountRecommendation(
            account_type="401(k) - To Match",
            recommended_contribution=match_amount / request.employer_401k_match,
            tax_treatment="Pre-tax (or Roth if available)",
            rationale="Capture full employer match - 100% immediate return on investment",
            priority=1
        ))

    # Roth IRA for younger savers or moderate income
    if request.current_age < 50 or request.annual_income < 150000:
        recommendations.append(RetirementAccountRecommendation(
            account_type="Roth IRA",
            recommended_contribution=7000,  # 2024 limit
            tax_treatment="After-tax contributions, tax-free growth",
            rationale="Tax-free growth for decades, flexible withdrawal rules",
            priority=2 if request.employer_401k_match else 1
        ))

    # Max 401k
    recommendations.append(RetirementAccountRecommendation(
        account_type="401(k) - Max",
        recommended_contribution=23000,  # 2024 limit
        tax_treatment="Pre-tax (reduces current taxable income)",
        rationale="Maximize tax-advantaged space, reduce current tax burden",
        priority=3
    ))

    # HSA if applicable
    recommendations.append(RetirementAccountRecommendation(
        account_type="HSA",
        recommended_contribution=4150,  # 2024 individual limit
        tax_treatment="Triple tax advantage",
        rationale="Only account with tax deduction, tax-free growth, AND tax-free withdrawals",
        priority=2
    ))

    return recommendations


def _generate_retirement_milestones(request: RetirementPlanningRequest, calcs: dict[str, float]) -> list[RetirementMilestone]:
    """Generate retirement planning milestones."""
    milestones = []
    current_age = request.current_age
    target_age = request.target_retirement_age
    years = target_age - current_age

    # Define milestone ages
    milestone_ages = []
    if current_age < 30:
        milestone_ages.extend([30, 40, 50, 55, 60, target_age])
    elif current_age < 40:
        milestone_ages.extend([40, 50, 55, 60, target_age])
    elif current_age < 50:
        milestone_ages.extend([50, 55, 60, target_age])
    else:
        milestone_ages.extend([current_age + 5, 60, target_age])

    milestone_ages = [a for a in milestone_ages if a > current_age and a <= target_age]

    for age in milestone_ages:
        years_to = age - current_age
        # Simple projection
        target = calcs["target_savings"] * (years_to / years) if years > 0 else calcs["target_savings"]

        actions = []
        if age == 50:
            actions = ["Eligible for catch-up contributions ($7,500 401k, $1,000 IRA)", "Review asset allocation"]
        elif age == 55:
            actions = ["Consider healthcare bridge costs", "Review pension options if applicable"]
        elif age == 59:
            actions = ["IRA penalty-free withdrawals available", "Review Roth conversion ladder"]
        elif age >= 62:
            actions = ["Review Social Security claiming strategy", "Consider Medicare enrollment (65)"]
        elif age == target_age:
            actions = ["Finalize withdrawal strategy", "Begin retirement income plan"]
        else:
            actions = ["Review portfolio allocation", "Maximize contributions"]

        milestones.append(RetirementMilestone(
            age=age,
            milestone=f"Age {age} checkpoint",
            target_savings=target,
            actions=actions
        ))

    return milestones


def _generate_social_security_strategy(request: RetirementPlanningRequest) -> str:
    """Generate Social Security claiming strategy."""
    if request.current_age < 50:
        return "Focus on maximizing career earnings now. Social Security benefits based on highest 35 years of earnings. Strategy decision can wait until closer to claiming age."

    if request.desired_retirement_income and request.desired_retirement_income > 100000:
        return "Consider delaying Social Security to age 70 for maximum benefit (8%/year increase from 67-70). Your income level suggests you can fund early retirement from savings while SS grows."
    else:
        return "Claiming at Full Retirement Age (67) often optimal. Delaying to 70 increases benefit by 24% but requires 12+ years to break even. Consider health and life expectancy."


def _generate_withdrawal_strategy(request: RetirementPlanningRequest) -> str:
    """Generate recommended withdrawal strategy."""
    risk = request.risk_tolerance

    if risk == "conservative":
        return "Bucket Strategy recommended: Bucket 1 (1-2 years cash), Bucket 2 (3-7 years bonds), Bucket 3 (8+ years stocks). This provides stability and reduces sequence-of-returns risk."
    elif risk == "aggressive":
        return "Dynamic Withdrawal Strategy: Start with 4% rule, adjust annually based on portfolio performance. In good years withdraw more, in down years reduce to 3%. Maintain 60%+ equity allocation."
    else:
        return "Hybrid approach: Income Floor (Social Security + pension covers essentials) + 4% rule for discretionary. Consider annuitizing portion of portfolio for guaranteed income baseline."


def _generate_retirement_tax_strategies(request: RetirementPlanningRequest) -> list[str]:
    """Generate retirement tax optimization strategies."""
    strategies = [
        "Tax-efficient withdrawal order: Taxable accounts first, then tax-deferred, then Roth",
        "Manage tax brackets in retirement to minimize lifetime taxes"
    ]

    if request.current_age < 60:
        strategies.append("Consider Roth conversion ladder in low-income years before Social Security starts")
        strategies.append("Front-load Roth contributions while in lower tax brackets")

    if request.annual_income > 150000:
        strategies.append("Maximize 401(k) contributions to reduce current marginal rate")
        strategies.append("Consider backdoor Roth IRA strategy if income exceeds direct contribution limits")

    strategies.append("Harvest capital gains in 0% bracket years during early retirement")
    strategies.append("Coordinate with Social Security to minimize taxation of benefits")

    return strategies


def _generate_retirement_risk_factors(request: RetirementPlanningRequest) -> list[str]:
    """Generate retirement plan risk factors."""
    risks = [
        "Sequence of returns risk in early retirement years",
        "Healthcare costs (average couple needs $315,000+ for retirement healthcare)",
        "Inflation eroding purchasing power",
        "Longevity risk - living longer than planned"
    ]

    if not request.has_pension:
        risks.append("No pension income increases reliance on portfolio withdrawals")

    if request.current_age > 50 and request.current_retirement_savings < request.annual_income * 3:
        risks.append("Late start requires higher savings rate or extended working years")

    return risks


def _generate_retirement_professionals(request: RetirementPlanningRequest) -> list[ProfessionalRecommendation]:
    """Generate professional recommendations for retirement planning."""
    return [
        ProfessionalRecommendation(
            role="CFP® Financial Planner",
            credentials=["CFP®"],
            responsibilities=["Retirement income planning", "Tax-efficient withdrawal strategies", "Social Security optimization"],
            why_recommended="Comprehensive retirement planning with fiduciary duty",
            priority=1
        ),
        ProfessionalRecommendation(
            role="CPA with Retirement Focus",
            credentials=["CPA"],
            responsibilities=["Tax projection", "Roth conversion analysis", "Required Minimum Distribution planning"],
            why_recommended="Critical for tax optimization in accumulation and distribution phases",
            priority=2
        )
    ]


def _generate_retirement_summary(request: RetirementPlanningRequest, calcs: dict[str, float], trajectory: str) -> str:
    """Generate retirement planning summary."""
    years = request.target_retirement_age - request.current_age

    status_msg = {
        "on_track": "You're on track for a comfortable retirement!",
        "needs_adjustment": "Some adjustments needed to meet your retirement goals.",
        "significant_gap": "Significant changes needed to reach retirement target."
    }

    return f"""Retirement Planning Summary for {request.current_age}-year-old retiring at {request.target_retirement_age}:

{status_msg[trajectory]}

- Years to retirement: {years}
- Target retirement savings: ${calcs['target_savings']:,.0f}
- Projected savings: ${calcs['projected_savings']:,.0f}
- Gap: ${calcs['savings_gap']:,.0f}
- Recommended monthly savings: ${calcs['recommended_monthly']:,.0f}

Your desired retirement income of ${calcs['desired_retirement_income']:,.0f}/year requires approximately ${calcs['target_savings']:,.0f} using the 4% safe withdrawal rule."""


# =============================================================================
# COLLEGE PLANNING HELPERS
# =============================================================================

def _generate_college_cost_projection(request: CollegePlanningRequest, years: int) -> CollegeCostProjection:
    """Generate college cost projection."""
    # 2024 average costs
    costs = {
        "public_in_state": {"current": 23250, "inflation": 0.05},
        "public_out_of_state": {"current": 40550, "inflation": 0.05},
        "private": {"current": 53430, "inflation": 0.04},
        "elite_private": {"current": 85000, "inflation": 0.035}
    }

    school = costs.get(request.target_school_type, costs["public_in_state"])
    current_cost = school["current"]
    inflation = school["inflation"]

    projected_annual = current_cost * ((1 + inflation) ** years)
    # Total 4-year cost with ongoing inflation
    total_4_year = sum(projected_annual * ((1 + inflation) ** i) for i in range(4))

    return CollegeCostProjection(
        school_type=request.target_school_type,
        current_annual_cost=current_cost,
        projected_annual_cost=projected_annual,
        total_4_year_cost=total_4_year,
        inflation_rate_used=inflation
    )


def _calculate_college_savings(request: CollegePlanningRequest, years: int, projection: CollegeCostProjection) -> dict[str, float]:
    """Calculate college savings projections."""
    current = request.current_529_balance
    monthly = request.monthly_contribution or 0
    growth_rate = 0.06  # Conservative 6% for age-based allocation

    # Project savings
    projected = current * ((1 + growth_rate) ** years)
    for year in range(years):
        projected += (monthly * 12) * ((1 + growth_rate) ** (years - year - 1))

    gap = max(0, projection.total_4_year_cost - projected)

    # Calculate needed monthly to close gap
    if gap > 0 and years > 0:
        needed_monthly = (gap / (((1 + growth_rate) ** years - 1) / growth_rate)) / 12
    else:
        needed_monthly = monthly

    return {
        "projected_savings": projected,
        "funding_gap": gap,
        "needed_monthly": needed_monthly,
        "total_cost": projection.total_4_year_cost
    }


def _determine_college_trajectory(calcs: dict[str, float]) -> str:
    """Determine college savings trajectory."""
    coverage = calcs["projected_savings"] / calcs["total_cost"] if calcs["total_cost"] > 0 else 0

    if coverage >= 0.90:
        return "on_track"
    elif coverage >= 0.60:
        return "needs_adjustment"
    else:
        return "significant_gap"


def _generate_college_savings_strategies(request: CollegePlanningRequest) -> list[CollegeSavingsStrategy]:
    """Generate college savings strategy recommendations."""
    strategies = []

    # 529 Plan
    strategies.append(CollegeSavingsStrategy(
        account_type="529 College Savings Plan",
        recommended_monthly_contribution=500,
        state_tax_benefit=f"Check {request.state_of_residence or 'your state'} for deduction",
        investment_approach="Age-based allocation (aggressive when young, conservative near college)",
        pros=["Tax-free growth", "High contribution limits", "State tax benefits", "SECURE 2.0 Roth IRA rollover option"],
        cons=["Must use for education", "Limited investment choices", "Potential penalty for non-education use"]
    ))

    # Coverdell ESA if income eligible
    if request.household_income and request.household_income < 220000:
        strategies.append(CollegeSavingsStrategy(
            account_type="Coverdell ESA",
            recommended_monthly_contribution=166,  # $2000/year max
            state_tax_benefit=None,
            investment_approach="Self-directed investments",
            pros=["More investment flexibility", "Can use for K-12", "Tax-free growth"],
            cons=["$2,000 annual limit", "Income limits", "Must use by age 30"]
        ))

    # UTMA/UGMA
    strategies.append(CollegeSavingsStrategy(
        account_type="UTMA/UGMA Custodial",
        recommended_monthly_contribution=200,
        state_tax_benefit="First $1,250 of gains tax-free for child",
        investment_approach="Any investments allowed",
        pros=["No contribution limits", "Flexible use", "Kiddie tax benefits"],
        cons=["Counts heavily against financial aid", "Becomes child's money at majority", "No tax-free growth"]
    ))

    return strategies


def _generate_financial_aid_estimate(request: CollegePlanningRequest, projection: CollegeCostProjection) -> FinancialAidEstimate:
    """Generate financial aid estimate."""
    income = request.household_income or 100000

    # Simplified EFC calculation (actual formula is more complex)
    if income < 60000:
        efc = 0  # Likely Pell eligible
    elif income < 100000:
        efc = (income - 60000) * 0.22
    elif income < 150000:
        efc = 8800 + (income - 100000) * 0.25
    else:
        efc = 21300 + (income - 150000) * 0.47

    need = max(0, projection.projected_annual_cost - efc)

    aid_types = ["Federal Direct Loans"]
    if efc == 0:
        aid_types.insert(0, "Pell Grant (up to $7,395)")
    if need > 10000:
        aid_types.append("Need-based institutional grants")
    aid_types.append("Merit scholarships (varies by school)")

    optimization = [
        "Front-load income in early high school years, reduce in junior/senior year",
        "Minimize assets in student's name (counted at 20% vs 5.64% for parents)",
        "Maximize retirement contributions (not counted in FAFSA)",
        "Consider timing of home equity (counted by CSS Profile schools)"
    ]

    return FinancialAidEstimate(
        estimated_efc=efc,
        estimated_need=need,
        likely_aid_types=aid_types,
        optimization_strategies=optimization
    )


def _generate_college_alternatives() -> list[str]:
    """Generate alternative education funding options."""
    return [
        "Community college for first 2 years (60-70% cost savings)",
        "In-state public universities vs out-of-state",
        "Merit scholarship hunting - apply to schools where student is top 25%",
        "Work-study programs and part-time employment",
        "ROTC or military service for GI Bill benefits",
        "Trade schools and apprenticeships for non-degree careers",
        "Employer tuition assistance programs",
        "Student loans as last resort (Federal before private)"
    ]


def _generate_college_tax_strategies(request: CollegePlanningRequest) -> list[str]:
    """Generate college tax strategies."""
    return [
        "American Opportunity Tax Credit: Up to $2,500/year for first 4 years (income limits apply)",
        "Lifetime Learning Credit: Up to $2,000/year (income limits apply)",
        "Student loan interest deduction: Up to $2,500/year",
        "529 qualified expenses include room/board, computers, books",
        "SECURE 2.0: Unused 529 funds can roll to Roth IRA (after 15 years, up to $35,000)",
        "Grandparent 529s no longer affect FAFSA (as of 2024-25)"
    ]


def _generate_college_timeline(request: CollegePlanningRequest, years: int) -> list[dict[str, Any]]:
    """Generate college planning timeline."""
    timeline = []

    if years > 10:
        timeline.append({"years_out": "10+", "actions": ["Start 529 contributions", "Establish regular savings habit", "Research scholarship opportunities early"]})
    if years > 5:
        timeline.append({"years_out": "5-10", "actions": ["Review 529 performance", "Research target schools", "Consider prepaid tuition plans"]})
    if years > 3:
        timeline.append({"years_out": "3-5", "actions": ["Shift 529 to conservative allocation", "Begin college visits", "Research financial aid policies"]})
    if years > 1:
        timeline.append({"years_out": "1-3", "actions": ["Complete FAFSA (opens Oct 1)", "Apply for scholarships", "Compare financial aid offers"]})

    timeline.append({"years_out": "College years", "actions": ["Reapply FAFSA annually", "Seek work-study", "Apply for scholarships each year"]})

    return timeline


def _generate_college_summary(request: CollegePlanningRequest, calcs: dict[str, float], trajectory: str) -> str:
    """Generate college planning summary."""
    years = request.target_college_start_age - request.child_current_age

    status = {
        "on_track": "Great progress toward college funding!",
        "needs_adjustment": "Some adjustments needed to meet college costs.",
        "significant_gap": "Significant planning needed - consider alternatives and financial aid."
    }

    return f"""College Planning Summary for {request.child_current_age}-year-old ({years} years until college):

{status[trajectory]}

- Projected total cost: ${calcs['total_cost']:,.0f}
- Projected savings: ${calcs['projected_savings']:,.0f}
- Funding gap: ${calcs['funding_gap']:,.0f}
- Needed monthly savings: ${calcs['needed_monthly']:,.0f}

Remember: You don't need to save 100% - financial aid, scholarships, and student contributions typically cover a portion."""


def _generate_college_professionals() -> list[ProfessionalRecommendation]:
    """Generate professional recommendations for college planning."""
    return [
        ProfessionalRecommendation(
            role="CFP® Financial Planner",
            credentials=["CFP®"],
            responsibilities=["Education funding analysis", "529 plan selection", "Financial aid strategy"],
            why_recommended="Integrates college planning with overall financial plan",
            priority=1
        ),
        ProfessionalRecommendation(
            role="College Planning Specialist",
            credentials=["College funding certifications"],
            responsibilities=["FAFSA optimization", "Scholarship search", "College selection strategy"],
            why_recommended="Specialized knowledge of financial aid system",
            priority=2
        )
    ]


# =============================================================================
# GOAL PLANNING HELPERS
# =============================================================================

def _determine_wealth_tier(assets: float) -> WealthTier:
    """Determine wealth tier from asset amount."""
    if assets < 10000:
        return WealthTier.FOUNDATION
    elif assets < 75000:
        return WealthTier.BUILDER
    elif assets < 500000:
        return WealthTier.GROWTH
    elif assets < 5000000:
        return WealthTier.AFFLUENT
    else:
        return WealthTier.HNW_UHNW


def _get_tier_minimum(tier: WealthTier) -> float:
    """Get minimum assets for a tier."""
    minimums = {
        WealthTier.FOUNDATION: 0,
        WealthTier.BUILDER: 10000,
        WealthTier.GROWTH: 75000,
        WealthTier.AFFLUENT: 500000,
        WealthTier.HNW_UHNW: 5000000
    }
    return minimums.get(tier, 0)


def _calculate_goal_projections(request: GoalPlanningRequest, target_assets: float) -> dict[str, Any]:
    """Calculate goal-based projections."""
    # Calculate current savings rate
    monthly_savings = request.monthly_savings or (request.annual_income * 0.10 / 12)
    current_savings_rate = (monthly_savings * 12) / request.annual_income if request.annual_income > 0 else 0

    # Assume 8% growth, 3% income growth
    growth_rate = 0.08
    income_growth = 0.03

    # Calculate years needed with current rate
    current_assets = request.current_assets
    annual_savings = monthly_savings * 12

    # Simulate year by year
    years_needed = 0
    projected_assets = current_assets
    projected_income = request.annual_income

    for year in range(50):  # Max 50 years
        projected_assets = projected_assets * (1 + growth_rate) + annual_savings
        projected_income *= (1 + income_growth)
        annual_savings = projected_income * current_savings_rate
        years_needed = year + 1

        if projected_assets >= target_assets:
            break

    # Calculate required savings rate to reach in requested timeline
    target_years = request.target_timeline_years or years_needed
    if target_years < years_needed:
        # Need higher savings rate
        required_rate = _calculate_required_savings_rate(
            current_assets, target_assets, request.annual_income, target_years, growth_rate, income_growth
        )
    else:
        required_rate = current_savings_rate

    # Project assets at timeline end with current rate
    projected_at_end = current_assets
    annual = request.annual_income * current_savings_rate
    for year in range(target_years):
        projected_at_end = projected_at_end * (1 + growth_rate) + annual
        annual *= (1 + income_growth)

    return {
        "current_savings_rate": current_savings_rate,
        "required_savings_rate": min(required_rate, 0.60),  # Cap at 60%
        "savings_rate_gap": max(0, required_rate - current_savings_rate),
        "recommended_years": years_needed,
        "projected_assets": projected_at_end,
        "target_years": target_years
    }


def _calculate_required_savings_rate(current: float, target: float, income: float, years: int, growth: float, income_growth: float) -> float:
    """Calculate required savings rate to reach target."""
    # Binary search for required rate
    low, high = 0.0, 1.0

    for _ in range(50):  # Binary search iterations
        mid = (low + high) / 2
        projected = current
        annual_income = income

        for year in range(years):
            projected = projected * (1 + growth) + (annual_income * mid)
            annual_income *= (1 + income_growth)

        if projected >= target:
            high = mid
        else:
            low = mid

    return high


def _determine_goal_feasibility(request: GoalPlanningRequest, calcs: dict[str, Any]) -> str:
    """Determine goal feasibility."""
    required_rate = calcs["required_savings_rate"]

    if required_rate <= 0.15:
        return "highly_achievable"
    elif required_rate <= 0.25:
        return "achievable"
    elif required_rate <= 0.40:
        return "stretch"
    else:
        return "aggressive"


def _generate_tier_roadmap(request: GoalPlanningRequest, current_tier: WealthTier, calcs: dict[str, Any]) -> list[TierProgressionMilestone]:
    """Generate year-by-year tier progression roadmap."""
    roadmap = []
    years = calcs["target_years"]

    # Define tier thresholds
    tier_thresholds = [
        (WealthTier.FOUNDATION, 0, 10000),
        (WealthTier.BUILDER, 10000, 75000),
        (WealthTier.GROWTH, 75000, 500000),
        (WealthTier.AFFLUENT, 500000, 5000000),
        (WealthTier.HNW_UHNW, 5000000, float('inf'))
    ]

    # Generate milestones at tier transitions
    income = request.annual_income
    savings_rate = calcs["required_savings_rate"]
    growth_rate = 0.08
    income_growth = 0.03

    milestone_years = []

    for tier, min_amt, max_amt in tier_thresholds:
        if min_amt > request.current_assets:
            # Find when we cross into this tier
            temp_assets = request.current_assets
            temp_income = request.annual_income
            for year in range(years + 1):
                if temp_assets >= min_amt:
                    milestone_years.append((year, tier, temp_assets, temp_income * savings_rate / 12))
                    break
                temp_assets = temp_assets * (1 + growth_rate) + (temp_income * savings_rate)
                temp_income *= (1 + income_growth)

    # Group into phases
    if not milestone_years:
        milestone_years = [(years, request.target_tier, calcs["projected_assets"], income * savings_rate / 12)]

    prev_year = 0
    for i, (year, tier, assets_at_end, monthly) in enumerate(milestone_years):
        if year <= prev_year:
            continue

        year_range = f"{prev_year + 1}-{year}" if year > prev_year + 1 else str(year)

        actions = _get_tier_actions(tier)
        career = _get_career_guidance(tier, request.career_flexibility)

        roadmap.append(TierProgressionMilestone(
            year_range=year_range,
            tier=tier,
            expected_assets=assets_at_end,
            monthly_savings_target=monthly,
            actions=actions,
            career_guidance=career
        ))
        prev_year = year

    return roadmap


def _get_tier_actions(tier: WealthTier) -> list[str]:
    """Get recommended actions for tier."""
    actions = {
        WealthTier.FOUNDATION: [
            "Build 6-month emergency fund",
            "Pay off high-interest debt",
            "Contribute to 401k up to employer match",
            "Open and fund Roth IRA",
            "Automate savings"
        ],
        WealthTier.BUILDER: [
            "Max 401k contributions",
            "Continue maxing Roth IRA",
            "Open taxable brokerage account",
            "Start tax-loss harvesting",
            "Review and optimize insurance"
        ],
        WealthTier.GROWTH: [
            "Maintain max retirement contributions",
            "Backdoor Roth if income exceeds limits",
            "Consider real estate investment",
            "Evaluate side business or consulting",
            "Create basic estate plan"
        ],
        WealthTier.AFFLUENT: [
            "Implement advanced tax strategies",
            "Consider business ownership or equity",
            "Diversify into alternative investments",
            "Establish irrevocable trusts",
            "Begin charitable giving strategy"
        ],
        WealthTier.HNW_UHNW: [
            "Formalize family office structure",
            "Create investment committee",
            "Implement family governance",
            "Multi-generational estate plan",
            "Philanthropic foundation or DAF"
        ]
    }
    return actions.get(tier, [])


def _get_career_guidance(tier: WealthTier, flexibility: str) -> str:
    """Get career guidance based on tier and flexibility."""
    if flexibility == "high":
        return "Actively pursue promotions, consider job changes every 2-4 years for 15-20% salary increases"
    elif flexibility == "medium":
        return "Seek advancement within current company, develop high-value skills, negotiate raises"
    else:
        return "Focus on job stability while maximizing current compensation and benefits"


def _generate_acceleration_strategies(request: GoalPlanningRequest) -> list[AccelerationStrategy]:
    """Generate wealth acceleration strategies."""
    strategies = [
        AccelerationStrategy(
            strategy_name="Income Growth",
            description="Proactively manage career for maximum income growth",
            tactics=[
                "Change jobs every 2-4 years for salary increases",
                "Develop high-value skills (leadership, technical)",
                "Negotiate aggressively at every opportunity",
                "Consider management track or specialist track"
            ],
            impact="Can double effective savings rate over 10 years",
            difficulty="medium",
            time_to_implement="Ongoing"
        ),
        AccelerationStrategy(
            strategy_name="Business Ownership",
            description="Build equity through business rather than just salary",
            tactics=[
                "Start side business that can scale",
                "Join startup with equity compensation",
                "Buy existing business with SBA financing",
                "Real estate investing for passive income"
            ],
            impact="Primary wealth acceleration vehicle for most millionaires",
            difficulty="high",
            time_to_implement="2-5 years to significant impact"
        ),
        AccelerationStrategy(
            strategy_name="Tax Optimization",
            description="Keep more of what you earn through legal tax strategies",
            tactics=[
                "Max all tax-advantaged accounts",
                "Tax-loss harvesting",
                "Roth conversions in low-income years",
                "Business expense optimization",
                "Charitable strategies (DAF bunching)"
            ],
            impact="Can increase effective savings by 15-25%",
            difficulty="low",
            time_to_implement="Immediate"
        )
    ]

    if request.geographic_flexibility:
        strategies.append(AccelerationStrategy(
            strategy_name="Geographic Arbitrage",
            description="Relocate to lower cost area while maintaining income",
            tactics=[
                "Remote work from lower cost-of-living area",
                "State income tax optimization (no-tax states)",
                "Housing cost reduction through relocation"
            ],
            impact="Can increase savings rate by 10-20% of income",
            difficulty="medium",
            time_to_implement="3-12 months"
        ))

    return strategies


def _generate_key_milestones(current: WealthTier, target: WealthTier) -> list[str]:
    """Generate key milestones between tiers."""
    milestones = [
        "Emergency fund complete (3-6 months)",
        "Debt-free (except mortgage)",
        "First $100K invested"
    ]

    if target in [WealthTier.GROWTH, WealthTier.AFFLUENT, WealthTier.HNW_UHNW]:
        milestones.extend([
            "Maxing all retirement accounts",
            "First $500K net worth"
        ])

    if target in [WealthTier.AFFLUENT, WealthTier.HNW_UHNW]:
        milestones.extend([
            "First million",
            "Coast FI achieved",
            "Financial independence number reached"
        ])

    if target == WealthTier.HNW_UHNW:
        milestones.extend([
            "$5M liquid net worth",
            "Family office threshold ($10M)"
        ])

    return milestones


def _generate_goal_risk_factors(request: GoalPlanningRequest) -> list[str]:
    """Generate goal plan risk factors."""
    risks = [
        "Market volatility affecting portfolio growth",
        "Job loss or income reduction",
        "Unexpected major expenses (health, family)",
        "Inflation eroding purchasing power"
    ]

    if request.target_tier == WealthTier.HNW_UHNW:
        risks.append("Aggressive timeline may require business success or equity windfall")

    if request.current_debt and request.current_debt > request.annual_income:
        risks.append("High debt-to-income ratio may slow progress")

    return risks


def _generate_advisors_by_stage(current: WealthTier, target: WealthTier) -> dict[str, list[str]]:
    """Generate recommended advisors at each stage."""
    advisors = {
        "foundation": ["CFP® (Fee-only financial planner)"],
        "builder": ["CFP®", "CPA for tax optimization"],
        "growth": ["CFP®", "CFA® (investment management)", "CPA"],
        "affluent": ["CFP®", "CFA®", "CPA", "Estate Planning Attorney"],
        "hnw_uhnw": ["CPWA®", "CFA®", "CPA", "Estate Attorney", "Tax Attorney", "Family Governance Officer"]
    }

    result = {}

    tier_order = [WealthTier.FOUNDATION, WealthTier.BUILDER, WealthTier.GROWTH, WealthTier.AFFLUENT, WealthTier.HNW_UHNW]
    start_idx = tier_order.index(current)
    end_idx = tier_order.index(target)

    for tier in tier_order[start_idx:end_idx + 1]:
        result[tier.value] = advisors.get(tier.value, ["CFP®"])

    return result


def _generate_goal_professionals(current_tier: WealthTier) -> list[ProfessionalRecommendation]:
    """Generate current professional recommendations."""
    return [
        ProfessionalRecommendation(
            role="CFP® Financial Planner",
            credentials=["CFP®"],
            responsibilities=["Goal planning", "Investment strategy", "Progress tracking"],
            why_recommended="Essential guide for wealth building journey - fiduciary duty",
            priority=1
        ),
        ProfessionalRecommendation(
            role="CPA",
            credentials=["CPA License"],
            responsibilities=["Tax optimization", "Entity structuring", "Compliance"],
            why_recommended="Tax efficiency accelerates wealth building significantly",
            priority=2
        )
    ]


def _generate_motivation_message(request: GoalPlanningRequest, feasibility: str) -> str:
    """Generate motivational message based on plan."""
    messages = {
        "highly_achievable": f"Your goal is very achievable! With your income of ${request.annual_income:,.0f} and disciplined saving, you're on a clear path to {request.target_tier.value.replace('_', '/')} status. Stay consistent and you'll get there.",
        "achievable": f"Your goal is achievable with dedication. The path to {request.target_tier.value.replace('_', '/')} is clear - it will require focus on savings and smart decisions, but it's well within reach.",
        "stretch": f"This is an ambitious goal - reaching {request.target_tier.value.replace('_', '/')} will require significant commitment to high savings rates and potentially income growth strategies. Challenge yourself!",
        "aggressive": f"This is an aggressive goal. Reaching {request.target_tier.value.replace('_', '/')} will likely require income acceleration through career advancement, business ownership, or equity compensation. It's possible with the right opportunities."
    }
    return messages.get(feasibility, "Every financial journey starts with a single step. Stay committed to your goals.")


def _generate_goal_summary(request: GoalPlanningRequest, calcs: dict[str, Any], feasibility: str) -> str:
    """Generate goal planning summary."""
    return f"""Goal-Based Wealth Progression Plan

From: {_determine_wealth_tier(request.current_assets).value.replace('_', ' ').title()} (${request.current_assets:,.0f})
To: {request.target_tier.value.replace('_', ' ').title()}

Feasibility: {feasibility.replace('_', ' ').title()}
Recommended Timeline: {calcs['recommended_years']} years
Required Savings Rate: {calcs['required_savings_rate'] * 100:.1f}%
Current Savings Rate: {calcs['current_savings_rate'] * 100:.1f}%

{_generate_motivation_message(request, feasibility)}"""
