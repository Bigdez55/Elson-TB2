/**
 * Mock trading slice for testing
 * 
 * TODO: REMOVE WHEN TESTS ARE FIXED
 * This file exists only to allow legacy tests to run.
 * Tests should be updated to mock the actual trading slice instead.
 * 
 * Created: January 2026
 * Issue: Tests reference a non-existent mock file
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface MockTradingState {
  symbol: string;
  currentPrice: number;
  orderType: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  limitPrice: number | null;
  stopPrice: number | null;
  side: 'buy' | 'sell';
  isLoading: boolean;
  error: string | null;
}

const initialState: MockTradingState = {
  symbol: 'AAPL',
  currentPrice: 150.00,
  orderType: 'market',
  quantity: 0,
  limitPrice: null,
  stopPrice: null,
  side: 'buy',
  isLoading: false,
  error: null,
};

export const mockTradingSlice = createSlice({
  name: 'mockTrading',
  initialState,
  reducers: {
    setSymbol: (state, action: PayloadAction<string>) => {
      state.symbol = action.payload;
    },
    setCurrentPrice: (state, action: PayloadAction<number>) => {
      state.currentPrice = action.payload;
    },
    setOrderType: (state, action: PayloadAction<MockTradingState['orderType']>) => {
      state.orderType = action.payload;
    },
    setQuantity: (state, action: PayloadAction<number>) => {
      state.quantity = action.payload;
    },
    setLimitPrice: (state, action: PayloadAction<number | null>) => {
      state.limitPrice = action.payload;
    },
    setStopPrice: (state, action: PayloadAction<number | null>) => {
      state.stopPrice = action.payload;
    },
    setSide: (state, action: PayloadAction<'buy' | 'sell'>) => {
      state.side = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    resetOrder: (state) => {
      state.quantity = 0;
      state.limitPrice = null;
      state.stopPrice = null;
      state.orderType = 'market';
      state.error = null;
    },
  },
});

export const {
  setSymbol,
  setCurrentPrice,
  setOrderType,
  setQuantity,
  setLimitPrice,
  setStopPrice,
  setSide,
  setLoading,
  setError,
  resetOrder,
} = mockTradingSlice.actions;

export default mockTradingSlice.reducer;
