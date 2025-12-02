import api, { handleApiError } from './api';
import { generateCacheKey } from '../utils/cacheUtils';

// Create a dedicated alerts cache
import { CacheManager } from '../utils/cacheUtils';
const alertsCache = new CacheManager<any>({
  namespace: 'elson_alerts',
  defaultTTL: 2 * 60 * 1000, // 2 minutes
  maxSize: 50
});

export interface AlertCondition {
  type: 'PRICE' | 'VOLUME' | 'INDICATOR';
  operator: '>' | '<' | '=' | '>=' | '<=';
  value: number;
  timeframe?: string;
}

export interface Alert {
  id: string;
  symbol: string;
  conditions: AlertCondition[];
  message: string;
  enabled: boolean;
  repeated: boolean;
  notificationChannels: ('email' | 'push' | 'webhook')[];
  createdAt: string;
  lastTriggered?: string;
}

export const alertsService = {
  async createAlert(data: Omit<Alert, 'id' | 'createdAt' | 'lastTriggered'>): Promise<Alert> {
    try {
      const response = await api.post('/alerts', data);
      
      // Clear alerts list cache since we've added a new alert
      // Use a generic alerts cache key (without params) to clear the default view
      const alertsListCacheKey = generateCacheKey('alerts');
      alertsCache.remove(alertsListCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async updateAlert(id: string, data: Partial<Alert>): Promise<Alert> {
    try {
      const response = await api.put(`/alerts/${id}`, data);
      
      // Clear both the specific alert cache and the alerts list cache
      const alertCacheKey = generateCacheKey(`alert_${id}`);
      const alertsListCacheKey = generateCacheKey('alerts');
      
      alertsCache.remove(alertCacheKey);
      alertsCache.remove(alertsListCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async deleteAlert(id: string): Promise<void> {
    try {
      await api.delete(`/alerts/${id}`);
      
      // Clear both the specific alert cache and the alerts list cache
      const alertCacheKey = generateCacheKey(`alert_${id}`);
      const alertsListCacheKey = generateCacheKey('alerts');
      
      alertsCache.remove(alertCacheKey);
      alertsCache.remove(alertsListCacheKey);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getAlerts(params?: {
    symbol?: string;
    enabled?: boolean;
    type?: AlertCondition['type'];
  }, forceRefresh: boolean = false): Promise<Alert[]> {
    try {
      // Create a cache key based on the parameters
      const cacheParams: Record<string, any> = {};
      if (params) {
        if (params.symbol) cacheParams.symbol = params.symbol;
        if (params.enabled !== undefined) cacheParams.enabled = params.enabled;
        if (params.type) cacheParams.type = params.type;
      }
      
      const cacheKey = generateCacheKey('alerts', cacheParams);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = alertsCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/alerts', { params });
      
      // Cache the response data
      alertsCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getAlert(id: string, forceRefresh: boolean = false): Promise<Alert> {
    try {
      const cacheKey = generateCacheKey(`alert_${id}`);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = alertsCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get(`/alerts/${id}`);
      
      // Cache the response data
      alertsCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async enableAlert(id: string): Promise<Alert> {
    try {
      const response = await api.post(`/alerts/${id}/enable`);
      
      // Clear caches since the alert has changed
      const alertCacheKey = generateCacheKey(`alert_${id}`);
      const alertsListCacheKey = generateCacheKey('alerts');
      const alertsEnabledCacheKey = generateCacheKey('alerts', { enabled: true });
      const alertsDisabledCacheKey = generateCacheKey('alerts', { enabled: false });
      
      alertsCache.remove(alertCacheKey);
      alertsCache.remove(alertsListCacheKey);
      alertsCache.remove(alertsEnabledCacheKey);
      alertsCache.remove(alertsDisabledCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async disableAlert(id: string): Promise<Alert> {
    try {
      const response = await api.post(`/alerts/${id}/disable`);
      
      // Clear caches since the alert has changed
      const alertCacheKey = generateCacheKey(`alert_${id}`);
      const alertsListCacheKey = generateCacheKey('alerts');
      const alertsEnabledCacheKey = generateCacheKey('alerts', { enabled: true });
      const alertsDisabledCacheKey = generateCacheKey('alerts', { enabled: false });
      
      alertsCache.remove(alertCacheKey);
      alertsCache.remove(alertsListCacheKey);
      alertsCache.remove(alertsEnabledCacheKey);
      alertsCache.remove(alertsDisabledCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getAlertHistory(id: string, params?: {
    startTime?: number;
    endTime?: number;
    limit?: number;
  }, forceRefresh: boolean = false): Promise<{
    timestamp: string;
    triggered: boolean;
    value: number;
  }[]> {
    try {
      // Create parameters object for cache key generation
      const cacheParams: Record<string, any> = { id };
      if (params) {
        if (params.startTime) cacheParams.startTime = params.startTime;
        if (params.endTime) cacheParams.endTime = params.endTime;
        if (params.limit) cacheParams.limit = params.limit;
      }
      
      const cacheKey = generateCacheKey('alert_history', cacheParams);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = alertsCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get(`/alerts/${id}/history`, { params });
      
      // Cache the response data
      alertsCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async testAlert(conditions: AlertCondition[], symbol: string): Promise<{
    wouldTrigger: boolean;
    currentValue: number;
    threshold: number;
  }> {
    try {
      const response = await api.post('/alerts/test', { conditions, symbol });
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
};