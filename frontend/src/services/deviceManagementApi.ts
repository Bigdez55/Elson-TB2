import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Base URL for the API (relative path works with proxy in dev, direct in prod)
const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// Device Management Types
export interface DeviceInfo {
  device_id: string;
  device_name: string;
  device_type: 'desktop' | 'mobile' | 'tablet';
  browser: string;
  os: string;
  ip_address: string;
  location?: {
    city?: string;
    country?: string;
    timezone?: string;
  };
  is_trusted: boolean;
  is_current: boolean;
  last_used: string;
  created_at: string;
  permissions: string[];
}

export interface SecuritySession {
  session_id: string;
  device_id: string;
  device_info: Pick<DeviceInfo, 'device_name' | 'device_type' | 'browser' | 'os'>;
  ip_address: string;
  location?: {
    city?: string;
    country?: string;
  };
  is_current: boolean;
  created_at: string;
  last_activity: string;
  expires_at: string;
}

export interface TwoFactorConfig {
  is_enabled: boolean;
  methods: Array<{
    type: 'sms' | 'email' | 'totp' | 'hardware_key';
    identifier: string; // phone number, email, or key name
    is_primary: boolean;
    verified: boolean;
    created_at: string;
  }>;
  backup_codes_count: number;
  last_used?: string;
}

export interface LoginAttempt {
  id: string;
  ip_address: string;
  device_fingerprint: string;
  location?: {
    city?: string;
    country?: string;
  };
  success: boolean;
  failure_reason?: string;
  timestamp: string;
  blocked: boolean;
}

export interface SecurityAlert {
  id: string;
  type: 'suspicious_login' | 'new_device' | 'unusual_activity' | 'security_violation';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  device_id?: string;
  ip_address?: string;
  location?: string;
  is_read: boolean;
  created_at: string;
  expires_at?: string;
}

export interface DeviceRegistrationRequest {
  device_name: string;
  device_fingerprint: string;
  permissions_requested: string[];
}

export interface DeviceVerificationRequest {
  device_id: string;
  verification_code: string;
  trust_device: boolean;
}

export interface SessionTerminationRequest {
  session_ids?: string[];
  terminate_all?: boolean;
  exclude_current?: boolean;
}

// Security Settings
export interface SecuritySettings {
  require_2fa: boolean;
  require_2fa_for_trading: boolean;
  session_timeout_minutes: number;
  max_concurrent_sessions: number;
  ip_whitelist_enabled: boolean;
  ip_whitelist: string[];
  device_trust_duration_days: number;
  login_attempt_limit: number;
  security_notifications: {
    email: boolean;
    sms: boolean;
    in_app: boolean;
  };
  geolocation_restrictions: {
    enabled: boolean;
    allowed_countries: string[];
  };
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

// Device Management API slice
export const deviceManagementApi = createApi({
  reducerPath: 'deviceManagementApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: [
    'Device', 
    'Session', 
    'SecuritySettings', 
    'TwoFactorConfig', 
    'LoginHistory', 
    'SecurityAlerts'
  ],
  endpoints: (builder) => ({
    // Device Management
    getDevices: builder.query<DeviceInfo[], void>({
      query: () => '/security/devices',
      providesTags: ['Device'],
    }),

    getCurrentDevice: builder.query<DeviceInfo, void>({
      query: () => '/security/devices/current',
      providesTags: (result) => result ? [{ type: 'Device', id: result.device_id }] : ['Device'],
    }),

    registerDevice: builder.mutation<{ device_id: string; requires_verification: boolean }, DeviceRegistrationRequest>({
      query: (deviceData) => ({
        url: '/security/devices/register',
        method: 'POST',
        body: deviceData,
      }),
      invalidatesTags: ['Device'],
    }),

    verifyDevice: builder.mutation<{ success: boolean; message: string }, DeviceVerificationRequest>({
      query: (verificationData) => ({
        url: '/security/devices/verify',
        method: 'POST',
        body: verificationData,
      }),
      invalidatesTags: ['Device'],
    }),

    trustDevice: builder.mutation<{ success: boolean }, { device_id: string }>({
      query: ({ device_id }) => ({
        url: `/security/devices/${device_id}/trust`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, { device_id }) => [
        'Device',
        { type: 'Device', id: device_id },
      ],
    }),

    revokeDevice: builder.mutation<{ success: boolean }, { device_id: string }>({
      query: ({ device_id }) => ({
        url: `/security/devices/${device_id}/revoke`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Device', 'Session'],
    }),

    updateDeviceName: builder.mutation<DeviceInfo, { device_id: string; name: string }>({
      query: ({ device_id, name }) => ({
        url: `/security/devices/${device_id}/name`,
        method: 'PATCH',
        body: { device_name: name },
      }),
      invalidatesTags: (result, error, { device_id }) => [
        'Device',
        { type: 'Device', id: device_id },
      ],
    }),

    // Session Management
    getSessions: builder.query<SecuritySession[], void>({
      query: () => '/security/sessions',
      providesTags: ['Session'],
    }),

    terminateSessions: builder.mutation<{ terminated_count: number }, SessionTerminationRequest>({
      query: (terminationData) => ({
        url: '/security/sessions/terminate',
        method: 'POST',
        body: terminationData,
      }),
      invalidatesTags: ['Session'],
    }),

    extendSession: builder.mutation<{ new_expires_at: string }, { session_id?: string }>({
      query: (data) => ({
        url: '/security/sessions/extend',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Session'],
    }),

    // Two-Factor Authentication
    getTwoFactorConfig: builder.query<TwoFactorConfig, void>({
      query: () => '/security/2fa',
      providesTags: ['TwoFactorConfig'],
    }),

    enable2FA: builder.mutation<{ qr_code?: string; backup_codes?: string[] }, { method: string; identifier?: string }>({
      query: (data) => ({
        url: '/security/2fa/enable',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['TwoFactorConfig'],
    }),

    verify2FA: builder.mutation<{ success: boolean; backup_codes?: string[] }, { code: string; method: string }>({
      query: (data) => ({
        url: '/security/2fa/verify',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['TwoFactorConfig'],
    }),

    disable2FA: builder.mutation<{ success: boolean }, { verification_code: string; method: string }>({
      query: (data) => ({
        url: '/security/2fa/disable',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['TwoFactorConfig'],
    }),

    regenerateBackupCodes: builder.mutation<{ backup_codes: string[] }, { verification_code: string }>({
      query: (data) => ({
        url: '/security/2fa/backup-codes/regenerate',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['TwoFactorConfig'],
    }),

    // Security Settings
    getSecuritySettings: builder.query<SecuritySettings, void>({
      query: () => '/security/settings',
      providesTags: ['SecuritySettings'],
    }),

    updateSecuritySettings: builder.mutation<SecuritySettings, Partial<SecuritySettings>>({
      query: (settings) => ({
        url: '/security/settings',
        method: 'PATCH',
        body: settings,
      }),
      invalidatesTags: ['SecuritySettings'],
    }),

    // Login History and Monitoring
    getLoginHistory: builder.query<LoginAttempt[], { limit?: number; days?: number }>({
      query: ({ limit = 50, days = 30 } = {}) => 
        `/security/login-history?limit=${limit}&days=${days}`,
      providesTags: ['LoginHistory'],
    }),

    getSecurityAlerts: builder.query<SecurityAlert[], { unread_only?: boolean }>({
      query: ({ unread_only = false } = {}) => 
        `/security/alerts${unread_only ? '?unread_only=true' : ''}`,
      providesTags: ['SecurityAlerts'],
    }),

    markAlertAsRead: builder.mutation<{ success: boolean }, { alert_id: string }>({
      query: ({ alert_id }) => ({
        url: `/security/alerts/${alert_id}/read`,
        method: 'POST',
      }),
      invalidatesTags: ['SecurityAlerts'],
    }),

    dismissAlert: builder.mutation<{ success: boolean }, { alert_id: string }>({
      query: ({ alert_id }) => ({
        url: `/security/alerts/${alert_id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['SecurityAlerts'],
    }),

    // IP Whitelist Management
    addIPToWhitelist: builder.mutation<{ success: boolean }, { ip_address: string; description?: string }>({
      query: (data) => ({
        url: '/security/ip-whitelist',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['SecuritySettings'],
    }),

    removeIPFromWhitelist: builder.mutation<{ success: boolean }, { ip_address: string }>({
      query: ({ ip_address }) => ({
        url: `/security/ip-whitelist/${encodeURIComponent(ip_address)}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['SecuritySettings'],
    }),

    // Emergency Security Actions
    lockAccount: builder.mutation<{ success: boolean }, { reason: string }>({
      query: (data) => ({
        url: '/security/emergency/lock-account',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Session', 'SecuritySettings'],
    }),

    reportSuspiciousActivity: builder.mutation<{ success: boolean }, {
      activity_type: string;
      description: string;
      related_session_id?: string;
      related_device_id?: string;
    }>({
      query: (data) => ({
        url: '/security/report-suspicious',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['SecurityAlerts'],
    }),

    // Device Fingerprinting
    generateDeviceFingerprint: builder.query<{ fingerprint: string; confidence: number }, void>({
      query: () => '/security/device-fingerprint',
    }),

    // Security Audit
    getSecurityAuditLog: builder.query<Array<{
      id: string;
      action: string;
      resource: string;
      user_agent: string;
      ip_address: string;
      result: 'success' | 'failure';
      timestamp: string;
      details?: Record<string, any>;
    }>, { limit?: number; days?: number }>({
      query: ({ limit = 100, days = 30 } = {}) => 
        `/security/audit?limit=${limit}&days=${days}`,
    }),
  }),
});

// Export hooks
export const {
  // Device Management
  useGetDevicesQuery,
  useGetCurrentDeviceQuery,
  useRegisterDeviceMutation,
  useVerifyDeviceMutation,
  useTrustDeviceMutation,
  useRevokeDeviceMutation,
  useUpdateDeviceNameMutation,
  
  // Session Management
  useGetSessionsQuery,
  useTerminateSessionsMutation,
  useExtendSessionMutation,
  
  // Two-Factor Authentication
  useGetTwoFactorConfigQuery,
  useEnable2FAMutation,
  useVerify2FAMutation,
  useDisable2FAMutation,
  useRegenerateBackupCodesMutation,
  
  // Security Settings
  useGetSecuritySettingsQuery,
  useUpdateSecuritySettingsMutation,
  
  // Login History and Monitoring
  useGetLoginHistoryQuery,
  useGetSecurityAlertsQuery,
  useMarkAlertAsReadMutation,
  useDismissAlertMutation,
  
  // IP Whitelist
  useAddIPToWhitelistMutation,
  useRemoveIPFromWhitelistMutation,
  
  // Emergency Actions
  useLockAccountMutation,
  useReportSuspiciousActivityMutation,
  
  // Device Fingerprinting
  useGenerateDeviceFingerprintQuery,
  
  // Security Audit
  useGetSecurityAuditLogQuery,
} = deviceManagementApi;

// Export the reducer to add to the store
export default deviceManagementApi;