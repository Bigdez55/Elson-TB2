import React from 'react';
import { useSettings } from '../hooks/useSettings';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Select from '../components/common/Select';
import { Switch } from '@headlessui/react';

export default function Settings() {
  const {
    tradingSettings,
    notificationSettings,
    uiSettings,
    loading,
    error,
    updateTradingSettings,
    updateNotificationSettings,
    updateUISettings,
  } = useSettings();

  if (loading) {
    return <div>Loading settings...</div>;
  }

  const handleTradingSettingsUpdate = async (changes: any) => {
    await updateTradingSettings({ ...tradingSettings, ...changes });
  };

  return (
    <div className="space-y-8">
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-6">Trading Settings</h2>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Default Leverage"
              type="number"
              value={tradingSettings?.defaultLeverage}
              onChange={(e) => handleTradingSettingsUpdate({
                defaultLeverage: parseFloat(e.target.value)
              })}
              min="1"
              max="100"
            />
            <Input
              label="Risk Per Trade (%)"
              type="number"
              value={tradingSettings?.riskPerTrade}
              onChange={(e) => handleTradingSettingsUpdate({
                riskPerTrade: parseFloat(e.target.value)
              })}
              min="0.1"
              max="100"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select
              label="Stop Loss Type"
              value={tradingSettings?.stopLossType}
              onChange={(value) => handleTradingSettingsUpdate({ stopLossType: value })}
              options={[
                { value: 'fixed', label: 'Fixed' },
                { value: 'trailing', label: 'Trailing' },
                { value: 'none', label: 'None' },
              ]}
            />
            <Select
              label="Take Profit Type"
              value={tradingSettings?.takeProfitType}
              onChange={(value) => handleTradingSettingsUpdate({ takeProfitType: value })}
              options={[
                { value: 'fixed', label: 'Fixed' },
                { value: 'trailing', label: 'Trailing' },
                { value: 'none', label: 'None' },
              ]}
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="font-medium">Enable Trading</span>
            <Switch
              checked={tradingSettings?.tradingEnabled}
              onChange={(enabled) => handleTradingSettingsUpdate({ tradingEnabled: enabled })}
              className={`${
                tradingSettings?.tradingEnabled ? 'bg-primary-600' : 'bg-gray-600'
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors`}
            >
              <span
                className={`${
                  tradingSettings?.tradingEnabled ? 'translate-x-6' : 'translate-x-1'
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-6">Notification Settings</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span>Email Notifications</span>
            <Switch
              checked={notificationSettings?.email}
              onChange={(enabled) => updateNotificationSettings({ email: enabled })}
              className={`${
                notificationSettings?.email ? 'bg-primary-600' : 'bg-gray-600'
              } relative inline-flex h-6 w-11 items-center rounded-full`}
            >
              <span
                className={`${
                  notificationSettings?.email ? 'translate-x-6' : 'translate-x-1'
                } inline-block h-4 w-4 transform rounded-full bg-white`}
              />
            </Switch>
          </div>

          <div className="flex items-center justify-between">
            <span>Push Notifications</span>
            <Switch
              checked={notificationSettings?.push}
              onChange={(enabled) => updateNotificationSettings({ push: enabled })}
              className={`${
                notificationSettings?.push ? 'bg-primary-600' : 'bg-gray-600'
              } relative inline-flex h-6 w-11 items-center rounded-full`}
            >
              <span
                className={`${
                  notificationSettings?.push ? 'translate-x-6' : 'translate-x-1'
                } inline-block h-4 w-4 transform rounded-full bg-white`}
              />
            </Switch>
          </div>

          <div className="flex items-center justify-between">
            <span>Telegram Notifications</span>
            <Switch
              checked={notificationSettings?.telegram}
              onChange={(enabled) => updateNotificationSettings({ telegram: enabled })}
              className={`${
                notificationSettings?.telegram ? 'bg-primary-600' : 'bg-gray-600'
              } relative inline-flex h-6 w-11 items-center rounded-full`}
            >
              <span
                className={`${
                  notificationSettings?.telegram ? 'translate-x-6' : 'translate-x-1'
                } inline-block h-4 w-4 transform rounded-full bg-white`}
              />
            </Switch>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-6">Interface Settings</h2>
        <div className="space-y-4">
          <Select
            label="Theme"
            value={uiSettings?.theme}
            onChange={(value) => updateUISettings({ theme: value })}
            options={[
              { value: 'dark', label: 'Dark' },
              { value: 'light', label: 'Light' },
            ]}
          />

          <Select
            label="Default Chart Type"
            value={uiSettings?.chartType}
            onChange={(value) => updateUISettings({ chartType: value })}
            options={[
              { value: 'candlestick', label: 'Candlestick' },
              { value: 'line', label: 'Line' },
            ]}
          />

          <Select
            label="Default Timeframe"
            value={uiSettings?.defaultTimeframe}
            onChange={(value) => updateUISettings({ defaultTimeframe: value })}
            options={[
              { value: '1m', label: '1 Minute' },
              { value: '5m', label: '5 Minutes' },
              { value: '15m', label: '15 Minutes' },
              { value: '1h', label: '1 Hour' },
              { value: '4h', label: '4 Hours' },
              { value: '1d', label: '1 Day' },
            ]}
          />
        </div>
      </div>

      {error && (
        <div className="text-red-500 mt-4">{error}</div>
      )}
    </div>
  );
}