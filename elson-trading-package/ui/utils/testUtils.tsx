import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { store as appStore } from '../store/store';
import { AccessibilityProvider } from '../hooks/useAccessibility';

// Add jest-axe custom matchers
expect.extend(toHaveNoViolations);

// Create a mock store for testing
const createTestStore = (preloadedState = {}) => {
  return configureStore({
    reducer: appStore.getState,
    preloadedState
  });
};

// Define the type for the All Providers wrapper
type AllProvidersProps = {
  children: React.ReactNode;
  store?: ReturnType<typeof createTestStore>;
};

// Create a wrapper with all providers needed for testing
const AllProviders = ({ children, store }: AllProvidersProps) => {
  return (
    <Provider store={store || appStore}>
      <BrowserRouter>
        <AccessibilityProvider>
          {children}
        </AccessibilityProvider>
      </BrowserRouter>
    </Provider>
  );
};

// Custom render method that includes the providers
const customRender = (
  ui: ReactElement, 
  options?: Omit<RenderOptions, 'wrapper'> & { 
    store?: ReturnType<typeof createTestStore>;
  }
) => {
  const { store, ...renderOptions } = options || {};
  
  return render(ui, {
    wrapper: (props) => <AllProviders store={store} {...props} />,
    ...renderOptions,
  });
};

// Accessibility test helper
const testAccessibility = async (ui: ReactElement) => {
  const { container } = customRender(ui);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
  return container;
};

// Export everything from testing-library
export * from '@testing-library/react';

// Export custom methods
export { customRender as render, testAccessibility, createTestStore, AllProviders };