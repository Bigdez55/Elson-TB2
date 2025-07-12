import api, { handleApiError } from './api';
import { 
  marketDataCache, 
  companyProfileCache, 
  historicalDataCache, 
  generateCacheKey 
} from '../utils/cacheUtils';

export interface StockQuote {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  open: number;
  high: number;
  low: number;
  prev_close: number;
  timestamp: string;
  source: string;
}

export interface HistoricalDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface HistoricalData {
  symbol: string;
  interval: string;
  data: HistoricalDataPoint[];
  provider?: string;
}

export interface CompanyProfile {
  symbol: string;
  name: string;
  description: string;
  sector: string;
  industry: string;
  employees: number;
  website: string;
  marketCap: number;
  peRatio: number;
  dividendYield: number;
  fiftyTwoWeekHigh: number;
  fiftyTwoWeekLow: number;
  address: string;
  country: string;
  phone: string;
  ceo: string;
  exchange: string;
  currency: string;
  [key: string]: any;  // For any additional fields
}

export interface ProviderHealth {
  alpha_vantage: {
    healthy: boolean;
    consecutive_failures: number;
    last_checked: number;
  };
  finnhub: {
    healthy: boolean;
    consecutive_failures: number;
    last_checked: number;
  };
  fmp: {
    healthy: boolean;
    consecutive_failures: number;
    last_checked: number;
  };
  [key: string]: {
    healthy: boolean;
    consecutive_failures: number;
    last_checked: number;
  };
}

const marketService = {
  /**
   * Get real-time quote for a stock symbol
   */
  async getQuote(symbol: string, forceRefresh = false): Promise<StockQuote> {
    try {
      // Generate a cache key for this request
      const cacheKey = generateCacheKey(`quote_${symbol}`);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = marketDataCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get(`/market-data/quote/${symbol}`, {
        params: { force_refresh: forceRefresh }
      });
      
      // Cache the response data
      marketDataCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get quotes for multiple symbols
   */
  async getBatchQuotes(symbols: string[], forceRefresh = false): Promise<Record<string, StockQuote>> {
    try {
      // Sort symbols to ensure consistent cache keys regardless of order
      const sortedSymbols = [...symbols].sort();
      const cacheKey = generateCacheKey('batch_quotes', { symbols: sortedSymbols.join(',') });
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = marketDataCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.post('/market-data/batch-quotes', {
        symbols,
        force_refresh: forceRefresh
      });
      
      // Cache the response data
      marketDataCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  /**
   * Get historical data for a stock symbol
   */
  async getHistoricalData(
    symbol: string,
    startDate: string,
    endDate?: string,
    interval = '1d'
  ): Promise<HistoricalData> {
    try {
      // Generate cache key with all parameters
      const cacheKey = generateCacheKey(`historical_${symbol}`, {
        start_date: startDate,
        end_date: endDate,
        interval: interval
      });
      
      // Historical data can be cached longer, check cache first
      const cachedData = historicalDataCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // If not in cache, fetch from API
      const response = await api.get(`/market-data/historical/${symbol}`, {
        params: {
          start_date: startDate,
          end_date: endDate,
          interval: interval
        }
      });
      
      // Cache the response data
      historicalDataCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  /**
   * Get historical data directly from external API
   */
  async getExternalHistoricalData(
    symbol: string,
    startDate: string,
    endDate?: string,
    interval = 'daily'
  ): Promise<HistoricalData> {
    try {
      // Generate cache key for external historical data
      const cacheKey = generateCacheKey(`external_historical_${symbol}`, {
        start_date: startDate,
        end_date: endDate,
        interval: interval
      });
      
      // Check cache first
      const cachedData = historicalDataCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // If not in cache, fetch from API
      const response = await api.get(`/market-data/external/historical/${symbol}`, {
        params: {
          start_date: startDate,
          end_date: endDate,
          interval: interval
        }
      });
      
      // Cache the response data
      historicalDataCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  /**
   * Get real-time quote directly from external API
   */
  async getExternalQuote(symbol: string): Promise<StockQuote> {
    try {
      // Generate cache key for external quote
      const cacheKey = generateCacheKey(`external_quote_${symbol}`);
      
      // Check cache first - shorter TTL for external quotes
      const cachedData = marketDataCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // If not in cache, fetch from API
      const response = await api.get(`/market-data/external/quote/${symbol}`);
      
      // Cache the response data
      marketDataCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  /**
   * Get company profile directly from external API
   */
  async getCompanyProfile(symbol: string): Promise<CompanyProfile> {
    try {
      // Generate cache key for company profile
      const cacheKey = generateCacheKey(`company_profile_${symbol}`);
      
      // Company profiles can be cached for longer periods
      const cachedData = companyProfileCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // If not in cache, fetch from API
      const response = await api.get(`/market-data/external/company/${symbol}`);
      
      // Cache the response data
      companyProfileCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  /**
   * Get market hours status
   */
  async getMarketHours(market = 'US'): Promise<{ is_open: boolean; next_open?: string; next_close?: string }> {
    try {
      // Generate cache key for market hours
      const cacheKey = generateCacheKey(`market_hours_${market}`);
      
      // Check cache first - market hours change infrequently during trading days
      const cachedData = marketDataCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // If not in cache, fetch from API
      const response = await api.get('/market-data/hours', {
        params: { market }
      });
      
      // Cache with a custom TTL of 5 minutes
      // This ensures we don't miss market open/close events
      marketDataCache.set(cacheKey, response.data, 5 * 60 * 1000);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  /**
   * Get health status of all data providers
   */
  async getProviderHealth(): Promise<ProviderHealth> {
    try {
      // Generate cache key for provider health
      const cacheKey = 'provider_health';
      
      // Check cache first - provider status changes infrequently
      const cachedData = marketDataCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // If not in cache, fetch from API
      const response = await api.get('/market-data/providers/health');
      
      // Cache with a custom TTL of 2 minutes
      // This ensures we detect provider issues in a timely manner
      marketDataCache.set(cacheKey, response.data, 2 * 60 * 1000);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  /**
   * Get list of available data providers
   */
  async getAvailableProviders(): Promise<string[]> {
    try {
      // Generate cache key for available providers
      const cacheKey = 'available_providers';
      
      // Check cache first - provider list changes very infrequently
      const cachedData = marketDataCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // If not in cache, fetch from API
      const response = await api.get('/market-data/providers/available');
      
      // Cache with a custom TTL of 1 hour - provider list rarely changes
      marketDataCache.set(cacheKey, response.data.providers, 60 * 60 * 1000);
      
      return response.data.providers;
    } catch (error) {
      throw handleApiError(error);
    }
  }
};

export default marketService;