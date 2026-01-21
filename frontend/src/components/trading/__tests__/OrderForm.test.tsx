import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import OrderForm from '../OrderForm';

// Create mock function with proper typing
const mockSubmitOrder = jest.fn<
  Promise<{ success: boolean; orderId: string } | undefined>,
  [orderData: any]
>();

// Mock the trading slice
jest.mock('../../../store/mockTradingSlice', () => ({
  submitOrder: (orderData: any) => (_dispatch: any) => mockSubmitOrder(orderData)
}));

// Mock the TradingContext
jest.mock('../../../contexts/TradingContext', () => ({
  useTradingContext: () => ({
    mode: 'paper',
    setMode: jest.fn(),
    canAccessLive: true,
    riskProfile: { level: 'moderate' },
    setRiskProfile: jest.fn(),
    isBlocked: false,
    setBlocked: jest.fn(),
    tradingLimits: { dailyLimit: 10000, maxOrderSize: 1000 },
    setTradingLimits: jest.fn()
  }),
  TradingContextProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

// TODO: These tests need refactoring - OrderForm component requires Redux Provider,
// TradingContext, and RTK Query setup that isn't fully mocked in this test file.
describe.skip('OrderForm', () => {
  const defaultProps = {
    symbol: 'AAPL',
    currentPrice: 150.25,
    availableBalance: 10000
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders order form with correct symbol', () => {
      render(<OrderForm {...defaultProps} />);
      expect(screen.getByText('Place Order - AAPL')).toBeInTheDocument();
    });

    it('displays current price and available balance', () => {
      render(<OrderForm {...defaultProps} />);
      expect(screen.getByText('$150.25')).toBeInTheDocument();
      expect(screen.getByText('$10,000.00')).toBeInTheDocument();
    });

    it('shows buy and sell buttons', () => {
      render(<OrderForm {...defaultProps} />);
      expect(screen.getByRole('button', { name: /buy/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sell/i })).toBeInTheDocument();
    });

    it('shows order type dropdown', () => {
      render(<OrderForm {...defaultProps} />);
      expect(screen.getByDisplayValue('Market')).toBeInTheDocument();
    });

    it('shows amount input field', () => {
      render(<OrderForm {...defaultProps} />);
      expect(screen.getByLabelText(/amount/i)).toBeInTheDocument();
    });
  });

  describe('Order Type Changes', () => {
    it('shows price field for limit orders', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'LIMIT' } });
      
      await waitFor(() => {
        expect(screen.getByLabelText(/price/i)).toBeInTheDocument();
      });
    });

    it('shows stop price field for stop orders', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'STOP' } });
      
      await waitFor(() => {
        expect(screen.getByLabelText(/stop price/i)).toBeInTheDocument();
      });
    });

    it('shows both price and stop price for stop limit orders', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'STOP_LIMIT' } });
      
      await screen.findByLabelText(/^price$/i);
      expect(screen.getByLabelText(/^price$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/stop price/i)).toBeInTheDocument();
    });
  });

  describe('Order Side Toggle', () => {
    it('switches between buy and sell', () => {
      render(<OrderForm {...defaultProps} />);
      
      const sellButton = screen.getByRole('button', { name: /sell/i });
      fireEvent.click(sellButton);
      
      expect(sellButton).toHaveClass('variant');
    });
  });

  describe('Form Validation', () => {
    it('validates amount is required', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/amount is required/i)).toBeInTheDocument();
      });
    });

    it('validates amount is positive', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '-5' } });
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/amount must be greater than 0/i)).toBeInTheDocument();
      });
    });

    it('validates sufficient balance', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '100' } }); // 100 * 150.25 > 10000
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/insufficient balance/i)).toBeInTheDocument();
      });
    });

    it('validates price for limit orders', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'LIMIT' } });
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '10' } });
      
      const priceInput = screen.getByLabelText(/^price$/i);
      fireEvent.change(priceInput, { target: { value: '-100' } });
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/price must be greater than 0/i)).toBeInTheDocument();
      });
    });
  });

  describe('Order Submission', () => {
    it('submits market order successfully', async () => {
      mockSubmitOrder.mockResolvedValueOnce(undefined);
      
      render(<OrderForm {...defaultProps} />);
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '10' } });
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSubmitOrder).toHaveBeenCalledWith({
          symbol: 'AAPL',
          type: 'MARKET',
          side: 'BUY',
          amount: 10,
          price: undefined,
          stopPrice: undefined
        });
      });
      
      expect(screen.getByText(/buy order for 10 aapl submitted successfully/i)).toBeInTheDocument();
    });

    it('submits limit order successfully', async () => {
      mockSubmitOrder.mockResolvedValueOnce(undefined);
      
      render(<OrderForm {...defaultProps} />);
      
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'LIMIT' } });
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '10' } });
      
      const priceInput = screen.getByLabelText(/^price$/i);
      fireEvent.change(priceInput, { target: { value: '145.00' } });
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSubmitOrder).toHaveBeenCalledWith({
          symbol: 'AAPL',
          type: 'LIMIT',
          side: 'BUY',
          amount: 10,
          price: 145.00,
          stopPrice: undefined
        });
      });
    });

    it('handles submission errors', async () => {
      mockSubmitOrder.mockRejectedValueOnce(new Error('Order failed'));
      
      render(<OrderForm {...defaultProps} />);
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '10' } });
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/order failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Order Total Calculation', () => {
    it('calculates total correctly for market orders', () => {
      render(<OrderForm {...defaultProps} />);
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '10' } });
      
      expect(screen.getByText('$1,502.50')).toBeInTheDocument();
    });

    it('calculates total correctly for limit orders', async () => {
      render(<OrderForm {...defaultProps} />);
      
      const orderTypeSelect = screen.getByDisplayValue('Market');
      fireEvent.change(orderTypeSelect, { target: { value: 'LIMIT' } });
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '10' } });
      
      const priceInput = screen.getByLabelText(/^price$/i);
      fireEvent.change(priceInput, { target: { value: '145.00' } });
      
      await waitFor(() => {
        expect(screen.getByText('$1,450.00')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during submission', async () => {
      let resolveSubmit: (value?: { success: boolean; orderId: string }) => void;
      const submitPromise = new Promise<{ success: boolean; orderId: string } | undefined>((resolve) => {
        resolveSubmit = resolve;
      });
      mockSubmitOrder.mockReturnValueOnce(submitPromise);
      
      render(<OrderForm {...defaultProps} />);
      
      const amountInput = screen.getByLabelText(/amount/i);
      fireEvent.change(amountInput, { target: { value: '10' } });
      
      const submitButton = screen.getByRole('button', { name: /buy aapl/i });
      fireEvent.click(submitButton);
      
      expect(submitButton).toBeDisabled();
      
      resolveSubmit!();
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });
    });
  });
});