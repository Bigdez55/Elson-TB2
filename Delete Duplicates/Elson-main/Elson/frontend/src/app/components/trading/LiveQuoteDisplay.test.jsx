import React from 'react';
import { render, screen } from '@testing-library/react';
import { LiveQuoteDisplay } from './LiveQuoteDisplay';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import userSlice from '../../store/slices/userSlice';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the useMarketWebSocket hook
vi.mock('../../hooks/useMarketWebSocket', () => {
  const quotes = {
    'AAPL': {
      symbol: 'AAPL',
      price: 175.25,
      bid: 175.20,
      ask: 175.30,
      volume: 1000,
      timestamp: new Date().toISOString(),
      source: 'mock'
    },
    'MSFT': {
      symbol: 'MSFT',
      price: 320.45,
      bid: 320.40,
      ask: 320.50,
      volume: 500,
      timestamp: new Date().toISOString(),
      source: 'mock'
    }
  };

  return {
    useMarketWebSocket: vi.fn(() => ({
      isConnected: true,
      error: null,
      quotes,
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      reconnect: vi.fn()
    }))
  };
});

// Create mock store
const createMockStore = () => configureStore({
  reducer: {
    user: userSlice
  }
});

describe('LiveQuoteDisplay Component', () => {
  let store;

  beforeEach(() => {
    store = createMockStore();
  });

  it('renders correctly with symbols', async () => {
    const { container } = render(
      <Provider store={store}>
        <LiveQuoteDisplay symbols={['AAPL', 'MSFT']} />
      </Provider>
    );

    // Check that symbols are displayed
    expect(container.textContent).includes('AAPL');
    expect(container.textContent).includes('MSFT');
    expect(container.textContent).includes('$175.25');
    expect(container.textContent).includes('$320.45');

    // Check for connection status
    expect(container.textContent).includes('Connected');
    expect(container.textContent).includes('Live Data');
  });

  it('renders empty state when no symbols provided', () => {
    const { container } = render(
      <Provider store={store}>
        <LiveQuoteDisplay symbols={[]} />
      </Provider>
    );

    expect(container.textContent).includes('No symbols selected for real-time quotes');
  });

  it('renders in light mode with correct styles', async () => {
    const { container } = render(
      <Provider store={store}>
        <LiveQuoteDisplay symbols={['AAPL']} darkMode={false} />
      </Provider>
    );

    // Check for light mode container (should have white background)
    const bgWhiteElement = container.querySelector('.bg-white');
    expect(bgWhiteElement).not.toBeNull();
  });

  it('renders compact view when compact prop is true', async () => {
    const { container } = render(
      <Provider store={store}>
        <LiveQuoteDisplay symbols={['AAPL']} compact={true} />
      </Provider>
    );

    // In compact mode, basic elements should be present
    expect(container.textContent).includes('AAPL');
    expect(container.textContent).includes('$175.25');

    // The percentage change text should not be in the document in compact mode
    expect(container.textContent).not.includes('0.00%');
  });
});