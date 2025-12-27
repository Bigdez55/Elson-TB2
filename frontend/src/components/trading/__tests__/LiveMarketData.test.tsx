/**
 * LiveMarketData Component Tests
 *
 * Tests for the LiveMarketData and MiniLiveMarketData components
 * that display real-time market data via WebSocket.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';

import { LiveMarketData, MiniLiveMarketData } from '../LiveMarketData';

// Mock the useMarketDataWebSocket hook
const mockMarketData: Record<string, any> = {
  'AAPL': {
    symbol: 'AAPL',
    price: 150.25,
    change: 2.15,
    change_percent: 1.45,
    volume: 1500000,
    bid: 150.20,
    ask: 150.30,
    timestamp: '2024-01-01T12:00:00Z'
  }
};

const mockUseMarketDataWebSocket = jest.fn((_symbols: string[]) => ({
  isConnected: true,
  marketData: mockMarketData,
  error: null as string | null,
}));

jest.mock('../../../hooks/useWebSocket', () => ({
  useMarketDataWebSocket: (symbols: string[]) => mockUseMarketDataWebSocket(symbols)
}));

// Mock the CompactConnectionStatus component
jest.mock('../../common/ConnectionStatusBanner', () => ({
  CompactConnectionStatus: () => <div data-testid="connection-status">Connected</div>
}));

// Mock the Badge component
jest.mock('../../common/Badge', () => ({
  Badge: ({ children }: { children: React.ReactNode }) => (
    <span data-testid="badge">{children}</span>
  )
}));

// Mock store setup
const createMockStore = (overrides?: { marketData?: Record<string, any> }) => {
  const customReducer = (state = {
    status: 'AUTHENTICATED' as const,
    marketData: overrides?.marketData ?? mockMarketData,
    subscriptions: [] as string[],
    error: null as string | null,
    portfolio: { paper: null, live: null },
    positions: {},
    orders: [],
    subscribedChannels: [] as string[],
    messageCount: 0
  }, _action: unknown) => state;

  return configureStore({
    reducer: {
      websocket: customReducer,
    },
  });
};

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const store = createMockStore();
  return <Provider store={store}>{children}</Provider>;
};

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  // Reset mock market data
  mockMarketData['AAPL'] = {
    symbol: 'AAPL',
    price: 150.25,
    change: 2.15,
    change_percent: 1.45,
    volume: 1500000,
    bid: 150.20,
    ask: 150.30,
    timestamp: '2024-01-01T12:00:00Z'
  };
  mockUseMarketDataWebSocket.mockReturnValue({
    isConnected: true,
    marketData: mockMarketData,
    error: null,
  });
});

describe('LiveMarketData Component', () => {
  describe('Basic Rendering', () => {
    it('renders live market data for a symbol', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('$150.25')).toBeInTheDocument();
      // Change is formatted as "+2.15 (+1.45%)"
      expect(screen.getByText('+2.15 (+1.45%)')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" className="custom-class" />
        </TestWrapper>
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('shows Live badge when connected', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" showConnectionStatus={true} />
        </TestWrapper>
      );

      expect(screen.getByText('Live')).toBeInTheDocument();
    });

    it('shows connection status component when enabled', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" showConnectionStatus={true} />
        </TestWrapper>
      );

      expect(screen.getByTestId('connection-status')).toBeInTheDocument();
    });
  });

  describe('Price Display and Formatting', () => {
    it('formats price with correct precision', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText('$150.25')).toBeInTheDocument();
    });

    it('displays positive change with green color', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      const changeElement = screen.getByText('+2.15 (+1.45%)');
      expect(changeElement).toHaveClass('text-green-400');
    });

    it('displays negative change with red color', () => {
      mockMarketData['AAPL'] = {
        ...mockMarketData['AAPL'],
        change: -1.25,
        change_percent: -0.83
      };
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: true,
        marketData: mockMarketData,
        error: null,
      });

      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      const changeElement = screen.getByText('-1.25 (-0.83%)');
      expect(changeElement).toHaveClass('text-red-400');
    });

    it('displays zero change with neutral color', () => {
      mockMarketData['AAPL'] = {
        ...mockMarketData['AAPL'],
        change: 0,
        change_percent: 0
      };
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: true,
        marketData: mockMarketData,
        error: null,
      });

      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      const changeElement = screen.getByText('0.00 (0.00%)');
      expect(changeElement).toHaveClass('text-gray-300');
    });
  });

  describe('Bid/Ask Display', () => {
    it('shows bid/ask spread when available', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText('Bid:')).toBeInTheDocument();
      expect(screen.getByText('$150.20')).toBeInTheDocument();
      expect(screen.getByText('Ask:')).toBeInTheDocument();
      expect(screen.getByText('$150.30')).toBeInTheDocument();
    });
  });

  describe('Volume Display', () => {
    it('shows volume information', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText('Volume')).toBeInTheDocument();
      expect(screen.getByText('1.5M')).toBeInTheDocument();
    });

    it('formats volume in thousands', () => {
      mockMarketData['AAPL'].volume = 750000;
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: true,
        marketData: mockMarketData,
        error: null,
      });

      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText('750.0K')).toBeInTheDocument();
    });
  });

  describe('Connection Status and Error Handling', () => {
    it('shows loading state when no data is available', () => {
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: true,
        marketData: {},
        error: null,
      });

      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText(/loading market data/i)).toBeInTheDocument();
    });

    it('shows market data unavailable when disconnected and no data', () => {
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: false,
        marketData: {},
        error: null,
      });

      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText(/market data unavailable/i)).toBeInTheDocument();
    });

    it('displays error message when WebSocket error occurs', () => {
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: false,
        marketData: {},
        error: 'Connection failed' as string | null,
      });

      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText(/connection failed/i)).toBeInTheDocument();
    });

    it('handles missing symbol gracefully', () => {
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: true,
        marketData: {},
        error: null,
      });

      render(
        <TestWrapper>
          <LiveMarketData symbol="NONEXISTENT" />
        </TestWrapper>
      );

      expect(screen.getByText(/loading market data/i)).toBeInTheDocument();
    });
  });

  describe('Timestamp Display', () => {
    it('shows last update label', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText('Last Update')).toBeInTheDocument();
    });
  });

  describe('Price Update Callback', () => {
    it('calls useMarketDataWebSocket with correct symbol', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(mockUseMarketDataWebSocket).toHaveBeenCalledWith(['AAPL']);
    });
  });
});

describe('MiniLiveMarketData Component', () => {
  describe('Compact Display', () => {
    it('renders mini version with essential data only', () => {
      render(
        <TestWrapper>
          <MiniLiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('$150.25')).toBeInTheDocument();
    });

    it('applies custom className to mini version', () => {
      const { container } = render(
        <TestWrapper>
          <MiniLiveMarketData symbol="AAPL" className="mini-class" />
        </TestWrapper>
      );

      expect(container.firstChild).toHaveClass('mini-class');
    });

    it('shows percentage change when showChange is true', () => {
      render(
        <TestWrapper>
          <MiniLiveMarketData symbol="AAPL" showChange={true} />
        </TestWrapper>
      );

      // Mini version formats as "(+1.45%)"
      expect(screen.getByText('(+1.45%)')).toBeInTheDocument();
    });

    it('hides change when showChange is false', () => {
      render(
        <TestWrapper>
          <MiniLiveMarketData symbol="AAPL" showChange={false} />
        </TestWrapper>
      );

      expect(screen.queryByText(/1\.45%/)).not.toBeInTheDocument();
    });
  });

  describe('Color Coding', () => {
    it('uses green for positive changes in mini version', () => {
      render(
        <TestWrapper>
          <MiniLiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      const changeElement = screen.getByText('(+1.45%)');
      expect(changeElement).toHaveClass('text-green-400');
    });

    it('uses red for negative changes in mini version', () => {
      mockMarketData['AAPL'] = {
        ...mockMarketData['AAPL'],
        change: -2.15,
        change_percent: -1.45
      };
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: true,
        marketData: mockMarketData,
        error: null,
      });

      render(
        <TestWrapper>
          <MiniLiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      const changeElement = screen.getByText('(-1.45%)');
      expect(changeElement).toHaveClass('text-red-400');
    });
  });

  describe('Loading State', () => {
    it('shows placeholder when no data available', () => {
      mockUseMarketDataWebSocket.mockReturnValue({
        isConnected: true,
        marketData: {},
        error: null,
      });

      // MiniLiveMarketData uses Redux state directly, so we need a store with empty marketData
      const emptyStore = createMockStore({ marketData: {} });
      render(
        <Provider store={emptyStore}>
          <MiniLiveMarketData symbol="AAPL" />
        </Provider>
      );

      expect(screen.getByText('--')).toBeInTheDocument();
    });
  });

  describe('Connected Indicator', () => {
    it('shows pulse indicator when connected', () => {
      render(
        <TestWrapper>
          <MiniLiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      // The green pulse indicator should be present
      const pulseIndicator = document.querySelector('.bg-green-400.animate-pulse');
      expect(pulseIndicator).toBeInTheDocument();
    });
  });
});

describe('Integration Tests', () => {
  describe('Hook Integration', () => {
    it('passes correct symbols to hook', () => {
      render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(mockUseMarketDataWebSocket).toHaveBeenCalledWith(['AAPL']);
    });

    it('re-calls hook when symbol changes', () => {
      const { rerender } = render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      rerender(
        <TestWrapper>
          <LiveMarketData symbol="GOOGL" />
        </TestWrapper>
      );

      expect(mockUseMarketDataWebSocket).toHaveBeenCalledWith(['GOOGL']);
    });
  });

  describe('Performance', () => {
    it('renders without performance issues', () => {
      const { container } = render(
        <TestWrapper>
          <LiveMarketData symbol="AAPL" />
        </TestWrapper>
      );

      expect(container.firstChild).toBeInTheDocument();
    });
  });
});
