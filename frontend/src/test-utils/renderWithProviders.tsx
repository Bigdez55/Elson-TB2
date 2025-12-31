import React, { PropsWithChildren } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore, PreloadedState } from '@reduxjs/toolkit';
import { MemoryRouter, MemoryRouterProps } from 'react-router-dom';
import type { RootState } from '../store/store';

// Import reducers
import authSlice from '../store/slices/authSlice';
import tradingSlice from '../store/slices/tradingSlice';
import portfolioSlice from '../store/slices/portfolioSlice';
import marketDataSlice from '../store/slices/marketDataSlice';
import websocketSlice from '../store/slices/websocketSlice';

// Import RTK Query APIs
import { marketDataApi } from '../services/marketDataApi';
import { riskManagementApi } from '../services/riskManagementApi';
import { tradingApi } from '../services/tradingApi';
import { deviceManagementApi } from '../services/deviceManagementApi';
import { aiTradingApi } from '../services/aiTradingApi';
import { autoTradingApi } from '../services/autoTradingApi';
import { familyApi } from '../services/familyApi';
import { educationApi } from '../services/educationApi';

// Create a test store factory
export const createTestStore = (preloadedState?: PreloadedState<RootState>) => {
  return configureStore({
    reducer: {
      auth: authSlice,
      trading: tradingSlice,
      portfolio: portfolioSlice,
      marketData: marketDataSlice,
      websocket: websocketSlice,
      [marketDataApi.reducerPath]: marketDataApi.reducer,
      [riskManagementApi.reducerPath]: riskManagementApi.reducer,
      [tradingApi.reducerPath]: tradingApi.reducer,
      [deviceManagementApi.reducerPath]: deviceManagementApi.reducer,
      [aiTradingApi.reducerPath]: aiTradingApi.reducer,
      [autoTradingApi.reducerPath]: autoTradingApi.reducer,
      [familyApi.reducerPath]: familyApi.reducer,
      [educationApi.reducerPath]: educationApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false, // Disable for testing
      }).concat(
        marketDataApi.middleware,
        riskManagementApi.middleware,
        tradingApi.middleware,
        deviceManagementApi.middleware,
        aiTradingApi.middleware,
        autoTradingApi.middleware,
        familyApi.middleware,
        educationApi.middleware
        // Note: websocketMiddleware excluded from tests by default
      ),
    preloadedState,
  });
};

// Extended render options
interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  preloadedState?: PreloadedState<RootState>;
  store?: ReturnType<typeof createTestStore>;
  routerOptions?: MemoryRouterProps;
}

/**
 * Custom render function that wraps components with all necessary providers
 *
 * @example
 * // Basic usage
 * const { getByText } = renderWithProviders(<MyComponent />);
 *
 * @example
 * // With preloaded state
 * const { getByText } = renderWithProviders(<MyComponent />, {
 *   preloadedState: {
 *     auth: { user: mockUser, token: 'test-token', loading: false, error: null }
 *   }
 * });
 *
 * @example
 * // With router options
 * const { getByText } = renderWithProviders(<MyComponent />, {
 *   routerOptions: { initialEntries: ['/dashboard'] }
 * });
 */
export function renderWithProviders(
  ui: React.ReactElement,
  {
    preloadedState,
    store = createTestStore(preloadedState),
    routerOptions = {},
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: PropsWithChildren<{}>): JSX.Element {
    return (
      <Provider store={store}>
        <MemoryRouter {...routerOptions}>
          {children}
        </MemoryRouter>
      </Provider>
    );
  }

  return {
    store,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

/**
 * Render with only Redux provider (no Router)
 * Useful for testing hooks or components that don't need routing
 */
export function renderWithRedux(
  ui: React.ReactElement,
  {
    preloadedState,
    store = createTestStore(preloadedState),
    ...renderOptions
  }: Omit<ExtendedRenderOptions, 'routerOptions'> = {}
) {
  function Wrapper({ children }: PropsWithChildren<{}>): JSX.Element {
    return <Provider store={store}>{children}</Provider>;
  }

  return {
    store,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

// Re-export testing library utilities
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
