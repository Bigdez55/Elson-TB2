import '@testing-library/jest-dom';
import { configureAxe } from 'jest-axe';
import { vi } from 'vitest';

// Configure axe for accessibility testing
window.axe = configureAxe({
  // Specify which rule categories to run
  // See: https://github.com/dequelabs/axe-core/blob/master/doc/API.md#axe-core-tags
  rules: {
    // Enable rules for specific accessibility guidelines
    'wcag2a': { enabled: true },
    'wcag2aa': { enabled: true },
    'wcag21a': { enabled: true },
    'wcag21aa': { enabled: true },
    'best-practice': { enabled: true },
    
    // Disable specific rules if needed
    'color-contrast': { enabled: true },
  },
});

// Mock ResizeObserver which isn't available in JSDom
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock matchMedia which isn't available in JSDom
global.matchMedia = vi.fn().mockImplementation((query) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));

// Mock IntersectionObserver which isn't available in JSDom
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));