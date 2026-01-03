/**
 * Education API Service - RTK Query
 * Handles educational content, learning paths, user progress, and trading permissions
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Use relative URL for production compatibility - the proxy handles routing in dev
const API_URL = process.env.REACT_APP_API_URL || '/api/v1';

// ==================== Type Definitions ====================

export interface EducationalContent {
  id: number;
  title: string;
  slug: string;
  description: string | null;
  content_type: 'MODULE' | 'QUIZ' | 'ARTICLE' | 'INTERACTIVE' | 'VIDEO';
  level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
  completion_requirement: 'NONE' | 'QUIZ' | 'TIME' | 'INTERACTION';
  estimated_minutes: number | null;
  min_age: number | null;
  max_age: number | null;
  importance_level: number | null;
  content_path: string | null;
  associated_quiz_id: number | null;
  passing_score: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface UserProgress {
  id: number;
  user_id: number;
  content_id: number;
  is_started: boolean;
  is_completed: boolean;
  progress_percent: number;
  score: number | null;
  passed: boolean | null;
  attempts: number;
  time_spent_seconds: number;
  last_accessed: string | null;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface ContentWithProgress extends EducationalContent {
  user_progress: UserProgress | null;
}

export interface LearningPathItem {
  id: number;
  learning_path_id: number;
  content_id: number;
  order: number;
  is_required: boolean;
}

export interface LearningPath {
  id: number;
  title: string;
  slug: string;
  description: string | null;
  min_age: number | null;
  max_age: number | null;
  created_at: string | null;
  updated_at: string | null;
  items: LearningPathItem[];
}

export interface LearningPathWithProgress extends LearningPath {
  completion_percent: number;
  items_completed: number;
  total_items: number;
}

export interface TradingPermission {
  id: number;
  name: string;
  description: string | null;
  permission_type: string;
  requires_guardian_approval: boolean;
  min_age: number | null;
  required_learning_path_id: number | null;
  required_content_id: number | null;
  required_score: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface UserPermission {
  id: number;
  user_id: number;
  permission_id: number;
  is_granted: boolean;
  granted_by_user_id: number | null;
  override_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
  granted_at: string | null;
}

export interface PermissionCheckResponse {
  is_granted: boolean;
  is_eligible: boolean;
  permission: TradingPermission;
  missing_requirements: string[];
  completed_requirements: string[];
}

export interface ProgressUpdateRequest {
  is_started?: boolean;
  is_completed?: boolean;
  progress_percent?: number;
  score?: number;
  passed?: boolean;
  attempts?: number;
  time_spent_seconds?: number;
}

// ==================== API Service ====================

export const educationApi = createApi({
  reducerPath: 'educationApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_URL}/education`,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Content', 'Progress', 'LearningPath', 'Permission', 'UserPermission'],
  endpoints: (builder) => ({
    // ==================== Educational Content ====================

    listContent: builder.query<EducationalContent[], {
      content_type?: string;
      level?: string;
      skip?: number;
      limit?: number;
    }>({
      query: (params) => ({
        url: '/content',
        params: {
          content_type: params.content_type,
          level: params.level,
          skip: params.skip || 0,
          limit: params.limit || 100,
        },
      }),
      providesTags: ['Content'],
    }),

    getContent: builder.query<ContentWithProgress, number>({
      query: (contentId) => `/content/${contentId}`,
      providesTags: (result, error, contentId) => [
        { type: 'Content', id: contentId },
        { type: 'Progress', id: contentId },
      ],
    }),

    // ==================== User Progress ====================

    getMyProgress: builder.query<UserProgress[], void>({
      query: () => '/progress',
      providesTags: ['Progress'],
    }),

    getContentProgress: builder.query<UserProgress, number>({
      query: (contentId) => `/progress/${contentId}`,
      providesTags: (result, error, contentId) => [
        { type: 'Progress', id: contentId },
      ],
    }),

    updateProgress: builder.mutation<UserProgress, {
      contentId: number;
      progress: ProgressUpdateRequest;
    }>({
      query: ({ contentId, progress }) => ({
        url: `/progress/${contentId}`,
        method: 'PUT',
        body: progress,
      }),
      invalidatesTags: (result, error, { contentId }) => [
        { type: 'Progress', id: contentId },
        'Progress',
        { type: 'Content', id: contentId },
        'UserPermission', // May unlock permissions
      ],
    }),

    // ==================== Learning Paths ====================

    listLearningPaths: builder.query<LearningPath[], {
      skip?: number;
      limit?: number;
    }>({
      query: (params) => ({
        url: '/paths',
        params: {
          skip: params.skip || 0,
          limit: params.limit || 100,
        },
      }),
      providesTags: ['LearningPath'],
    }),

    getLearningPath: builder.query<LearningPathWithProgress, number>({
      query: (pathId) => `/paths/${pathId}`,
      providesTags: (result, error, pathId) => [
        { type: 'LearningPath', id: pathId },
      ],
    }),

    // ==================== Trading Permissions ====================

    listPermissions: builder.query<TradingPermission[], void>({
      query: () => '/permissions',
      providesTags: ['Permission'],
    }),

    getMyPermissions: builder.query<UserPermission[], void>({
      query: () => '/permissions/my',
      providesTags: ['UserPermission'],
    }),

    checkPermission: builder.query<PermissionCheckResponse, number>({
      query: (permissionId) => `/permissions/${permissionId}/check`,
      providesTags: (result, error, permissionId) => [
        { type: 'Permission', id: permissionId },
        'UserPermission',
      ],
    }),

    grantPermissionToSelf: builder.mutation<UserPermission, number>({
      query: (permissionId) => ({
        url: `/permissions/${permissionId}/grant`,
        method: 'POST',
      }),
      invalidatesTags: ['UserPermission'],
    }),
  }),
});

// Export hooks for usage in components
export const {
  useListContentQuery,
  useGetContentQuery,
  useGetMyProgressQuery,
  useGetContentProgressQuery,
  useUpdateProgressMutation,
  useListLearningPathsQuery,
  useGetLearningPathQuery,
  useListPermissionsQuery,
  useGetMyPermissionsQuery,
  useCheckPermissionQuery,
  useGrantPermissionToSelfMutation,
} = educationApi;
