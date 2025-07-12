import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { api } from '../../services/api';

// Enhanced market data types for real-time trading
interface QuoteData {
  symbol: string;
  price: number;
  bid?: number;
  ask?: number;
  bidSize?: number;
  askSize?: number;
  volume: number;
  dayChange: number;
  dayChangePercent: number;
  timestamp: string;
  source: string;
}

interface Level2Data {
  symbol: string;
  bids: [number, number][]; // [price, size]
  asks: [number, number][]; // [price, size]
  timestamp: string;
}

interface MarketStatus {
  isOpen: boolean;
  nextOpen?: string;
  nextClose?: string;
  timezone: string;
}

interface MarketState {
  quotes: Record<string, QuoteData>;
  level2Data: Record<string, Level2Data>;
  marketStatus: MarketStatus | null;
  selectedSymbol: string | null;
  watchlist: string[];
  wsConnected: boolean;
  subscriptions: string[];
  loading: boolean;
  error: string | null;
}

const initialState: MarketState = {
  quotes: {},
  level2Data: {},
  marketStatus: null,
  selectedSymbol: null,
  watchlist: [],
  wsConnected: false,
  subscriptions: [],
  loading: false,
  error: null,
};

// Async thunks for market data API calls
export const fetchQuote = createAsyncThunk(
  'market/fetchQuote',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/market/quote/${symbol}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch quote');
    }
  }
);

export const fetchMultipleQuotes = createAsyncThunk(
  'market/fetchMultipleQuotes',
  async (symbols: string[], { rejectWithValue }) => {
    try {
      const response = await api.get(`/market/quotes?symbols=${symbols.join(',')}`);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch quotes');
    }
  }
);

export const fetchMarketStatus = createAsyncThunk(
  'market/fetchMarketStatus',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/market/status');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch market status');
    }
  }
);

export const searchSymbols = createAsyncThunk(
  'market/searchSymbols',
  async (query: string, { rejectWithValue }) => {
    try {
      const response = await api.get(`/market/search?query=${query}&limit=10`);
      return response.data.results;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to search symbols');
    }
  }
);

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    // WebSocket connection status
    setWsConnected: (state, action: PayloadAction<boolean>) => {
      state.wsConnected = action.payload;
    },
    
    // Real-time quote updates from WebSocket
    updateQuote: (state, action: PayloadAction<QuoteData>) => {
      const quote = action.payload;
      state.quotes[quote.symbol] = quote;
    },
    
    // Level 2 data updates
    updateLevel2Data: (state, action: PayloadAction<Level2Data>) => {
      const level2 = action.payload;
      state.level2Data[level2.symbol] = level2;
    },
    
    // Symbol selection
    setSelectedSymbol: (state, action: PayloadAction<string | null>) => {
      state.selectedSymbol = action.payload;
    },
    
    // Watchlist management
    addToWatchlist: (state, action: PayloadAction<string>) => {
      const symbol = action.payload.toUpperCase();
      if (!state.watchlist.includes(symbol)) {
        state.watchlist.push(symbol);
      }
    },
    
    removeFromWatchlist: (state, action: PayloadAction<string>) => {
      const symbol = action.payload.toUpperCase();
      state.watchlist = state.watchlist.filter(s => s !== symbol);
    },
    
    // Subscription management
    addSubscription: (state, action: PayloadAction<string>) => {
      const symbol = action.payload.toUpperCase();
      if (!state.subscriptions.includes(symbol)) {
        state.subscriptions.push(symbol);
      }
    },
    
    removeSubscription: (state, action: PayloadAction<string>) => {
      const symbol = action.payload.toUpperCase();
      state.subscriptions = state.subscriptions.filter(s => s !== symbol);
    },
    
    clearSubscriptions: (state) => {
      state.subscriptions = [];
    },
    
    // Error handling
    clearError: (state) => {
      state.error = null;
    },
    
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Fetch single quote
    builder
      .addCase(fetchQuote.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchQuote.fulfilled, (state, action) => {
        state.loading = false;
        const quote = action.payload as QuoteData;
        state.quotes[quote.symbol] = quote;
      })
      .addCase(fetchQuote.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch multiple quotes
    builder
      .addCase(fetchMultipleQuotes.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMultipleQuotes.fulfilled, (state, action) => {
        state.loading = false;
        const quotes = action.payload as QuoteData[];
        quotes.forEach(quote => {
          state.quotes[quote.symbol] = quote;
        });
      })
      .addCase(fetchMultipleQuotes.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch market status
    builder
      .addCase(fetchMarketStatus.fulfilled, (state, action) => {
        state.marketStatus = action.payload as MarketStatus;
      })
      .addCase(fetchMarketStatus.rejected, (state, action) => {
        state.error = action.payload as string;
      });

    // Search symbols
    builder
      .addCase(searchSymbols.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const {
  setWsConnected,
  updateQuote,
  updateLevel2Data,
  setSelectedSymbol,
  addToWatchlist,
  removeFromWatchlist,
  addSubscription,
  removeSubscription,
  clearSubscriptions,
  clearError,
  setError,
} = marketSlice.actions;

export default marketSlice.reducer;