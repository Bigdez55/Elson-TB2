import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../services/api';

interface MarketState {
  marketData: Record<string, any>;
  selectedSymbol: string | null;
  watchlist: string[];
  orderBook: any;
  recentTrades: any[];
  loading: boolean;
  error: string | null;
}

const initialState: MarketState = {
  marketData: {},
  selectedSymbol: null,
  watchlist: [],
  orderBook: { bids: [], asks: [] },
  recentTrades: [],
  loading: false,
  error: null,
};

// Async thunks
export const fetchMarketData = createAsyncThunk(
  'market/fetchMarketData',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/market/data/${symbol}`);
      return { symbol, data: response.data };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch market data');
    }
  }
);

export const fetchOrderBook = createAsyncThunk(
  'market/fetchOrderBook',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/market/orderbook/${symbol}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch order book');
    }
  }
);

export const fetchRecentTrades = createAsyncThunk(
  'market/fetchRecentTrades',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/market/trades/${symbol}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch recent trades');
    }
  }
);

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    setSelectedSymbol: (state, action) => {
      state.selectedSymbol = action.payload;
    },
    updateMarketData: (state, action) => {
      const { symbol, data } = action.payload;
      state.marketData[symbol] = {
        ...state.marketData[symbol],
        ...data,
        lastUpdated: new Date().toISOString(),
      };
    },
    updateOrderBook: (state, action) => {
      state.orderBook = action.payload;
    },
    addToWatchlist: (state, action) => {
      if (!state.watchlist.includes(action.payload)) {
        state.watchlist.push(action.payload);
      }
    },
    removeFromWatchlist: (state, action) => {
      state.watchlist = state.watchlist.filter(symbol => symbol !== action.payload);
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch Market Data
    builder
      .addCase(fetchMarketData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMarketData.fulfilled, (state, action) => {
        state.loading = false;
        const { symbol, data } = action.payload;
        state.marketData[symbol] = {
          ...data,
          lastUpdated: new Date().toISOString(),
        };
      })
      .addCase(fetchMarketData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch Order Book
    builder
      .addCase(fetchOrderBook.fulfilled, (state, action) => {
        state.orderBook = action.payload;
      });

    // Fetch Recent Trades
    builder
      .addCase(fetchRecentTrades.fulfilled, (state, action) => {
        state.recentTrades = action.payload;
      });
  },
});

export const {
  setSelectedSymbol,
  updateMarketData,
  updateOrderBook,
  addToWatchlist,
  removeFromWatchlist,
  clearError,
} = marketSlice.actions;

export default marketSlice.reducer;