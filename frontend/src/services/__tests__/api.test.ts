import axios from 'axios';
import { authAPI, tradingAPI, marketDataAPI, portfolioAPI } from '../api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock the axios instance created in api.ts
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

mockedAxios.create = jest.fn().mockReturnValue(mockApiInstance);

describe('API Service Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('Auth API', () => {
    describe('login', () => {
      it('should login successfully and store token', async () => {
        const mockResponse = {
          access_token: 'test-token',
          user: { id: 1, email: 'test@example.com' }
        };
        mockApiInstance.post.mockResolvedValue({ data: mockResponse });

        const result = await authAPI.login('test@example.com', 'password');

        expect(mockApiInstance.post).toHaveBeenCalledWith('/auth/login', {
          email: 'test@example.com',
          password: 'password'
        });
        expect(result).toEqual(mockResponse);
        expect(localStorage.getItem('token')).toBe('test-token');
      });

      it('should handle login errors', async () => {
        const error = {
          response: {
            data: { detail: 'Invalid credentials' },
            status: 401
          }
        };
        mockApiInstance.post.mockRejectedValue(error);

        await expect(authAPI.login('test@example.com', 'wrong-password'))
          .rejects.toEqual(error);
      });

      it('should handle network errors', async () => {
        const networkError = new Error('Network Error');
        mockApiInstance.post.mockRejectedValue(networkError);

        await expect(authAPI.login('test@example.com', 'password'))
          .rejects.toEqual(networkError);
      });
    });

    describe('register', () => {
      it('should register successfully', async () => {
        const userData = {
          email: 'test@example.com',
          password: 'password',
          full_name: 'Test User'
        };
        const mockResponse = {
          access_token: 'test-token',
          user: { id: 1, ...userData }
        };
        mockApiInstance.post.mockResolvedValue({ data: mockResponse });

        const result = await authAPI.register(userData);

        expect(mockApiInstance.post).toHaveBeenCalledWith('/auth/register', userData);
        expect(result).toEqual(mockResponse);
        expect(localStorage.getItem('token')).toBe('test-token');
      });

      it('should handle registration validation errors', async () => {
        const error = {
          response: {
            data: { detail: 'Email already exists' },
            status: 400
          }
        };
        mockApiInstance.post.mockRejectedValue(error);

        await expect(authAPI.register({
          email: 'existing@example.com',
          password: 'password'
        })).rejects.toEqual(error);
      });
    });

    describe('getCurrentUser', () => {
      it('should get current user successfully', async () => {
        const mockUser = {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          risk_tolerance: 'moderate',
          trading_style: 'conservative',
          is_active: true,
          is_verified: true
        };
        mockApiInstance.get.mockResolvedValue({ data: mockUser });

        const result = await authAPI.getCurrentUser();

        expect(mockApiInstance.get).toHaveBeenCalledWith('/auth/me');
        expect(result).toEqual(mockUser);
      });

      it('should handle authentication errors', async () => {
        const error = {
          response: {
            data: { detail: 'Token expired' },
            status: 401
          }
        };
        mockApiInstance.get.mockRejectedValue(error);

        await expect(authAPI.getCurrentUser()).rejects.toEqual(error);
      });
    });
  });

  describe('Trading API', () => {
    describe('placeOrder', () => {
      it('should place order successfully', async () => {
        const orderData = {
          symbol: 'AAPL',
          trade_type: 'buy',
          order_type: 'market',
          quantity: 10
        };
        const mockResponse = {
          id: 1,
          ...orderData,
          status: 'pending',
          created_at: '2023-01-01T00:00:00Z'
        };
        mockApiInstance.post.mockResolvedValue({ data: mockResponse });

        const result = await tradingAPI.placeOrder(orderData);

        expect(mockApiInstance.post).toHaveBeenCalledWith('/trading/order', orderData);
        expect(result).toEqual(mockResponse);
      });

      it('should handle insufficient funds error', async () => {
        const error = {
          response: {
            data: { detail: 'Insufficient funds' },
            status: 400
          }
        };
        mockApiInstance.post.mockRejectedValue(error);

        await expect(tradingAPI.placeOrder({
          symbol: 'AAPL',
          trade_type: 'buy',
          order_type: 'market',
          quantity: 1000000
        })).rejects.toEqual(error);
      });
    });

    describe('getOpenOrders', () => {
      it('should get open orders successfully', async () => {
        const mockOrders = [
          {
            id: 1,
            symbol: 'AAPL',
            trade_type: 'buy',
            order_type: 'limit',
            quantity: 10,
            price: 150,
            status: 'pending',
            created_at: '2023-01-01T00:00:00Z'
          }
        ];
        mockApiInstance.get.mockResolvedValue({ data: mockOrders });

        const result = await tradingAPI.getOpenOrders();

        expect(mockApiInstance.get).toHaveBeenCalledWith('/trading/orders');
        expect(result).toEqual(mockOrders);
      });
    });

    describe('getTradeHistory', () => {
      it('should get trade history with default limit', async () => {
        const mockHistory = [
          {
            id: 1,
            symbol: 'AAPL',
            trade_type: 'buy',
            order_type: 'market',
            quantity: 10,
            status: 'executed',
            created_at: '2023-01-01T00:00:00Z',
            executed_at: '2023-01-01T00:01:00Z'
          }
        ];
        mockApiInstance.get.mockResolvedValue({ data: mockHistory });

        const result = await tradingAPI.getTradeHistory();

        expect(mockApiInstance.get).toHaveBeenCalledWith('/trading/history?limit=100');
        expect(result).toEqual(mockHistory);
      });

      it('should get trade history with custom limit', async () => {
        const mockHistory: any[] = [];
        mockApiInstance.get.mockResolvedValue({ data: mockHistory });

        await tradingAPI.getTradeHistory(50);

        expect(mockApiInstance.get).toHaveBeenCalledWith('/trading/history?limit=50');
      });
    });
  });

  describe('Market Data API', () => {
    describe('getQuote', () => {
      it('should get quote successfully', async () => {
        const mockQuote = {
          symbol: 'AAPL',
          open: 150,
          high: 155,
          low: 149,
          price: 152,
          volume: 1000000,
          change: 2,
          change_percent: 1.33,
          previous_close: 150,
          source: 'test',
          timestamp: '2023-01-01T00:00:00Z'
        };
        mockApiInstance.get.mockResolvedValue({ data: mockQuote });

        const result = await marketDataAPI.getQuote('AAPL');

        expect(mockApiInstance.get).toHaveBeenCalledWith('/market/quote/AAPL');
        expect(result).toEqual(mockQuote);
      });

      it('should handle invalid symbol error', async () => {
        const error = {
          response: {
            data: { detail: 'Symbol not found' },
            status: 404
          }
        };
        mockApiInstance.get.mockRejectedValue(error);

        await expect(marketDataAPI.getQuote('INVALID')).rejects.toEqual(error);
      });
    });

    describe('getMultipleQuotes', () => {
      it('should get multiple quotes successfully', async () => {
        const symbols = ['AAPL', 'GOOGL', 'MSFT'];
        const mockResponse = {
          quotes: [
            { symbol: 'AAPL', price: 152, source: 'test' },
            { symbol: 'GOOGL', price: 2800, source: 'test' },
            { symbol: 'MSFT', price: 310, source: 'test' }
          ],
          timestamp: '2023-01-01T00:00:00Z'
        };
        mockApiInstance.post.mockResolvedValue({ data: mockResponse });

        const result = await marketDataAPI.getMultipleQuotes(symbols);

        expect(mockApiInstance.post).toHaveBeenCalledWith('/market/quotes', symbols);
        expect(result).toEqual(mockResponse);
      });
    });

    describe('getAssets', () => {
      it('should get assets without filters', async () => {
        const mockAssets = [
          {
            id: 1,
            symbol: 'AAPL',
            name: 'Apple Inc.',
            asset_type: 'stock',
            exchange: 'NASDAQ',
            sector: 'Technology',
            is_tradable: true
          }
        ];
        mockApiInstance.get.mockResolvedValue({ data: mockAssets });

        const result = await marketDataAPI.getAssets();

        expect(mockApiInstance.get).toHaveBeenCalledWith('/market/assets?');
        expect(result).toEqual(mockAssets);
      });

      it('should get assets with filters', async () => {
        const params = {
          asset_type: 'stock',
          sector: 'Technology',
          limit: 50
        };
        const mockAssets: any[] = [];
        mockApiInstance.get.mockResolvedValue({ data: mockAssets });

        await marketDataAPI.getAssets(params);

        expect(mockApiInstance.get).toHaveBeenCalledWith(
          '/market/assets?asset_type=stock&sector=Technology&limit=50'
        );
      });
    });
  });

  describe('Portfolio API', () => {
    describe('getPortfolioSummary', () => {
      it('should get portfolio summary successfully', async () => {
        const mockSummary = {
          portfolio: {
            id: 1,
            name: 'Main Portfolio',
            total_value: 10000,
            cash_balance: 1000,
            invested_amount: 9000,
            total_return: 500,
            total_return_percentage: 5.56,
            auto_rebalance: false,
            is_active: true,
            created_at: '2023-01-01T00:00:00Z'
          },
          holdings: [
            {
              id: 1,
              symbol: 'AAPL',
              asset_type: 'stock',
              quantity: 10,
              average_cost: 150,
              current_price: 152,
              market_value: 1520,
              unrealized_gain_loss: 20,
              unrealized_gain_loss_percentage: 1.33
            }
          ],
          total_positions: 1
        };
        mockApiInstance.get.mockResolvedValue({ data: mockSummary });

        const result = await portfolioAPI.getPortfolioSummary();

        expect(mockApiInstance.get).toHaveBeenCalledWith('/portfolio/');
        expect(result).toEqual(mockSummary);
      });
    });

    describe('updatePortfolio', () => {
      it('should update portfolio successfully', async () => {
        const updateData = {
          name: 'Updated Portfolio',
          auto_rebalance: true
        };
        const mockUpdated = {
          id: 1,
          ...updateData,
          total_value: 10000,
          cash_balance: 1000,
          invested_amount: 9000,
          total_return: 500,
          total_return_percentage: 5.56,
          is_active: true,
          created_at: '2023-01-01T00:00:00Z'
        };
        mockApiInstance.put.mockResolvedValue({ data: mockUpdated });

        const result = await portfolioAPI.updatePortfolio(updateData);

        expect(mockApiInstance.put).toHaveBeenCalledWith('/portfolio/', updateData);
        expect(result).toEqual(mockUpdated);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle 500 server errors', async () => {
      const serverError = {
        response: {
          data: { detail: 'Internal server error' },
          status: 500
        }
      };
      mockApiInstance.get.mockRejectedValue(serverError);

      await expect(portfolioAPI.getPortfolioSummary()).rejects.toEqual(serverError);
    });

    it('should handle network timeout errors', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      };
      mockApiInstance.get.mockRejectedValue(timeoutError);

      await expect(portfolioAPI.getPortfolioSummary()).rejects.toEqual(timeoutError);
    });

    it('should handle 403 authorization errors', async () => {
      const authError = {
        response: {
          data: { detail: 'Insufficient permissions' },
          status: 403
        }
      };
      mockApiInstance.get.mockRejectedValue(authError);

      await expect(tradingAPI.getOpenOrders()).rejects.toEqual(authError);
    });
  });
});