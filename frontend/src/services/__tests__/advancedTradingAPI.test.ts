import axios from 'axios';
import { advancedTradingAPI } from '../advancedTradingAPI';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock the axios instance from api.ts
const mockApiInstance = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() }
  }
};

// Mock the default export from api.ts
jest.mock('../api', () => mockApiInstance);

describe('Advanced Trading API Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initialize', () => {
    it('should initialize trading system successfully', async () => {
      const request = {
        symbols: ['AAPL', 'GOOGL', 'MSFT'],
        risk_profile: 'moderate' as const,
        enable_ai_models: true
      };
      const mockResponse = {
        success: true,
        message: 'Trading system initialized',
        strategies_loaded: 3,
        ai_models_status: 'ready'
      };
      mockApiInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await advancedTradingAPI.initialize(request);

      expect(mockApiInstance.post).toHaveBeenCalledWith('/advanced/initialize', request);
      expect(result).toEqual(mockResponse);
    });

    it('should handle initialization errors', async () => {
      const error = {
        response: {
          data: { detail: 'Invalid risk profile' },
          status: 400
        }
      };
      mockApiInstance.post.mockRejectedValue(error);

      await expect(advancedTradingAPI.initialize({
        symbols: ['AAPL'],
        risk_profile: 'invalid' as any,
        enable_ai_models: false
      })).rejects.toEqual(error);
    });
  });

  describe('generateSignals', () => {
    it('should generate trading signals successfully', async () => {
      const request = {
        portfolio_id: 1,
        symbols: ['AAPL', 'GOOGL']
      };
      const mockSignals = [
        {
          symbol: 'AAPL',
          action: 'BUY',
          confidence: 0.85,
          price: 152.50,
          timestamp: '2023-01-01T10:00:00Z',
          indicators: {
            rsi: 35,
            macd: 0.5,
            bollinger_position: 0.2
          },
          reason: 'Oversold conditions with positive momentum',
          stop_loss: 145.00,
          take_profit: 160.00,
          ai_confidence: 0.92,
          ai_prediction: 158.00,
          combined_confidence: 0.88
        },
        {
          symbol: 'GOOGL',
          action: 'HOLD',
          confidence: 0.65,
          price: 2850.00,
          timestamp: '2023-01-01T10:00:00Z',
          indicators: {
            rsi: 55,
            macd: -0.1,
            bollinger_position: 0.5
          },
          reason: 'Neutral market conditions',
          ai_confidence: 0.60,
          ai_prediction: 2860.00,
          combined_confidence: 0.62
        }
      ];
      mockApiInstance.post.mockResolvedValue({ data: mockSignals });

      const result = await advancedTradingAPI.generateSignals(request);

      expect(mockApiInstance.post).toHaveBeenCalledWith('/advanced/signals', request);
      expect(result).toEqual(mockSignals);
      expect(result).toHaveLength(2);
      expect(result[0].action).toBe('BUY');
      expect(result[0].confidence).toBeGreaterThan(0.8);
    });

    it('should handle empty signals response', async () => {
      const request = {
        portfolio_id: 1,
        symbols: ['INVALID']
      };
      mockApiInstance.post.mockResolvedValue({ data: [] });

      const result = await advancedTradingAPI.generateSignals(request);

      expect(result).toEqual([]);
    });

    it('should handle portfolio not found error', async () => {
      const error = {
        response: {
          data: { detail: 'Portfolio not found' },
          status: 404
        }
      };
      mockApiInstance.post.mockRejectedValue(error);

      await expect(advancedTradingAPI.generateSignals({
        portfolio_id: 999,
        symbols: ['AAPL']
      })).rejects.toEqual(error);
    });
  });

  describe('executeTrades', () => {
    it('should execute trades successfully', async () => {
      const request = {
        portfolio_id: 1,
        auto_execute: true
      };
      const mockResponse = {
        executed_trades: 3,
        total_value: 15000,
        successful_orders: [
          { symbol: 'AAPL', quantity: 10, price: 152.50 },
          { symbol: 'GOOGL', quantity: 5, price: 2850.00 }
        ],
        failed_orders: [],
        risk_checks_passed: true
      };
      mockApiInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await advancedTradingAPI.executeTrades(request);

      expect(mockApiInstance.post).toHaveBeenCalledWith('/advanced/execute', request);
      expect(result).toEqual(mockResponse);
      expect(result.executed_trades).toBe(3);
      expect(result.risk_checks_passed).toBe(true);
    });

    it('should handle insufficient funds error', async () => {
      const error = {
        response: {
          data: { detail: 'Insufficient funds for trade execution' },
          status: 400
        }
      };
      mockApiInstance.post.mockRejectedValue(error);

      await expect(advancedTradingAPI.executeTrades({
        portfolio_id: 1,
        auto_execute: true
      })).rejects.toEqual(error);
    });
  });

  describe('monitorPositions', () => {
    it('should monitor positions successfully', async () => {
      const portfolioId = 1;
      const mockMonitoring = {
        total_positions: 5,
        total_value: 50000,
        unrealized_pnl: 2500,
        risk_metrics: {
          portfolio_beta: 1.2,
          var_95: -1500,
          sharpe_ratio: 1.8,
          max_drawdown: -0.08
        },
        alerts: [
          {
            type: 'RISK_WARNING',
            message: 'Portfolio concentration risk in technology sector',
            severity: 'medium'
          },
          {
            type: 'PERFORMANCE_ALERT',
            message: 'AAPL position up 15% - consider taking profits',
            severity: 'low'
          }
        ]
      };
      mockApiInstance.get.mockResolvedValue({ data: mockMonitoring });

      const result = await advancedTradingAPI.monitorPositions(portfolioId);

      expect(mockApiInstance.get).toHaveBeenCalledWith('/advanced/monitor/1');
      expect(result).toEqual(mockMonitoring);
      expect(result.alerts).toHaveLength(2);
      expect(result.risk_metrics.sharpe_ratio).toBeGreaterThan(1.5);
    });
  });

  describe('getPerformanceSummary', () => {
    it('should get performance summary successfully', async () => {
      const mockSummary = {
        performance_metrics: {
          total_return: 0.125,
          annualized_return: 0.15,
          volatility: 0.18,
          sharpe_ratio: 1.8,
          max_drawdown: -0.08,
          win_rate: 0.68
        },
        active_strategies: 3,
        trained_ai_models: 5,
        risk_profile: 'moderate',
        circuit_breaker_status: {
          global_breaker: false,
          position_breaker: false,
          volatility_breaker: false
        }
      };
      mockApiInstance.get.mockResolvedValue({ data: mockSummary });

      const result = await advancedTradingAPI.getPerformanceSummary();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/advanced/performance');
      expect(result).toEqual(mockSummary);
      expect(result.performance_metrics.total_return).toBeGreaterThan(0.1);
    });
  });

  describe('updateRiskProfile', () => {
    it('should update risk profile successfully', async () => {
      const riskProfile = 'aggressive';
      const mockResponse = {
        success: true,
        message: 'Risk profile updated',
        new_profile: 'aggressive',
        strategies_adjusted: 3
      };
      mockApiInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await advancedTradingAPI.updateRiskProfile(riskProfile);

      expect(mockApiInstance.post).toHaveBeenCalledWith('/advanced/risk-profile', {
        risk_profile: riskProfile
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getCircuitBreakerStatus', () => {
    it('should get circuit breaker status successfully', async () => {
      const mockStatus = {
        trading_allowed: true,
        breaker_status: 'NORMAL',
        active_breakers: {
          global_loss_limit: false,
          daily_loss_limit: false,
          position_concentration: false,
          volatility_spike: false
        },
        position_sizing_multiplier: 1.0
      };
      mockApiInstance.get.mockResolvedValue({ data: mockStatus });

      const result = await advancedTradingAPI.getCircuitBreakerStatus();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/advanced/circuit-breakers');
      expect(result).toEqual(mockStatus);
      expect(result.trading_allowed).toBe(true);
    });

    it('should handle circuit breaker triggered status', async () => {
      const mockStatus = {
        trading_allowed: false,
        breaker_status: 'TRIGGERED',
        active_breakers: {
          global_loss_limit: true,
          daily_loss_limit: false,
          position_concentration: false,
          volatility_spike: true
        },
        position_sizing_multiplier: 0.5
      };
      mockApiInstance.get.mockResolvedValue({ data: mockStatus });

      const result = await advancedTradingAPI.getCircuitBreakerStatus();

      expect(result.trading_allowed).toBe(false);
      expect(result.active_breakers.global_loss_limit).toBe(true);
      expect(result.position_sizing_multiplier).toBe(0.5);
    });
  });

  describe('resetCircuitBreaker', () => {
    it('should reset circuit breaker successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Circuit breaker reset',
        breaker_type: 'global_loss_limit',
        trading_resumed: true
      };
      mockApiInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await advancedTradingAPI.resetCircuitBreaker('global_loss_limit');

      expect(mockApiInstance.post).toHaveBeenCalledWith('/advanced/circuit-breakers/reset', {
        breaker_type: 'global_loss_limit',
        scope: undefined
      });
      expect(result).toEqual(mockResponse);
    });

    it('should reset circuit breaker with scope', async () => {
      const mockResponse = {
        success: true,
        message: 'Position breaker reset for AAPL',
        breaker_type: 'position_concentration',
        scope: 'AAPL'
      };
      mockApiInstance.post.mockResolvedValue({ data: mockResponse });

      await advancedTradingAPI.resetCircuitBreaker('position_concentration', 'AAPL');

      expect(mockApiInstance.post).toHaveBeenCalledWith('/advanced/circuit-breakers/reset', {
        breaker_type: 'position_concentration',
        scope: 'AAPL'
      });
    });
  });

  describe('getAIModelsStatus', () => {
    it('should get AI models status successfully', async () => {
      const mockStatus = {
        total_models: 5,
        trained_models: 4,
        models: {
          'AAPL': {
            is_trained: true,
            last_prediction: 158.50,
            prediction_confidence: 0.92,
            training_summary: {
              data_points: 1000,
              accuracy: 0.89,
              last_trained: '2023-01-01T00:00:00Z'
            }
          },
          'GOOGL': {
            is_trained: true,
            last_prediction: 2890.00,
            prediction_confidence: 0.85
          },
          'MSFT': {
            is_trained: false,
            last_prediction: undefined,
            prediction_confidence: undefined
          }
        }
      };
      mockApiInstance.get.mockResolvedValue({ data: mockStatus });

      const result = await advancedTradingAPI.getAIModelsStatus();

      expect(mockApiInstance.get).toHaveBeenCalledWith('/advanced/ai-models/status', { params: {} });
      expect(result).toEqual(mockStatus);
      expect(result.trained_models).toBe(4);
      expect(result.models['AAPL'].is_trained).toBe(true);
    });

    it('should get AI models status for specific symbols', async () => {
      const symbols = ['AAPL', 'GOOGL'];
      const mockStatus = {
        total_models: 2,
        trained_models: 2,
        models: {
          'AAPL': { is_trained: true },
          'GOOGL': { is_trained: true }
        }
      };
      mockApiInstance.get.mockResolvedValue({ data: mockStatus });

      await advancedTradingAPI.getAIModelsStatus(symbols);

      expect(mockApiInstance.get).toHaveBeenCalledWith('/advanced/ai-models/status', {
        params: { symbols }
      });
    });
  });

  describe('retrainAIModels', () => {
    it('should retrain AI models successfully', async () => {
      const symbols = ['AAPL', 'GOOGL'];
      const mockResponse = {
        success: true,
        message: 'AI models retraining initiated',
        symbols: ['AAPL', 'GOOGL'],
        estimated_completion: '2023-01-01T12:00:00Z',
        training_jobs: [
          { symbol: 'AAPL', job_id: 'job_123', status: 'started' },
          { symbol: 'GOOGL', job_id: 'job_124', status: 'started' }
        ]
      };
      mockApiInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await advancedTradingAPI.retrainAIModels(symbols);

      expect(mockApiInstance.post).toHaveBeenCalledWith('/advanced/ai-models/retrain', {
        symbols
      });
      expect(result).toEqual(mockResponse);
      expect(result.training_jobs).toHaveLength(2);
    });

    it('should handle insufficient data error', async () => {
      const error = {
        response: {
          data: { detail: 'Insufficient historical data for training' },
          status: 400
        }
      };
      mockApiInstance.post.mockRejectedValue(error);

      await expect(advancedTradingAPI.retrainAIModels(['NEW_SYMBOL']))
        .rejects.toEqual(error);
    });
  });
});