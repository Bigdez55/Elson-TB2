import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../services/api';

interface TradingState {
  orders: any[];
  trades: any[];
  positions: any[];
  portfolio: {
    balance: number;
    equity: number;
    margin: number;
    positions: any[];
  };
  performance: {
    dailyPnL: number;
    totalPnL: number;
    winRate: number;
  };
  // Fractional share configuration
  minInvestmentAmount: number;
  maxInvestmentAmount: number;
  fractionalSharesEnabled: boolean;
  // Loading and error states
  loading: boolean;
  error: string | null;
}

const initialState: TradingState = {
  orders: [],
  trades: [],
  positions: [],
  portfolio: {
    balance: 0,
    equity: 0,
    margin: 0,
    positions: [],
  },
  performance: {
    dailyPnL: 0,
    totalPnL: 0,
    winRate: 0,
  },
  // Fractional share configuration defaults
  minInvestmentAmount: 1.00,
  maxInvestmentAmount: 100000.00,
  fractionalSharesEnabled: true,
  // Loading and error states
  loading: false,
  error: null,
};

// Async thunks
export const placeOrder = createAsyncThunk(
  'trading/placeOrder',
  async (orderData: any, { rejectWithValue }) => {
    try {
      const response = await api.post('/trading/orders', orderData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to place order');
    }
  }
);

export const cancelOrder = createAsyncThunk(
  'trading/cancelOrder',
  async (orderId: string, { rejectWithValue }) => {
    try {
      await api.delete(`/trading/orders/${orderId}`);
      return orderId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to cancel order');
    }
  }
);

export const fetchOrders = createAsyncThunk(
  'trading/fetchOrders',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/trading/orders');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch orders');
    }
  }
);

export const fetchTrades = createAsyncThunk(
  'trading/fetchTrades',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/trading/trades');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch trades');
    }
  }
);

export const fetchPortfolio = createAsyncThunk(
  'trading/fetchPortfolio',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/trading/portfolio');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch portfolio');
    }
  }
);

const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    updateOrder: (state, action) => {
      const index = state.orders.findIndex(order => order.id === action.payload.id);
      if (index !== -1) {
        state.orders[index] = action.payload;
      }
    },
    updatePosition: (state, action) => {
      const index = state.positions.findIndex(pos => pos.symbol === action.payload.symbol);
      if (index !== -1) {
        state.positions[index] = action.payload;
      } else {
        state.positions.push(action.payload);
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Place Order
    builder
      .addCase(placeOrder.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(placeOrder.fulfilled, (state, action) => {
        state.loading = false;
        state.orders.unshift(action.payload);
      })
      .addCase(placeOrder.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Cancel Order
    builder
      .addCase(cancelOrder.fulfilled, (state, action) => {
        state.orders = state.orders.filter(order => order.id !== action.payload);
      });

    // Fetch Orders
    builder
      .addCase(fetchOrders.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.loading = false;
        state.orders = action.payload;
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch Trades
    builder
      .addCase(fetchTrades.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchTrades.fulfilled, (state, action) => {
        state.loading = false;
        state.trades = action.payload;
      })
      .addCase(fetchTrades.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch Portfolio
    builder
      .addCase(fetchPortfolio.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchPortfolio.fulfilled, (state, action) => {
        state.loading = false;
        state.portfolio = action.payload;
      })
      .addCase(fetchPortfolio.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
    
    // Fetch Trading Configuration
    builder
      .addCase(fetchTradingConfig.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchTradingConfig.fulfilled, (state, action) => {
        state.loading = false;
        // Update configuration values from API
        if (action.payload.minInvestmentAmount !== undefined) {
          state.minInvestmentAmount = action.payload.minInvestmentAmount;
        }
        if (action.payload.maxInvestmentAmount !== undefined) {
          state.maxInvestmentAmount = action.payload.maxInvestmentAmount;
        }
        if (action.payload.fractionalSharesEnabled !== undefined) {
          state.fractionalSharesEnabled = action.payload.fractionalSharesEnabled;
        }
      })
      .addCase(fetchTradingConfig.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

// Add new async thunk to fetch trading configuration
export const fetchTradingConfig = createAsyncThunk(
  'trading/fetchTradingConfig',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/trading/config');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch trading configuration');
    }
  }
);

export const { 
  updateOrder, 
  updatePosition, 
  clearError 
} = tradingSlice.actions;

export default tradingSlice.reducer;