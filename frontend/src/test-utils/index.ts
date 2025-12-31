/**
 * Test utilities index
 * Re-exports all test utilities for easy importing
 */

// Render utilities
export {
  renderWithProviders,
  renderWithRedux,
  createTestStore,
} from './renderWithProviders';

// Test data factories
export {
  createUser,
  createTrade,
  createExecutedTrade,
  createQuote,
  createQuotes,
  createPortfolio,
  createHolding,
  createHoldings,
  createAsset,
  createTradingStats,
  createAuthState,
  createTradingState,
  createPortfolioState,
  createWebsocketState,
  createPreloadedState,
  resetIdCounter,
} from './factories';

// WebSocket testing utilities
export {
  MockWebSocket,
  MockWebSocketServer,
  installMockWebSocket,
  restoreMockWebSocket,
  waitForConnection,
  waitForMessage,
} from './websocket';

// Re-export testing library utilities
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';

// Re-export MSW utilities
export { server } from '../mocks/server';
export { handlers, resetTradingState } from '../mocks/handlers';
export {
  defaultUser,
  defaultTrade,
  defaultPosition,
  defaultTradingStats,
  defaultPortfolio,
  defaultHoldings,
  defaultPerformance,
  defaultRiskMetrics,
  defaultRiskLimits,
  defaultCircuitBreakers,
  defaultAssets,
  createQuote as createMSWQuote,
} from '../mocks/handlers';
