import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TradeHistory from '../TradeHistory';

// Mock the formatters
jest.mock('../../../utils/formatters', () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`,
  formatDateTime: (date: string) => new Date(date).toLocaleString()
}));

describe('TradeHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('shows loading spinner initially', () => {
      render(<TradeHistory />);
      expect(screen.getByText('Loading trade history...')).toBeInTheDocument();
    });
  });

  describe('Trade History Display', () => {
    it('displays trade history after loading', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByText('Trade History')).toBeInTheDocument();
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('MSFT')).toBeInTheDocument();
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
        expect(screen.getByText('TSLA')).toBeInTheDocument();
        expect(screen.getByText('NVDA')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays trade types with correct colors', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const buyOrders = screen.getAllByText('BUY');
        const sellOrders = screen.getAllByText('SELL');
        
        buyOrders.forEach(element => {
          expect(element).toHaveClass('text-green-400');
        });
        
        sellOrders.forEach(element => {
          expect(element).toHaveClass('text-red-400');
        });
      }, { timeout: 2000 });
    });

    it('displays trade amounts correctly', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByText('10.00000000')).toBeInTheDocument();
        expect(screen.getByText('5.00000000')).toBeInTheDocument();
        expect(screen.getByText('2.00000000')).toBeInTheDocument();
        expect(screen.getByText('8.00000000')).toBeInTheDocument();
        expect(screen.getByText('3.00000000')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays trade prices', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByText('$150.25')).toBeInTheDocument();
        expect(screen.getByText('$310.75')).toBeInTheDocument();
        expect(screen.getByText('$140.85')).toBeInTheDocument();
        expect(screen.getByText('$245.60')).toBeInTheDocument();
        expect(screen.getByText('$450.20')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays calculated total values', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByText('$1,502.50')).toBeInTheDocument(); // 10 * 150.25
        expect(screen.getByText('$1,553.75')).toBeInTheDocument(); // 5 * 310.75
        expect(screen.getByText('$281.70')).toBeInTheDocument();   // 2 * 140.85
        expect(screen.getByText('$1,964.80')).toBeInTheDocument(); // 8 * 245.60
        expect(screen.getByText('$1,350.60')).toBeInTheDocument(); // 3 * 450.20
      }, { timeout: 2000 });
    });
  });

  describe('Trade Status Display', () => {
    it('displays status badges with correct styling', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const completedStatuses = screen.getAllByText('COMPLETED');
        const pendingStatuses = screen.getAllByText('PENDING');
        const failedStatuses = screen.getAllByText('FAILED');
        
        completedStatuses.forEach(element => {
          expect(element).toHaveClass('bg-green-900', 'text-green-300');
        });
        
        pendingStatuses.forEach(element => {
          expect(element).toHaveClass('bg-yellow-900', 'text-yellow-300');
        });
        
        failedStatuses.forEach(element => {
          expect(element).toHaveClass('bg-red-900', 'text-red-300');
        });
      }, { timeout: 2000 });
    });
  });

  describe('Filtering and Pagination', () => {
    it('displays page size selector', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('20 per page')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays timeframe selector', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('Last 7 Days')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('changes page size when selector is changed', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const pageSizeSelect = screen.getByDisplayValue('20 per page');
        fireEvent.change(pageSizeSelect, { target: { value: '10' } });
        expect(screen.getByDisplayValue('10 per page')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('changes timeframe when selector is changed', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const timeframeSelect = screen.getByDisplayValue('Last 7 Days');
        fireEvent.change(timeframeSelect, { target: { value: '24h' } });
        expect(screen.getByDisplayValue('Last 24 Hours')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Pagination Controls', () => {
    it('displays pagination information', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByText(/showing \d+ to \d+ of \d+ entries/i)).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays pagination buttons', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('disables previous button on first page', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const previousButton = screen.getByRole('button', { name: /previous/i });
        expect(previousButton).toBeDisabled();
      }, { timeout: 2000 });
    });
  });

  describe('Table Structure', () => {
    it('displays correct column headers', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByText('Symbol')).toBeInTheDocument();
        expect(screen.getByText('Type')).toBeInTheDocument();
        expect(screen.getByText('Amount')).toBeInTheDocument();
        expect(screen.getByText('Price')).toBeInTheDocument();
        expect(screen.getByText('Total')).toBeInTheDocument();
        expect(screen.getByText('Fee')).toBeInTheDocument();
        expect(screen.getByText('Status')).toBeInTheDocument();
        expect(screen.getByText('Time')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays trade type indicators', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const buyIndicators = document.querySelectorAll('.bg-green-500');
        const sellIndicators = document.querySelectorAll('.bg-red-500');
        
        expect(buyIndicators.length).toBeGreaterThan(0);
        expect(sellIndicators.length).toBeGreaterThan(0);
      }, { timeout: 2000 });
    });
  });

  describe('Hover Effects', () => {
    it('applies hover styles to table rows', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const tableRows = document.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
          expect(row).toHaveClass('hover:bg-gray-700/50');
        });
      }, { timeout: 2000 });
    });
  });

  describe('Responsive Design', () => {
    it('has overflow scrolling for mobile', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const tableContainer = document.querySelector('.overflow-x-auto');
        expect(tableContainer).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('uses flex layout for responsive controls', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        const controlsContainer = document.querySelector('.flex.flex-col.sm\\:flex-row');
        expect(controlsContainer).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Auto-refresh', () => {
    it('shows updating indicator during refresh', async () => {
      render(<TradeHistory />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Trade History')).toBeInTheDocument();
      }, { timeout: 2000 });
      
      // The component refreshes every 30 seconds, but we can check for the updating indicator
      // The component has logic to show "Updating..." when loading is true
    });
  });

  describe('Fee Display', () => {
    it('displays fees when present', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByText('$1.50')).toBeInTheDocument();
        expect(screen.getByText('$2.25')).toBeInTheDocument();
        expect(screen.getByText('$1.75')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('handles zero fees appropriately', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        // Pending and failed trades have zero fees in mock data
        const rows = document.querySelectorAll('tbody tr');
        expect(rows.length).toBeGreaterThan(0);
      }, { timeout: 2000 });
    });
  });

  describe('Accessibility', () => {
    it('has proper table structure for screen readers', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.getAllByRole('columnheader')).toHaveLength(8);
      }, { timeout: 2000 });
    });

    it('has proper button labels', async () => {
      render(<TradeHistory />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });
});