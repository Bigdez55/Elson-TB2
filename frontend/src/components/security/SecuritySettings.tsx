import React, { useState } from 'react';
import {
  useGetSecuritySettingsQuery,
  useUpdateSecuritySettingsMutation,
  useAddIPToWhitelistMutation,
  useRemoveIPFromWhitelistMutation,
  SecuritySettings as SecuritySettingsType,
} from '../../services/deviceManagementApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Button } from '../common/Button';
import { Toggle } from '../common/Toggle';

interface SecuritySettingsProps {
  className?: string;
}

export const SecuritySettings: React.FC<SecuritySettingsProps> = ({ className = '' }) => {
  const [newIP, setNewIP] = useState('');
  const [ipDescription, setIPDescription] = useState('');
  const [newCountry, setNewCountry] = useState('');
  const [localSettings, setLocalSettings] = useState<SecuritySettingsType | null>(null);

  // API hooks
  const { data: settings, isLoading, refetch } = useGetSecuritySettingsQuery();
  const [updateSettings, { isLoading: isUpdating }] = useUpdateSecuritySettingsMutation();
  const [addIPToWhitelist, { isLoading: isAddingIP }] = useAddIPToWhitelistMutation();
  const [removeIPFromWhitelist] = useRemoveIPFromWhitelistMutation();

  // Use local settings for immediate UI updates, fall back to server settings
  const currentSettings = localSettings || settings;

  const handleUpdateSetting = async (updates: Partial<SecuritySettingsType>) => {
    const newSettings = { ...currentSettings, ...updates } as SecuritySettingsType;
    setLocalSettings(newSettings);
    
    try {
      await updateSettings(updates).unwrap();
      refetch();
    } catch (error) {
      console.error('Failed to update settings:', error);
      // Revert local changes on error
      setLocalSettings(null);
      alert('Failed to update settings. Please try again.');
    }
  };

  const handleAddIP = async () => {
    if (!newIP.trim()) return;
    
    try {
      await addIPToWhitelist({
        ip_address: newIP.trim(),
        description: ipDescription.trim() || undefined,
      }).unwrap();
      
      setNewIP('');
      setIPDescription('');
      refetch();
    } catch (error) {
      console.error('Failed to add IP to whitelist:', error);
      alert('Failed to add IP address. Please check the format and try again.');
    }
  };

  const handleRemoveIP = async (ip: string) => {
    if (!window.confirm(`Remove ${ip} from whitelist?`)) return;
    
    try {
      await removeIPFromWhitelist({ ip_address: ip }).unwrap();
      refetch();
    } catch (error) {
      console.error('Failed to remove IP from whitelist:', error);
      alert('Failed to remove IP address.');
    }
  };

  const handleAddCountry = () => {
    if (!newCountry.trim() || !currentSettings) return;
    
    const countries = [...currentSettings.geolocation_restrictions.allowed_countries, newCountry.trim()];
    handleUpdateSetting({
      geolocation_restrictions: {
        ...currentSettings.geolocation_restrictions,
        allowed_countries: countries,
      },
    });
    setNewCountry('');
  };

  const handleRemoveCountry = (country: string) => {
    if (!currentSettings) return;
    
    const countries = currentSettings.geolocation_restrictions.allowed_countries.filter(c => c !== country);
    handleUpdateSetting({
      geolocation_restrictions: {
        ...currentSettings.geolocation_restrictions,
        allowed_countries: countries,
      },
    });
  };

  const validateIP = (ip: string) => {
    const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
    const cidrRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-9]|[1-2][0-9]|3[0-2])$/;
    
    return ipv4Regex.test(ip) || ipv6Regex.test(ip) || cidrRegex.test(ip);
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <LoadingSpinner size="md" />
        <span className="ml-3 text-gray-400">Loading security settings...</span>
      </div>
    );
  }

  if (!currentSettings) {
    return (
      <div className={`text-center p-8 ${className}`}>
        <p className="text-gray-400">Failed to load security settings</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Authentication Settings */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Authentication</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">Require Two-Factor Authentication</div>
              <div className="text-gray-400 text-sm">Require 2FA for all account access</div>
            </div>
            <Toggle
              checked={currentSettings.require_2fa}
              onChange={(checked) => handleUpdateSetting({ require_2fa: checked })}
              disabled={isUpdating}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">Require 2FA for Trading</div>
              <div className="text-gray-400 text-sm">Require 2FA specifically for trading operations</div>
            </div>
            <Toggle
              checked={currentSettings.require_2fa_for_trading}
              onChange={(checked) => handleUpdateSetting({ require_2fa_for_trading: checked })}
              disabled={isUpdating}
            />
          </div>
        </div>
      </div>

      {/* Session Management */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Session Management</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-white font-medium mb-2">
              Session Timeout (minutes)
            </label>
            <div className="text-gray-400 text-sm mb-2">
              Sessions will expire after this period of inactivity
            </div>
            <input
              type="number"
              min="5"
              max="1440"
              value={currentSettings.session_timeout_minutes}
              onChange={(e) => handleUpdateSetting({ 
                session_timeout_minutes: Math.max(5, Math.min(1440, parseInt(e.target.value) || 60))
              })}
              className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white w-32 focus:outline-none focus:border-purple-500"
              disabled={isUpdating}
            />
          </div>
          
          <div>
            <label className="block text-white font-medium mb-2">
              Maximum Concurrent Sessions
            </label>
            <div className="text-gray-400 text-sm mb-2">
              Maximum number of active sessions allowed at once
            </div>
            <input
              type="number"
              min="1"
              max="10"
              value={currentSettings.max_concurrent_sessions}
              onChange={(e) => handleUpdateSetting({ 
                max_concurrent_sessions: Math.max(1, Math.min(10, parseInt(e.target.value) || 3))
              })}
              className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white w-32 focus:outline-none focus:border-purple-500"
              disabled={isUpdating}
            />
          </div>

          <div>
            <label className="block text-white font-medium mb-2">
              Device Trust Duration (days)
            </label>
            <div className="text-gray-400 text-sm mb-2">
              How long trusted devices remain trusted
            </div>
            <input
              type="number"
              min="1"
              max="365"
              value={currentSettings.device_trust_duration_days}
              onChange={(e) => handleUpdateSetting({ 
                device_trust_duration_days: Math.max(1, Math.min(365, parseInt(e.target.value) || 30))
              })}
              className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white w-32 focus:outline-none focus:border-purple-500"
              disabled={isUpdating}
            />
          </div>
        </div>
      </div>

      {/* IP Restrictions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">IP Address Restrictions</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">Enable IP Whitelist</div>
              <div className="text-gray-400 text-sm">Only allow access from whitelisted IP addresses</div>
            </div>
            <Toggle
              checked={currentSettings.ip_whitelist_enabled}
              onChange={(checked) => handleUpdateSetting({ ip_whitelist_enabled: checked })}
              disabled={isUpdating}
            />
          </div>
          
          {currentSettings.ip_whitelist_enabled && (
            <div className="space-y-4">
              <div>
                <h4 className="text-white font-medium mb-2">Whitelisted IP Addresses</h4>
                <div className="space-y-2 mb-4">
                  {currentSettings.ip_whitelist.map((ip, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between bg-gray-700 rounded p-3"
                    >
                      <span className="text-white font-mono">{ip}</span>
                      <button
                        onClick={() => handleRemoveIP(ip)}
                        className="text-red-400 hover:text-red-300 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  {currentSettings.ip_whitelist.length === 0 && (
                    <div className="text-gray-400 text-sm">No IP addresses whitelisted</div>
                  )}
                </div>
                
                <div className="space-y-3">
                  <div>
                    <input
                      type="text"
                      placeholder="IP address or CIDR (e.g., 192.168.1.1 or 192.168.1.0/24)"
                      value={newIP}
                      onChange={(e) => setNewIP(e.target.value)}
                      className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white w-full focus:outline-none focus:border-purple-500"
                    />
                    {newIP && !validateIP(newIP) && (
                      <div className="text-red-400 text-xs mt-1">
                        Please enter a valid IP address or CIDR notation
                      </div>
                    )}
                  </div>
                  <div>
                    <input
                      type="text"
                      placeholder="Description (optional)"
                      value={ipDescription}
                      onChange={(e) => setIPDescription(e.target.value)}
                      className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white w-full focus:outline-none focus:border-purple-500"
                    />
                  </div>
                  <Button
                    onClick={handleAddIP}
                    disabled={!newIP.trim() || !validateIP(newIP) || isAddingIP}
                    size="sm"
                  >
                    {isAddingIP ? <LoadingSpinner size="xs" /> : 'Add IP'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Geolocation Restrictions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Geolocation Restrictions</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">Enable Country Restrictions</div>
              <div className="text-gray-400 text-sm">Only allow access from specific countries</div>
            </div>
            <Toggle
              checked={currentSettings.geolocation_restrictions.enabled}
              onChange={(checked) => handleUpdateSetting({
                geolocation_restrictions: {
                  ...currentSettings.geolocation_restrictions,
                  enabled: checked,
                },
              })}
              disabled={isUpdating}
            />
          </div>
          
          {currentSettings.geolocation_restrictions.enabled && (
            <div className="space-y-4">
              <div>
                <h4 className="text-white font-medium mb-2">Allowed Countries</h4>
                <div className="space-y-2 mb-4">
                  {currentSettings.geolocation_restrictions.allowed_countries.map((country, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between bg-gray-700 rounded p-3"
                    >
                      <span className="text-white">{country}</span>
                      <button
                        onClick={() => handleRemoveCountry(country)}
                        className="text-red-400 hover:text-red-300 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  {currentSettings.geolocation_restrictions.allowed_countries.length === 0 && (
                    <div className="text-gray-400 text-sm">No countries specified</div>
                  )}
                </div>
                
                <div className="flex space-x-3">
                  <input
                    type="text"
                    placeholder="Country name or code"
                    value={newCountry}
                    onChange={(e) => setNewCountry(e.target.value)}
                    className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white flex-1 focus:outline-none focus:border-purple-500"
                  />
                  <Button
                    onClick={handleAddCountry}
                    disabled={!newCountry.trim()}
                    size="sm"
                  >
                    Add Country
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Login Protection */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Login Protection</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-white font-medium mb-2">
              Login Attempt Limit
            </label>
            <div className="text-gray-400 text-sm mb-2">
              Number of failed login attempts before account lockout
            </div>
            <input
              type="number"
              min="3"
              max="20"
              value={currentSettings.login_attempt_limit}
              onChange={(e) => handleUpdateSetting({ 
                login_attempt_limit: Math.max(3, Math.min(20, parseInt(e.target.value) || 5))
              })}
              className="bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white w-32 focus:outline-none focus:border-purple-500"
              disabled={isUpdating}
            />
          </div>
        </div>
      </div>

      {/* Notification Preferences */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Security Notifications</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">Email Notifications</div>
              <div className="text-gray-400 text-sm">Receive security alerts via email</div>
            </div>
            <Toggle
              checked={currentSettings.security_notifications.email}
              onChange={(checked) => handleUpdateSetting({
                security_notifications: {
                  ...currentSettings.security_notifications,
                  email: checked,
                },
              })}
              disabled={isUpdating}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">SMS Notifications</div>
              <div className="text-gray-400 text-sm">Receive security alerts via SMS</div>
            </div>
            <Toggle
              checked={currentSettings.security_notifications.sms}
              onChange={(checked) => handleUpdateSetting({
                security_notifications: {
                  ...currentSettings.security_notifications,
                  sms: checked,
                },
              })}
              disabled={isUpdating}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="text-white font-medium">In-App Notifications</div>
              <div className="text-gray-400 text-sm">Show security alerts in the application</div>
            </div>
            <Toggle
              checked={currentSettings.security_notifications.in_app}
              onChange={(checked) => handleUpdateSetting({
                security_notifications: {
                  ...currentSettings.security_notifications,
                  in_app: checked,
                },
              })}
              disabled={isUpdating}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecuritySettings;