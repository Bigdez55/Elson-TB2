import { configureStore } from '@reduxjs/toolkit';
import marketReducer from './slices/marketSlice';
import tradingReducer from './slices/tradingSlice';
import alertsReducer from './slices/alertsSlice';
import settingsReducer from './slices/settingsSlice';
import userReducer from './slices/userSlice';
import subscriptionReducer from './slices/subscriptionSlice';
import authReducer from './slices/authSlice';
import websocketReducer from './slices/websocketSlice';
import portfolioReducer from './slices/portfolioSlice';
import toastReducer from './slices/toastSlice';
import marketDataApi from '../services/marketDataApi';
import wealthAdvisoryApi from '../services/wealthAdvisoryApi';
import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';
import { errorMiddleware } from '../middleware/errorMiddleware';

export const store = configureStore({
  reducer: {
    market: marketReducer,
    trading: tradingReducer,
    alerts: alertsReducer,
    settings: settingsReducer,
    user: userReducer,
    subscription: subscriptionReducer,
    auth: authReducer,
    websocket: websocketReducer,
    portfolio: portfolioReducer,
    toast: toastReducer,
    [marketDataApi.reducerPath]: marketDataApi.reducer,
    [wealthAdvisoryApi.reducerPath]: wealthAdvisoryApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['market/updateMarketData', 'trading/updatePredictions'],
        ignoredPaths: ['market.realTimeData', 'trading.predictions'],
      },
    }).concat(marketDataApi.middleware, wealthAdvisoryApi.middleware, errorMiddleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
