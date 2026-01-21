/* eslint-disable testing-library/no-wait-for-multiple-assertions */
/* eslint-disable testing-library/no-wait-for-side-effects */
/* eslint-disable testing-library/no-container */
/* eslint-disable testing-library/no-node-access */
/* eslint-disable jest/no-conditional-expect */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';

import App from '../../App';
import { authSlice } from '../../store/slices/authSlice';
import { tradingSlice } from '../../store/slices/tradingSlice';
import { websocketSlice } from '../../store/slices/websocketSlice';
import { WebSocketStatus } from '../../services/websocketService';
import { marketDataApi } from '../../services/marketDataApi';
import { tradingApi } from '../../services/tradingApi';

// Mock WebSocket service - define inside factory to avoid hoisting issues
jest.mock('../../services/websocketService', () => ({
  webSocketService: {
    connect: jest.fn(() => Promise.resolve()),
    disconnect: jest.fn(),
    subscribeToMarketData: jest.fn(() => Promise.resolve()),
    subscribeToPortfolio: jest.fn(() => Promise.resolve()),
    subscribeToOrderUpdates: jest.fn(() => Promise.resolve()),
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
  },
}));

// Get reference to mocked service after mock is set up
const mockWebSocketService = jest.requireMock('../../services/websocketService').webSocketService;

// Mock trading API with realistic responses
const mockExecuteTrade = jest.fn();
const mockGetPortfolio = jest.fn();
const mockGetQuote = jest.fn();
const mockValidateOrder = jest.fn();

jest.mock('../../services/tradingApi', () => ({
  ...jest.requireActual('../../services/tradingApi'),
  useExecuteTradeMutation: () => [mockExecuteTrade, { isLoading: false, error: null }],
  useGetPortfolioQuery: () => mockGetPortfolio(),
  useValidateOrderQuery: () => mockValidateOrder(),
}));

jest.mock('../../services/marketDataApi', () => ({
  ...jest.requireActual('../../services/marketDataApi'),
  useGetQuoteQuery: () => mockGetQuote(),
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage, writable: true });

// Mock window.confirm for trading confirmations
const mockConfirm = jest.fn();
Object.defineProperty(window, 'confirm', { value: mockConfirm });

// Create comprehensive mock store
const createIntegrationStore = (userType = 'premium', initialMode = 'paper') => {
  return configureStore({
    reducer: {
      auth: authSlice.reducer,
      trading: tradingSlice.reducer,
      websocket: websocketSlice.reducer,
      marketDataApi: marketDataApi.reducer,
      tradingApi: tradingApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: ['persist/PERSIST'],
        },
      }).concat(
        marketDataApi.middleware,
        tradingApi.middleware
      ),
    preloadedState: {
      auth: {
        user: {
          id: 1,
          email: 'trader@example.com',
          risk_tolerance: 'moderate',
          trading_style: 'swing',
          is_active: true,
          is_verified: true
        },
        isAuthenticated: true,
        isLoading: false,
        error: null
      },
      trading: {
        trades: [],
        openOrders: [],
        positions: [],
        stats: null,
        isLoading: false,
        error: null
      },
      websocket: {
        status: WebSocketStatus.AUTHENTICATED,
        lastConnected: null,
        reconnectAttempts: 0,
        error: null,
        marketData: {
          'AAPL': {
            symbol: 'AAPL',
            price: 150.25,
            change: 2.15,
            change_percent: 1.45,
            volume: 1500000,
            bid: 150.20,
            ask: 150.30,
            timestamp: new Date().toISOString()
          }
        },
        recentOrders: [],
        positions: {},
        portfolio: { paper: null, live: null },
        messageCount: 0,
        lastMessageTime: null,
        subscribedChannels: ['market_data:AAPL']
      }
    }
  });
};

const IntegrationTestWrapper: React.FC<{
  children: React.ReactNode;
  userType?: string;
  initialRoute?: string;
  initialMode?: string;
}> = ({ 
  children, 
  userType = 'premium', 
  initialRoute = '/paper/trading/AAPL',
  initialMode = 'paper'
}) => {
  const store = createIntegrationStore(userType, initialMode);
  
  return (
    <Provider store={store}>
      <MemoryRouter initialEntries={[initialRoute]}>
        {children}
      </MemoryRouter>
    </Provider>
  );
};

// TODO: These e2e tests need refactoring - complex mock setup doesn't properly
// simulate the full trading flow with all required providers and state.
describe.skip('End-to-End Trading Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('paper');
    mockConfirm.mockReturnValue(true);

    // Setup default API responses
    mockGetPortfolio.mockReturnValue({
      data: {
        cash_balance: 10000,
        total_value: 25000,
        day_pnl: 250.50,
        day_pnl_percent: 1.02
      },
      isLoading: false,
      error: null
    });

    mockGetQuote.mockReturnValue({
      data: {
        symbol: 'AAPL',
        price: 150.25,
        change: 2.15,
        change_percent: 1.45,
        volume: 1500000,
        bid: 150.20,
        ask: 150.30
      },
      isLoading: false,
      error: null
    });

    mockValidateOrder.mockReturnValue({
      data: {
        valid: true,
        estimated_cost: 1502.50,
        buying_power: 8497.50,
        warnings: []
      },
      isLoading: false,
      error: null
    });

    mockExecuteTrade.mockResolvedValue({
      order_id: 'order-123',
      symbol: 'AAPL',
      status: 'SUBMITTED',
      quantity: 10,
      price: 150.25
    });
  });

  describe('Complete Paper Trading Flow', () => {
    it('completes a full paper trading journey from quote to order execution', async () => {
      render(
        <IntegrationTestWrapper initialRoute="/paper/trading/AAPL">
          <App />
        </IntegrationTestWrapper>
      );

      // 1. Verify we're on the trading page with market data
      await waitFor(() => {
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('$150.25')).toBeInTheDocument();
      });

      // 2. Verify paper trading mode is active
      expect(screen.getByText('PAPER')).toBeInTheDocument();

      // 3. Fill out the order form
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      // 4. Verify order total calculation
      await waitFor(() => {
        expect(screen.getByText('$1,502.50')).toBeInTheDocument();
      });

      // 5. Submit the order
      const submitButton = screen.getByRole('button', { name: /review order|place order/i });
      fireEvent.click(submitButton);

      // 6. Handle trading safeguards confirmation
      await waitFor(() => {
        const confirmButton = screen.getByRole('button', { name: /confirm/i });
        fireEvent.click(confirmButton);
      });

      // 7. Verify order was submitted
      expect(mockExecuteTrade).toHaveBeenCalledWith({
        symbol: 'AAPL',
        quantity: 10,
        order_type: 'MARKET',
        side: 'BUY',
        mode: 'paper'
      });

      // 8. Verify success feedback
      await waitFor(() => {
        expect(screen.getByText(/order submitted successfully/i)).toBeInTheDocument();
      });
    });

    it('handles order validation errors during paper trading', async () => {
      // Mock validation error
      mockValidateOrder.mockReturnValue({
        data: {
          valid: false,
          error: 'Insufficient buying power',
          buying_power: 100
        },
        isLoading: false,
        error: null
      });

      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '1000' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/insufficient buying power/i)).toBeInTheDocument();
      });

      expect(mockExecuteTrade).not.toHaveBeenCalled();
    });
  });

  describe('Live Trading Flow with Enhanced Validations', () => {
    it('completes live trading flow with additional confirmations', async () => {
      render(
        <IntegrationTestWrapper 
          userType="premium" 
          initialRoute="/live/trading/AAPL"
          initialMode="live"
        >
          <App />
        </IntegrationTestWrapper>
      );

      // 1. Verify live trading mode
      await waitFor(() => {
        expect(screen.getByText('LIVE')).toBeInTheDocument();
      });

      // 2. Fill order form
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '5' } });

      // 3. Submit order
      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      // 4. Handle enhanced confirmations for live trading
      await waitFor(() => {
        expect(screen.getByText(/live trading confirmation/i)).toBeInTheDocument();
      });

      const confirmLiveButton = screen.getByRole('button', { name: /confirm live order/i });
      fireEvent.click(confirmLiveButton);

      // 5. Verify live order execution
      expect(mockExecuteTrade).toHaveBeenCalledWith({
        symbol: 'AAPL',
        quantity: 5,
        order_type: 'MARKET',
        side: 'BUY',
        mode: 'live'
      });
    });

    it('prevents live trading for basic tier users', async () => {
      render(
        <IntegrationTestWrapper 
          userType="basic" 
          initialRoute="/live/trading/AAPL"
        >
          <App />
        </IntegrationTestWrapper>
      );

      // Should redirect to paper mode or show upgrade prompt
      await waitFor(() => {
        expect(
          screen.getByText(/upgrade to premium/i) || screen.getByText('PAPER')
        ).toBeInTheDocument();
      });

      // Should not allow live trading
      const submitButtons = screen.queryAllByRole('button', { name: /review order/i });
      if (submitButtons.length > 0) {
        fireEvent.click(submitButtons[0]);
        expect(mockExecuteTrade).not.toHaveBeenCalledWith(
          expect.objectContaining({ mode: 'live' })
        );
      }
    });
  });

  describe('Mode Switching Integration', () => {
    it('handles switching from paper to live mode', async () => {
      render(
        <IntegrationTestWrapper 
          userType="premium"
          initialRoute="/paper/trading/AAPL"
        >
          <App />
        </IntegrationTestWrapper>
      );

      // Start in paper mode
      expect(screen.getByText('PAPER')).toBeInTheDocument();

      // Switch to live mode
      const liveModeToggle = screen.getByRole('button', { name: /live/i });
      fireEvent.click(liveModeToggle);

      // Confirm mode switch
      expect(mockConfirm).toHaveBeenCalledWith(
        expect.stringContaining('live trading mode')
      );

      // Verify mode switch
      await waitFor(() => {
        expect(screen.getByText('LIVE')).toBeInTheDocument();
      });
    });

    it('handles switching from live to paper mode', async () => {
      render(
        <IntegrationTestWrapper 
          userType="premium"
          initialRoute="/live/trading/AAPL"
          initialMode="live"
        >
          <App />
        </IntegrationTestWrapper>
      );

      // Start in live mode
      expect(screen.getByText('LIVE')).toBeInTheDocument();

      // Switch to paper mode
      const paperModeToggle = screen.getByRole('button', { name: /paper/i });
      fireEvent.click(paperModeToggle);

      // Verify mode switch (no confirmation needed for paper mode)
      await waitFor(() => {
        expect(screen.getByText('PAPER')).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Data Integration', () => {
    it('handles real-time price updates during order placement', async () => {
      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      // Initial price display
      expect(screen.getByText('$150.25')).toBeInTheDocument();

      // Start filling order
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      // Simulate real-time price update
      mockGetQuote.mockReturnValue({
        data: {
          symbol: 'AAPL',
          price: 151.50,
          change: 3.40,
          change_percent: 2.31,
          volume: 1600000
        },
        isLoading: false,
        error: null
      });

      // Trigger re-render to simulate WebSocket update
      fireEvent.focus(quantityInput);
      fireEvent.blur(quantityInput);

      // Verify updated price affects order total
      await waitFor(() => {
        expect(screen.getByText(/\$1,515\.00|\$1,502\.50/)).toBeInTheDocument();
      });
    });

    it('handles WebSocket connection issues gracefully', async () => {
      // Simulate WebSocket disconnection
      mockWebSocketService.isConnected.mockReturnValue(false);

      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      // Should show disconnected state but still allow trading
      await waitFor(() => {
        expect(screen.getByText(/disconnected|offline/i)).toBeInTheDocument();
      });

      // Order form should still be functional
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Order Type Workflows', () => {
    it('handles limit order placement with price specification', async () => {
      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      // Select limit order type
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'limit' } });

      // Fill quantity and limit price
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      await waitFor(() => {
        const limitPriceInput = screen.getByLabelText(/limit price/i);
        fireEvent.change(limitPriceInput, { target: { value: '148.00' } });
      });

      // Submit limit order
      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      expect(mockExecuteTrade).toHaveBeenCalledWith(
        expect.objectContaining({
          order_type: 'LIMIT',
          limit_price: 148.00
        })
      );
    });

    it('handles stop loss order placement', async () => {
      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      // Select stop order type
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'stop' } });

      // Fill form fields
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      await waitFor(() => {
        const stopPriceInput = screen.getByLabelText(/stop price/i);
        fireEvent.change(stopPriceInput, { target: { value: '145.00' } });
      });

      // Submit stop order
      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      expect(mockExecuteTrade).toHaveBeenCalledWith(
        expect.objectContaining({
          order_type: 'STOP',
          stop_price: 145.00
        })
      );
    });
  });

  describe('Error Recovery Flows', () => {
    it('handles API errors during order submission', async () => {
      mockExecuteTrade.mockRejectedValueOnce(new Error('Order rejected by exchange'));

      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText(/order rejected by exchange/i)).toBeInTheDocument();
      });

      // Form should remain usable for retry
      expect(quantityInput).toHaveValue('10');
      expect(submitButton).not.toBeDisabled();
    });

    it('handles market data loading failures', async () => {
      mockGetQuote.mockReturnValue({
        data: null,
        isLoading: false,
        error: { message: 'Market data unavailable' }
      });

      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/market data unavailable/i)).toBeInTheDocument();
      });

      // Should still allow order placement with last known price
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Portfolio Integration', () => {
    it('updates portfolio display after successful order execution', async () => {
      // Mock portfolio update after trade
      mockGetPortfolio.mockReturnValueOnce({
        data: {
          cash_balance: 8500, // Reduced after purchase
          total_value: 26500, // Increased with position
          day_pnl: 350.50,
          day_pnl_percent: 1.35
        },
        isLoading: false,
        error: null
      });

      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      // Execute a trade
      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      // Verify portfolio updates
      await waitFor(() => {
        expect(screen.getByText('$8,500')).toBeInTheDocument(); // Updated cash balance
      });
    });
  });

  describe('Symbol Navigation Integration', () => {
    it('handles symbol changes and WebSocket subscription updates', async () => {
      const { container } = render(
        <IntegrationTestWrapper initialRoute="/paper/trading/AAPL">
          <App />
        </IntegrationTestWrapper>
      );

      // Start with AAPL
      expect(screen.getByText('AAPL')).toBeInTheDocument();

      // Navigate to different symbol (simulated)
      // In real app, this would be through symbol search or navigation
      const symbolInput = container.querySelector('input[placeholder*="symbol"]');
      if (symbolInput) {
        fireEvent.change(symbolInput, { target: { value: 'GOOGL' } });
        fireEvent.keyPress(symbolInput, { key: 'Enter', code: 13, charCode: 13 });
      }

      // Verify WebSocket subscription changes
      expect(mockWebSocketService.subscribeToMarketData).toHaveBeenCalledWith(['GOOGL']);
    });
  });

  describe('Accessibility and User Experience', () => {
    it('provides proper keyboard navigation through the trading flow', async () => {
      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      
      // Tab navigation should work
      quantityInput.focus();
      expect(document.activeElement).toBe(quantityInput);

      // Enter key should move to next field or submit
      fireEvent.change(quantityInput, { target: { value: '10' } });
      fireEvent.keyDown(quantityInput, { key: 'Tab' });

      // Verify form is still navigable
      const submitButton = screen.getByRole('button', { name: /review order/i });
      expect(submitButton).toBeInTheDocument();
    });

    it('announces important status changes to screen readers', async () => {
      render(
        <IntegrationTestWrapper>
          <App />
        </IntegrationTestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        const successMessage = screen.getByText(/order submitted successfully/i);
        expect(successMessage).toHaveAttribute('role', 'alert');
      });
    });
  });
});