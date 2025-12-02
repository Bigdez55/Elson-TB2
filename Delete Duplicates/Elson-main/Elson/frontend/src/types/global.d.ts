// Include jest-dom matchers
import '@testing-library/jest-dom';

// Add axe-core configuration to window
declare global {
  interface Window {
    axe: {
      configure: (options: any) => void;
      run: (element: Element, options?: any) => Promise<any>;
    };
  }
}

// Add jest-axe types
declare module 'jest-axe' {
  import { AxeResults, RunOptions, Spec } from 'axe-core';
  
  export interface JestAxeConfigureOptions extends RunOptions {
    rules?: Record<string, { enabled: boolean }>;
  }
  
  export const axe: (
    element: Element | React.ReactElement,
    options?: JestAxeConfigureOptions,
  ) => Promise<AxeResults>;
  
  export const configureAxe: (options?: JestAxeConfigureOptions) => typeof axe;
  
  export const toHaveNoViolations: jest.CustomMatcher;
}

export {};