import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// This configures a Service Worker with the given request handlers
export const server = setupServer(...handlers);

// Export handlers for test-specific overrides
export { handlers };

// Re-export useful functions for tests
export { resetTradingState } from './handlers/trading';
