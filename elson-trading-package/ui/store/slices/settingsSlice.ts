// frontend/src/app/store/slices/settingsSlice.ts

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SettingsState {
  language: string;
  theme: 'light' | 'dark' | 'system';
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  displayCurrency: string;
  riskTolerance: 'low' | 'medium' | 'high';
  isOnboarded: boolean;
  tutorialCompleted: boolean;
  featuresViewed: string[];
  preferredChartType: 'candle' | 'line' | 'bar';
  chartTimeframe: '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL';
  marketDataRefreshRate: number; // in seconds
}

const initialState: SettingsState = {
  language: 'en',
  theme: 'system',
  notifications: {
    email: true,
    push: true,
    sms: false,
  },
  displayCurrency: 'USD',
  riskTolerance: 'medium',
  isOnboarded: false,
  tutorialCompleted: false,
  featuresViewed: [],
  preferredChartType: 'candle',
  chartTimeframe: '1M',
  marketDataRefreshRate: 5,
};

export const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'system'>) => {
      state.theme = action.payload;
    },
    setNotificationPreferences: (state, action: PayloadAction<{
      email?: boolean;
      push?: boolean;
      sms?: boolean;
    }>) => {
      state.notifications = {
        ...state.notifications,
        ...action.payload,
      };
    },
    setDisplayCurrency: (state, action: PayloadAction<string>) => {
      state.displayCurrency = action.payload;
    },
    setRiskTolerance: (state, action: PayloadAction<'low' | 'medium' | 'high'>) => {
      state.riskTolerance = action.payload;
    },
    completeOnboarding: (state) => {
      state.isOnboarded = true;
    },
    completeTutorial: (state) => {
      state.tutorialCompleted = true;
    },
    viewFeature: (state, action: PayloadAction<string>) => {
      if (!state.featuresViewed.includes(action.payload)) {
        state.featuresViewed.push(action.payload);
      }
    },
    setPreferredChartType: (state, action: PayloadAction<'candle' | 'line' | 'bar'>) => {
      state.preferredChartType = action.payload;
    },
    setChartTimeframe: (state, action: PayloadAction<'1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'>) => {
      state.chartTimeframe = action.payload;
    },
    setMarketDataRefreshRate: (state, action: PayloadAction<number>) => {
      state.marketDataRefreshRate = action.payload;
    },
    resetSettings: (state) => {
      return initialState;
    },
  },
});

export const {
  setLanguage,
  setTheme,
  setNotificationPreferences,
  setDisplayCurrency,
  setRiskTolerance,
  completeOnboarding,
  completeTutorial,
  viewFeature,
  setPreferredChartType,
  setChartTimeframe,
  setMarketDataRefreshRate,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;