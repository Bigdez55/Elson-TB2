import api from './api';

export interface AdvancedTradingSignal {
  symbol: string;
  action: string;
  confidence: number;
  price: number;
  timestamp: string;
  indicators: Record<string, number>;
  reason: string;
  stop_loss?: number;
  take_profit?: number;
  ai_confidence?: number;
  ai_prediction?: number;
  combined_confidence?: number;
}

export interface TradingInitRequest {
  symbols: string[];
  risk_profile: 'conservative' | 'moderate' | 'aggressive';
  enable_ai_models: boolean;
}

export interface TradingSignalsRequest {
  portfolio_id: number;
  symbols?: string[];
}

export interface ExecuteTradesRequest {
  portfolio_id: number;
  auto_execute: boolean;
}

export interface PositionMonitoring {
  total_positions: number;
  total_value: number;
  unrealized_pnl: number;
  risk_metrics: Record<string, any>;
  alerts: Array<{
    type: string;
    message: string;
    severity: string;
  }>;
}

export interface PerformanceSummary {
  performance_metrics: Record<string, any>;
  active_strategies: number;
  trained_ai_models: number;
  risk_profile: string;
  circuit_breaker_status: Record<string, any>;
}

export interface CircuitBreakerStatus {
  trading_allowed: boolean;
  breaker_status: string;
  active_breakers: Record<string, any>;
  position_sizing_multiplier: number;
}

export interface AIModelStatus {
  total_models: number;
  trained_models: number;
  models: Record<string, {
    is_trained: boolean;
    last_prediction?: number;
    prediction_confidence?: number;
    training_summary?: Record<string, any>;
  }>;
}

// Advanced Trading API
export const advancedTradingAPI = {
  /**
   * Initialize advanced trading system with strategies and AI models
   */
  initialize: async (request: TradingInitRequest) => {
    const response = await api.post('/advanced/initialize', request);
    return response.data;
  },

  /**
   * Generate trading signals for the specified portfolio
   */
  generateSignals: async (request: TradingSignalsRequest): Promise<AdvancedTradingSignal[]> => {
    const response = await api.post('/advanced/signals', request);
    return response.data;
  },

  /**
   * Execute trades based on generated signals
   */
  executeTrades: async (request: ExecuteTradesRequest) => {
    const response = await api.post('/advanced/execute', request);
    return response.data;
  },

  /**
   * Monitor portfolio positions and risk metrics
   */
  monitorPositions: async (portfolioId: number): Promise<PositionMonitoring> => {
    const response = await api.get(`/advanced/monitor/${portfolioId}`);
    return response.data;
  },

  /**
   * Get trading performance summary
   */
  getPerformanceSummary: async (): Promise<PerformanceSummary> => {
    const response = await api.get('/advanced/performance');
    return response.data;
  },

  /**
   * Update risk profile for trading
   */
  updateRiskProfile: async (riskProfile: 'conservative' | 'moderate' | 'aggressive') => {
    const response = await api.post('/advanced/risk-profile', { risk_profile: riskProfile });
    return response.data;
  },

  /**
   * Get current circuit breaker status
   */
  getCircuitBreakerStatus: async (): Promise<CircuitBreakerStatus> => {
    const response = await api.get('/advanced/circuit-breakers');
    return response.data;
  },

  /**
   * Reset a specific circuit breaker
   */
  resetCircuitBreaker: async (breakerType: string, scope?: string) => {
    const response = await api.post('/advanced/circuit-breakers/reset', {
      breaker_type: breakerType,
      scope,
    });
    return response.data;
  },

  /**
   * Get status of AI models for trading
   */
  getAIModelsStatus: async (symbols?: string[]): Promise<AIModelStatus> => {
    const params = symbols ? { symbols } : {};
    const response = await api.get('/advanced/ai-models/status', { params });
    return response.data;
  },

  /**
   * Retrain AI models for specified symbols
   */
  retrainAIModels: async (symbols: string[]) => {
    const response = await api.post('/advanced/ai-models/retrain', { symbols });
    return response.data;
  },
};

export default advancedTradingAPI;