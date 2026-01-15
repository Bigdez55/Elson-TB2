"""
Elson Financial AI - API Schemas

Pydantic models for request/response validation across all API endpoints.
"""

# Wealth Advisory Schemas
from .wealth_advisory import (
    # Enums
    AdvisoryMode,
    WealthTier,
    CredentialType,
    ProfessionalRoleType,
    # Base models
    Citation,
    ProfessionalRecommendation,
    ActionItem,
    # Request models
    WealthAdvisoryRequest,
    EstatePlanningRequest,
    SuccessionPlanningRequest,
    TeamCoordinationRequest,
    FinancialLiteracyRequest,
    CredentialInfoRequest,
    RoleInfoRequest,
    # Response models
    WealthAdvisoryResponse,
    EstatePlanningResponse,
    SuccessionPlanningResponse,
    TeamCoordinationResponse,
    FinancialLiteracyResponse,
    CredentialInfoResponse,
    RoleInfoResponse,
    KnowledgeBaseStatsResponse,
)

__all__ = [
    # Wealth Advisory
    "AdvisoryMode",
    "WealthTier",
    "CredentialType",
    "ProfessionalRoleType",
    "Citation",
    "ProfessionalRecommendation",
    "ActionItem",
    "WealthAdvisoryRequest",
    "EstatePlanningRequest",
    "SuccessionPlanningRequest",
    "TeamCoordinationRequest",
    "FinancialLiteracyRequest",
    "CredentialInfoRequest",
    "RoleInfoRequest",
    "WealthAdvisoryResponse",
    "EstatePlanningResponse",
    "SuccessionPlanningResponse",
    "TeamCoordinationResponse",
    "FinancialLiteracyResponse",
    "CredentialInfoResponse",
    "RoleInfoResponse",
    "KnowledgeBaseStatsResponse",
]
