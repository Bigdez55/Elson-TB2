import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// Family Account types
export interface FamilyMember {
  id: string;
  user_id: string;
  name: string;
  email?: string;
  role: 'OWNER' | 'ADULT' | 'TEEN' | 'CHILD';
  age?: number;
  date_of_birth?: string;
  portfolio_value: number;
  cash_balance: number;
  monthly_return: number;
  monthly_return_percent: number;
  permissions: {
    can_trade: boolean;
    can_withdraw: boolean;
    max_trade_amount?: number;
    requires_approval: boolean;
  };
  created_at: string;
  last_active: string;
}

export interface PendingApproval {
  id: string;
  family_member_id: string;
  member_name: string;
  request_type: 'TRADE' | 'WITHDRAWAL' | 'PERMISSION_CHANGE';
  details: {
    symbol?: string;
    trade_type?: 'BUY' | 'SELL';
    quantity?: number;
    amount?: number;
    reason?: string;
  };
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  requested_at: string;
  reviewed_at?: string;
  reviewed_by?: string;
}

export interface FamilyInvite {
  id: string;
  email: string;
  role: 'ADULT' | 'TEEN' | 'CHILD';
  invited_at: string;
  expires_at: string;
  status: 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'CANCELLED';
}

export interface FamilySettings {
  require_approval_for_trades: boolean;
  require_approval_for_withdrawals: boolean;
  max_teen_trade_amount: number;
  max_child_balance: number;
  educational_mode: boolean;
  notifications_enabled: boolean;
}

export interface CreateFamilyMemberRequest {
  name: string;
  email?: string;
  role: 'ADULT' | 'TEEN' | 'CHILD';
  date_of_birth?: string;
  initial_balance?: number;
  permissions?: {
    can_trade?: boolean;
    can_withdraw?: boolean;
    max_trade_amount?: number;
  };
}

export interface UpdatePermissionsRequest {
  family_member_id: string;
  permissions: {
    can_trade?: boolean;
    can_withdraw?: boolean;
    max_trade_amount?: number;
    requires_approval?: boolean;
  };
}

export interface ApprovalDecisionRequest {
  approval_id: string;
  decision: 'APPROVE' | 'REJECT';
  reason?: string;
}

// Base query with auth
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

export const familyApi = createApi({
  reducerPath: 'familyApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['FamilyMember', 'PendingApproval', 'FamilyInvite', 'FamilySettings'],
  endpoints: (builder) => ({
    // Get all family members
    getFamilyMembers: builder.query<FamilyMember[], void>({
      query: () => '/family/members',
      providesTags: (result) =>
        result
          ? [...result.map(member => ({ type: 'FamilyMember' as const, id: member.id })), 'FamilyMember']
          : ['FamilyMember'],
      keepUnusedDataFor: 60, // Cache for 1 minute
    }),

    // Get specific family member
    getFamilyMember: builder.query<FamilyMember, string>({
      query: (memberId) => `/family/members/${memberId}`,
      providesTags: (result, error, id) => [{ type: 'FamilyMember', id }],
    }),

    // Create family member
    createFamilyMember: builder.mutation<FamilyMember, CreateFamilyMemberRequest>({
      query: (memberData) => ({
        url: '/family/members',
        method: 'POST',
        body: memberData,
      }),
      invalidatesTags: ['FamilyMember'],
    }),

    // Update family member permissions
    updateMemberPermissions: builder.mutation<FamilyMember, UpdatePermissionsRequest>({
      query: ({ family_member_id, permissions }) => ({
        url: `/family/members/${family_member_id}/permissions`,
        method: 'PUT',
        body: permissions,
      }),
      invalidatesTags: (result, error, { family_member_id }) => [
        { type: 'FamilyMember', id: family_member_id },
      ],
    }),

    // Get pending approvals
    getPendingApprovals: builder.query<PendingApproval[], { status?: 'PENDING' | 'ALL' }>({
      query: ({ status = 'PENDING' }) => ({
        url: '/family/approvals',
        params: { status: status !== 'ALL' ? status : undefined },
      }),
      providesTags: (result) =>
        result
          ? [...result.map(approval => ({ type: 'PendingApproval' as const, id: approval.id })), 'PendingApproval']
          : ['PendingApproval'],
      keepUnusedDataFor: 30,
    }),

    // Approve or reject a request
    reviewApproval: builder.mutation<{ success: boolean; message: string }, ApprovalDecisionRequest>({
      query: ({ approval_id, decision, reason }) => ({
        url: `/family/approvals/${approval_id}/review`,
        method: 'POST',
        body: { decision, reason },
      }),
      invalidatesTags: (result, error, { approval_id }) => [
        { type: 'PendingApproval', id: approval_id },
        'PendingApproval',
        'FamilyMember', // Refresh member data as balance may have changed
      ],
    }),

    // Get family invites
    getFamilyInvites: builder.query<FamilyInvite[], void>({
      query: () => '/family/invites',
      providesTags: ['FamilyInvite'],
    }),

    // Send family invite
    sendFamilyInvite: builder.mutation<FamilyInvite, { email: string; role: 'ADULT' | 'TEEN' | 'CHILD' }>({
      query: (inviteData) => ({
        url: '/family/invites',
        method: 'POST',
        body: inviteData,
      }),
      invalidatesTags: ['FamilyInvite'],
    }),

    // Cancel family invite
    cancelInvite: builder.mutation<{ success: boolean }, string>({
      query: (inviteId) => ({
        url: `/family/invites/${inviteId}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: ['FamilyInvite'],
    }),

    // Get family settings
    getFamilySettings: builder.query<FamilySettings, void>({
      query: () => '/family/settings',
      providesTags: ['FamilySettings'],
    }),

    // Update family settings
    updateFamilySettings: builder.mutation<FamilySettings, Partial<FamilySettings>>({
      query: (settings) => ({
        url: '/family/settings',
        method: 'PUT',
        body: settings,
      }),
      invalidatesTags: ['FamilySettings'],
    }),

    // Get member's portfolio details
    getMemberPortfolio: builder.query<{
      portfolio_value: number;
      cash_balance: number;
      positions: Array<{
        symbol: string;
        quantity: number;
        average_cost: number;
        current_value: number;
        pnl: number;
      }>;
      performance: {
        daily_pnl: number;
        monthly_pnl: number;
        total_pnl: number;
      };
    }, string>({
      query: (memberId) => `/family/members/${memberId}/portfolio`,
      providesTags: (result, error, memberId) => [
        { type: 'FamilyMember', id: `${memberId}_portfolio` },
      ],
      keepUnusedDataFor: 60,
    }),

    // Transfer funds between family members
    transferFunds: builder.mutation<{ success: boolean; message: string }, {
      from_member_id: string;
      to_member_id: string;
      amount: number;
      note?: string;
    }>({
      query: (transferData) => ({
        url: '/family/transfer',
        method: 'POST',
        body: transferData,
      }),
      invalidatesTags: ['FamilyMember'],
    }),
  }),
});

export const {
  useGetFamilyMembersQuery,
  useGetFamilyMemberQuery,
  useCreateFamilyMemberMutation,
  useUpdateMemberPermissionsMutation,
  useGetPendingApprovalsQuery,
  useReviewApprovalMutation,
  useGetFamilyInvitesQuery,
  useSendFamilyInviteMutation,
  useCancelInviteMutation,
  useGetFamilySettingsQuery,
  useUpdateFamilySettingsMutation,
  useGetMemberPortfolioQuery,
  useTransferFundsMutation,
  // Lazy queries
  useLazyGetFamilyMembersQuery,
  useLazyGetMemberPortfolioQuery,
} = familyApi;

export default familyApi;
