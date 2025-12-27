import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { tradingAPI } from '../../services/api';
import { Trade, TradeOrderRequest, TradingStats, Holding } from '../../types';

interface TradingState {
  trades: Trade[];
  openOrders: Trade[];
  positions: Holding[];
  stats: TradingStats | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: TradingState = {
  trades: [],
  openOrders: [],
  positions: [],
  stats: null,
  isLoading: false,
  error: null,
};

// Async thunks
export const placeOrder = createAsyncThunk(
  'trading/placeOrder',
  async (orderData: TradeOrderRequest, { rejectWithValue }) => {
    try {
      const trade = await tradingAPI.placeOrder(orderData);
      return trade;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to place order');
    }
  }
);

export const cancelOrder = createAsyncThunk(
  'trading/cancelOrder',
  async (tradeId: number, { rejectWithValue }) => {
    try {
      const trade = await tradingAPI.cancelOrder(tradeId);
      return trade;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to cancel order');
    }
  }
);

export const fetchOpenOrders = createAsyncThunk(
  'trading/fetchOpenOrders',
  async (_, { rejectWithValue }) => {
    try {
      const orders = await tradingAPI.getOpenOrders();
      return orders;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch open orders');
    }
  }
);

export const fetchTradeHistory = createAsyncThunk(
  'trading/fetchTradeHistory',
  async (limit: number = 100, { rejectWithValue }) => {
    try {
      const trades = await tradingAPI.getTradeHistory(limit);
      return trades;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch trade history');
    }
  }
);

export const fetchPositions = createAsyncThunk(
  'trading/fetchPositions',
  async (_, { rejectWithValue }) => {
    try {
      const positions = await tradingAPI.getPositions();
      return positions;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch positions');
    }
  }
);

export const fetchTradingStats = createAsyncThunk(
  'trading/fetchTradingStats',
  async (_, { rejectWithValue }) => {
    try {
      const stats = await tradingAPI.getTradingStats();
      return stats;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch trading stats');
    }
  }
);

const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Place Order
    builder
      .addCase(placeOrder.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(placeOrder.fulfilled, (state, action) => {
        state.isLoading = false;
        state.trades.unshift(action.payload);
        if (action.payload.status === 'pending') {
          state.openOrders.unshift(action.payload);
        }
      })
      .addCase(placeOrder.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Cancel Order
    builder
      .addCase(cancelOrder.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(cancelOrder.fulfilled, (state, action) => {
        state.isLoading = false;
        const updatedTrade = action.payload;
        
        // Update in trades array
        const tradeIndex = state.trades.findIndex(t => t.id === updatedTrade.id);
        if (tradeIndex !== -1) {
          state.trades[tradeIndex] = updatedTrade;
        }
        
        // Remove from open orders
        state.openOrders = state.openOrders.filter(o => o.id !== updatedTrade.id);
      })
      .addCase(cancelOrder.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Open Orders
    builder
      .addCase(fetchOpenOrders.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchOpenOrders.fulfilled, (state, action) => {
        state.isLoading = false;
        state.openOrders = action.payload;
      })
      .addCase(fetchOpenOrders.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Trade History
    builder
      .addCase(fetchTradeHistory.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTradeHistory.fulfilled, (state, action) => {
        state.isLoading = false;
        state.trades = action.payload;
      })
      .addCase(fetchTradeHistory.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Positions
    builder
      .addCase(fetchPositions.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPositions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.positions = action.payload;
      })
      .addCase(fetchPositions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Trading Stats
    builder
      .addCase(fetchTradingStats.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTradingStats.fulfilled, (state, action) => {
        state.isLoading = false;
        state.stats = action.payload;
      })
      .addCase(fetchTradingStats.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = tradingSlice.actions;
export { tradingSlice };
export default tradingSlice.reducer;