import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { subscriptionService, Subscription, SubscriptionPlan, FeatureAccessResponse } from '../../services/subscriptionService';

interface SubscriptionState {
  subscription: Subscription | null;
  loading: boolean;
  error: string | null;
  featureAccess: Record<string, boolean>;
  isPremium: boolean;
  isFamily: boolean;
}

const initialState: SubscriptionState = {
  subscription: null,
  loading: false,
  error: null,
  featureAccess: {},
  isPremium: false,
  isFamily: false,
};

// Async actions
export const fetchActiveSubscription = createAsyncThunk(
  'subscription/fetchActive',
  async (_, { rejectWithValue }) => {
    try {
      const subscription = await subscriptionService.getActiveSubscription();
      return subscription;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch subscription');
    }
  }
);

export const checkFeatureAccess = createAsyncThunk(
  'subscription/checkFeature',
  async (feature: string, { rejectWithValue }) => {
    try {
      const result = await subscriptionService.checkFeatureAccess(feature);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to check feature access');
    }
  }
);

export const cancelSubscription = createAsyncThunk(
  'subscription/cancel',
  async ({ id, immediate, reason }: { id: number; immediate: boolean; reason?: string }, { rejectWithValue }) => {
    try {
      const subscription = await subscriptionService.cancelSubscription(id, { immediate, reason });
      return subscription;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to cancel subscription');
    }
  }
);

const subscriptionSlice = createSlice({
  name: 'subscription',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setSubscription: (state, action: PayloadAction<Subscription | null>) => {
      state.subscription = action.payload;
      
      // Update premium and family flags based on subscription
      if (action.payload) {
        const planType = action.payload.plan;
        state.isPremium = planType === SubscriptionPlan.PREMIUM || planType === SubscriptionPlan.FAMILY;
        state.isFamily = planType === SubscriptionPlan.FAMILY;
      } else {
        state.isPremium = false;
        state.isFamily = false;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch active subscription
    builder.addCase(fetchActiveSubscription.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchActiveSubscription.fulfilled, (state, action) => {
      state.loading = false;
      state.subscription = action.payload;
      
      // Update premium and family flags based on subscription
      if (action.payload) {
        const planType = action.payload.plan;
        state.isPremium = planType === SubscriptionPlan.PREMIUM || planType === SubscriptionPlan.FAMILY;
        state.isFamily = planType === SubscriptionPlan.FAMILY;
      } else {
        state.isPremium = false;
        state.isFamily = false;
      }
    });
    builder.addCase(fetchActiveSubscription.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
    
    // Check feature access
    builder.addCase(checkFeatureAccess.fulfilled, (state, action) => {
      const { feature, has_access } = action.payload as FeatureAccessResponse;
      state.featureAccess[feature] = has_access;
    });
    
    // Cancel subscription
    builder.addCase(cancelSubscription.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(cancelSubscription.fulfilled, (state, action) => {
      state.loading = false;
      state.subscription = action.payload;
    });
    builder.addCase(cancelSubscription.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
  },
});

export const { clearError, setSubscription } = subscriptionSlice.actions;

export default subscriptionSlice.reducer;