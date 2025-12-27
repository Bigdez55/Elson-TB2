import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// Auto Trading types
export interface AvailableStrategy {
  name: string;
  category: string;
  description: string;
  risk_level: string;
  default_parameters: Record<string, any>;
  timeframes: string[];
}

export interface StrategyPerformance {
  strategy_name: string;
  symbol: string;
  total_trades: number;
  win_rate: number;
  total_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  is_active: boolean;
  last_signal_time: string | null;
}

export interface ActiveStrategy {
  name: string;
  symbol: string;
  is_active: boolean;
  last_signal_time: string | null;
  performance: StrategyPerformance;
}

export interface AutoTradingStatus {
  is_active: boolean;
  active_strategies: Record<string, ActiveStrategy>;
  portfolio_id?: number;
}

export interface StartAutoTradingRequest {
  portfolio_id: number;
  strategy_names: string[];
  symbols: string[];
  parameters?: Record<string, Record<string, any>>;
}

export interface AddStrategyRequest {
  strategy_name: string;
  symbol: string;
  parameters?: Record<string, any>;
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

export const autoTradingApi = createApi({
  reducerPath: 'autoTradingApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['AutoTradingStatus', 'Strategies'],
  endpoints: (builder) => ({
    // Start automated trading
    startAutoTrading: builder.mutation<
      { status: string; message: string },
      StartAutoTradingRequest
    >({
      query: (request) => ({
        url: '/auto-trading/start',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['AutoTradingStatus'],
    }),

    // Stop automated trading
    stopAutoTrading: builder.mutation<{ status: string; message: string }, void>({
      query: () => ({
        url: '/auto-trading/stop',
        method: 'POST',
      }),
      invalidatesTags: ['AutoTradingStatus'],
    }),

    // Get auto-trading status
    getAutoTradingStatus: builder.query<AutoTradingStatus, void>({
      query: () => '/auto-trading/status',
      providesTags: ['AutoTradingStatus'],
      // Poll every 10 seconds when auto-trading is active
      keepUnusedDataFor: 10,
    }),

    // Add strategy to active session
    addStrategy: builder.mutation<{ status: string; message: string }, AddStrategyRequest>({
      query: (request) => ({
        url: '/auto-trading/strategies/add',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['AutoTradingStatus'],
    }),

    // Remove strategy from active session
    removeStrategy: builder.mutation<
      { status: string; message: string },
      { strategy_name: string; symbol: string }
    >({
      query: ({ strategy_name, symbol }) => ({
        url: `/auto-trading/strategies/remove?strategy_name=${strategy_name}&symbol=${symbol}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['AutoTradingStatus'],
    }),

    // List available strategies
    getAvailableStrategies: builder.query<AvailableStrategy[], { category?: string }>({
      query: ({ category }) => ({
        url: '/auto-trading/strategies/available',
        params: category ? { category } : {},
      }),
      providesTags: ['Strategies'],
    }),

    // List strategy categories
    getStrategyCategories: builder.query<string[], void>({
      query: () => '/auto-trading/strategies/categories',
    }),
  }),
});

export const {
  useStartAutoTradingMutation,
  useStopAutoTradingMutation,
  useGetAutoTradingStatusQuery,
  useAddStrategyMutation,
  useRemoveStrategyMutation,
  useGetAvailableStrategiesQuery,
  useGetStrategyCategoriesQuery,
  // Lazy queries
  useLazyGetAutoTradingStatusQuery,
  useLazyGetAvailableStrategiesQuery,
} = autoTradingApi;

export default autoTradingApi;
