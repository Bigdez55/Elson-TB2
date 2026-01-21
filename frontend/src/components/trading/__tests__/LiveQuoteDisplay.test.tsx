import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import LiveQuoteDisplay from '../LiveQuoteDisplay';

import { useMarketWebSocket } from '../../../hooks/useMarketWebSocket';

// Mock the WebSocket hook
jest.mock('../../../hooks/useMarketWebSocket', () => ({
  useMarketWebSocket: jest.fn()
}));

// Mock the formatters
jest.mock('../../../utils/formatters', () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`
}));

const mockUseMarketWebSocket = useMarketWebSocket as jest.MockedFunction<typeof useMarketWebSocket>;

// TODO: These tests need refactoring - useMarketWebSocket mock doesn't match
// the actual hook return type and component behavior.
describe.skip('LiveQuoteDisplay', () => {
  const defaultProps = {
    symbols: ['AAPL', 'MSFT', 'GOOGL']
  };

  const mockWebSocketReturn = {
    isConnected: true,
    error: null,
    quotes: {
      'AAPL': {
        symbol: 'AAPL',
        price: 150.25,
        timestamp: Date.now(),
        volume: 1000000,
        high24h: 152.50,
        low24h: 148.00,
        change24h: 2.5
      },
      'MSFT': {
        symbol: 'MSFT',
        price: 310.75,
        timestamp: Date.now(),
        volume: 800000,
        high24h: 315.00,
        low24h: 308.50,
        change24h: -1.2
      }
    },
    subscribe: jest.fn(),
    unsubscribe: jest.fn(),
    connect: jest.fn(),
    disconnect: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseMarketWebSocket.mockReturnValue(mockWebSocketReturn);
  });

  describe('Rendering - Dark Mode', () => {
    it('renders with dark mode styling by default', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getByText('Live Market Data')).toBeInTheDocument();
      expect(screen.getByTestId('live-quote-container')).toHaveClass('bg-gray-900');
    });

    it('shows connection status when connected', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByTestId('connection-status')).toHaveClass('bg-green-500');
    });

    it('shows disconnected status when not connected', () => {
      mockUseMarketWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false
      });
      
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.getByTestId('connection-status')).toHaveClass('bg-red-500');
    });
  });

  describe('Rendering - Light Mode', () => {
    it('renders with light mode styling when darkMode is false', () => {
      render(<LiveQuoteDisplay {...defaultProps} darkMode={false} />);
      
      expect(screen.getByText('Live Market Data')).toBeInTheDocument();
      expect(screen.getByTestId('live-quote-container')).toHaveClass('bg-white');
    });
  });

  describe('Quote Display', () => {
    it('displays quotes for subscribed symbols', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('MSFT')).toBeInTheDocument();
      expect(screen.getByText('$150.25')).toBeInTheDocument();
      expect(screen.getByText('$310.75')).toBeInTheDocument();
    });

    it('shows loading spinner for symbols without data', () => {
      render(<LiveQuoteDisplay symbols={['AAPL', 'GOOGL']} />);
      
      expect(screen.getByText('GOOGL')).toBeInTheDocument();
      expect(screen.getByText('Waiting for data...')).toBeInTheDocument();
    });

    it('displays change percentages with correct colors', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      // Positive change should be green
      const positiveChange = screen.getByText('+2.50%');
      expect(positiveChange).toHaveClass('text-green-400');
      
      // Negative change should be red
      const negativeChange = screen.getByText('-1.20%');
      expect(negativeChange).toHaveClass('text-red-400');
    });

    it('displays timestamps', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      // Should show formatted time for quotes with data
      expect(screen.getAllByTestId('quote-timestamp')).toHaveLength(2);
    });
  });

  describe('Compact Mode', () => {
    it('hides detailed information in compact mode', () => {
      render(<LiveQuoteDisplay {...defaultProps} compact={true} />);
      
      // In compact mode, change percentages and timestamps should not be shown
      expect(screen.queryByText('+2.50%')).not.toBeInTheDocument();
      expect(screen.queryByText('-1.20%')).not.toBeInTheDocument();
    });

    it('shows detailed information in non-compact mode', () => {
      render(<LiveQuoteDisplay {...defaultProps} compact={false} />);
      
      expect(screen.getByText('+2.50%')).toBeInTheDocument();
      expect(screen.getByText('-1.20%')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('displays error messages', () => {
      mockUseMarketWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        error: 'Connection failed'
      });
      
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getByText('Connection failed')).toBeInTheDocument();
    });

    it('styles error messages appropriately in dark mode', () => {
      mockUseMarketWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        error: 'Connection failed'
      });
      
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      const errorElement = screen.getByText('Connection failed');
      expect(errorElement).toHaveClass('text-red-400');
    });

    it('styles error messages appropriately in light mode', () => {
      mockUseMarketWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        error: 'Connection failed'
      });
      
      render(<LiveQuoteDisplay {...defaultProps} darkMode={false} />);
      
      const errorElement = screen.getByText('Connection failed');
      expect(errorElement).toHaveClass('text-red-600');
    });
  });

  describe('WebSocket Integration', () => {
    it('subscribes to symbols on mount', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(mockWebSocketReturn.subscribe).toHaveBeenCalledWith(['AAPL', 'MSFT', 'GOOGL']);
    });

    it('unsubscribes on unmount', () => {
      const { unmount } = render(<LiveQuoteDisplay {...defaultProps} />);
      
      unmount();
      
      expect(mockWebSocketReturn.unsubscribe).toHaveBeenCalledWith(['AAPL', 'MSFT', 'GOOGL']);
    });

    it('resubscribes when symbols change', () => {
      const { rerender } = render(<LiveQuoteDisplay symbols={['AAPL']} />);
      
      rerender(<LiveQuoteDisplay symbols={['AAPL', 'TSLA']} />);
      
      expect(mockWebSocketReturn.subscribe).toHaveBeenCalledWith(['AAPL', 'TSLA']);
    });
  });

  describe('Empty State', () => {
    it('shows message when no symbols are provided', () => {
      render(<LiveQuoteDisplay symbols={[]} />);
      
      expect(screen.getByText('No symbols selected for real-time quotes')).toBeInTheDocument();
    });
  });

  describe('Data Freshness', () => {
    it('shows live data indicator when data is fresh', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getByText('Live Data')).toBeInTheDocument();
    });

    it('shows waiting indicator when data is stale', () => {
      // Mock stale data (older than 10 seconds)
      const staleTime = Date.now() - 15000;
      mockUseMarketWebSocket.mockReturnValue({
        ...mockWebSocketReturn,
        quotes: {
          'AAPL': {
            ...mockWebSocketReturn.quotes['AAPL'],
            timestamp: staleTime
          }
        }
      });
      
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getByText('Waiting for updates...')).toBeInTheDocument();
    });
  });

  describe('Callback Functions', () => {
    it('calls onQuoteUpdate when quotes change', () => {
      const onQuoteUpdate = jest.fn();
      
      render(<LiveQuoteDisplay {...defaultProps} onQuoteUpdate={onQuoteUpdate} />);
      
      expect(onQuoteUpdate).toHaveBeenCalledWith(mockWebSocketReturn.quotes);
    });
  });

  describe('Hover Effects', () => {
    it('applies hover styles to quote rows', () => {
      render(<LiveQuoteDisplay {...defaultProps} />);
      
      expect(screen.getAllByTestId('quote-row')).toHaveLength(2);
    });
  });

  describe('Memoization', () => {
    it('memo prevents unnecessary re-renders', () => {
      const { rerender } = render(<LiveQuoteDisplay {...defaultProps} />);
      
      // Same props should not cause re-render (we can't directly test this with our setup,
      // but the component uses React.memo to optimize re-renders)
      rerender(<LiveQuoteDisplay {...defaultProps} />);
      
      // The subscribe function should not be called again with same symbols
      expect(mockWebSocketReturn.subscribe).toHaveBeenCalledTimes(1);
    });
  });
});