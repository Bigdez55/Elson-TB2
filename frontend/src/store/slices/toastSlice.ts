import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number; // in milliseconds, 0 = no auto-dismiss
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastState {
  toasts: Toast[];
  position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  maxToasts: number;
}

const initialState: ToastState = {
  toasts: [],
  position: 'bottom-right',
  maxToasts: 5,
};

// Helper to generate unique ID
const generateId = () => `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

const toastSlice = createSlice({
  name: 'toast',
  initialState,
  reducers: {
    addToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const newToast: Toast = {
        ...action.payload,
        id: generateId(),
        duration: action.payload.duration ?? 5000, // Default 5 seconds
      };

      // Limit number of toasts
      if (state.toasts.length >= state.maxToasts) {
        state.toasts.shift(); // Remove oldest
      }

      state.toasts.push(newToast);
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload);
    },
    clearAllToasts: (state) => {
      state.toasts = [];
    },
    setPosition: (state, action: PayloadAction<ToastState['position']>) => {
      state.position = action.payload;
    },
    setMaxToasts: (state, action: PayloadAction<number>) => {
      state.maxToasts = action.payload;
    },
  },
});

export const {
  addToast,
  removeToast,
  clearAllToasts,
  setPosition,
  setMaxToasts,
} = toastSlice.actions;

// Helper action creators for common toast types
export const showSuccessToast = (title: string, message?: string) =>
  addToast({ type: 'success', title, message });

export const showErrorToast = (title: string, message?: string) =>
  addToast({ type: 'error', title, message, duration: 8000 }); // Errors stay longer

export const showWarningToast = (title: string, message?: string) =>
  addToast({ type: 'warning', title, message });

export const showInfoToast = (title: string, message?: string) =>
  addToast({ type: 'info', title, message });

export default toastSlice.reducer;
