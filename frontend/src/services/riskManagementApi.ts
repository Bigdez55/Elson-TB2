import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Base URL for the API (relative path works with proxy in dev, direct in prod)
const baseUrl = process.env.REACT_APP_API_URL || '/api/v1';

// Risk management types
export interface TradeRiskRequest {
  symbol: string;
  trade_type: 'BUY' | 'SELL';
  quantity: number;
  price?: number;
  trade_id?: string;
}

export interface TradeRiskResponse {
  trade_id: string;
  symbol: string;
  risk_level: string;
  risk_score: number;
  check_result: string;
  violations: string[];
  warnings: string[];
  impact_analysis: {
    position_value: number;
    portfolio_impact_pct: number;
    concentration_after: number;
    var_impact: number;
  };
  recommended_action: string;
  max_allowed_quantity?: number;
  metadata: Record<string, any>;
}

export interface RiskMetricsResponse {
  portfolio_value: number;
  daily_var: number;
  portfolio_beta: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  concentration_risk: number;
  sector_concentration: Record<string, number>;
  largest_position_pct: number;
  cash_percentage: number;
  leverage_ratio: number;
}

export interface PositionRiskResponse {
  symbol: string;
  position_value: number;
  position_percentage: number;
  daily_var: number;
  beta: number;
  volatility: number;
  correlation_score: number;
  sector: string;
  risk_contribution: number;
}

export interface CircuitBreaker {
  breaker_type: string;
  is_triggered: boolean;
  threshold_value: number;
  current_value: number;
  reset_time?: string;
  triggered_at?: string;
  description: string;
}

export interface RiskLimits {
  user_id: number;
  active_limits: {
    position_limits: {
      max_position_size_pct: number;
      max_sector_concentration_pct: number;
      min_cash_percentage: number;
    };
    loss_limits: {
      max_daily_loss_pct: number;
      max_weekly_loss_pct: number;
    };
    trading_limits: {
      max_trade_value: number;
      max_daily_trades: number;
      confirmation_threshold: number;
    };
    leverage_limits: {
      max_portfolio_leverage: number;
      max_correlation_threshold: number;
    };
  };
  user_tier: string;
  risk_tolerance: string;
  customizable_limits: string[];
  admin_only_limits: string[];
  last_updated?: string;
}

export interface SymbolRiskScore {
  symbol: string;
  risk_score: number;
  volatility: number;
  beta: number;
  liquidity_score: number;
  sector: string;
  market_cap_category: string;
  risk_factors: string[];
  recommendation: string;
  optimal_position_size_pct: number;
  analysis_timestamp: string;
}

export interface PortfolioValidation {
  user_id: number;
  portfolio_value: number;
  overall_risk_level: 'low' | 'medium' | 'high';
  compliance_status: 'compliant' | 'non_compliant';
  violations: string[];
  warnings: string[];
  recommendations: string[];
  risk_metrics_summary: {
    daily_var_pct: number;
    concentration_risk: number;
    largest_position_pct: number;
    cash_percentage: number;
    sector_count: number;
  };
  validation_timestamp: string;
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

// Risk Management API slice
export const riskManagementApi = createApi({
  reducerPath: 'riskManagementApi',
  baseQuery: baseQueryWithAuth,
  tagTypes: ['RiskMetrics', 'PositionRisk', 'CircuitBreakers', 'RiskLimits', 'PortfolioValidation'],
  endpoints: (builder) => ({
    // Assess trade risk
    assessTradeRisk: builder.mutation<TradeRiskResponse, TradeRiskRequest>({
      query: (tradeRequest) => ({
        url: '/risk/assess-trade',
        method: 'POST',
        body: tradeRequest,
      }),
    }),

    // Get portfolio risk metrics
    getPortfolioRiskMetrics: builder.query<RiskMetricsResponse, void>({
      query: () => '/risk/portfolio-metrics',
      providesTags: ['RiskMetrics'],
    }),

    // Get position risk analysis
    getPositionRiskAnalysis: builder.query<PositionRiskResponse[], void>({
      query: () => '/risk/position-analysis',
      providesTags: ['PositionRisk'],
    }),

    // Check circuit breakers
    getCircuitBreakers: builder.query<CircuitBreaker[], void>({
      query: () => '/risk/circuit-breakers',
      providesTags: ['CircuitBreakers'],
    }),

    // Get risk limits
    getRiskLimits: builder.query<RiskLimits, void>({
      query: () => '/risk/risk-limits',
      providesTags: ['RiskLimits'],
    }),

    // Get symbol risk score
    getSymbolRiskScore: builder.query<SymbolRiskScore, string>({
      query: (symbol) => `/risk/risk-score/${symbol.toUpperCase()}`,
    }),

    // Validate portfolio
    validatePortfolio: builder.mutation<PortfolioValidation, void>({
      query: () => ({
        url: '/risk/validate-portfolio',
        method: 'POST',
      }),
      invalidatesTags: ['RiskMetrics', 'PositionRisk', 'PortfolioValidation'],
    }),
  }),
});

// Export hooks for use in components
export const {
  useAssessTradeRiskMutation,
  useGetPortfolioRiskMetricsQuery,
  useGetPositionRiskAnalysisQuery,
  useGetCircuitBreakersQuery,
  useGetRiskLimitsQuery,
  useGetSymbolRiskScoreQuery,
  useValidatePortfolioMutation,
  // For lazy queries
  useLazyGetPortfolioRiskMetricsQuery,
  useLazyGetPositionRiskAnalysisQuery,
  useLazyGetSymbolRiskScoreQuery,
} = riskManagementApi;

// Export the reducer to add to the store
export default riskManagementApi;