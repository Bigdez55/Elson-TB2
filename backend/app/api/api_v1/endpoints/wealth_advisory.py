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
    # Response models
    WealthAdvisoryResponse,
    EstatePlanningResponse,
    SuccessionPlanningResponse,
    TeamCoordinationResponse,
    FinancialLiteracyResponse,
    CredentialInfoResponse,
    RoleInfoResponse,
    KnowledgeBaseStatsResponse,
    Citation,
    ProfessionalRecommendation,
    ActionItem,
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
        {"phase": "Preparation", "duration": f"Years 1-{max(1, years-2)}", "activities": "Assemble team, valuation, value enhancement"},
        {"phase": "Marketing", "duration": f"3-12 months", "activities": "Identify buyers, confidential outreach, evaluate offers"},
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
