import axios, { AxiosError } from 'axios';
import { 
  User, 
  Trade, 
  TradeOrderRequest, 
  Quote, 
  Asset, 
  PortfolioSummary, 
  Portfolio,
  Holding,
  TradingStats 
} from '../types';

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (userData: {
    email: string;
    password: string;
    full_name?: string;
    risk_tolerance?: string;
    trading_style?: string;
  }) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Trading API
export const tradingAPI = {
  placeOrder: async (orderData: TradeOrderRequest): Promise<Trade> => {
    const response = await api.post('/trading/order', orderData);
    return response.data;
  },

  cancelOrder: async (tradeId: number): Promise<Trade> => {
    const response = await api.post('/trading/cancel', { trade_id: tradeId });
    return response.data;
  },

  getOpenOrders: async (): Promise<Trade[]> => {
    const response = await api.get('/trading/orders');
    return response.data;
  },

  getTradeHistory: async (limit: number = 100): Promise<Trade[]> => {
    const response = await api.get(`/trading/history?limit=${limit}`);
    return response.data;
  },

  getPositions: async (): Promise<Holding[]> => {
    const response = await api.get('/trading/positions');
    return response.data;
  },

  getTradingStats: async (): Promise<TradingStats> => {
    const response = await api.get('/trading/stats');
    return response.data;
  },

  validateSymbol: async (symbol: string) => {
    const response = await api.get(`/trading/validate/${symbol}`);
    return response.data;
  },
};

// Market Data API
export const marketDataAPI = {
  getQuote: async (symbol: string): Promise<Quote> => {
    const response = await api.get(`/market/quote/${symbol}`);
    return response.data;
  },

  getMultipleQuotes: async (symbols: string[]): Promise<{ quotes: Quote[]; timestamp: string }> => {
    const response = await api.post('/market/quotes', symbols);
    return response.data;
  },

  getAssets: async (params?: {
    asset_type?: string;
    sector?: string;
    limit?: number;
  }): Promise<Asset[]> => {
    const queryParams = new URLSearchParams();
    if (params?.asset_type) queryParams.append('asset_type', params.asset_type);
    if (params?.sector) queryParams.append('sector', params.sector);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
    const response = await api.get(`/market/assets?${queryParams.toString()}`);
    return response.data;
  },

  getHistoricalData: async (symbol: string, timeframe: string = '1day', limit: number = 100) => {
    const response = await api.get(`/market/history/${symbol}?timeframe=${timeframe}&limit=${limit}`);
    return response.data;
  },

  createAsset: async (assetData: {
    symbol: string;
    name: string;
    asset_type: string;
    exchange?: string;
    sector?: string;
    industry?: string;
  }): Promise<Asset> => {
    const response = await api.post('/market/assets', assetData);
    return response.data;
  },
};

// Portfolio API
export const portfolioAPI = {
  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    const response = await api.get('/portfolio/');
    return response.data;
  },

  getPortfolioDetails: async (): Promise<Portfolio> => {
    const response = await api.get('/portfolio/details');
    return response.data;
  },

  getHoldings: async (): Promise<Holding[]> => {
    const response = await api.get('/portfolio/holdings');
    return response.data;
  },

  updatePortfolio: async (updateData: {
    name?: string;
    description?: string;
    cash_balance?: number;
    auto_rebalance?: boolean;
  }): Promise<Portfolio> => {
    const response = await api.put('/portfolio/', updateData);
    return response.data;
  },

  getPerformance: async () => {
    const response = await api.get('/portfolio/performance');
    return response.data;
  },

  refreshPortfolioData: async () => {
    const response = await api.post('/portfolio/refresh');
    return response.data;
  },
};

// Export advanced trading API
export { advancedTradingAPI } from './advancedTradingAPI';

// Export trading service
export { tradingService } from './tradingService';

// Named export for slices that use { api } import pattern
export { api };

export default api;