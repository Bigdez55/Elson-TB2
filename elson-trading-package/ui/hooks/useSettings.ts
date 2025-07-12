import { useState, useEffect, useCallback } from 'react';
import { settingsService } from '../services/settingsService';
import type { 
  TradingSettings, 
  NotificationSettings, 
  UISettings 
} from '../services/settingsService';

export function useSettings() {
  const [tradingSettings, setTradingSettings] = useState<TradingSettings | null>(null);
  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings | null>(null);
  const [uiSettings, setUiSettings] = useState<UISettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      const [trading, notifications, ui] = await Promise.all([
        settingsService.getTradingSettings(),
        settingsService.getNotificationSettings(),
        settingsService.getUISettings(),
      ]);
      
      setTradingSettings(trading);
      setNotificationSettings(notifications);
      setUiSettings(ui);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  const updateTradingSettings = useCallback(async (settings: Partial<TradingSettings>) => {
    try {
      const updated = await settingsService.updateTradingSettings(settings);
      setTradingSettings(updated);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update trading settings');
      return false;
    }
  }, []);

  const updateNotificationSettings = useCallback(async (settings: Partial<NotificationSettings>) => {
    try {
      const updated = await settingsService.updateNotificationSettings(settings);
      setNotificationSettings(updated);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update notification settings');
      return false;
    }
  }, []);

  const updateUISettings = useCallback(async (settings: Partial<UISettings>) => {
    try {
      const updated = await settingsService.updateUISettings(settings);
      setUiSettings(updated);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update UI settings');
      return false;
    }
  }, []);

  const resetAllSettings = useCallback(async () => {
    try {
      await settingsService.resetSettings();
      await fetchSettings();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset settings');
      return false;
    }
  }, [fetchSettings]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  return {
    tradingSettings,
    notificationSettings,
    uiSettings,
    loading,
    error,
    updateTradingSettings,
    updateNotificationSettings,
    updateUISettings,
    resetAllSettings,
    refreshSettings: fetchSettings,
  };
}