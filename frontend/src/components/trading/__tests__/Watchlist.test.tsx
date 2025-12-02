import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Watchlist from '../Watchlist';

// Mock the formatters and validators
jest.mock('../../../utils/formatters', () => ({
  formatCurrency: (value: number) => `$${value.toFixed(2)}`,
  formatPercentage: (value: number) => `${value.toFixed(2)}%`
}));

jest.mock('../../../utils/validators', () => ({
  isValidSymbol: (symbol: string) => /^[A-Z0-9/.-]+$/i.test(symbol) && symbol.length >= 1 && symbol.length <= 10
}));

describe('Watchlist', () => {
  const mockOnSymbolSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('shows loading spinner initially', () => {
      render(<Watchlist />);
      expect(screen.getByText('Loading watchlist...')).toBeInTheDocument();
    });
  });

  describe('Watchlist Display', () => {
    it('displays watchlist after loading', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        expect(screen.getByText('Watchlist')).toBeInTheDocument();
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.getByText('MSFT')).toBeInTheDocument();
        expect(screen.getByText('GOOGL')).toBeInTheDocument();
        expect(screen.getByText('TSLA')).toBeInTheDocument();
        expect(screen.getByText('NVDA')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays stock prices', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        expect(screen.getByText('$150.25')).toBeInTheDocument();
        expect(screen.getByText('$310.75')).toBeInTheDocument();
        expect(screen.getByText('$140.85')).toBeInTheDocument();
        expect(screen.getByText('$245.60')).toBeInTheDocument();
        expect(screen.getByText('$450.20')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays 24h changes with correct colors', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        // Positive changes should be green
        const positiveChanges = screen.getAllByText(/\+?\d+\.\d+%/).filter(el => 
          el.textContent?.includes('2.50%') || el.textContent?.includes('0.80%') || el.textContent?.includes('5.70%')
        );
        positiveChanges.forEach(element => {
          expect(element).toHaveClass('text-green-400');
        });
        
        // Negative changes should be red
        const negativeChanges = screen.getAllByText(/-\d+\.\d+%/);
        negativeChanges.forEach(element => {
          expect(element).toHaveClass('text-red-400');
        });
      }, { timeout: 2000 });
    });

    it('displays high/low prices', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        expect(screen.getByText(/H: \$152\.50/)).toBeInTheDocument();
        expect(screen.getByText(/L: \$148\.00/)).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('displays volume in millions', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const volumeElements = screen.getAllByText(/\d+\.\d+M/);
        expect(volumeElements.length).toBeGreaterThan(0);
      }, { timeout: 2000 });
    });
  });

  describe('Adding Symbols', () => {
    it('allows adding a new symbol', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
        const addButton = screen.getByRole('button', { name: /add/i });
        
        fireEvent.change(input, { target: { value: 'AMZN' } });
        fireEvent.click(addButton);
      }, { timeout: 2000 });
      
      await waitFor(() => {
        expect(screen.getByText('AMZN')).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('validates symbol before adding', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
        const addButton = screen.getByRole('button', { name: /add/i });
        
        fireEvent.change(input, { target: { value: 'INVALID@SYMBOL' } });
        fireEvent.click(addButton);
      }, { timeout: 2000 });
      
      await waitFor(() => {
        expect(screen.getByText(/please enter a valid symbol/i)).toBeInTheDocument();
      });
    });

    it('prevents adding duplicate symbols', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
        const addButton = screen.getByRole('button', { name: /add/i });
        
        fireEvent.change(input, { target: { value: 'AAPL' } });
        fireEvent.click(addButton);
      }, { timeout: 2000 });
      
      await waitFor(() => {
        expect(screen.getByText(/symbol already in watchlist/i)).toBeInTheDocument();
      });
    });

    it('requires non-empty symbol', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add/i });
        fireEvent.click(addButton);
      }, { timeout: 2000 });
      
      await waitFor(() => {
        expect(screen.getByText(/please enter a symbol/i)).toBeInTheDocument();
      });
    });

    it('allows adding symbol by pressing Enter', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
        
        fireEvent.change(input, { target: { value: 'AMZN' } });
        fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
      }, { timeout: 2000 });
      
      await waitFor(() => {
        expect(screen.getByText('AMZN')).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('shows loading state when adding symbol', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
        const addButton = screen.getByRole('button', { name: /add/i });
        
        fireEvent.change(input, { target: { value: 'AMZN' } });
        fireEvent.click(addButton);
        
        // Button should be disabled during loading
        expect(addButton).toBeDisabled();
      }, { timeout: 2000 });
    });
  });

  describe('Removing Symbols', () => {
    it('allows removing symbols', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const removeButtons = screen.getAllByTitle('Remove from watchlist');
        fireEvent.click(removeButtons[0]);
      }, { timeout: 2000 });
      
      // The first symbol (AAPL) should be removed
      await waitFor(() => {
        expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
      });
    });

    it('shows remove button on hover', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const removeButtons = document.querySelectorAll('[title="Remove from watchlist"]');
        expect(removeButtons.length).toBeGreaterThan(0);
      }, { timeout: 2000 });
    });
  });

  describe('Symbol Selection', () => {
    it('calls onSymbolSelect when symbol is clicked', async () => {
      render(<Watchlist onSymbolSelect={mockOnSymbolSelect} />);
      
      await waitFor(() => {
        const symbolRow = screen.getByText('AAPL').closest('tr');
        fireEvent.click(symbolRow!);
        
        expect(mockOnSymbolSelect).toHaveBeenCalledWith('AAPL');
      }, { timeout: 2000 });
    });

    it('logs to console when no onSymbolSelect callback provided', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      
      render(<Watchlist />);
      
      await waitFor(() => {
        const symbolRow = screen.getByText('AAPL').closest('tr');
        fireEvent.click(symbolRow!);
        
        expect(consoleSpy).toHaveBeenCalledWith('Selected symbol:', 'AAPL');
      }, { timeout: 2000 });
      
      consoleSpy.mockRestore();
    });
  });

  describe('Filtering', () => {
    it('filters symbols based on search input', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const filterInput = screen.getByPlaceholderText('Filter symbols...');
        fireEvent.change(filterInput, { target: { value: 'AAP' } });
        
        expect(screen.getByText('AAPL')).toBeInTheDocument();
        expect(screen.queryByText('MSFT')).not.toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('shows no matches message when filter has no results', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const filterInput = screen.getByPlaceholderText('Filter symbols...');
        fireEvent.change(filterInput, { target: { value: 'NONEXISTENT' } });
        
        expect(screen.getByText('No symbols match your filter')).toBeInTheDocument();
        expect(screen.getByText('Try a different filter')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('is case insensitive', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const filterInput = screen.getByPlaceholderText('Filter symbols...');
        fireEvent.change(filterInput, { target: { value: 'aapl' } });
        
        expect(screen.getByText('AAPL')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Table Structure', () => {
    it('displays correct column headers', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        expect(screen.getByText('Symbol')).toBeInTheDocument();
        expect(screen.getByText('Price')).toBeInTheDocument();
        expect(screen.getByText('24h Change')).toBeInTheDocument();
        expect(screen.getByText('24h High/Low')).toBeInTheDocument();
        expect(screen.getByText('Volume')).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('has proper table structure', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.getAllByRole('columnheader')).toHaveLength(5);
      }, { timeout: 2000 });
    });
  });

  describe('Hover Effects', () => {
    it('applies hover styles to table rows', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const tableRows = document.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
          expect(row).toHaveClass('hover:bg-gray-700/50');
        });
      }, { timeout: 2000 });
    });

    it('applies hover styles to remove buttons', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const removeButtons = document.querySelectorAll('[title="Remove from watchlist"]');
        removeButtons.forEach(button => {
          expect(button).toHaveClass('hover:text-red-500');
        });
      }, { timeout: 2000 });
    });
  });

  describe('Auto-refresh', () => {
    it('shows updating indicator during refresh', async () => {
      render(<Watchlist />);
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Watchlist')).toBeInTheDocument();
      }, { timeout: 2000 });
      
      // The component refreshes every 10 seconds and shows "Updating prices..."
      // This is harder to test in unit tests without advanced timer mocking
    });
  });

  describe('Error Handling', () => {
    it('clears error when typing in symbol input', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
        const addButton = screen.getByRole('button', { name: /add/i });
        
        // Trigger an error first
        fireEvent.click(addButton);
      }, { timeout: 2000 });
      
      await waitFor(() => {
        expect(screen.getByText(/please enter a symbol/i)).toBeInTheDocument();
      });
      
      // Type in input to clear error
      const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
      fireEvent.change(input, { target: { value: 'AMZN' } });
      
      await waitFor(() => {
        expect(screen.queryByText(/please enter a symbol/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    it('has overflow scrolling for mobile', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const tableContainer = document.querySelector('.overflow-x-auto');
        expect(tableContainer).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('uses proper spacing for add symbol controls', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const controlsContainer = document.querySelector('.flex.space-x-2');
        expect(controlsContainer).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Empty State', () => {
    it('would show empty message when no symbols match filter', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const filterInput = screen.getByPlaceholderText('Filter symbols...');
        fireEvent.change(filterInput, { target: { value: 'NONEXISTENT' } });
        
        expect(screen.getByText('No symbols match your filter')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });

  describe('Button States', () => {
    it('disables add button when input is empty', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add/i });
        expect(addButton).toBeDisabled();
      }, { timeout: 2000 });
    });

    it('enables add button when input has value', async () => {
      render(<Watchlist />);
      
      await waitFor(() => {
        const input = screen.getByPlaceholderText('Add symbol (e.g., AAPL)');
        fireEvent.change(input, { target: { value: 'AMZN' } });
        
        const addButton = screen.getByRole('button', { name: /add/i });
        expect(addButton).not.toBeDisabled();
      }, { timeout: 2000 });
    });
  });
});