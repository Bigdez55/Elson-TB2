import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Base URL for the API (relative path works with proxy in dev, direct in prod)
const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// Market data types
export interface Quote {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change?: number;
  change_percent?: number;
  previous_close?: number;
  source: string;
  timestamp: string;
}

export interface EnhancedQuote {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change?: number;
  change_percent?: number;
  previous_close?: number;
  provider: string;
  timestamp: string;
  market_cap?: string;
  pe_ratio?: number;
  dividend_yield?: string;
  week_52_high?: number;
  week_52_low?: number;
}

export interface HistoricalData {
  symbol: string;
  period: string;
  data: Array<{
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  statistics: {
    count: number;
    min_price: number;
    max_price: number;
    avg_price: number;
    price_change: number;
    price_change_percent: number;
  };
  data_points: number;
}

export interface Asset {
  symbol: string;
  name: string;
  asset_type: string;
  exchange?: string;
  sector?: string;
  industry?: string;
  is_active: boolean;
}

export interface SearchResult {
  symbol: string;
  name: string;
  exchange: string;
  asset_type: string;
  sector?: string;
  industry?: string;
}

export interface MultipleQuotesResponse {
  quotes: { [symbol: string]: EnhancedQuote | null };
  summary: {
    total_requested: number;
    successful: number;
    failed: number;
  };
  timestamp?: string;
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

// Market Data API slice
export const marketDataApi = createApi({
  reducerPath: 'marketDataApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['Quote', 'Historical', 'Asset'],
  endpoints: (builder) => ({
    // Get single quote (enhanced)
    getQuote: builder.query<EnhancedQuote, string>({
      query: (symbol) => `/market-enhanced/quote/${symbol.toUpperCase()}`,
      providesTags: (result, error, symbol) => [{ type: 'Quote', id: symbol }],
    }),

    // Get multiple quotes
    getMultipleQuotes: builder.query<MultipleQuotesResponse, string[]>({
      query: (symbols) => `/market-enhanced/quotes?symbols=${symbols.join(',')}`,
      providesTags: (result, error, symbols) =>
        symbols.map(symbol => ({ type: 'Quote' as const, id: symbol })),
    }),

    // Get historical data
    getHistoricalData: builder.query<HistoricalData, { symbol: string; period?: string }>({
      query: ({ symbol, period = '1mo' }) => 
        `/market-enhanced/historical/${symbol.toUpperCase()}?period=${period}`,
      providesTags: (result, error, { symbol }) => [{ type: 'Historical', id: symbol }],
    }),

    // Search symbols
    searchSymbols: builder.query<SearchResult[], string>({
      query: (query) => `/market-enhanced/search?query=${encodeURIComponent(query)}`,
      // Only cache for 1 minute for search results
      keepUnusedDataFor: 60,
    }),

    // Get available assets
    getAssets: builder.query<Asset[], { asset_type?: string; sector?: string; limit?: number }>({
      query: ({ asset_type, sector, limit = 100 }) => {
        const params = new URLSearchParams();
        if (asset_type) params.append('asset_type', asset_type);
        if (sector) params.append('sector', sector);
        params.append('limit', limit.toString());
        return `/market/assets?${params.toString()}`;
      },
      providesTags: ['Asset'],
    }),

    // Get market data health
    getMarketDataHealth: builder.query<any, void>({
      query: () => '/market-enhanced/health',
      // Refresh health status every 5 minutes
      keepUnusedDataFor: 300,
    }),
  }),
});

// Export hooks for use in components
export const {
  useGetQuoteQuery,
  useGetMultipleQuotesQuery,
  useGetHistoricalDataQuery,
  useSearchSymbolsQuery,
  useGetAssetsQuery,
  useGetMarketDataHealthQuery,
  // For lazy queries (manual triggering)
  useLazyGetQuoteQuery,
  useLazyGetMultipleQuotesQuery,
  useLazyGetHistoricalDataQuery,
  useLazySearchSymbolsQuery,
} = marketDataApi;

// Export the reducer to add to the store
export default marketDataApi;