import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Base URL for the API
const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// Service tiers aligned with $66,622 US average salary
export type ServiceTier = 'foundation' | 'builder' | 'growth' | 'affluent' | 'hnw_uhnw';

// Advisory modes for different expertise areas
export type AdvisoryMode =
  | 'estate_planning'
  | 'investment_advisory'
  | 'tax_optimization'
  | 'succession_planning'
  | 'family_governance'
  | 'trust_administration'
  | 'credit_financing'
  | 'compliance_operations'
  | 'general';

// Decision authority levels
export type DecisionAuthority = 'binding' | 'senior_advisory' | 'advisory' | 'support_role';

// Request/Response types
export interface WealthAdvisoryRequest {
  query: string;
  advisory_mode?: AdvisoryMode;
  include_citations?: boolean;
  family_context?: Record<string, unknown>;
  user_tier?: ServiceTier;
}

export interface Citation {
  source: string;
  category: string;
  relevance_score: number;
  content_preview: string;
}

export interface ProfessionalRole {
  title: string;
  credentials: string[];
  category: string;
  decision_authority: DecisionAuthority;
  key_responsibilities: string[];
  recommended_for: string;
}

export interface WealthAdvisoryResponse {
  response: string;
  citations: Citation[];
  recommended_professionals: ProfessionalRole[];
  next_steps: string[];
  confidence: number;
  compliance_flags?: string[];
  service_tier: ServiceTier;
}

export interface EstatePlanningRequest {
  client_age: number;
  marital_status: string;
  dependents: number;
  estimated_estate_value: number;
  has_business: boolean;
  concerns: string[];
}

export interface SuccessionRequest {
  business_type: string;
  estimated_value: number;
  owner_age: number;
  family_successors: number;
  key_employees: number;
  timeline_years?: number;
}

export interface TeamCoordinationRequest {
  planning_type: string;
  complexity_level: 'basic' | 'moderate' | 'complex' | 'highly_complex';
  estimated_value: number;
  specific_needs: string[];
}

export interface TeamRecommendation {
  primary_advisor: ProfessionalRole;
  supporting_team: ProfessionalRole[];
  coordination_structure: string;
  meeting_cadence: string;
  estimated_fee_range: string;
}

export interface KnowledgeStats {
  total_documents: number;
  categories: Record<string, number>;
  last_updated: string;
  embedding_model: string;
}

export interface RoleInfo {
  title: string;
  credentials: string[];
  study_hours?: string;
  exam_sections?: string[];
  continuing_education?: string;
  key_responsibilities: string[];
  typical_clients: string[];
  average_compensation?: string;
  career_path?: string[];
}

export interface CertificationInfo {
  name: string;
  acronym: string;
  issuing_body: string;
  prerequisites: string[];
  study_hours: string;
  exam_format: string;
  passing_rate?: string;
  cost_range: string;
  continuing_education: string;
  career_benefits: string[];
}

// Custom base query with authentication
const baseQueryWithAuth = fetchBaseQuery({
  baseUrl,
  prepareHeaders: (headers) => {
    const token = localStorage.getItem('token');
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    return headers;
  },
});

// Wealth Advisory API slice
export const wealthAdvisoryApi = createApi({
  reducerPath: 'wealthAdvisoryApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['WealthAdvisory', 'Knowledge', 'Roles', 'Certifications'],
  endpoints: (builder) => ({
    // General wealth advisory query
    wealthAdvisoryQuery: builder.mutation<WealthAdvisoryResponse, WealthAdvisoryRequest>({
      query: (request) => ({
        url: '/wealth/advisory/query',
        method: 'POST',
        body: request,
      }),
    }),

    // Estate planning advisory
    estatePlanningAdvisory: builder.mutation<WealthAdvisoryResponse, EstatePlanningRequest>({
      query: (request) => ({
        url: '/wealth/advisory/estate-planning',
        method: 'POST',
        body: request,
      }),
    }),

    // Succession planning advisory
    successionPlanning: builder.mutation<WealthAdvisoryResponse, SuccessionRequest>({
      query: (request) => ({
        url: '/wealth/advisory/succession',
        method: 'POST',
        body: request,
      }),
    }),

    // Team coordination recommendations
    teamCoordination: builder.mutation<TeamRecommendation, TeamCoordinationRequest>({
      query: (request) => ({
        url: '/wealth/advisory/team-coordination',
        method: 'POST',
        body: request,
      }),
    }),

    // Get knowledge base statistics
    getKnowledgeStats: builder.query<KnowledgeStats, void>({
      query: () => '/wealth/knowledge/stats',
      providesTags: ['Knowledge'],
    }),

    // Get professional role information
    getRoleInfo: builder.query<RoleInfo, string>({
      query: (roleType) => `/wealth/knowledge/roles/${roleType}`,
      providesTags: (result, error, roleType) => [
        { type: 'Roles', id: roleType },
      ],
    }),

    // Get all roles by category
    getRolesByCategory: builder.query<ProfessionalRole[], string>({
      query: (category) => `/wealth/knowledge/roles?category=${category}`,
      providesTags: ['Roles'],
    }),

    // Get certification information
    getCertificationInfo: builder.query<CertificationInfo, string>({
      query: (certType) => `/wealth/knowledge/certifications/${certType}`,
      providesTags: (result, error, certType) => [
        { type: 'Certifications', id: certType },
      ],
    }),

    // Get all certifications
    getAllCertifications: builder.query<CertificationInfo[], void>({
      query: () => '/wealth/knowledge/certifications',
      providesTags: ['Certifications'],
    }),

    // Search knowledge base
    searchKnowledge: builder.query<{
      results: Array<{
        content: string;
        category: string;
        relevance_score: number;
        metadata: Record<string, unknown>;
      }>;
      total: number;
    }, { query: string; category?: string; limit?: number }>({
      query: ({ query, category, limit = 10 }) => {
        const params = new URLSearchParams();
        params.append('q', query);
        if (category) params.append('category', category);
        params.append('limit', limit.toString());
        return `/wealth/knowledge/search?${params.toString()}`;
      },
      providesTags: ['Knowledge'],
    }),

    // Get service tier information
    getServiceTierInfo: builder.query<{
      tier: ServiceTier;
      aum_range: [number, number];
      available_advisors: string[];
      features: string[];
      description: string;
    }, ServiceTier>({
      query: (tier) => `/wealth/service-tiers/${tier}`,
    }),

    // Compliance check for a planning scenario
    complianceCheck: builder.mutation<{
      compliant: boolean;
      flags: Array<{
        rule: string;
        severity: 'info' | 'warning' | 'critical';
        message: string;
        authority: string;
      }>;
      recommendations: string[];
    }, {
      scenario_type: string;
      parameters: Record<string, unknown>;
    }>({
      query: (request) => ({
        url: '/wealth/compliance/check',
        method: 'POST',
        body: request,
      }),
    }),
  }),
});

// Export hooks
export const {
  useWealthAdvisoryQueryMutation,
  useEstatePlanningAdvisoryMutation,
  useSuccessionPlanningMutation,
  useTeamCoordinationMutation,
  useGetKnowledgeStatsQuery,
  useGetRoleInfoQuery,
  useGetRolesByCategoryQuery,
  useGetCertificationInfoQuery,
  useGetAllCertificationsQuery,
  useSearchKnowledgeQuery,
  useLazySearchKnowledgeQuery,
  useGetServiceTierInfoQuery,
  useComplianceCheckMutation,
} = wealthAdvisoryApi;

export default wealthAdvisoryApi;
