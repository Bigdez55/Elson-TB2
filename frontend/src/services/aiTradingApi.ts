import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// AI Trading types
export interface AISignal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number; // 0-100
  reasons: string[];
  technical_indicators: Record<string, number>;
  price_target?: number;
  stop_loss?: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  timestamp: string;
}

export interface AIStrategy {
  strategy_id: string;
  name: string;
  description: string;
  is_enabled: boolean;
  risk_tolerance: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';
  target_allocation: Record<string, number>;
  rebalance_frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY';
  performance: {
    total_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
  };
}

export interface RiskAssessment {
  symbol: string;
  risk_score: number; // 0-100
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';
  volatility: number;
  beta: number;
  value_at_risk: number;
  factors: {
    market_risk: number;
    liquidity_risk: number;
    concentration_risk: number;
  };
  recommendations: string[];
  timestamp: string;
}

export interface AIPortfolioAnalysis {
  current_allocation: Record<string, number>;
  recommended_allocation: Record<string, number>;
  rebalance_suggestions: Array<{
    symbol: string;
    action: 'BUY' | 'SELL';
    quantity: number;
    reason: string;
  }>;
  risk_score: number;
  diversification_score: number;
  expected_return: number;
  optimization_score: number;
}

export interface NewsItem {
  title: string;
  summary: string;
  url: string;
  source: string;
  published_at: string;
  sentiment: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
  relevance_score: number;
  symbols: string[];
}

export interface CompanyInfo {
  symbol: string;
  name: string;
  sector: string;
  industry: string;
  market_cap: number;
  pe_ratio?: number;
  dividend_yield?: number;
  beta?: number;
  week_52_high: number;
  week_52_low: number;
  average_volume: number;
  description: string;
  ceo?: string;
  employees?: number;
  founded?: string;
  headquarters?: string;
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

export const aiTradingApi = createApi({
  reducerPath: 'aiTradingApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['AISignal', 'AIStrategy', 'RiskAssessment', 'News', 'CompanyInfo'],
  endpoints: (builder) => ({
    // Get AI trading signal for a symbol
    getAISignal: builder.query<AISignal, { symbol: string; mode: 'paper' | 'live' }>({
      query: ({ symbol, mode }) => ({
        url: `/ai/signals/${symbol.toUpperCase()}`,
        params: { paper_trading: mode === 'paper' },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'AISignal', id: symbol }],
      keepUnusedDataFor: 300, // Cache for 5 minutes
    }),

    // Get multiple AI signals
    getAISignals: builder.query<AISignal[], { symbols: string[]; mode: 'paper' | 'live' }>({
      query: ({ symbols, mode }) => ({
        url: `/ai/signals`,
        params: {
          symbols: symbols.map(s => s.toUpperCase()).join(','),
          paper_trading: mode === 'paper',
        },
      }),
      providesTags: (result) =>
        result
          ? [...result.map(signal => ({ type: 'AISignal' as const, id: signal.symbol })), 'AISignal']
          : ['AISignal'],
      keepUnusedDataFor: 300,
    }),

    // Get AI trading strategies
    getAIStrategies: builder.query<AIStrategy[], void>({
      query: () => '/ai/strategies',
      providesTags: ['AIStrategy'],
    }),

    // Get specific AI strategy
    getAIStrategy: builder.query<AIStrategy, string>({
      query: (strategyId) => `/ai/strategies/${strategyId}`,
      providesTags: (result, error, id) => [{ type: 'AIStrategy', id }],
    }),

    // Enable/disable AI strategy
    toggleAIStrategy: builder.mutation<{ success: boolean }, { strategyId: string; enabled: boolean }>({
      query: ({ strategyId, enabled }) => ({
        url: `/ai/strategies/${strategyId}/toggle`,
        method: 'POST',
        body: { enabled },
      }),
      invalidatesTags: (result, error, { strategyId }) => [{ type: 'AIStrategy', id: strategyId }],
    }),

    // Get risk assessment
    getRiskAssessment: builder.query<RiskAssessment, { symbol: string; mode: 'paper' | 'live' }>({
      query: ({ symbol, mode }) => ({
        url: `/ai/risk/${symbol.toUpperCase()}`,
        params: { paper_trading: mode === 'paper' },
      }),
      providesTags: (result, error, { symbol }) => [{ type: 'RiskAssessment', id: symbol }],
      keepUnusedDataFor: 600, // Cache for 10 minutes
    }),

    // Get AI portfolio analysis
    getAIPortfolioAnalysis: builder.query<AIPortfolioAnalysis, { mode: 'paper' | 'live' }>({
      query: ({ mode }) => ({
        url: '/ai/portfolio/analyze',
        params: { paper_trading: mode === 'paper' },
      }),
      keepUnusedDataFor: 300,
    }),

    // Get news for symbol
    getNews: builder.query<NewsItem[], { symbol?: string; limit?: number }>({
      query: ({ symbol, limit = 10 }) => ({
        url: '/market-enhanced/news',
        params: {
          symbol: symbol?.toUpperCase(),
          limit,
        },
      }),
      providesTags: (result, error, { symbol }) =>
        symbol ? [{ type: 'News', id: symbol }] : ['News'],
      keepUnusedDataFor: 300,
    }),

    // Get company information
    getCompanyInfo: builder.query<CompanyInfo, string>({
      query: (symbol) => `/market-enhanced/company/${symbol.toUpperCase()}`,
      providesTags: (result, error, symbol) => [{ type: 'CompanyInfo', id: symbol }],
      keepUnusedDataFor: 3600, // Cache for 1 hour
    }),
  }),
});

export const {
  useGetAISignalQuery,
  useGetAISignalsQuery,
  useGetAIStrategiesQuery,
  useGetAIStrategyQuery,
  useToggleAIStrategyMutation,
  useGetRiskAssessmentQuery,
  useGetAIPortfolioAnalysisQuery,
  useGetNewsQuery,
  useGetCompanyInfoQuery,
  // Lazy queries
  useLazyGetAISignalQuery,
  useLazyGetNewsQuery,
  useLazyGetCompanyInfoQuery,
} = aiTradingApi;

export default aiTradingApi;
