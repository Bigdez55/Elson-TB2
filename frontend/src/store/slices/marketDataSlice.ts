import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { marketDataAPI } from '../../services/api';
import { Quote, Asset } from '../../types';

interface MarketDataState {
  quotes: { [symbol: string]: Quote };
  assets: Asset[];
  watchlist: string[];
  isLoading: boolean;
  error: string | null;
}

const initialState: MarketDataState = {
  quotes: {},
  assets: [],
  watchlist: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY'], // Default watchlist
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchQuote = createAsyncThunk(
  'marketData/fetchQuote',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const quote = await marketDataAPI.getQuote(symbol);
      return { symbol, quote };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || `Failed to fetch quote for ${symbol}`);
    }
  }
);

export const fetchMultipleQuotes = createAsyncThunk(
  'marketData/fetchMultipleQuotes',
  async (symbols: string[], { rejectWithValue }) => {
    try {
      const response = await marketDataAPI.getMultipleQuotes(symbols);
      return response.quotes;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch quotes');
    }
  }
);

export const fetchAssets = createAsyncThunk(
  'marketData/fetchAssets',
  async (params: {
    asset_type?: string;
    sector?: string;
    limit?: number;
  } = {}, { rejectWithValue }) => {
    try {
      const assets = await marketDataAPI.getAssets(params);
      return assets;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch assets');
    }
  }
);

export const validateSymbol = createAsyncThunk(
  'marketData/validateSymbol',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const result = await marketDataAPI.getQuote(symbol);
      return { symbol, valid: true, quote: result };
    } catch (error: any) {
      return rejectWithValue({ symbol, valid: false, error: error.response?.data?.detail || 'Symbol not found' });
    }
  }
);

const marketDataSlice = createSlice({
  name: 'marketData',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    addToWatchlist: (state, action) => {
      const symbol = action.payload.toUpperCase();
      if (!state.watchlist.includes(symbol)) {
        state.watchlist.push(symbol);
      }
    },
    removeFromWatchlist: (state, action) => {
      const symbol = action.payload.toUpperCase();
      state.watchlist = state.watchlist.filter(s => s !== symbol);
    },
    updateQuote: (state, action) => {
      const { symbol, quote } = action.payload;
      state.quotes[symbol] = quote;
    },
  },
  extraReducers: (builder) => {
    // Fetch Quote
    builder
      .addCase(fetchQuote.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchQuote.fulfilled, (state, action) => {
        state.isLoading = false;
        const { symbol, quote } = action.payload;
        state.quotes[symbol] = quote;
      })
      .addCase(fetchQuote.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Multiple Quotes
    builder
      .addCase(fetchMultipleQuotes.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchMultipleQuotes.fulfilled, (state, action) => {
        state.isLoading = false;
        action.payload.forEach((quote: Quote) => {
          state.quotes[quote.symbol] = quote;
        });
      })
      .addCase(fetchMultipleQuotes.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Assets
    builder
      .addCase(fetchAssets.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchAssets.fulfilled, (state, action) => {
        state.isLoading = false;
        state.assets = action.payload;
      })
      .addCase(fetchAssets.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Validate Symbol
    builder
      .addCase(validateSymbol.fulfilled, (state, action) => {
        const { symbol, quote } = action.payload;
        state.quotes[symbol] = quote;
      })
      .addCase(validateSymbol.rejected, (state, action) => {
        state.error = (action.payload as any).error;
      });
  },
});

export const { clearError, addToWatchlist, removeFromWatchlist, updateQuote } = marketDataSlice.actions;
export default marketDataSlice.reducer;