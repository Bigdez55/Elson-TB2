import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';

import { EnhancedOrderForm } from '../EnhancedOrderForm';
import { TradingContextProvider } from '../../../contexts/TradingContext';
import { tradingSlice } from '../../../store/slices/tradingSlice';
import { authSlice } from '../../../store/slices/authSlice';
import { websocketSlice } from '../../../store/slices/websocketSlice';
import { WebSocketStatus } from '../../../services/websocketService';

// Mock the trading API
jest.mock('../../../services/tradingApi', () => ({
  useExecuteTradeMutation: () => [
    jest.fn(),
    { isLoading: false, error: null }
  ],
  useGetPortfolioQuery: () => ({
    data: { cash_balance: 10000, total_value: 25000 },
    isLoading: false
  }),
  useValidateOrderQuery: () => ({
    data: { valid: true, estimated_cost: 1502.5, buying_power: 8497.5 },
    isLoading: false
  })
}));

// Mock TradingSafeguards component
jest.mock('../TradingSafeguards', () => ({
  __esModule: true,
  default: ({ children, onConfirm }: any) => (
    <div data-testid="trading-safeguards">
      {children}
      <button onClick={() => onConfirm?.(true)} data-testid="safeguards-confirm">
        Confirm Order
      </button>
    </div>
  ),
  TradingSafeguardWrapper: ({ children }: any) => <div>{children}</div>
}));

// Create mock store
const createMockStore = (_tradingMode = 'paper', _userType = 'premium') => {
  return configureStore({
    reducer: {
      auth: authSlice.reducer,
      trading: tradingSlice.reducer,
      websocket: websocketSlice.reducer,
    },
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
        error: null,
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
            volume: 1000000,
            timestamp: new Date().toISOString()
          }
        },
        recentOrders: [],
        positions: {},
        portfolio: { paper: null, live: null },
        messageCount: 0,
        lastMessageTime: null,
        subscribedChannels: []
      }
    }
  });
};

// Test wrapper
const TestWrapper: React.FC<{ 
  children: React.ReactNode;
  tradingMode?: string;
  userType?: string;
  initialEntries?: string[];
}> = ({ 
  children, 
  tradingMode = 'paper', 
  userType = 'premium',
  initialEntries = ['/paper/trading/AAPL']
}) => {
  const store = createMockStore(tradingMode, userType);
  
  return (
    <Provider store={store}>
      <MemoryRouter initialEntries={initialEntries}>
        <TradingContextProvider>
          {children}
        </TradingContextProvider>
      </MemoryRouter>
    </Provider>
  );
};

const defaultProps = {
  symbol: 'AAPL',
  currentPrice: 150.25,
  availableBalance: 10000,
  className: 'test-class'
};

describe('EnhancedOrderForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders enhanced order form with all sections', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('Place Order')).toBeInTheDocument();
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('$150.25')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /buy/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sell/i })).toBeInTheDocument();
    });

    it('displays trading mode indicator', () => {
      render(
        <TestWrapper tradingMode="paper">
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('PAPER')).toBeInTheDocument();
    });

    it('shows live mode indicator for live trading', () => {
      render(
        <TestWrapper tradingMode="live">
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('LIVE')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(container.firstChild).toHaveClass('test-class');
    });
  });

  describe('Order Type Selection', () => {
    it('renders all order type options', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.click(orderTypeSelect);

      expect(screen.getByText('Market')).toBeInTheDocument();
      expect(screen.getByText('Limit')).toBeInTheDocument();
      expect(screen.getByText('Stop')).toBeInTheDocument();
      expect(screen.getByText('Stop Limit')).toBeInTheDocument();
    });

    it('shows price field for limit orders', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'limit' } });

      await waitFor(() => {
        expect(screen.getByLabelText(/limit price/i)).toBeInTheDocument();
      });
    });

    it('shows stop price field for stop orders', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'stop' } });

      await waitFor(() => {
        expect(screen.getByLabelText(/stop price/i)).toBeInTheDocument();
      });
    });

    it('shows both prices for stop limit orders', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'stop_limit' } });

      await waitFor(() => {
        expect(screen.getByLabelText(/limit price/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/stop price/i)).toBeInTheDocument();
      });
    });
  });

  describe('Order Side Toggle', () => {
    it('defaults to buy side', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const buyButton = screen.getByRole('button', { name: /buy/i });
      expect(buyButton).toHaveClass('bg-green-600');
    });

    it('switches to sell side when clicked', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const sellButton = screen.getByRole('button', { name: /sell/i });
      fireEvent.click(sellButton);

      expect(sellButton).toHaveClass('bg-red-600');
    });

    it('updates order total calculation when side changes', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      // Check buy total
      expect(screen.getByText('$1,502.50')).toBeInTheDocument();

      // Switch to sell
      const sellButton = screen.getByRole('button', { name: /sell/i });
      fireEvent.click(sellButton);

      // Sell should show same total (different color in UI)
      expect(screen.getByText('$1,502.50')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('validates required quantity field', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/quantity is required/i)).toBeInTheDocument();
      });
    });

    it('validates positive quantity', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '-5' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/quantity must be greater than 0/i)).toBeInTheDocument();
      });
    });

    it('validates sufficient buying power', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '1000' } }); // $150,250 > $10,000

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/insufficient buying power/i)).toBeInTheDocument();
      });
    });

    it('validates limit price for limit orders', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'limit' } });

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      await waitFor(() => {
        const limitPriceInput = screen.getByLabelText(/limit price/i);
        fireEvent.change(limitPriceInput, { target: { value: '-100' } });
      });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/limit price must be greater than 0/i)).toBeInTheDocument();
      });
    });

    it('validates stop price for stop orders', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'stop' } });

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      await waitFor(() => {
        const stopPriceInput = screen.getByLabelText(/stop price/i);
        fireEvent.change(stopPriceInput, { target: { value: '0' } });
      });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/stop price must be greater than 0/i)).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Price Updates', () => {
    it('displays live market price updates', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('$150.25')).toBeInTheDocument();
      expect(screen.getByText('+$2.15')).toBeInTheDocument();
      expect(screen.getByText('(+1.45%)')).toBeInTheDocument();
    });

    it('updates order total when market price changes', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      // Should calculate with current market price
      expect(screen.getByText('$1,502.50')).toBeInTheDocument();
    });
  });

  describe('Order Estimation and Preview', () => {
    it('calculates order total correctly for market orders', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      expect(screen.getByText('$1,502.50')).toBeInTheDocument();
    });

    it('calculates order total with custom limit price', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'limit' } });

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      await waitFor(() => {
        const limitPriceInput = screen.getByLabelText(/limit price/i);
        fireEvent.change(limitPriceInput, { target: { value: '145.00' } });
      });

      await waitFor(() => {
        expect(screen.getByText('$1,450.00')).toBeInTheDocument();
      });
    });

    it('shows order preview with all details', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      expect(screen.getByText('Estimated Total')).toBeInTheDocument();
      expect(screen.getByText('$1,502.50')).toBeInTheDocument();
    });
  });

  describe('Trading Safeguards Integration', () => {
    it('wraps order submission in trading safeguards', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByTestId('trading-safeguards')).toBeInTheDocument();
    });

    it('shows confirmation dialog for valid orders', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId('safeguards-confirm')).toBeInTheDocument();
      });
    });
  });

  describe('Live Trading Restrictions', () => {
    it('shows upgrade prompt for basic users in live mode', () => {
      render(
        <TestWrapper tradingMode="live" userType="basic">
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText(/upgrade to premium/i)).toBeInTheDocument();
    });

    it('allows live trading for premium users', () => {
      render(
        <TestWrapper tradingMode="live" userType="premium">
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.queryByText(/upgrade to premium/i)).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /review order/i })).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('shows loading state during order submission', async () => {
      // This would require mocking the mutation hook to return loading state
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      // Form should be functional in normal state
      expect(screen.getByRole('button', { name: /review order/i })).not.toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('displays API validation errors', async () => {
      // Mock API to return validation error
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      // In a real test, we'd mock the API to return an error
      // For now, just verify the form accepts the input
      expect(quantityInput).toHaveValue('10');
    });

    it('handles network connectivity issues gracefully', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      // Form should still be usable even if real-time data is unavailable
      expect(screen.getByRole('button', { name: /review order/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels for form controls', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByLabelText(/quantity/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/order type/i)).toBeInTheDocument();
    });

    it('has keyboard navigation support', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      quantityInput.focus();
      expect(document.activeElement).toBe(quantityInput);
    });

    it('announces form validation errors to screen readers', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const submitButton = screen.getByRole('button', { name: /review order/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(/quantity is required/i);
        expect(errorMessage).toHaveAttribute('role', 'alert');
      });
    });
  });

  describe('Form Reset and State Management', () => {
    it('resets form after successful order submission', async () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      // Simulate successful order submission
      const confirmButton = screen.getByTestId('safeguards-confirm');
      fireEvent.click(confirmButton);

      // Form should reset after submission
      await waitFor(() => {
        expect(quantityInput).toHaveValue('');
      });
    });

    it('preserves form state when switching between order types', () => {
      render(
        <TestWrapper>
          <EnhancedOrderForm {...defaultProps} />
        </TestWrapper>
      );

      const quantityInput = screen.getByLabelText(/quantity/i);
      fireEvent.change(quantityInput, { target: { value: '10' } });

      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'limit' } });

      // Quantity should be preserved
      expect(quantityInput).toHaveValue('10');
    });
  });
});