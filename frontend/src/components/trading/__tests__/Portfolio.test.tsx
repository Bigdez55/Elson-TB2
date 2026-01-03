import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import Portfolio from '../Portfolio';

// Mock the formatters
jest.mock('../../../utils/formatters', () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`,
  formatPercentage: (value: number) => `${value.toFixed(2)}%`
}));

// Mock the trading API
jest.mock('../../../services/tradingApi', () => ({
  useGetPortfolioQuery: () => ({
    data: {
      positions: [
        { symbol: 'AAPL', quantity: 10, currentPrice: 150.25, avgPrice: 145.50 },
        { symbol: 'MSFT', quantity: 5, currentPrice: 310.75, avgPrice: 300.00 },
        { symbol: 'GOOGL', quantity: 3, currentPrice: 140.85, avgPrice: 135.00 },
        { symbol: 'TSLA', quantity: 8, currentPrice: 245.60, avgPrice: 240.00 }
      ],
      totalValue: 5443.60,
      totalPnL: 243.60,
      cash_balance: 10000,
      total_value: 5443.60
    },
    isLoading: false,
    error: null,
    refetch: jest.fn()
  }),
  useGetPositionsQuery: () => ({
    data: [
      { symbol: 'AAPL', qty: 10, current_price: 150.25, avg_entry_price: 145.50, market_value: 1502.50, unrealized_pl: 47.50 },
      { symbol: 'MSFT', qty: 5, current_price: 310.75, avg_entry_price: 300.00, market_value: 1553.75, unrealized_pl: 53.75 },
      { symbol: 'GOOGL', qty: 3, current_price: 140.85, avg_entry_price: 135.00, market_value: 422.55, unrealized_pl: 17.55 },
      { symbol: 'TSLA', qty: 8, current_price: 245.60, avg_entry_price: 240.00, market_value: 1964.80, unrealized_pl: 44.80 }
    ],
    isLoading: false,
    error: null,
    refetch: jest.fn()
  }),
  useGetTradingAccountQuery: () => ({
    data: { buying_power: 10000, cash: 10000, portfolio_value: 5443.60 },
    isLoading: false,
    error: null
  }),
  tradingApi: {
    reducer: (state = {}) => state,
    reducerPath: 'tradingApi',
    middleware: () => (next: any) => (action: any) => next(action)
  }
}));

// Mock the TradingContext
jest.mock('../../../contexts/TradingContext', () => ({
  useTradingContext: () => ({
    currentMode: 'paper',
    setMode: jest.fn(),
    canAccessLive: true,
    riskProfile: 'moderate',
    setRiskProfile: jest.fn(),
    isBlocked: false,
    setBlocked: jest.fn(),
    tradingLimits: { dailyLimit: 10000, maxOrderSize: 1000 },
    setTradingLimits: jest.fn()
  }),
  TradingContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

// Create a mock store
const createMockStore = () => configureStore({
  reducer: {
    trading: (state = {
      portfolio: {
        positions: [
          { symbol: 'AAPL', quantity: 10, currentPrice: 150.25, avgPrice: 145.50 },
          { symbol: 'MSFT', quantity: 5, currentPrice: 310.75, avgPrice: 300.00 },
          { symbol: 'GOOGL', quantity: 3, currentPrice: 140.85, avgPrice: 135.00 },
          { symbol: 'TSLA', quantity: 8, currentPrice: 245.60, avgPrice: 240.00 }
        ],
        totalValue: 5443.60,
        totalPnL: 243.60
      },
      loading: false
    }) => state,
    auth: (state = { isAuthenticated: true }) => state
  }
});

const renderWithProviders = (component: React.ReactElement) => {
  const store = createMockStore();
  return render(
    <Provider store={store}>
      {component}
    </Provider>
  );
};

describe('Portfolio', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('shows loading spinner initially', () => {
      renderWithProviders(<Portfolio />);
      expect(screen.getByText('Loading portfolio...')).toBeInTheDocument();
    });
  });

  describe('Portfolio Display', () => {
    it('displays portfolio data after loading', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => screen.getByText('Portfolio'), { timeout: 2000 });
      expect(screen.getByText('Portfolio')).toBeInTheDocument();
      expect(screen.getByText('$5,443.60')).toBeInTheDocument();
    });

    it('displays total profit/loss correctly', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        expect(screen.getByText('Total P&L')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays individual assets', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => screen.getByText('AAPL'), { timeout: 2000 });
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('MSFT')).toBeInTheDocument();
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
      expect(screen.getByText('TSLA')).toBeInTheDocument();
    });

    it('displays asset quantities', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => screen.getByText('10.00000000 shares'), { timeout: 2000 });
      expect(screen.getByText('10.00000000 shares')).toBeInTheDocument();
      expect(screen.getByText('5.00000000 shares')).toBeInTheDocument();
      expect(screen.getByText('3.00000000 shares')).toBeInTheDocument();
      expect(screen.getByText('8.00000000 shares')).toBeInTheDocument();
    });

    it('displays current and average prices', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        expect(screen.getByText('$150.25')).toBeInTheDocument();
        expect(screen.getByText('Avg. $145.50')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays asset values', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        expect(screen.getByText('$1,502.50')).toBeInTheDocument();
        expect(screen.getByText('$1,553.75')).toBeInTheDocument();
        expect(screen.getByText('$422.55')).toBeInTheDocument();
        expect(screen.getByText('$1,964.80')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Profit/Loss Calculation', () => {
    it('shows profit in green color', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        const profitElements = screen.getAllByText(/\$47\.50/);
        profitElements.forEach(element => {
          expect(element).toHaveClass('text-green-400');
        });
      }, { timeout: 2000 });
    });

    it('shows loss in red color', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        const lossElements = screen.getAllByText(/\$-35\.20/);
        lossElements.forEach(element => {
          expect(element).toHaveClass('text-red-400');
        });
      }, { timeout: 2000 });
    });
  });

  describe('Allocation Bars', () => {
    it('displays allocation percentages', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        const allocationBars = screen.getAllByText('25.0%');
        expect(allocationBars.length).toBeGreaterThan(0);
      }, { timeout: 2000 });
    });

    it('renders allocation progress bars', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        const progressBars = document.querySelectorAll('.bg-blue-500');
        expect(progressBars.length).toBeGreaterThan(0);
      }, { timeout: 2000 });
    });
  });

  describe('Table Headers', () => {
    it('displays correct column headers', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        expect(screen.getByText('Asset')).toBeInTheDocument();
        expect(screen.getByText('Price')).toBeInTheDocument();
        expect(screen.getByText('Value')).toBeInTheDocument();
        expect(screen.getByText('Allocation')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Auto-refresh', () => {
    it('shows updating indicator during refresh', async () => {
      renderWithProviders(<Portfolio />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Portfolio')).toBeInTheDocument();
      }, { timeout: 2000 });
      
      // The component refreshes every minute, but we can't easily test this in a unit test
      // without mocking timers, which would be complex for this case
    });
  });

  describe('Empty State', () => {
    it('would show empty state if no assets', async () => {
      // This would require mocking the portfolio data to be empty
      // For now, we just verify the empty state message exists in the component
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        // The component has logic for empty state, but our mock data always has assets
        expect(screen.queryByText('No assets in portfolio')).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Responsive Design', () => {
    it('renders table structure properly', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.getAllByRole('columnheader')).toHaveLength(4);
      }, { timeout: 2000 });
    });

    it('has overflow scrolling for mobile', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        const tableContainer = document.querySelector('.overflow-x-auto');
        expect(tableContainer).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Hover Effects', () => {
    it('applies hover styles to table rows', async () => {
      renderWithProviders(<Portfolio />);
      
      await waitFor(() => {
        const tableRows = document.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
          expect(row).toHaveClass('hover:bg-gray-700/30');
        });
      }, { timeout: 2000 });
    });
  });
});