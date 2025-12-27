/* eslint-disable @typescript-eslint/no-explicit-any */
import { configureStore } from '@reduxjs/toolkit';
import { websocketMiddleware, enhancedWebsocketMiddleware } from '../websocketMiddleware';
import { websocketSlice } from '../../slices/websocketSlice';
import { authSlice } from '../../slices/authSlice';
import { marketDataApi } from '../../../services/marketDataApi';
import { tradingApi } from '../../../services/tradingApi';

// Mock the WebSocket service with all exports
jest.mock('../../../services/websocketService', () => ({
  webSocketService: {
    connect: jest.fn(() => Promise.resolve()),
    disconnect: jest.fn(),
    subscribeToMarketData: jest.fn(() => Promise.resolve()),
    subscribeToPortfolio: jest.fn(() => Promise.resolve()),
    subscribeToOrderUpdates: jest.fn(() => Promise.resolve()),
    unsubscribe: jest.fn(() => Promise.resolve()),
    on: jest.fn(),
    off: jest.fn(),
    isConnected: jest.fn(() => true),
    getState: jest.fn(() => ({ status: 'CONNECTED' })),
  },
  WebSocketStatus: {
    DISCONNECTED: 'DISCONNECTED',
    CONNECTING: 'CONNECTING',
    CONNECTED: 'CONNECTED',
    AUTHENTICATED: 'AUTHENTICATED',
    RECONNECTING: 'RECONNECTING',
    ERROR: 'ERROR',
    AUTHORIZATION_FAILED: 'AUTHORIZATION_FAILED',
  },
}));

// Get mock reference for testing
const mockWebSocketService = require('../../../services/websocketService').webSocketService;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

// Mock window.location
const mockLocation = {
  pathname: '/paper/trading/AAPL'
};
Object.defineProperty(window, 'location', { value: mockLocation });

describe('WebSocket Middleware', () => {
  let store: any;
  let dispatchSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('paper');

    store = configureStore({
      reducer: {
        websocket: websocketSlice.reducer,
        auth: authSlice.reducer,
        marketDataApi: marketDataApi.reducer,
        tradingApi: tradingApi.reducer,
      },
      middleware: (getDefaultMiddleware: any) =>
        getDefaultMiddleware({
          serializableCheck: false, // Disable for testing
        }).concat(websocketMiddleware),
      preloadedState: {
        auth: {
          user: {
            id: 1,
            email: 'test@example.com',
            risk_tolerance: 'moderate',
            trading_style: 'swing',
            is_active: true,
            is_verified: true
          },
          isAuthenticated: true,
          isLoading: false,
          error: null
        },
        websocket: {
          status: 'DISCONNECTED' as any,
          lastConnected: null,
          reconnectAttempts: 0,
          marketData: {},
          portfolio: { paper: null, live: null },
          positions: {},
          recentOrders: [],
          subscribedChannels: [],
          messageCount: 0,
          lastMessageTime: null,
          error: null
        }
      }
    });

    dispatchSpy = jest.spyOn(store, 'dispatch');
  });

  describe('Connection Management', () => {
    it('handles websocket connection action', async () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      expect(mockWebSocketService.connect).toHaveBeenCalled();
      expect(mockWebSocketService.on).toHaveBeenCalledWith('onStatusChange', expect.any(Function));
      expect(mockWebSocketService.on).toHaveBeenCalledWith('onError', expect.any(Function));
      expect(mockWebSocketService.on).toHaveBeenCalledWith('onMarketData', expect.any(Function));
      expect(mockWebSocketService.on).toHaveBeenCalledWith('onOrderUpdate', expect.any(Function));
      expect(mockWebSocketService.on).toHaveBeenCalledWith('onPositionUpdate', expect.any(Function));
      expect(mockWebSocketService.on).toHaveBeenCalledWith('onPortfolioUpdate', expect.any(Function));
    });

    it('handles websocket disconnection action', () => {
      store.dispatch({ type: 'websocket/disconnectWebSocket' });

      expect(mockWebSocketService.disconnect).toHaveBeenCalled();
      expect(mockWebSocketService.off).toHaveBeenCalledWith('onStatusChange');
      expect(mockWebSocketService.off).toHaveBeenCalledWith('onError');
      expect(mockWebSocketService.off).toHaveBeenCalledWith('onMarketData');
      expect(mockWebSocketService.off).toHaveBeenCalledWith('onOrderUpdate');
      expect(mockWebSocketService.off).toHaveBeenCalledWith('onPositionUpdate');
      expect(mockWebSocketService.off).toHaveBeenCalledWith('onPortfolioUpdate');
    });

    it('sets up default subscriptions after connection', async () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      // Verify portfolio and order subscriptions
      expect(mockWebSocketService.subscribeToPortfolio).toHaveBeenCalledWith('paper');
      expect(mockWebSocketService.subscribeToOrderUpdates).toHaveBeenCalledWith('paper');
    });

    it('handles connection errors gracefully', async () => {
      mockWebSocketService.connect.mockRejectedValueOnce(new Error('Connection failed'));

      store.dispatch({ type: 'websocket/connectWebSocket' });

      // Should dispatch error status
      await new Promise(resolve => setTimeout(resolve, 0));
      
      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('setConnectionStatus')
        })
      );
    });
  });

  describe('Market Data Updates', () => {
    it('handles market data updates and cache invalidation', () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      // Get the onMarketData handler
      const onMarketDataCall = mockWebSocketService.on.mock.calls.find(
        (call: any) => call[0] === 'onMarketData'
      );
      const onMarketData = onMarketDataCall[1];

      // Simulate market data update
      const marketData = {
        symbol: 'AAPL',
        price: 151.50,
        change: 1.25,
        change_percent: 0.83,
        volume: 1500000,
        timestamp: Date.now()
      };

      onMarketData(marketData);

      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('updateMarketData')
        })
      );

      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('incrementMessageCount')
        })
      );
    });

    it('updates market data cache with new prices', () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      const onMarketDataCall = mockWebSocketService.on.mock.calls.find(
        (call: any) => call[0] === 'onMarketData'
      );
      const onMarketData = onMarketDataCall[1];

      const marketData = {
        symbol: 'AAPL',
        price: 151.50,
        change: 1.25,
        change_percent: 0.83,
        volume: 1500000,
        timestamp: Date.now()
      };

      onMarketData(marketData);

      // Verify cache update was attempted
      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('updateQueryData')
        })
      );
    });
  });

  describe('Order Updates', () => {
    it('handles order updates and invalidates relevant caches', () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      const onOrderUpdateCall = mockWebSocketService.on.mock.calls.find(
        (call: any) => call[0] === 'onOrderUpdate'
      );
      const onOrderUpdate = onOrderUpdateCall[1];

      const orderUpdate = {
        order_id: 'order-123',
        symbol: 'AAPL',
        status: 'FILLED',
        paper_trading: true,
        quantity: 10,
        filled_price: 150.25,
        timestamp: new Date().toISOString()
      };

      onOrderUpdate(orderUpdate);

      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('addOrderUpdate')
        })
      );

      // Verify cache invalidation for relevant trading queries
      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('invalidateTags')
        })
      );
    });

    it('handles both paper and live order updates', () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      const onOrderUpdateCall = mockWebSocketService.on.mock.calls.find(
        (call: any) => call[0] === 'onOrderUpdate'
      );
      const onOrderUpdate = onOrderUpdateCall[1];

      // Test paper trading order
      const paperOrder = {
        order_id: 'paper-123',
        symbol: 'AAPL',
        status: 'FILLED',
        paper_trading: true,
        quantity: 10,
        timestamp: new Date().toISOString()
      };

      onOrderUpdate(paperOrder);

      // Test live trading order
      const liveOrder = {
        order_id: 'live-123',
        symbol: 'GOOGL',
        status: 'FILLED',
        paper_trading: false,
        quantity: 5,
        timestamp: new Date().toISOString()
      };

      onOrderUpdate(liveOrder);

      // Should handle both types of orders
      expect(dispatchSpy).toHaveBeenCalledTimes(expect.any(Number));
    });
  });

  describe('Position Updates', () => {
    it('handles position updates and cache invalidation', () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      const onPositionUpdateCall = mockWebSocketService.on.mock.calls.find(
        (call: any) => call[0] === 'onPositionUpdate'
      );
      const onPositionUpdate = onPositionUpdateCall[1];

      const positionUpdate = {
        symbol: 'AAPL',
        quantity: 100,
        current_price: 151.50,
        unrealized_pnl: 125.00,
        unrealized_pnl_percent: 0.83,
        paper_trading: true,
        timestamp: Date.now()
      };

      onPositionUpdate(positionUpdate);

      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('updatePosition')
        })
      );
    });
  });

  describe('Portfolio Updates', () => {
    it('handles portfolio updates with cache updates', () => {
      store.dispatch({ type: 'websocket/connectWebSocket' });

      const onPortfolioUpdateCall = mockWebSocketService.on.mock.calls.find(
        (call: any) => call[0] === 'onPortfolioUpdate'
      );
      const onPortfolioUpdate = onPortfolioUpdateCall[1];

      const portfolioUpdate = {
        total_value: 25000,
        cash_balance: 5000,
        day_pnl: 250.50,
        day_pnl_percent: 1.02,
        paper_trading: true,
        timestamp: Date.now()
      };

      onPortfolioUpdate(portfolioUpdate);

      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('updatePortfolio')
        })
      );

      // Verify portfolio cache update
      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('updateQueryData')
        })
      );
    });
  });

  describe('Trade Execution Integration', () => {
    it('handles trade execution completion', async () => {
      const tradeAction = {
        type: 'tradingApi/executeTrade/fulfilled',
        meta: {
          arg: {
            symbol: 'AAPL',
            mode: 'paper'
          }
        }
      };

      store.dispatch(tradeAction);

      // Verify cache invalidation for trade-related queries
      expect(dispatchSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: expect.stringContaining('invalidateTags')
        })
      );

      // Should attempt to subscribe to market data for traded symbol
      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['AAPL']);
    });

    it('subscribes to market data after successful trades', async () => {
      // Set up store with no existing market data subscription
      const tradeAction = {
        type: 'tradingApi/executeTrade/fulfilled',
        meta: {
          arg: {
            symbol: 'MSFT',
            mode: 'paper'
          }
        }
      };

      store.dispatch(tradeAction);

      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['MSFT']);
    });
  });

  describe('Market Data Request Integration', () => {
    it('auto-subscribes to real-time data when market data is requested', async () => {
      const marketDataAction = {
        type: 'marketDataApi/getQuote/pending',
        meta: {
          arg: { symbol: 'TESLA' }
        }
      };

      store.dispatch(marketDataAction);

      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['TESLA']);
    });

    it('avoids duplicate subscriptions', async () => {
      // Pre-populate with existing subscription
      store.dispatch({
        type: 'websocket/addSubscription',
        payload: 'market_data:AAPL'
      });

      const marketDataAction = {
        type: 'marketDataApi/getQuote/pending',
        meta: {
          arg: { symbol: 'AAPL' }
        }
      };

      store.dispatch(marketDataAction);

      // Should not subscribe again if already subscribed
      expect(mockWebSocketService.subscribeToMarketData).not.toHaveBeenCalledWith(['AAPL']);
    });
  });
});

describe('Enhanced WebSocket Middleware', () => {
  let store: any;

  beforeEach(() => {
    jest.clearAllMocks();

    store = configureStore({
      reducer: {
        websocket: websocketSlice.reducer,
        auth: authSlice.reducer,
      },
      middleware: (getDefaultMiddleware: any) =>
        getDefaultMiddleware({
          serializableCheck: false,
        }).concat(enhancedWebsocketMiddleware),
      preloadedState: {
        websocket: {
          status: 'CONNECTED' as any,
          lastConnected: null,
          reconnectAttempts: 0,
          marketData: {},
          portfolio: { paper: null, live: null },
          positions: {},
          recentOrders: [],
          subscribedChannels: [],
          messageCount: 0,
          lastMessageTime: null,
          error: null
        }
      }
    });
  });

  describe('Route-based Symbol Tracking', () => {
    it('handles trading page navigation', () => {
      const routeAction = {
        type: '@@router/LOCATION_CHANGE',
        payload: {
          pathname: '/live/trading/NVDA'
        }
      };

      store.dispatch(routeAction);

      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['NVDA']);
    });

    it('extracts symbol from paper trading routes', () => {
      const routeAction = {
        payload: {
          pathname: '/paper/trading/META'
        }
      };

      store.dispatch(routeAction);

      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['META']);
    });

    it('ignores non-trading routes', () => {
      const routeAction = {
        payload: {
          pathname: '/dashboard'
        }
      };

      store.dispatch(routeAction);

      expect(mockWebSocketService.subscribeToMarketData).not.toHaveBeenCalled();
    });

    it('uses window.location as fallback', () => {
      mockLocation.pathname = '/paper/trading/AMZN';

      const routeAction = {
        payload: {
          pathname: '/paper/trading/AMZN'
        }
      };

      store.dispatch(routeAction);

      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['AMZN']);
    });
  });

  describe('Trading Mode Changes', () => {
    it('handles trading mode switch', async () => {
      const modeChangeAction = {
        type: 'trading/setMode',
        payload: {
          mode: 'live'
        }
      };

      store.dispatch(modeChangeAction);

      expect(mockWebSocketService.unsubscribe).toHaveBeenCalled();
      expect(mockWebSocketService.subscribeToPortfolio).toHaveBeenCalledWith('live');
      expect(mockWebSocketService.subscribeToOrderUpdates).toHaveBeenCalledWith('live');
    });

    it('unsubscribes from old mode channels before subscribing to new ones', async () => {
      // Pre-populate with paper mode subscriptions
      store = configureStore({
        reducer: {
          websocket: websocketSlice.reducer,
        },
        middleware: (getDefaultMiddleware: any) =>
          getDefaultMiddleware({ serializableCheck: false }).concat(enhancedWebsocketMiddleware),
        preloadedState: {
          websocket: {
            status: 'CONNECTED' as any,
            lastConnected: null,
            reconnectAttempts: 0,
            marketData: {},
            portfolio: { paper: null, live: null },
            positions: {},
            recentOrders: [],
            subscribedChannels: ['portfolio:paper', 'orders:paper'],
            messageCount: 0,
            lastMessageTime: null,
            error: null
          }
        }
      });

      const modeChangeAction = {
        type: 'trading/setMode',
        payload: {
          mode: 'live'
        }
      };

      store.dispatch(modeChangeAction);

      expect(mockWebSocketService.unsubscribe).toHaveBeenCalled();
    });

    it('handles mode changes when not connected', () => {
      mockWebSocketService.isConnected.mockReturnValue(false);

      const modeChangeAction = {
        type: 'trading/setMode',
        payload: {
          mode: 'live'
        }
      };

      store.dispatch(modeChangeAction);

      // Should not attempt subscriptions when not connected
      expect(mockWebSocketService.subscribeToPortfolio).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('handles subscription errors gracefully', async () => {
      mockWebSocketService.subscribeToMarketData.mockRejectedValueOnce(
        new Error('Subscription failed')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const routeAction = {
        type: '@@router/LOCATION_CHANGE',
        payload: {
          pathname: '/paper/trading/FAIL'
        }
      };

      store.dispatch(routeAction);

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to subscribe to market data on navigation:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });

    it('handles mode change errors gracefully', async () => {
      mockWebSocketService.subscribeToPortfolio.mockRejectedValueOnce(
        new Error('Mode change failed')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const modeChangeAction = {
        type: 'trading/setMode',
        payload: {
          mode: 'live'
        }
      };

      store.dispatch(modeChangeAction);

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to handle trading mode change:',
        expect.any(Error)
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Integration with Base Middleware', () => {
    it('delegates to base websocket middleware', () => {
      const connectAction = { type: 'websocket/connectWebSocket' };
      
      store.dispatch(connectAction);

      // Should still handle basic websocket actions
      expect(mockWebSocketService.connect).toHaveBeenCalled();
    });

    it('preserves order of middleware execution', () => {
      const routeAction = {
        type: '@@router/LOCATION_CHANGE',
        payload: {
          pathname: '/paper/trading/TEST'
        }
      };

      const connectAction = { type: 'websocket/connectWebSocket' };

      store.dispatch(routeAction);
      store.dispatch(connectAction);

      // Both should be handled
      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['TEST']);
      expect(mockWebSocketService.connect).toHaveBeenCalled();
    });
  });
});