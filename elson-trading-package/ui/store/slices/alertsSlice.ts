import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../services/api';

interface Alert {
  id: string;
  symbol: string;
  type: 'PRICE' | 'VOLUME' | 'INDICATOR' | 'NEWS';
  condition: string;
  value: number;
  triggered: boolean;
  createdAt: string;
  triggeredAt?: string;
}

interface AlertsState {
  alerts: Alert[];
  activeAlerts: Alert[];
  triggeredAlerts: Alert[];
  loading: boolean;
  error: string | null;
}

const initialState: AlertsState = {
  alerts: [],
  activeAlerts: [],
  triggeredAlerts: [],
  loading: false,
  error: null,
};

// Async thunks
export const fetchAlerts = createAsyncThunk(
  'alerts/fetchAlerts',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/alerts');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to fetch alerts');
    }
  }
);

export const createAlert = createAsyncThunk(
  'alerts/createAlert',
  async (alertData: Partial<Alert>, { rejectWithValue }) => {
    try {
      const response = await api.post('/alerts', alertData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to create alert');
    }
  }
);

export const deleteAlert = createAsyncThunk(
  'alerts/deleteAlert',
  async (alertId: string, { rejectWithValue }) => {
    try {
      await api.delete(`/alerts/${alertId}`);
      return alertId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to delete alert');
    }
  }
);

export const updateAlert = createAsyncThunk(
  'alerts/updateAlert',
  async ({ alertId, data }: { alertId: string; data: Partial<Alert> }, { rejectWithValue }) => {
    try {
      const response = await api.put(`/alerts/${alertId}`, data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Failed to update alert');
    }
  }
);

const alertsSlice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {
    triggerAlert: (state, action) => {
      const alert = state.alerts.find(a => a.id === action.payload.alertId);
      if (alert && !alert.triggered) {
        alert.triggered = true;
        alert.triggeredAt = new Date().toISOString();
        state.triggeredAlerts.push(alert);
        state.activeAlerts = state.activeAlerts.filter(a => a.id !== alert.id);
      }
    },
    clearTriggeredAlerts: (state) => {
      state.triggeredAlerts = [];
    },
    resetAlert: (state, action) => {
      const alert = state.alerts.find(a => a.id === action.payload);
      if (alert) {
        alert.triggered = false;
        alert.triggeredAt = undefined;
        state.activeAlerts.push(alert);
        state.triggeredAlerts = state.triggeredAlerts.filter(a => a.id !== alert.id);
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch Alerts
    builder
      .addCase(fetchAlerts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAlerts.fulfilled, (state, action) => {
        state.loading = false;
        state.alerts = action.payload;
        state.activeAlerts = action.payload.filter((alert: Alert) => !alert.triggered);
        state.triggeredAlerts = action.payload.filter((alert: Alert) => alert.triggered);
      })
      .addCase(fetchAlerts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Create Alert
    builder
      .addCase(createAlert.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createAlert.fulfilled, (state, action) => {
        state.loading = false;
        state.alerts.push(action.payload);
        state.activeAlerts.push(action.payload);
      })
      .addCase(createAlert.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Delete Alert
    builder
      .addCase(deleteAlert.fulfilled, (state, action) => {
        state.alerts = state.alerts.filter(alert => alert.id !== action.payload);
        state.activeAlerts = state.activeAlerts.filter(alert => alert.id !== action.payload);
        state.triggeredAlerts = state.triggeredAlerts.filter(alert => alert.id !== action.payload);
      });

    // Update Alert
    builder
      .addCase(updateAlert.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateAlert.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.alerts.findIndex(alert => alert.id === action.payload.id);
        if (index !== -1) {
          state.alerts[index] = action.payload;
          if (action.payload.triggered) {
            state.activeAlerts = state.activeAlerts.filter(alert => alert.id !== action.payload.id);
            state.triggeredAlerts.push(action.payload);
          } else {
            state.triggeredAlerts = state.triggeredAlerts.filter(alert => alert.id !== action.payload.id);
            state.activeAlerts.push(action.payload);
          }
        }
      })
      .addCase(updateAlert.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  triggerAlert,
  clearTriggeredAlerts,
  resetAlert,
  clearError,
} = alertsSlice.actions;

export default alertsSlice.reducer;