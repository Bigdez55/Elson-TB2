import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import tradingSlice from './slices/tradingSlice';
import portfolioSlice from './slices/portfolioSlice';
import marketDataSlice from './slices/marketDataSlice';
import websocketSlice from './slices/websocketSlice';
import { marketDataApi } from '../services/marketDataApi';
import { riskManagementApi } from '../services/riskManagementApi';
import { tradingApi } from '../services/tradingApi';
import { deviceManagementApi } from '../services/deviceManagementApi';
import { aiTradingApi } from '../services/aiTradingApi';
import { autoTradingApi } from '../services/autoTradingApi';
import { familyApi } from '../services/familyApi';
import { educationApi } from '../services/educationApi';
import enhancedWebsocketMiddleware from './middleware/websocketMiddleware';

export const store = configureStore({
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
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }).concat(
      marketDataApi.middleware,
      riskManagementApi.middleware,
      tradingApi.middleware,
      deviceManagementApi.middleware,
      aiTradingApi.middleware,
      autoTradingApi.middleware,
      familyApi.middleware,
      educationApi.middleware,
      enhancedWebsocketMiddleware
    ),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;