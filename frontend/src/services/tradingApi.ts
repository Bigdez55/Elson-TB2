import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Base URL for the API (relative path works with proxy in dev, direct in prod)
const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// Trading types
export interface TradeRequest {
  symbol: string;
  trade_type: 'BUY' | 'SELL';
  order_type: 'MARKET' | 'LIMIT' | 'STOP_LOSS' | 'STOP_LIMIT';
  quantity: number;
  price?: number;
  stop_price?: number;
  time_in_force?: 'DAY' | 'GTC' | 'IOC' | 'FOK';
  paper_trading?: boolean;
  trade_mode?: 'paper' | 'live';
}

export interface TradeResponse {
  trade_id: string;
  status: string;
  symbol: string;
  trade_type: string;
  order_type: string;
  quantity: number;
  filled_quantity?: number;
  price?: number;
  filled_price?: number;
  total_value: number;
  fees: number;
  paper_trading: boolean;
  created_at: string;
  updated_at: string;
  execution_details?: {
    execution_time?: string;
    execution_venue?: string;
    market_impact?: number;
  };
}

export interface Position {
  id: string;
  symbol: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  paper_trading: boolean;
  last_updated: string;
}

export interface OrderHistory {
  id: string;
  symbol: string;
  trade_type: string;
  order_type: string;
  quantity: number;
  price?: number;
  status: string;
  filled_quantity: number;
  filled_price?: number;
  paper_trading: boolean;
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  total_value: number;
  cash_balance: number;
  positions_value: number;
  day_pnl: number;
  day_pnl_percent: number;
  total_pnl: number;
  total_pnl_percent: number;
  paper_trading: boolean;
  positions: Position[];
  last_updated: string;
}

export interface TradingAccount {
  account_id: string;
  account_type: 'paper' | 'live';
  buying_power: number;
  cash_balance: number;
  portfolio_value: number;
  day_trade_count: number;
  pattern_day_trader: boolean;
  trading_blocked: boolean;
  last_equity_close: number;
  created_at: string;
}

// Mode-aware cache tags
const getModeTag = (mode: 'paper' | 'live') => `${mode}_data` as const;

// Custom base query with authentication and mode awareness
const baseQueryWithAuth = fetchBaseQuery({
  baseUrl,
  prepareHeaders: (headers, { getState, endpoint }) => {
    const token = localStorage.getItem('token');
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    
    // Add trading mode header for mode-specific endpoints
    if (endpoint?.includes('trading') || endpoint?.includes('portfolio')) {
      const tradingMode = localStorage.getItem('tradingMode') || 'paper';
      headers.set('x-trading-mode', tradingMode);
    }
    
    return headers;
  },
});

// Trading API slice with mode-aware caching
export const tradingApi = createApi({
  reducerPath: 'tradingApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['Trade', 'Portfolio', 'Position', 'OrderHistory', 'TradingAccount'],
  endpoints: (builder) => ({
    // Execute trade with mode awareness
    executeTrade: builder.mutation<TradeResponse, TradeRequest & { mode: 'paper' | 'live' }>({
      query: ({ mode, ...tradeRequest }) => ({
        url: '/trading/order',
        method: 'POST',
        body: {
          ...tradeRequest,
          paper_trading: mode === 'paper',
          trade_mode: mode,
        },
      }),
      invalidatesTags: (result, error, { mode }) => [
        { type: 'Portfolio', id: getModeTag(mode) },
        { type: 'Position', id: getModeTag(mode) },
        { type: 'OrderHistory', id: getModeTag(mode) },
        { type: 'TradingAccount', id: getModeTag(mode) },
      ],
    }),

    // Get portfolio with mode-specific caching
    getPortfolio: builder.query<Portfolio, { mode: 'paper' | 'live' }>({
      query: ({ mode }) => ({
        url: '/portfolio',
        headers: {
          'x-trading-mode': mode,
        },
      }),
      providesTags: (result, error, { mode }) => [
        { type: 'Portfolio', id: getModeTag(mode) },
      ],
      // Cache for 30 seconds, refresh when focused
      keepUnusedDataFor: 30,
    }),

    // Get positions with mode-specific caching
    getPositions: builder.query<Position[], { mode: 'paper' | 'live' }>({
      query: ({ mode }) => ({
        url: '/trading/positions',
        headers: {
          'x-trading-mode': mode,
        },
      }),
      providesTags: (result, error, { mode }) => [
        { type: 'Position', id: getModeTag(mode) },
        ...(result || []).map(position => ({ type: 'Position' as const, id: `${mode}_${position.symbol}` })),
      ],
      keepUnusedDataFor: 30,
    }),

    // Get specific position
    getPosition: builder.query<Position, { symbol: string; mode: 'paper' | 'live' }>({
      query: ({ symbol, mode }) => ({
        url: `/trading/positions/${symbol.toUpperCase()}`,
        headers: {
          'x-trading-mode': mode,
        },
      }),
      providesTags: (result, error, { symbol, mode }) => [
        { type: 'Position', id: `${mode}_${symbol}` },
      ],
    }),

    // Get order history with mode-specific caching
    getOrderHistory: builder.query<OrderHistory[], { 
      mode: 'paper' | 'live'; 
      limit?: number; 
      symbol?: string;
      status?: string;
    }>({
      query: ({ mode, limit = 50, symbol, status }) => {
        const params = new URLSearchParams();
        params.append('limit', limit.toString());
        if (symbol) params.append('symbol', symbol.toUpperCase());
        if (status) params.append('status', status);
        
        return {
          url: `/trading/orders?${params.toString()}`,
          headers: {
            'x-trading-mode': mode,
          },
        };
      },
      providesTags: (result, error, { mode }) => [
        { type: 'OrderHistory', id: getModeTag(mode) },
        ...(result || []).map(order => ({ type: 'OrderHistory' as const, id: `${mode}_${order.id}` })),
      ],
      keepUnusedDataFor: 300, // Cache for 5 minutes
    }),

    // Get trading account info
    getTradingAccount: builder.query<TradingAccount, { mode: 'paper' | 'live' }>({
      query: ({ mode }) => ({
        url: '/trading/account',
        headers: {
          'x-trading-mode': mode,
        },
      }),
      providesTags: (result, error, { mode }) => [
        { type: 'TradingAccount', id: getModeTag(mode) },
      ],
      keepUnusedDataFor: 60, // Cache for 1 minute
    }),

    // Cancel order
    cancelOrder: builder.mutation<{ success: boolean; message: string }, { 
      orderId: string; 
      mode: 'paper' | 'live' 
    }>({
      query: ({ orderId, mode }) => ({
        url: `/trading/orders/${orderId}/cancel`,
        method: 'POST',
        headers: {
          'x-trading-mode': mode,
        },
      }),
      invalidatesTags: (result, error, { mode }) => [
        { type: 'OrderHistory', id: getModeTag(mode) },
        { type: 'Portfolio', id: getModeTag(mode) },
      ],
    }),

    // Get order status
    getOrderStatus: builder.query<OrderHistory, { 
      orderId: string; 
      mode: 'paper' | 'live' 
    }>({
      query: ({ orderId, mode }) => ({
        url: `/trading/orders/${orderId}`,
        headers: {
          'x-trading-mode': mode,
        },
      }),
      providesTags: (result, error, { orderId, mode }) => [
        { type: 'OrderHistory', id: `${mode}_${orderId}` },
      ],
    }),

    // Get portfolio performance
    getPortfolioPerformance: builder.query<{
      daily_returns: Array<{ date: string; return: number; portfolio_value: number }>;
      monthly_returns: Array<{ month: string; return: number }>;
      yearly_return: number;
      sharpe_ratio: number;
      max_drawdown: number;
      volatility: number;
    }, { 
      mode: 'paper' | 'live'; 
      period?: '1W' | '1M' | '3M' | '1Y' | 'ALL' 
    }>({
      query: ({ mode, period = '1M' }) => ({
        url: `/portfolio/performance?period=${period}`,
        headers: {
          'x-trading-mode': mode,
        },
      }),
      providesTags: (result, error, { mode }) => [
        { type: 'Portfolio', id: `${getModeTag(mode)}_performance` },
      ],
      keepUnusedDataFor: 300, // Cache for 5 minutes
    }),

    // Batch operations for better performance
    getBatchData: builder.query<{
      portfolio: Portfolio;
      positions: Position[];
      recent_orders: OrderHistory[];
      account: TradingAccount;
    }, { mode: 'paper' | 'live' }>({
      query: ({ mode }) => ({
        url: '/trading/batch-data',
        headers: {
          'x-trading-mode': mode,
        },
      }),
      providesTags: (result, error, { mode }) => [
        { type: 'Portfolio', id: getModeTag(mode) },
        { type: 'Position', id: getModeTag(mode) },
        { type: 'OrderHistory', id: getModeTag(mode) },
        { type: 'TradingAccount', id: getModeTag(mode) },
      ],
      keepUnusedDataFor: 30,
    }),

    // Sync trading data across modes (for migration)
    syncTradingModes: builder.mutation<{ success: boolean; message: string }, void>({
      query: () => ({
        url: '/trading/sync-modes',
        method: 'POST',
      }),
      invalidatesTags: [
        { type: 'Portfolio', id: 'paper_data' },
        { type: 'Portfolio', id: 'live_data' },
        { type: 'Position', id: 'paper_data' },
        { type: 'Position', id: 'live_data' },
      ],
    }),
  }),
});

// Export hooks with mode awareness
export const {
  useExecuteTradeMutation,
  useGetPortfolioQuery,
  useGetPositionsQuery,
  useGetPositionQuery,
  useGetOrderHistoryQuery,
  useGetTradingAccountQuery,
  useCancelOrderMutation,
  useGetOrderStatusQuery,
  useGetPortfolioPerformanceQuery,
  useGetBatchDataQuery,
  useSyncTradingModesMutation,
  // Lazy queries
  useLazyGetPortfolioQuery,
  useLazyGetPositionsQuery,
  useLazyGetOrderHistoryQuery,
  useLazyGetPortfolioPerformanceQuery,
} = tradingApi;

// Utility hooks for mode-aware data fetching
export const useTradingData = (mode: 'paper' | 'live') => {
  const portfolio = useGetPortfolioQuery({ mode });
  const positions = useGetPositionsQuery({ mode });
  const orderHistory = useGetOrderHistoryQuery({ mode, limit: 20 });
  const account = useGetTradingAccountQuery({ mode });

  return {
    portfolio: portfolio.data,
    positions: positions.data || [],
    orderHistory: orderHistory.data || [],
    account: account.data,
    isLoading: portfolio.isLoading || positions.isLoading || orderHistory.isLoading || account.isLoading,
    error: portfolio.error || positions.error || orderHistory.error || account.error,
    refetch: () => {
      portfolio.refetch();
      positions.refetch();
      orderHistory.refetch();
      account.refetch();
    },
  };
};

// Export the reducer to add to the store
export default tradingApi;