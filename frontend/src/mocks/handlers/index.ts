import { authHandlers, defaultUser } from './auth';
import { tradingHandlers, resetTradingState, defaultTrade, defaultPosition, defaultTradingStats } from './trading';
import { marketHandlers, createQuote, defaultAssets } from './market';
import { portfolioHandlers, defaultPortfolio, defaultHoldings, defaultPerformance } from './portfolio';
import { riskHandlers, defaultRiskMetrics, defaultRiskLimits, defaultCircuitBreakers } from './risk';

// Combine all handlers
export const handlers = [
  ...authHandlers,
  ...tradingHandlers,
  ...marketHandlers,
  ...portfolioHandlers,
  ...riskHandlers,
];

// Export individual handler groups for selective use in tests
export {
  authHandlers,
  tradingHandlers,
  marketHandlers,
  portfolioHandlers,
  riskHandlers,
};

// Export default data for assertions in tests
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
};

// Export utility functions
export {
  resetTradingState,
  createQuote,
};
