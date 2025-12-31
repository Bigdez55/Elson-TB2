import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

// This configures a Service Worker with the given request handlers
// for use in the browser (development mode)
export const worker = setupWorker(...handlers);

// Export handlers for runtime modifications
export { handlers };
