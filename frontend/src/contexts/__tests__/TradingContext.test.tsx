import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { authSlice } from '../../store/slices/authSlice';
import {
  TradingContextProvider,
  useTradingContext,
  TradingMode,
} from '../TradingContext';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Test component to access and display context values
const TestComponent: React.FC = () => {
  const {
    mode,
    accountId,
    riskProfile,
    dailyLimits,
    isBlocked,
    blockReason,
    isLiveMode,
    isPaperMode,
    canAccessLiveTrading,
    switchMode,
    setMode,
    updateRiskProfile,
    updateDailyLimits,
    blockTrading,
    unblockTrading,
    getBaseRoute,
    confirmModeSwitch,
  } = useTradingContext();

  return (
    <div>
      <div data-testid="current-mode">{mode}</div>
      <div data-testid="account-id">{accountId}</div>
      <div data-testid="is-live-mode">{isLiveMode.toString()}</div>
      <div data-testid="is-paper-mode">{isPaperMode.toString()}</div>
      <div data-testid="can-access-live">{canAccessLiveTrading.toString()}</div>
      <div data-testid="base-route">{getBaseRoute()}</div>
      <div data-testid="risk-level">{riskProfile.level}</div>
      <div data-testid="max-position-size">{riskProfile.maxPositionSize}</div>
      <div data-testid="orders-remaining">{dailyLimits.ordersRemaining}</div>
      <div data-testid="is-blocked">{isBlocked.toString()}</div>
      <div data-testid="block-reason">{blockReason || 'none'}</div>

      <button onClick={() => setMode('paper')} data-testid="switch-to-paper">
        Switch to Paper
      </button>
      <button onClick={() => setMode('live')} data-testid="switch-to-live">
        Switch to Live
      </button>
      <button
        onClick={() => confirmModeSwitch('live', '/live/trading/AAPL')}
        data-testid="confirm-live-switch"
      >
        Confirm Live Switch
      </button>
      <button
        onClick={() => updateRiskProfile({ level: 'aggressive', maxPositionSize: 50000 })}
        data-testid="update-risk"
      >
        Update Risk
      </button>
      <button
        onClick={() => updateDailyLimits({ ordersRemaining: 10 })}
        data-testid="update-limits"
      >
        Update Limits
      </button>
      <button
        onClick={() => blockTrading('Daily loss limit exceeded')}
        data-testid="block-trading"
      >
        Block Trading
      </button>
      <button onClick={() => unblockTrading()} data-testid="unblock-trading">
        Unblock Trading
      </button>
    </div>
  );
};

// Mock store factory
const createMockStore = (_userType = 'premium', isVerified = true) => {
  return configureStore({
    reducer: {
      auth: authSlice.reducer,
    },
    preloadedState: {
      auth: {
        user: {
          id: 1,
          email: 'test@example.com',
          risk_tolerance: 'moderate',
          trading_style: 'swing',
          is_active: true,
          is_verified: isVerified,
        },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      },
    },
  });
};

// Test wrapper component
const TestWrapper: React.FC<{
  children: React.ReactNode;
  initialEntries?: string[];
  userType?: string;
  isVerified?: boolean;
  initialMode?: TradingMode;
}> = ({
  children,
  initialEntries = ['/'],
  userType = 'premium',
  isVerified = true,
  initialMode = 'paper',
}) => {
  const mockStore = createMockStore(userType, isVerified);

  return (
    <Provider store={mockStore}>
      <MemoryRouter initialEntries={initialEntries}>
        <TradingContextProvider initialMode={initialMode}>
          {children}
        </TradingContextProvider>
      </MemoryRouter>
    </Provider>
  );
};

describe('TradingContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('Initial State and Mode Detection', () => {
    it('should default to paper mode when no initial mode specified', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('current-mode')).toHaveTextContent('paper');
      expect(screen.getByTestId('is-paper-mode')).toHaveTextContent('true');
      expect(screen.getByTestId('is-live-mode')).toHaveTextContent('false');
    });

    it('should accept initial mode prop', () => {
      render(
        <TestWrapper initialMode="live">
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('current-mode')).toHaveTextContent('live');
      expect(screen.getByTestId('is-live-mode')).toHaveTextContent('true');
      expect(screen.getByTestId('is-paper-mode')).toHaveTextContent('false');
    });

    it('should initialize with default risk profile', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('risk-level')).toHaveTextContent('moderate');
      expect(screen.getByTestId('max-position-size')).toHaveTextContent('10000');
    });

    it('should initialize with default daily limits', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('orders-remaining')).toHaveTextContent('50');
    });
  });

  describe('Route Generation', () => {
    it('should generate correct paper routes', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('base-route')).toHaveTextContent('/paper');
    });

    it('should generate correct live routes', () => {
      render(
        <TestWrapper initialMode="live">
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('base-route')).toHaveTextContent('/live');
    });
  });

  describe('Live Trading Access Control', () => {
    it('should allow live trading for premium users', () => {
      render(
        <TestWrapper userType="premium" isVerified={true}>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('can-access-live')).toHaveTextContent('true');
    });

    it('should allow live trading for pro users', () => {
      render(
        <TestWrapper userType="pro" isVerified={true}>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('can-access-live')).toHaveTextContent('true');
    });

    it('should deny live trading for basic users', () => {
      render(
        <TestWrapper userType="basic" isVerified={true}>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('can-access-live')).toHaveTextContent('false');
    });

    it('should deny live trading for unverified users', () => {
      render(
        <TestWrapper userType="premium" isVerified={false}>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('can-access-live')).toHaveTextContent('false');
    });

    it('should deny live trading when user is not authenticated', () => {
      const storeWithoutUser = configureStore({
        reducer: {
          auth: authSlice.reducer,
        },
        preloadedState: {
          auth: {
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          },
        },
      });

      render(
        <Provider store={storeWithoutUser}>
          <MemoryRouter>
            <TradingContextProvider>
              <TestComponent />
            </TradingContextProvider>
          </MemoryRouter>
        </Provider>
      );

      expect(screen.getByTestId('can-access-live')).toHaveTextContent('false');
    });
  });

  describe('Mode Switching with setMode', () => {
    it('should switch to paper mode successfully', async () => {
      render(
        <TestWrapper initialMode="live">
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('current-mode')).toHaveTextContent('live');

      fireEvent.click(screen.getByTestId('switch-to-paper'));

      await waitFor(() => {
        expect(screen.getByTestId('current-mode')).toHaveTextContent('paper');
      });
    });

    it('should prevent live mode switch for ineligible users', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      render(
        <TestWrapper userType="basic">
          <TestComponent />
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('switch-to-live'));

      await waitFor(() => {
        expect(screen.getByTestId('current-mode')).toHaveTextContent('paper');
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'User cannot access live trading: insufficient permissions'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Confirmation Flows with confirmModeSwitch', () => {
    it('should show confirmation and navigate for live mode switch', async () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

      render(
        <TestWrapper userType="premium" isVerified={true}>
          <TestComponent />
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('confirm-live-switch'));

      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalledWith(
          expect.stringContaining('live trading mode')
        );
      });

      expect(mockNavigate).toHaveBeenCalledWith('/live/trading/AAPL');
      expect(localStorage.getItem('tradingMode')).toBe('live');

      confirmSpy.mockRestore();
    });

    it('should cancel mode switch when confirmation is denied', async () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

      render(
        <TestWrapper userType="premium" isVerified={true}>
          <TestComponent />
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('confirm-live-switch'));

      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
      });

      expect(mockNavigate).not.toHaveBeenCalled();
      expect(screen.getByTestId('current-mode')).toHaveTextContent('paper');

      confirmSpy.mockRestore();
    });

    it('should block confirmModeSwitch for ineligible users', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      const confirmSpy = jest.spyOn(window, 'confirm');

      render(
        <TestWrapper userType="basic">
          <TestComponent />
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('confirm-live-switch'));

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'User cannot access live trading: insufficient permissions'
        );
      });

      expect(confirmSpy).not.toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
      confirmSpy.mockRestore();
    });
  });

  describe('Risk Profile Management', () => {
    it('should update risk profile partially', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('risk-level')).toHaveTextContent('moderate');
      expect(screen.getByTestId('max-position-size')).toHaveTextContent('10000');

      fireEvent.click(screen.getByTestId('update-risk'));

      expect(screen.getByTestId('risk-level')).toHaveTextContent('aggressive');
      expect(screen.getByTestId('max-position-size')).toHaveTextContent('50000');
    });
  });

  describe('Daily Limits Management', () => {
    it('should update daily limits partially', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('orders-remaining')).toHaveTextContent('50');

      fireEvent.click(screen.getByTestId('update-limits'));

      expect(screen.getByTestId('orders-remaining')).toHaveTextContent('10');
    });
  });

  describe('Trading Blocking', () => {
    it('should block trading with a reason', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      expect(screen.getByTestId('is-blocked')).toHaveTextContent('false');
      expect(screen.getByTestId('block-reason')).toHaveTextContent('none');

      fireEvent.click(screen.getByTestId('block-trading'));

      expect(screen.getByTestId('is-blocked')).toHaveTextContent('true');
      expect(screen.getByTestId('block-reason')).toHaveTextContent(
        'Daily loss limit exceeded'
      );
    });

    it('should unblock trading and clear reason', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Block trading first
      fireEvent.click(screen.getByTestId('block-trading'));
      expect(screen.getByTestId('is-blocked')).toHaveTextContent('true');

      // Unblock trading
      fireEvent.click(screen.getByTestId('unblock-trading'));
      expect(screen.getByTestId('is-blocked')).toHaveTextContent('false');
      expect(screen.getByTestId('block-reason')).toHaveTextContent('none');
    });
  });

  describe('LocalStorage Persistence', () => {
    it('should persist mode to localStorage on confirmModeSwitch', async () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

      render(
        <TestWrapper userType="premium" isVerified={true}>
          <TestComponent />
        </TestWrapper>
      );

      fireEvent.click(screen.getByTestId('confirm-live-switch'));

      await waitFor(() => {
        expect(localStorage.getItem('tradingMode')).toBe('live');
      });

      confirmSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    it('should throw error when useTradingContext is used outside provider', () => {
      const TestWithoutProvider = () => {
        try {
          useTradingContext();
          return <div>Should not render</div>;
        } catch (error) {
          return <div data-testid="error">{(error as Error).message}</div>;
        }
      };

      // We need to wrap in Provider and Router for the component itself,
      // but the context will throw
      const store = createMockStore();
      render(
        <Provider store={store}>
          <MemoryRouter>
            <TestWithoutProvider />
          </MemoryRouter>
        </Provider>
      );

      expect(screen.getByTestId('error')).toHaveTextContent(
        'useTradingContext must be used within a TradingContextProvider'
      );
    });

    it('should handle missing user gracefully', () => {
      const storeWithoutUser = configureStore({
        reducer: {
          auth: authSlice.reducer,
        },
        preloadedState: {
          auth: {
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          },
        },
      });

      render(
        <Provider store={storeWithoutUser}>
          <MemoryRouter>
            <TradingContextProvider>
              <TestComponent />
            </TradingContextProvider>
          </MemoryRouter>
        </Provider>
      );

      expect(screen.getByTestId('current-mode')).toHaveTextContent('paper');
      expect(screen.getByTestId('can-access-live')).toHaveTextContent('false');
    });
  });

  describe('Integration Scenarios', () => {
    it('should handle complete trading session workflow', async () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

      render(
        <TestWrapper userType="premium" isVerified={true}>
          <TestComponent />
        </TestWrapper>
      );

      // 1. Start in paper mode
      expect(screen.getByTestId('current-mode')).toHaveTextContent('paper');
      expect(screen.getByTestId('can-access-live')).toHaveTextContent('true');

      // 2. Update risk profile
      fireEvent.click(screen.getByTestId('update-risk'));
      expect(screen.getByTestId('risk-level')).toHaveTextContent('aggressive');

      // 3. Simulate some trading (reduce limits)
      fireEvent.click(screen.getByTestId('update-limits'));
      expect(screen.getByTestId('orders-remaining')).toHaveTextContent('10');

      // 4. Switch to live mode via confirmModeSwitch
      fireEvent.click(screen.getByTestId('confirm-live-switch'));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/live/trading/AAPL');
      });

      // 5. Block trading due to risk
      fireEvent.click(screen.getByTestId('block-trading'));
      expect(screen.getByTestId('is-blocked')).toHaveTextContent('true');

      // 6. Unblock and switch back to paper
      fireEvent.click(screen.getByTestId('unblock-trading'));
      fireEvent.click(screen.getByTestId('switch-to-paper'));

      await waitFor(() => {
        expect(screen.getByTestId('current-mode')).toHaveTextContent('paper');
      });
      expect(screen.getByTestId('is-blocked')).toHaveTextContent('false');

      confirmSpy.mockRestore();
    });
  });
});
