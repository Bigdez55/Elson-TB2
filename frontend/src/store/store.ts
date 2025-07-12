import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import tradingSlice from './slices/tradingSlice';
import portfolioSlice from './slices/portfolioSlice';
import marketDataSlice from './slices/marketDataSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    trading: tradingSlice,
    portfolio: portfolioSlice,
    marketData: marketDataSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;