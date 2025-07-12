import api, { handleApiError } from './api';
import { portfolioCache, generateCacheKey } from '../utils/cacheUtils';

export interface SystemStatus {
  component: string;
  status: 'operational' | 'degraded' | 'outage' | 'maintenance';
  lastUpdated: string;
  message?: string;
}

export interface AlertData {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  timestamp: string;
  message: string;
  source: string;
  acknowledged: boolean;
}

export interface MetricData {
  label: string;
  value: number;
  change?: number;
  direction?: 'up' | 'down' | 'stable';
  unit?: string;
}

export interface AdminDashboardData {
  systemStatuses: SystemStatus[];
  alerts: AlertData[];
  userMetrics: MetricData[];
  financialMetrics: MetricData[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'inactive' | 'pending' | 'suspended' | 'locked';
  role: string;
  verified: boolean;
  createdAt: string;
  lastLogin?: string;
  subscription?: string;
  loginAttempts?: number;
  twoFactorEnabled: boolean;
}

export interface UserListParams {
  search?: string;
  status?: string;
  role?: string;
  verified?: string;
  subscription?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total_items: number;
    total_pages: number;
  };
}

export interface KYCDocument {
  id: string;
  type: 'passport' | 'drivers_license' | 'id_card' | 'residence_proof' | 'selfie';
  fileName: string;
  uploadedAt: string;
  status: 'pending' | 'approved' | 'rejected';
  notes?: string;
}

export interface KYCVerificationRequest {
  id: string;
  userId: string;
  userName: string;
  email: string;
  requestDate: string;
  status: 'pending' | 'in_review' | 'approved' | 'rejected' | 'info_required';
  documents: KYCDocument[];
  priority: 'high' | 'medium' | 'low';
  assignedTo?: string;
  lastUpdated?: string;
  riskScore?: number;
  fraudFlags: string[];
  notes?: string;
}

export interface KYCListParams {
  search?: string;
  status?: string;
  priority?: string;
  dateRange?: string;
  assignedTo?: string;
  page?: number;
  limit?: number;
}

export const adminService = {
  // Dashboard data
  async getDashboardData(forceRefresh = false): Promise<AdminDashboardData> {
    try {
      const cacheKey = generateCacheKey('admin_dashboard');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/admin/dashboard');
      
      // Cache the response data with a short TTL (1 minute)
      portfolioCache.set(cacheKey, response.data, 60);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // System status operations
  async getSystemStatus(forceRefresh = false): Promise<SystemStatus[]> {
    try {
      const cacheKey = generateCacheKey('admin_system_status');
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/admin/system/status');
      portfolioCache.set(cacheKey, response.data, 60); // 1 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Alert operations
  async getAlerts(forceRefresh = false): Promise<AlertData[]> {
    try {
      const cacheKey = generateCacheKey('admin_alerts');
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/admin/alerts');
      portfolioCache.set(cacheKey, response.data, 60); // 1 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async acknowledgeAlert(alertId: string): Promise<void> {
    try {
      await api.post(`/admin/alerts/${alertId}/acknowledge`);
      
      // Clear alert cache since data has changed
      portfolioCache.remove(generateCacheKey('admin_alerts'));
      portfolioCache.remove(generateCacheKey('admin_dashboard'));
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Metric operations
  async getUserMetrics(forceRefresh = false): Promise<MetricData[]> {
    try {
      const cacheKey = generateCacheKey('admin_user_metrics');
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/admin/metrics/users');
      portfolioCache.set(cacheKey, response.data, 300); // 5 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getFinancialMetrics(forceRefresh = false): Promise<MetricData[]> {
    try {
      const cacheKey = generateCacheKey('admin_financial_metrics');
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/admin/metrics/financial');
      portfolioCache.set(cacheKey, response.data, 300); // 5 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // User management operations
  async getUsers(params: UserListParams = {}, forceRefresh = false): Promise<PaginatedResponse<User>> {
    try {
      const cacheKey = generateCacheKey('admin_users', params);
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/admin/users', { params });
      portfolioCache.set(cacheKey, response.data, 120); // 2 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getUserById(userId: string, forceRefresh = false): Promise<User> {
    try {
      const cacheKey = generateCacheKey(`admin_user_${userId}`);
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get(`/admin/users/${userId}`);
      portfolioCache.set(cacheKey, response.data, 120); // 2 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async updateUser(userId: string, updates: Partial<User>): Promise<User> {
    try {
      const response = await api.put(`/admin/users/${userId}`, updates);
      
      // Clear user caches
      portfolioCache.remove(generateCacheKey(`admin_user_${userId}`));
      portfolioCache.remove(generateCacheKey('admin_users'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async lockUser(userId: string): Promise<User> {
    try {
      const response = await api.post(`/admin/users/${userId}/lock`);
      
      // Clear user caches
      portfolioCache.remove(generateCacheKey(`admin_user_${userId}`));
      portfolioCache.remove(generateCacheKey('admin_users'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async unlockUser(userId: string): Promise<User> {
    try {
      const response = await api.post(`/admin/users/${userId}/unlock`);
      
      // Clear user caches
      portfolioCache.remove(generateCacheKey(`admin_user_${userId}`));
      portfolioCache.remove(generateCacheKey('admin_users'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async verifyUser(userId: string): Promise<User> {
    try {
      const response = await api.post(`/admin/users/${userId}/verify`);
      
      // Clear user caches
      portfolioCache.remove(generateCacheKey(`admin_user_${userId}`));
      portfolioCache.remove(generateCacheKey('admin_users'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async deleteUser(userId: string): Promise<void> {
    try {
      await api.delete(`/admin/users/${userId}`);
      
      // Clear user caches
      portfolioCache.remove(generateCacheKey(`admin_user_${userId}`));
      portfolioCache.remove(generateCacheKey('admin_users'));
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async sendEmailToUser(userId: string, subject: string, content: string): Promise<void> {
    try {
      await api.post(`/admin/users/${userId}/email`, { subject, content });
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // KYC verification operations
  async getKYCRequests(params: KYCListParams = {}, forceRefresh = false): Promise<PaginatedResponse<KYCVerificationRequest>> {
    try {
      const cacheKey = generateCacheKey('admin_kyc_requests', params);
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/admin/kyc', { params });
      portfolioCache.set(cacheKey, response.data, 120); // 2 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getKYCRequestById(requestId: string, forceRefresh = false): Promise<KYCVerificationRequest> {
    try {
      const cacheKey = generateCacheKey(`admin_kyc_request_${requestId}`);
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get(`/admin/kyc/${requestId}`);
      portfolioCache.set(cacheKey, response.data, 120); // 2 minute TTL
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async updateKYCRequest(requestId: string, updates: Partial<KYCVerificationRequest>): Promise<KYCVerificationRequest> {
    try {
      const response = await api.put(`/admin/kyc/${requestId}`, updates);
      
      // Clear KYC caches
      portfolioCache.remove(generateCacheKey(`admin_kyc_request_${requestId}`));
      portfolioCache.remove(generateCacheKey('admin_kyc_requests'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async approveKYCRequest(requestId: string, notes?: string): Promise<KYCVerificationRequest> {
    try {
      const response = await api.post(`/admin/kyc/${requestId}/approve`, { notes });
      
      // Clear KYC caches
      portfolioCache.remove(generateCacheKey(`admin_kyc_request_${requestId}`));
      portfolioCache.remove(generateCacheKey('admin_kyc_requests'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async rejectKYCRequest(requestId: string, notes: string): Promise<KYCVerificationRequest> {
    try {
      const response = await api.post(`/admin/kyc/${requestId}/reject`, { notes });
      
      // Clear KYC caches
      portfolioCache.remove(generateCacheKey(`admin_kyc_request_${requestId}`));
      portfolioCache.remove(generateCacheKey('admin_kyc_requests'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async requestAdditionalInfo(requestId: string, notes: string): Promise<KYCVerificationRequest> {
    try {
      const response = await api.post(`/admin/kyc/${requestId}/request-info`, { notes });
      
      // Clear KYC caches
      portfolioCache.remove(generateCacheKey(`admin_kyc_request_${requestId}`));
      portfolioCache.remove(generateCacheKey('admin_kyc_requests'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async approveKYCDocument(requestId: string, documentId: string): Promise<KYCDocument> {
    try {
      const response = await api.post(`/admin/kyc/${requestId}/documents/${documentId}/approve`);
      
      // Clear KYC caches
      portfolioCache.remove(generateCacheKey(`admin_kyc_request_${requestId}`));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async rejectKYCDocument(requestId: string, documentId: string, notes: string): Promise<KYCDocument> {
    try {
      const response = await api.post(`/admin/kyc/${requestId}/documents/${documentId}/reject`, { notes });
      
      // Clear KYC caches
      portfolioCache.remove(generateCacheKey(`admin_kyc_request_${requestId}`));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getKYCDocumentUrl(requestId: string, documentId: string): Promise<string> {
    try {
      const response = await api.get(`/admin/kyc/${requestId}/documents/${documentId}/url`);
      return response.data.url;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // System operations
  async restartService(serviceName: string): Promise<void> {
    try {
      await api.post(`/admin/system/services/${serviceName}/restart`);
      
      // Clear system status cache
      portfolioCache.remove(generateCacheKey('admin_system_status'));
      portfolioCache.remove(generateCacheKey('admin_dashboard'));
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getSystemLogs(service?: string, severity?: string, limit = 100): Promise<any[]> {
    try {
      const params: any = { limit };
      if (service) params.service = service;
      if (severity) params.severity = severity;
      
      const response = await api.get('/admin/system/logs', { params });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getSystemPerformance(): Promise<any> {
    try {
      const response = await api.get('/admin/system/performance');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  }
};

export default adminService;