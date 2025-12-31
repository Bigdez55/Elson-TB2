import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authService } from '../../services/auth';

interface Portfolio {
  id: number;
  name: string;
  value: number;
}

interface UserState {
  user: any | null;
  currentUser: any | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  requires2FA: boolean;
  twoFactorEmail: string | null;
  portfolios: Portfolio[];
}

const initialState: UserState = {
  user: null,
  currentUser: null,
  token: localStorage.getItem('token'),
  loading: false,
  error: null,
  requires2FA: false,
  twoFactorEmail: null,
  portfolios: [],
};

// Async thunks
export const login = createAsyncThunk(
  'user/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials);

      // Check if the response indicates 2FA is required
      if (response.requires2FA) {
        return {
          ...response,
          requires2FA: true as const,
          email: credentials.email,
          message: 'Two-factor authentication required'
        };
      }

      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Login failed');
    }
  }
);

export const verify2FA = createAsyncThunk(
  'user/verify2FA',
  async (data: { token: string; refreshToken?: string; user: any }, { rejectWithValue }) => {
    try {
      return data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Two-factor verification failed');
    }
  }
);

export const register = createAsyncThunk(
  'user/register',
  async (data: { username: string; email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await authService.register(data);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Registration failed');
    }
  }
);

export const fetchUserProfile = createAsyncThunk(
  'user/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.getProfile();
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch profile');
    }
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null;
      state.currentUser = null;
      state.token = null;
      state.portfolios = [];
      localStorage.removeItem('token');
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.requires2FA = false;
        state.twoFactorEmail = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        
        // Handle 2FA requirement
        if (action.payload.requires2FA) {
          state.requires2FA = true;
          state.twoFactorEmail = action.payload.email || null;
          state.user = null;
          state.currentUser = null;
          state.token = null;
        } else {
          state.requires2FA = false;
          state.twoFactorEmail = null;
          state.user = action.payload.user;
          state.currentUser = action.payload.user;
          state.token = action.payload.token;
          localStorage.setItem('token', action.payload.token);
        }
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.requires2FA = false;
        state.twoFactorEmail = null;
      });
      
    // Verify 2FA
    builder
      .addCase(verify2FA.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(verify2FA.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.currentUser = action.payload.user;
        state.token = action.payload.token;
        state.requires2FA = false;
        state.twoFactorEmail = null;
      })
      .addCase(verify2FA.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Register
    builder
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.currentUser = action.payload.user;
        state.token = action.payload.token;
        localStorage.setItem('token', action.payload.token);
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch Profile
    builder
      .addCase(fetchUserProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.currentUser = action.payload;
      })
      .addCase(fetchUserProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { logout, clearError } = userSlice.actions;
export default userSlice.reducer;