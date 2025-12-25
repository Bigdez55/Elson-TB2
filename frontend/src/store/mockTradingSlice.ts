// Mock Redux actions and selectors for trading components
// In a real application, these would be proper Redux Toolkit slice actions

import { logger } from '../utils/logger';

export const submitOrder = (orderData: any) => async (_dispatch: any) => {
  logger.debug('Mock submitOrder called with:', orderData);
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true, orderId: Math.random().toString(36) });
    }, 1000);
  });
};

export const fetchPortfolio = () => async (_dispatch: any) => {
  logger.debug('Mock fetchPortfolio called');
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        assets: [
          {
            symbol: 'AAPL',
            amount: 10,
            currentPrice: 150.25,
            averagePrice: 145.50,
            totalValue: 1502.50,
          },
          {
            symbol: 'MSFT',
            amount: 5,
            currentPrice: 310.75,
            averagePrice: 300.00,
            totalValue: 1553.75,
          },
        ],
        totalValue: 3056.25,
      });
    }, 1000);
  });
};

export const fetchTradeHistory = (params: any) => async (_dispatch: any) => {
  logger.debug('Mock fetchTradeHistory called with:', params);
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        trades: [
          {
            id: '1',
            symbol: 'AAPL',
            type: 'BUY',
            amount: 5,
            price: 150.25,
            status: 'COMPLETED',
            timestamp: new Date().toISOString(),
          },
          {
            id: '2',
            symbol: 'MSFT',
            type: 'BUY',
            amount: 2,
            price: 310.75,
            status: 'COMPLETED',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
          },
        ],
      });
    }, 1000);
  });
};

export const fetchWatchlist = () => async (_dispatch: any) => {
  logger.debug('Mock fetchWatchlist called');
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        items: [
          {
            symbol: 'AAPL',
            price: 150.25,
            change24h: 2.5,
            volume24h: 1000000,
            high24h: 152.50,
            low24h: 148.00,
          },
          {
            symbol: 'MSFT',
            price: 310.75,
            change24h: -1.2,
            volume24h: 800000,
            high24h: 315.00,
            low24h: 308.50,
          },
        ],
      });
    }, 1000);
  });
};

export const addToWatchlist = (symbol: string) => async (_dispatch: any) => {
  logger.debug('Mock addToWatchlist called with:', symbol);
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 500);
  });
};

export const removeFromWatchlist = (symbol: string) => async (_dispatch: any) => {
  logger.debug('Mock removeFromWatchlist called with:', symbol);
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 500);
  });
};