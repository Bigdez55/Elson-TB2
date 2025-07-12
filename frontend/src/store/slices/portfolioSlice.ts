import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { portfolioAPI } from '../../services/api';
import { Portfolio, PortfolioSummary, Holding } from '../../types';

interface PortfolioState {
  summary: PortfolioSummary | null;
  portfolio: Portfolio | null;
  holdings: Holding[];
  performance: any | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: PortfolioState = {
  summary: null,
  portfolio: null,
  holdings: [],
  performance: null,
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchPortfolioSummary = createAsyncThunk(
  'portfolio/fetchSummary',
  async (_, { rejectWithValue }) => {
    try {
      const summary = await portfolioAPI.getPortfolioSummary();
      return summary;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch portfolio summary');
    }
  }
);

export const fetchPortfolioDetails = createAsyncThunk(
  'portfolio/fetchDetails',
  async (_, { rejectWithValue }) => {
    try {
      const portfolio = await portfolioAPI.getPortfolioDetails();
      return portfolio;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch portfolio details');
    }
  }
);

export const fetchHoldings = createAsyncThunk(
  'portfolio/fetchHoldings',
  async (_, { rejectWithValue }) => {
    try {
      const holdings = await portfolioAPI.getHoldings();
      return holdings;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch holdings');
    }
  }
);

export const updatePortfolio = createAsyncThunk(
  'portfolio/update',
  async (updateData: {
    name?: string;
    description?: string;
    cash_balance?: number;
    auto_rebalance?: boolean;
  }, { rejectWithValue }) => {
    try {
      const portfolio = await portfolioAPI.updatePortfolio(updateData);
      return portfolio;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update portfolio');
    }
  }
);

export const fetchPerformance = createAsyncThunk(
  'portfolio/fetchPerformance',
  async (_, { rejectWithValue }) => {
    try {
      const performance = await portfolioAPI.getPerformance();
      return performance;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch performance data');
    }
  }
);

export const refreshPortfolioData = createAsyncThunk(
  'portfolio/refresh',
  async (_, { rejectWithValue }) => {
    try {
      const result = await portfolioAPI.refreshPortfolioData();
      return result;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to refresh portfolio data');
    }
  }
);

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch Portfolio Summary
    builder
      .addCase(fetchPortfolioSummary.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPortfolioSummary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.summary = action.payload;
        state.portfolio = action.payload.portfolio;
        state.holdings = action.payload.holdings;
      })
      .addCase(fetchPortfolioSummary.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Portfolio Details
    builder
      .addCase(fetchPortfolioDetails.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPortfolioDetails.fulfilled, (state, action) => {
        state.isLoading = false;
        state.portfolio = action.payload;
      })
      .addCase(fetchPortfolioDetails.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Holdings
    builder
      .addCase(fetchHoldings.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchHoldings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.holdings = action.payload;
      })
      .addCase(fetchHoldings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Update Portfolio
    builder
      .addCase(updatePortfolio.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updatePortfolio.fulfilled, (state, action) => {
        state.isLoading = false;
        state.portfolio = action.payload;
        if (state.summary) {
          state.summary.portfolio = action.payload;
        }
      })
      .addCase(updatePortfolio.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch Performance
    builder
      .addCase(fetchPerformance.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPerformance.fulfilled, (state, action) => {
        state.isLoading = false;
        state.performance = action.payload;
      })
      .addCase(fetchPerformance.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Refresh Portfolio Data
    builder
      .addCase(refreshPortfolioData.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(refreshPortfolioData.fulfilled, (state, action) => {
        state.isLoading = false;
        // Update portfolio values from refresh result
        if (state.portfolio) {
          state.portfolio.total_value = action.payload.total_value;
          state.portfolio.total_return = action.payload.total_return;
          state.portfolio.total_return_percentage = action.payload.total_return_percentage;
        }
        if (state.summary) {
          state.summary.portfolio.total_value = action.payload.total_value;
          state.summary.portfolio.total_return = action.payload.total_return;
          state.summary.portfolio.total_return_percentage = action.payload.total_return_percentage;
        }
      })
      .addCase(refreshPortfolioData.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = portfolioSlice.actions;
export default portfolioSlice.reducer;