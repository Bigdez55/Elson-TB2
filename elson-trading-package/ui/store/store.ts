// frontend/src/app/store/store.ts

import { configureStore } from '@reduxjs/toolkit';
import marketReducer from './slices/marketSlice';
import tradingReducer from './slices/tradingSlice';
import alertsReducer from './slices/alertsSlice';
import settingsReducer from './slices/settingsSlice';
import userReducer from './slices/userSlice';
import subscriptionReducer from './slices/subscriptionSlice';
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
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['market/updateMarketData', 'trading/updatePredictions'],
        ignoredPaths: ['market.realTimeData', 'trading.predictions'],
      },
    }).concat(errorMiddleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// frontend/src/store/slices/marketSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { MarketData, MarketEnvironment } from '../../types';

interface MarketState {
  realTimeData: Record<string, MarketData>;
  marketEnvironment: MarketEnvironment | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: MarketState = {
  realTimeData: {},
  marketEnvironment: null,
  isLoading: false,
  error: null,
};

export const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    updateMarketData: (state, action: PayloadAction<MarketData>) => {
      const { symbol } = action.payload;
      state.realTimeData[symbol] = action.payload;
    },
    updateMarketEnvironment: (state, action: PayloadAction<MarketEnvironment>) => {
      state.marketEnvironment = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  updateMarketData,
  updateMarketEnvironment,
  setLoading,
  setError,
} = marketSlice.actions;

export default marketSlice.reducer;

// frontend/src/store/slices/tradingSlice.ts
import { Position, Order, Performance, PredictionData } from '../../types';

interface TradingState {
  positions: Position[];
  orders: Order[];
  performance: Performance | null;
  predictions: Record<string, PredictionData>;
  isLoading: boolean;
  error: string | null;
}

const initialTradingState: TradingState = {
  positions: [],
  orders: [],
  performance: null,
  predictions: {},
  isLoading: false,
  error: null,
};

export const tradingSlice = createSlice({
  name: 'trading',
  initialState: initialTradingState,
  reducers: {
    updatePositions: (state, action: PayloadAction<Position[]>) => {
      state.positions = action.payload;
    },
    updateOrders: (state, action: PayloadAction<Order[]>) => {
      state.orders = action.payload;
    },
    updatePerformance: (state, action: PayloadAction<Performance>) => {
      state.performance = action.payload;
    },
    updatePredictions: (state, action: PayloadAction<PredictionData>) => {
      const { symbol } = action.payload;
      state.predictions[symbol] = action.payload;
    },
    setTradingLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setTradingError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const {
  updatePositions,
  updateOrders,
  updatePerformance,
  updatePredictions,
  setTradingLoading,
  setTradingError,
} = tradingSlice.actions;

export default tradingSlice.reducer;