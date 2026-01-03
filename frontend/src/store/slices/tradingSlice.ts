import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { api } from '../../services/api';

export interface Position {
  id: string;
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  side: 'long' | 'short';
  last_updated: string;
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  status: 'pending' | 'filled' | 'partially_filled' | 'cancelled' | 'rejected';
  order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
  time_in_force: 'day' | 'gtc' | 'ioc' | 'fok';
  created_at: string;
  filled_at?: string;
  filled_qty: number;
  filled_avg_price?: number;
  commission?: number;
  error_message?: string;
}

export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
  price?: number;
  stop_price?: number;
  time_in_force: 'day' | 'gtc' | 'ioc' | 'fok';
  status: 'pending' | 'filled' | 'partially_filled' | 'cancelled' | 'rejected';
  created_at: string;
  filled_qty: number;
  remaining_qty: number;
}

interface TradingState {
  orders: Order[];
  trades: Trade[];
  positions: Position[];
  pendingOrders: Order[];
  portfolio: {
    balance: number;
    equity: number;
    margin: number;
    positions: Position[];
    totalValue: number;
    buyingPower: number;
  };
  performance: {
    dailyPnL: number;
    totalPnL: number;
    winRate: number;
    dayTradeCount: number;
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
  pendingOrders: [],
  portfolio: {
    balance: 0,
    equity: 0,
    margin: 0,
    positions: [],
    totalValue: 0,
    buyingPower: 0,
  },
  performance: {
    dailyPnL: 0,
    totalPnL: 0,
    winRate: 0,
    dayTradeCount: 0,
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
    updateOrder: (state, action: PayloadAction<Order>) => {
      const index = state.orders.findIndex(order => order.id === action.payload.id);
      if (index !== -1) {
        state.orders[index] = action.payload;
      } else {
        state.orders.unshift(action.payload);
      }
      
      // Update pending orders
      if (action.payload.status === 'pending') {
        const pendingIndex = state.pendingOrders.findIndex(o => o.id === action.payload.id);
        if (pendingIndex === -1) {
          state.pendingOrders.push(action.payload);
        }
      } else {
        state.pendingOrders = state.pendingOrders.filter(o => o.id !== action.payload.id);
      }
    },
    
    updatePosition: (state, action: PayloadAction<Position>) => {
      const index = state.positions.findIndex(pos => pos.symbol === action.payload.symbol);
      if (index !== -1) {
        state.positions[index] = action.payload;
      } else {
        state.positions.push(action.payload);
      }
      
      // Update portfolio calculations
      state.portfolio.positions = state.positions;
      state.portfolio.totalValue = state.positions.reduce((total, pos) => total + pos.market_value, 0);
      state.performance.totalPnL = state.positions.reduce((total, pos) => total + pos.unrealized_pnl, 0);
    },
    
    updateTrade: (state, action: PayloadAction<Trade>) => {
      const index = state.trades.findIndex(trade => trade.id === action.payload.id);
      if (index !== -1) {
        state.trades[index] = action.payload;
      } else {
        state.trades.unshift(action.payload);
      }
    },
    
    removePosition: (state, action: PayloadAction<string>) => {
      state.positions = state.positions.filter(pos => pos.symbol !== action.payload);
      state.portfolio.positions = state.positions;
      state.portfolio.totalValue = state.positions.reduce((total, pos) => total + pos.market_value, 0);
      state.performance.totalPnL = state.positions.reduce((total, pos) => total + pos.unrealized_pnl, 0);
    },
    
    updatePortfolioBalance: (state, action: PayloadAction<{ balance: number; buyingPower: number }>) => {
      state.portfolio.balance = action.payload.balance;
      state.portfolio.buyingPower = action.payload.buyingPower;
    },
    
    updatePerformance: (state, action: PayloadAction<Partial<typeof initialState.performance>>) => {
      state.performance = { ...state.performance, ...action.payload };
    },
    
    clearError: (state) => {
      state.error = null;
    },
    
    resetTradingState: () => initialState,
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
  updateTrade,
  removePosition,
  updatePortfolioBalance,
  updatePerformance,
  clearError,
  resetTradingState
} = tradingSlice.actions;

export { tradingSlice };
export default tradingSlice.reducer;