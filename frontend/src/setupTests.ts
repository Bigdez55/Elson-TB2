// Jest setup file - runs before each test file

// Polyfills for MSW v2 (MUST be before any MSW imports)
// Using require to ensure these run before hoisted imports
const { TextEncoder: UtilTextEncoder, TextDecoder: UtilTextDecoder } = require('util');
global.TextEncoder = UtilTextEncoder;
global.TextDecoder = UtilTextDecoder;

// Web Streams API polyfill for MSW v2
const { ReadableStream, WritableStream, TransformStream } = require('web-streams-polyfill');
global.ReadableStream = ReadableStream;
global.WritableStream = WritableStream;
global.TransformStream = TransformStream;

// Add fetch polyfill for Node environment
require('whatwg-fetch');

// BroadcastChannel polyfill for MSW
class BroadcastChannelPolyfill {
  name: string;
  onmessage: ((event: MessageEvent) => void) | null = null;
  constructor(name: string) { this.name = name; }
  postMessage() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true; }
}
global.BroadcastChannel = BroadcastChannelPolyfill as any;

// Now safe to import MSW and testing utilities
import '@testing-library/jest-dom';

// Use require for MSW to ensure polyfills are applied first
const { server } = require('./mocks/server');
const { resetTradingState } = require('./mocks/handlers/trading');

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: jest.fn((index: number) => Object.keys(store)[index] || null),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage similarly
Object.defineProperty(window, 'sessionStorage', {
  value: localStorageMock,
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
class ResizeObserverMock {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

Object.defineProperty(window, 'ResizeObserver', {
  value: ResizeObserverMock,
});

// Mock IntersectionObserver
class IntersectionObserverMock {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
}

Object.defineProperty(window, 'IntersectionObserver', {
  value: IntersectionObserverMock,
});

// Mock scrollTo
window.scrollTo = jest.fn();

// Setup MSW server
beforeAll(() => {
  // Start the MSW server before all tests
  server.listen({
    onUnhandledRequest: 'warn', // Warn about unhandled requests
  });
});

afterEach(() => {
  // Reset handlers after each test to ensure clean state
  server.resetHandlers();

  // Reset trading state (orders, history)
  resetTradingState();

  // Clear localStorage
  localStorage.clear();

  // Reset all mocks
  jest.clearAllMocks();
});

afterAll(() => {
  // Stop the MSW server after all tests
  server.close();
});

// Suppress specific console errors during tests
const originalError = console.error;
console.error = (...args: any[]) => {
  // Suppress React Router warnings in tests
  if (typeof args[0] === 'string' && args[0].includes('React Router')) {
    return;
  }
  // Suppress act() warnings that are often false positives
  if (typeof args[0] === 'string' && args[0].includes('act(...)')) {
    return;
  }
  originalError.call(console, ...args);
};

// Export utilities for tests
export { server };
