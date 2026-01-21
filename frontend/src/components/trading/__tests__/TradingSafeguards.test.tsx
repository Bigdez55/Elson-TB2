/* eslint-disable testing-library/no-wait-for-multiple-assertions */
/* eslint-disable testing-library/no-wait-for-side-effects */
/* eslint-disable testing-library/no-node-access */
/* eslint-disable testing-library/no-container */
/**
 * TradingSafeguards Component Tests
 *
 * Tests for the trading safeguards components that provide safety measures
 * for paper and live trading modes.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import {
  TradingSafeguardWrapper,
  RiskLimitWarning,
  TradingModeStatusAlert,
  TradingSessionTimer,
} from '../TradingSafeguards';
import { TradingContextProvider } from '../../../contexts/TradingContext';
import authReducer from '../../../store/slices/authSlice';
import tradingReducer from '../../../store/slices/tradingSlice';

// Mock websocketSlice
jest.mock('../../../store/slices/websocketSlice', () => ({
  default: (state = {}) => state,
  websocketSlice: {
    reducer: (state = {}) => state,
  },
}));

// Mock websocketService
jest.mock('../../../services/websocketService', () => ({
  webSocketService: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    subscribe: jest.fn(),
    unsubscribe: jest.fn(),
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

// Create mock store factory
const createMockStore = (authState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      trading: tradingReducer,
      websocket: (state = {}) => state,
    },
    preloadedState: {
      auth: {
        user: {
          id: 1,
          email: 'test@example.com',
          risk_tolerance: 'moderate',
          trading_style: 'swing',
          is_active: true,
          is_verified: true,
        },
        isAuthenticated: true,
        isLoading: false,
        error: null,
        ...authState,
      },
      trading: {
        trades: [],
        openOrders: [],
        positions: [],
        stats: null,
        isLoading: false,
        error: null,
      },
      websocket: {},
    },
  });
};

// Test wrapper with all required providers
interface TestWrapperProps {
  children: React.ReactNode;
  store?: ReturnType<typeof createMockStore>;
  initialMode?: 'paper' | 'live';
  initialPath?: string;
}

const TestWrapper: React.FC<TestWrapperProps> = ({
  children,
  store = createMockStore(),
  initialMode = 'paper',
  initialPath = '/',
}) => {
  return (
    <Provider store={store}>
      <MemoryRouter initialEntries={[initialPath]}>
        <TradingContextProvider initialMode={initialMode}>
          {children}
        </TradingContextProvider>
      </MemoryRouter>
    </Provider>
  );
};

describe('TradingSafeguards Component', () => {
  describe('TradingSafeguardWrapper', () => {
    describe('Basic Rendering', () => {
      it('renders children correctly', () => {
        render(
          <TestWrapper>
            <TradingSafeguardWrapper actionType="general">
              <button>Test Button</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        expect(screen.getByRole('button', { name: 'Test Button' })).toBeInTheDocument();
      });

      it('renders with default props', () => {
        render(
          <TestWrapper>
            <TradingSafeguardWrapper actionType="order">
              <span>Child Content</span>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        expect(screen.getByText('Child Content')).toBeInTheDocument();
      });
    });

    describe('Confirmation Flow', () => {
      it('does not show confirmation modal by default on click in paper mode', () => {
        render(
          <TestWrapper initialMode="paper">
            <TradingSafeguardWrapper actionType="general">
              <button>Test Button</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        fireEvent.click(screen.getByText('Test Button'));

        // No modal should appear for general action type without requiresConfirmation
        expect(screen.queryByText('Confirm')).not.toBeInTheDocument();
      });

      it('shows confirmation modal when requiresConfirmation is true', () => {
        render(
          <TestWrapper>
            <TradingSafeguardWrapper
              actionType="order"
              requiresConfirmation={true}
              title="Confirm Order"
              message="Are you sure?"
            >
              <button>Place Order</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        // Click the wrapper to trigger confirmation
        fireEvent.click(screen.getByText('Place Order'));

        // Modal should now be visible
        expect(screen.getByText('Confirm Order')).toBeInTheDocument();
        expect(screen.getByText('Are you sure?')).toBeInTheDocument();
      });

      it('shows confirmation modal in live mode for order actions', () => {
        render(
          <TestWrapper initialMode="live">
            <TradingSafeguardWrapper actionType="order" title="Live Order Confirmation">
              <button>Execute Trade</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        fireEvent.click(screen.getByText('Execute Trade'));

        expect(screen.getByText('Live Order Confirmation')).toBeInTheDocument();
      });

      it('calls onExecute when confirmed', async () => {
        const onExecute = jest.fn();

        render(
          <TestWrapper>
            <TradingSafeguardWrapper
              actionType="general"
              requiresConfirmation={true}
              title="Confirm Action"
              onExecute={onExecute}
            >
              <button>Do Something</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        // Open modal
        fireEvent.click(screen.getByText('Do Something'));

        // Click confirm
        fireEvent.click(screen.getByRole('button', { name: /confirm/i }));

        await waitFor(() => {
          expect(onExecute).toHaveBeenCalledTimes(1);
        });
      });

      it('closes modal when cancelled', async () => {
        render(
          <TestWrapper>
            <TradingSafeguardWrapper
              actionType="general"
              requiresConfirmation={true}
              title="Confirm Action"
            >
              <button>Action</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        // Open modal
        fireEvent.click(screen.getByText('Action'));
        expect(screen.getByText('Confirm Action')).toBeInTheDocument();

        // Click cancel
        fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

        await waitFor(() => {
          expect(screen.queryByText('Confirm Action')).not.toBeInTheDocument();
        });
      });
    });

    describe('Disabled State', () => {
      it('applies disabled styling when disabled prop is true', () => {
        render(
          <TestWrapper>
            <TradingSafeguardWrapper actionType="order" disabled={true}>
              <button>Disabled Action</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        const wrapper = screen.getByText('Disabled Action').closest('div');
        expect(wrapper).toHaveClass('opacity-50', 'cursor-not-allowed');
      });

      it('does not show confirmation when disabled', () => {
        render(
          <TestWrapper>
            <TradingSafeguardWrapper
              actionType="order"
              requiresConfirmation={true}
              disabled={true}
              title="Should Not Show"
            >
              <button>Disabled</button>
            </TradingSafeguardWrapper>
          </TestWrapper>
        );

        fireEvent.click(screen.getByText('Disabled'));

        expect(screen.queryByText('Should Not Show')).not.toBeInTheDocument();
      });
    });
  });

  describe('RiskLimitWarning Component', () => {
    describe('Rendering Based on Usage', () => {
      it('does not render when usage is below 50%', () => {
        const { container } = render(
          <TestWrapper>
            <RiskLimitWarning currentValue={20} limit={100} type="orders" />
          </TestWrapper>
        );

        // Component returns null when below 50%
        expect(container.querySelector('.border')).not.toBeInTheDocument();
      });

      it('renders when usage is at 50%', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={50} limit={100} type="orders" />
          </TestWrapper>
        );

        expect(screen.getByText(/Daily Order Limit/i)).toBeInTheDocument();
      });

      it('renders when usage is above 75%', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={80} limit={100} type="orders" />
          </TestWrapper>
        );

        expect(screen.getByText(/Approaching limit/i)).toBeInTheDocument();
      });

      it('renders critical warning when usage is above 90%', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={95} limit={100} type="orders" />
          </TestWrapper>
        );

        expect(screen.getByText(/Critical/i)).toBeInTheDocument();
      });
    });

    describe('Different Warning Types', () => {
      it('displays order limit warning correctly', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={40} limit={50} type="orders" />
          </TestWrapper>
        );

        expect(screen.getByText(/Daily Order Limit: 40\/50/i)).toBeInTheDocument();
      });

      it('displays loss limit warning correctly', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={800} limit={1000} type="loss" />
          </TestWrapper>
        );

        expect(screen.getByText(/Daily Loss Limit/i)).toBeInTheDocument();
      });

      it('displays position size warning correctly', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={8000} limit={10000} type="position" />
          </TestWrapper>
        );

        expect(screen.getByText(/Position Size/i)).toBeInTheDocument();
      });
    });

    describe('Warning Levels', () => {
      it('applies correct styling for medium warning (50-75%)', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={60} limit={100} type="orders" />
          </TestWrapper>
        );

        const warningDiv = screen.getByText(/Daily Order Limit/i).closest('.border');
        expect(warningDiv).toHaveClass('bg-yellow-100');
      });

      it('applies correct styling for high warning (75-90%)', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={80} limit={100} type="orders" />
          </TestWrapper>
        );

        const warningDiv = screen.getByText(/Daily Order Limit/i).closest('.border');
        expect(warningDiv).toHaveClass('bg-orange-100');
      });

      it('applies correct styling for critical warning (90%+)', () => {
        render(
          <TestWrapper>
            <RiskLimitWarning currentValue={95} limit={100} type="orders" />
          </TestWrapper>
        );

        const warningDiv = screen.getByText(/Daily Order Limit/i).closest('.border');
        expect(warningDiv).toHaveClass('bg-red-100');
      });
    });
  });

  describe('TradingModeStatusAlert Component', () => {
    it('does not render in paper mode when not blocked', () => {
      const { container } = render(
        <TestWrapper initialMode="paper">
          <TradingModeStatusAlert />
        </TestWrapper>
      );

      expect(container.querySelector('.sticky')).not.toBeInTheDocument();
    });

    it('renders live trading alert in live mode', () => {
      render(
        <TestWrapper initialMode="live">
          <TradingModeStatusAlert />
        </TestWrapper>
      );

      expect(screen.getByText(/LIVE TRADING ACTIVE/i)).toBeInTheDocument();
      expect(screen.getByText(/Real money transactions enabled/i)).toBeInTheDocument();
    });
  });

  describe('TradingSessionTimer Component', () => {
    it('does not render when no mode switch has occurred', () => {
      const { container } = render(
        <TestWrapper>
          <TradingSessionTimer />
        </TestWrapper>
      );

      // Component returns null when lastModeSwitch is not set or timeInMode is empty
      expect(container.querySelector('.text-xs')).not.toBeInTheDocument();
    });
  });

  describe('Order Details Display', () => {
    it('displays order details in confirmation modal', () => {
      render(
        <TestWrapper>
          <TradingSafeguardWrapper
            actionType="order"
            requiresConfirmation={true}
            title="Confirm Order"
            orderDetails={{
              symbol: 'AAPL',
              quantity: 100,
              price: 150.00,
              action: 'buy',
              orderType: 'market',
            }}
          >
            <button>Buy Stock</button>
          </TradingSafeguardWrapper>
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Buy Stock'));

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('$150.00')).toBeInTheDocument();
      expect(screen.getByText('buy')).toBeInTheDocument();
      expect(screen.getByText('market')).toBeInTheDocument();
      // Total includes fees: $15,000 + $0.50 (100 shares * $0.005) = $15,000.50
      expect(screen.getByText('$15,000.50')).toBeInTheDocument();
    });
  });

  describe('Live Mode Specific Features', () => {
    it('shows live trading warning in confirmation modal', () => {
      render(
        <TestWrapper initialMode="live">
          <TradingSafeguardWrapper
            actionType="order"
            title="Live Order"
          >
            <button>Execute</button>
          </TradingSafeguardWrapper>
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Execute'));

      expect(screen.getByText(/LIVE TRADING MODE ACTIVE/i)).toBeInTheDocument();
      expect(screen.getByText(/This order will execute with real money/i)).toBeInTheDocument();
    });

    it('shows required checkboxes for live order confirmation', () => {
      render(
        <TestWrapper initialMode="live">
          <TradingSafeguardWrapper
            actionType="order"
            title="Live Order"
          >
            <button>Execute</button>
          </TradingSafeguardWrapper>
        </TestWrapper>
      );

      fireEvent.click(screen.getByText('Execute'));

      // Find checkboxes by their labels
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes).toHaveLength(3);
      expect(screen.getByText(/I understand this transaction uses real money/i)).toBeInTheDocument();
      expect(screen.getByText(/I have reviewed the order details above/i)).toBeInTheDocument();
      expect(screen.getByText(/I am authorized to execute this trade/i)).toBeInTheDocument();
    });
  });

  describe('Integration Tests', () => {
    it('complete order confirmation flow in paper mode', async () => {
      const onExecute = jest.fn();

      render(
        <TestWrapper initialMode="paper">
          <TradingSafeguardWrapper
            actionType="order"
            requiresConfirmation={true}
            title="Paper Order"
            message="Confirm paper trading order"
            orderDetails={{
              symbol: 'GOOGL',
              quantity: 10,
              price: 100,
              action: 'sell',
              orderType: 'limit',
            }}
            onExecute={onExecute}
          >
            <button>Sell GOOGL</button>
          </TradingSafeguardWrapper>
        </TestWrapper>
      );

      // Click to open modal
      fireEvent.click(screen.getByText('Sell GOOGL'));

      // Verify modal content
      expect(screen.getByText('Paper Order')).toBeInTheDocument();
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
      expect(screen.getByText('sell')).toBeInTheDocument();

      // Confirm the order
      fireEvent.click(screen.getByRole('button', { name: /Execute Order/i }));

      await waitFor(() => {
        expect(onExecute).toHaveBeenCalled();
      });
    });

    it('complete order confirmation flow in live mode', async () => {
      const onExecute = jest.fn();

      render(
        <TestWrapper initialMode="live">
          <TradingSafeguardWrapper
            actionType="order"
            title="Live Order"
            orderDetails={{
              symbol: 'TSLA',
              quantity: 5,
              price: 200,
              action: 'buy',
              orderType: 'market',
            }}
            onExecute={onExecute}
          >
            <button>Buy TSLA</button>
          </TradingSafeguardWrapper>
        </TestWrapper>
      );

      // Click to open modal (live mode auto-shows for order type)
      fireEvent.click(screen.getByText('Buy TSLA'));

      // Verify live mode warnings
      expect(screen.getByText(/LIVE TRADING MODE ACTIVE/i)).toBeInTheDocument();

      // Verify order details
      expect(screen.getByText('TSLA')).toBeInTheDocument();
      // Total includes fees: $1,000 + $3.50 (0.35% commission) = $1,003.50
      expect(screen.getByText('$1,003.50')).toBeInTheDocument();

      // Confirm
      fireEvent.click(screen.getByRole('button', { name: /Execute Order/i }));

      await waitFor(() => {
        expect(onExecute).toHaveBeenCalled();
      });
    });

    it('cancelling closes modal without executing', async () => {
      const onExecute = jest.fn();

      render(
        <TestWrapper>
          <TradingSafeguardWrapper
            actionType="order"
            requiresConfirmation={true}
            title="Order Modal"
            onExecute={onExecute}
          >
            <button>Place Order</button>
          </TradingSafeguardWrapper>
        </TestWrapper>
      );

      // Open modal
      fireEvent.click(screen.getByText('Place Order'));
      expect(screen.getByText('Order Modal')).toBeInTheDocument();

      // Cancel
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      await waitFor(() => {
        expect(screen.queryByText('Order Modal')).not.toBeInTheDocument();
      });

      expect(onExecute).not.toHaveBeenCalled();
    });
  });
});
