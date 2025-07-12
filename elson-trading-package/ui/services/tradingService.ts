import api, { handleApiError } from './api';
import type { Order, Trade, Position, RecurringInvestment, RoundupTransaction, RoundupSummary } from '../types';
import { portfolioCache, generateCacheKey } from '../utils/cacheUtils';

export interface PlaceOrderParams {
  symbol: string;
  type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
  side: 'BUY' | 'SELL';
  amount: number;
  price?: number;
  stopPrice?: number;
}

export interface RecurringInvestmentParams {
  symbol: string;
  portfolio_id: string | number;
  investment_amount: number;
  trade_type: string;
  frequency: string;
  start_date?: string;
  end_date?: string;
  description?: string;
}

export const tradingService = {
  // Order operations
  async placeOrder(params: PlaceOrderParams): Promise<Order> {
    try {
      const response = await api.post('/trading/orders', params);
      
      // This will potentially affect positions and portfolio data
      // Clear related caches since the data may change shortly
      const positionsCacheKey = generateCacheKey('positions');
      const portfolioCacheKey = generateCacheKey('portfolio');
      
      portfolioCache.remove(positionsCacheKey);
      portfolioCache.remove(portfolioCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async cancelOrder(orderId: string): Promise<void> {
    try {
      await api.delete(`/trading/orders/${orderId}`);
      
      // Orders list will change
      const ordersKey = generateCacheKey('orders');
      portfolioCache.remove(ordersKey);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getOrders(params?: {
    symbol?: string;
    status?: 'OPEN' | 'CLOSED' | 'CANCELED';
    limit?: number;
    offset?: number;
  }, forceRefresh = false): Promise<{ orders: Order[]; total: number }> {
    try {
      // Create parameters object for cache key generation
      const cacheParams: Record<string, any> = {};
      if (params) {
        if (params.symbol) cacheParams.symbol = params.symbol;
        if (params.status) cacheParams.status = params.status;
        if (params.limit) cacheParams.limit = params.limit;
        if (params.offset) cacheParams.offset = params.offset;
      }
      
      const cacheKey = generateCacheKey('orders', cacheParams);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/trading/orders', { params });
      
      // Cache the response data
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Trade operations
  async getTrades(params?: {
    symbol?: string;
    startTime?: number;
    endTime?: number;
    limit?: number;
    offset?: number;
  }, forceRefresh = false): Promise<{ trades: Trade[]; total: number }> {
    try {
      // Create parameters object for cache key generation
      const cacheParams: Record<string, any> = {};
      if (params) {
        if (params.symbol) cacheParams.symbol = params.symbol;
        if (params.startTime) cacheParams.startTime = params.startTime;
        if (params.endTime) cacheParams.endTime = params.endTime;
        if (params.limit) cacheParams.limit = params.limit;
        if (params.offset) cacheParams.offset = params.offset;
      }
      
      const cacheKey = generateCacheKey('trades', cacheParams);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/trading/trades', { params });
      
      // Cache the response data
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Position operations
  async getPositions(forceRefresh = false): Promise<Position[]> {
    try {
      const cacheKey = generateCacheKey('positions');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/trading/positions');
      
      // Cache the response data with default TTL
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async closePosition(symbol: string): Promise<void> {
    try {
      await api.post(`/trading/positions/${symbol}/close`);
      
      // Clear positions and portfolio cache since data has changed
      const positionsCacheKey = generateCacheKey('positions');
      const portfolioCacheKey = generateCacheKey('portfolio');
      
      portfolioCache.remove(positionsCacheKey);
      portfolioCache.remove(portfolioCacheKey);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Portfolio operations
  async getPortfolio(forceRefresh = false): Promise<{
    balance: number;
    positions: Position[];
    totalValue: number;
    dailyPnL: number;
  }> {
    try {
      const cacheKey = generateCacheKey('portfolio');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/trading/portfolio');
      
      // Cache the response data with default TTL (1 minute as configured in cacheUtils.ts)
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Performance metrics
  async getPerformanceMetrics(timeframe = '24h', forceRefresh = false): Promise<{
    winRate: number;
    profitFactor: number;
    totalTrades: number;
    averageWin: number;
    averageLoss: number;
    largestWin: number;
    largestLoss: number;
    dailyPnL: number[];
  }> {
    try {
      const cacheKey = generateCacheKey('performance_metrics', { timeframe });
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/trading/performance', {
        params: { timeframe },
      });
      
      // Cache the response data with default TTL
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Risk management
  async getRiskMetrics(symbol: string, forceRefresh = false): Promise<{
    maxDrawdown: number;
    sharpeRatio: number;
    volatility: number;
    exposureRatio: number;
  }> {
    try {
      const cacheKey = generateCacheKey(`risk_metrics_${symbol}`);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get(`/trading/risk/${symbol}`);
      
      // Cache the response data
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Strategy operations
  async executeStrategy(strategyId: string, params: any): Promise<void> {
    try {
      await api.post(`/trading/strategies/${strategyId}/execute`, params);
      
      // Executing a strategy may affect performance metrics
      const strategyPerfCacheKey = generateCacheKey(`strategy_performance_${strategyId}`);
      portfolioCache.remove(strategyPerfCacheKey);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async stopStrategy(strategyId: string): Promise<void> {
    try {
      await api.post(`/trading/strategies/${strategyId}/stop`);
      
      // Stopping a strategy may affect performance metrics
      const strategyPerfCacheKey = generateCacheKey(`strategy_performance_${strategyId}`);
      portfolioCache.remove(strategyPerfCacheKey);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getStrategyPerformance(strategyId: string, forceRefresh = false): Promise<{
    returns: number;
    trades: number;
    winRate: number;
    profitFactor: number;
  }> {
    try {
      const cacheKey = generateCacheKey(`strategy_performance_${strategyId}`);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get(`/trading/strategies/${strategyId}/performance`);
      
      // Cache the response data
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  // Recurring investment operations
  async createRecurringInvestment(params: RecurringInvestmentParams): Promise<RecurringInvestment> {
    try {
      const response = await api.post('/api/v1/investments/recurring', params);
      
      // Clear the recurring investments cache since the data has changed
      const allInvestmentsCacheKey = generateCacheKey('recurring_investments');
      portfolioCache.remove(allInvestmentsCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getRecurringInvestments(forceRefresh = false): Promise<RecurringInvestment[]> {
    try {
      const cacheKey = generateCacheKey('recurring_investments');
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get('/api/v1/investments/recurring');
      
      // Cache the response data
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async getRecurringInvestmentById(id: string | number, forceRefresh = false): Promise<RecurringInvestment> {
    try {
      const cacheKey = generateCacheKey(`recurring_investment_${id}`);
      
      // Check cache first if not forcing refresh
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      // If not in cache or force refresh, fetch from API
      const response = await api.get(`/api/v1/investments/recurring/${id}`);
      
      // Cache the response data
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async updateRecurringInvestment(id: string | number, updates: Partial<RecurringInvestmentParams>): Promise<RecurringInvestment> {
    try {
      const response = await api.put(`/api/v1/investments/recurring/${id}`, updates);
      
      // Clear related caches since the data has changed
      const singleInvestmentCacheKey = generateCacheKey(`recurring_investment_${id}`);
      const allInvestmentsCacheKey = generateCacheKey('recurring_investments');
      
      portfolioCache.remove(singleInvestmentCacheKey);
      portfolioCache.remove(allInvestmentsCacheKey);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
  
  async cancelRecurringInvestment(id: string | number): Promise<void> {
    try {
      await api.delete(`/api/v1/investments/recurring/${id}`);
      
      // Clear related caches since the data has changed
      const singleInvestmentCacheKey = generateCacheKey(`recurring_investment_${id}`);
      const allInvestmentsCacheKey = generateCacheKey('recurring_investments');
      
      portfolioCache.remove(singleInvestmentCacheKey);
      portfolioCache.remove(allInvestmentsCacheKey);
    } catch (error) {
      throw handleApiError(error);
    }
  },

  // Micro-investing and roundup operations
  async getRoundupTransactions(
    params?: {
      status?: string;
      startDate?: string;
      endDate?: string;
      limit?: number;
      offset?: number;
    }, 
    forceRefresh = false
  ): Promise<{ transactions: RoundupTransaction[]; total: number }> {
    try {
      const cacheKey = generateCacheKey('roundup_transactions', params);
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/api/v1/micro-invest/roundups', { params });
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async getRoundupSummary(forceRefresh = false): Promise<RoundupSummary> {
    try {
      const cacheKey = generateCacheKey('roundup_summary');
      
      if (!forceRefresh) {
        const cachedData = portfolioCache.get(cacheKey);
        if (cachedData) {
          return cachedData;
        }
      }
      
      const response = await api.get('/api/v1/micro-invest/roundups/summary');
      portfolioCache.set(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  async investPendingRoundups(): Promise<{ tradeId: number; totalAmount: number }> {
    try {
      const response = await api.post('/api/v1/micro-invest/roundups/invest');
      
      // Clear caches since data has changed
      portfolioCache.remove(generateCacheKey('roundup_transactions'));
      portfolioCache.remove(generateCacheKey('roundup_summary'));
      
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
};