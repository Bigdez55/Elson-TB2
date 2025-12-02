import api, { handleApiError } from './api';
import { generateCacheKey } from '../utils/cacheUtils';

// Create a dedicated settings cache
import { CacheManager } from '../utils/cacheUtils';
const settingsCache = new CacheManager<any>({
  namespace: 'elson_settings',
  defaultTTL: 10 * 60 * 1000, // 10 minutes
  maxSize: 20
});

export interface TradingSettings {
  defaultLeverage: number;
  riskPerTrade: number;
  maxDrawdown: number;
  stopLossType: 'fixed' | 'trailing' | 'none';
  takeProfitType: 'fixed' | 'trailing' | 'none';
  stopLossValue: number;
  takeProfitValue: number;
  tradingEnabled: boolean;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  telegram: boolean;
  orderNotifications: boolean;
  tradeNotifications: boolean;
  alertNotifications: boolean;
  marketingNotifications: boolean;
}

export interface UISettings {
  theme: 'light' | 'dark';
  chartType: 'candlestick' | 'line';
  defaultTimeframe: string;
  showOrderBook: boolean;
  showTrades: boolean;
  layout: 'default' | 'compact' | 'advanced';
}

export interface APIKeySettings {
  id: string;
  name: string;
  key: string;
  permissions: string[];
  createdAt: string;
  lastUsed: string;
}

export const settingsService = {
  async getTradingSettings(forceRefresh: boolean = false): Promise<TradingSettings> {
    try {
      const cacheKey = generateCacheKey('trading_settings');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = settingsCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/settings/trading');
      
      // Cache the response data
      settingsCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async updateTradingSettings(settings: Partial<TradingSettings>): Promise<TradingSettings> {
    try {
      const response = await api.put('/settings/trading', settings);
      
      // Clear the cache since we've updated the settings
      const cacheKey = generateCacheKey('trading_settings');
      settingsCache.remove(cacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getNotificationSettings(forceRefresh: boolean = false): Promise<NotificationSettings> {
    try {
      const cacheKey = generateCacheKey('notification_settings');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = settingsCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/settings/notifications');
      
      // Cache the response data
      settingsCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async updateNotificationSettings(settings: Partial<NotificationSettings>): Promise<NotificationSettings> {
    try {
      const response = await api.put('/settings/notifications', settings);
      
      // Clear the cache since we've updated the settings
      const cacheKey = generateCacheKey('notification_settings');
      settingsCache.remove(cacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getUISettings(forceRefresh: boolean = false): Promise<UISettings> {
    try {
      const cacheKey = generateCacheKey('ui_settings');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = settingsCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/settings/ui');
      
      // Cache the response data
      settingsCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async updateUISettings(settings: Partial<UISettings>): Promise<UISettings> {
    try {
      const response = await api.put('/settings/ui', settings);
      
      // Clear the cache since we've updated the settings
      const cacheKey = generateCacheKey('ui_settings');
      settingsCache.remove(cacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getAPIKeys(forceRefresh: boolean = false): Promise<APIKeySettings[]> {
    try {
      const cacheKey = generateCacheKey('api_keys');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = settingsCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/settings/api-keys');
      
      // Cache the response data
      settingsCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async createAPIKey(name: string, permissions: string[]): Promise<APIKeySettings> {
    try {
      const response = await api.post('/settings/api-keys', { name, permissions });
      
      // Clear the API keys cache
      const apiKeysCache = generateCacheKey('api_keys');
      settingsCache.remove(apiKeysCache);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async deleteAPIKey(id: string): Promise<void> {
    try {
      await api.delete(`/settings/api-keys/${id}`);
      
      // Clear the API keys cache
      const apiKeysCache = generateCacheKey('api_keys');
      settingsCache.remove(apiKeysCache);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async updateAPIKeyPermissions(id: string, permissions: string[]): Promise<APIKeySettings> {
    try {
      const response = await api.put(`/settings/api-keys/${id}/permissions`, { permissions });
      
      // Clear the API keys cache
      const apiKeysCache = generateCacheKey('api_keys');
      settingsCache.remove(apiKeysCache);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async verifyTelegramBot(token: string): Promise<boolean> {
    try {
      const response = await api.post('/settings/verify-telegram', { token });
      return response.data.success;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async exportSettings(): Promise<any> {
    try {
      const response = await api.get('/settings/export');
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async importSettings(settings: any): Promise<void> {
    try {
      await api.post('/settings/import', settings);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async resetSettings(): Promise<void> {
    try {
      await api.post('/settings/reset');
      
      // Clear all settings caches
      settingsCache.clear();
    } catch (error) {
      throw handleApiError(error);
    }
  },
};