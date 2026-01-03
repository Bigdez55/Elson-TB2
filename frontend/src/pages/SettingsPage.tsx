import React, { useState } from 'react';
import { Toggle } from '../components/common/Toggle';
import { Badge } from '../components/common/Badge';
import { ThemeSelector } from '../components/settings/ThemeSelector';

interface SettingsSidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const SettingsSidebar: React.FC<SettingsSidebarProps> = ({ activeSection, onSectionChange }) => {
  const sections = [
    { id: 'profile', label: 'Profile Information', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
    { id: 'security', label: 'Security', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
    { id: 'api', label: 'API Access', icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4' },
    { id: 'notifications', label: 'Notifications', icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' },
    { id: 'devices', label: 'Devices', icon: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
    { id: 'preferences', label: 'Preferences', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065zM15 12a3 3 0 11-6 0 3 3 0 016 0z' },
    { id: 'subscription', label: 'Subscription', icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z' }
  ];

  return (
    <div className="bg-gray-900 min-h-screen p-4" style={{ width: '280px' }}>
      <div className="pt-2 pb-6">
        <h2 className="text-xl font-bold text-white mb-6">Account Settings</h2>
        
        <ul className="space-y-2">
          {sections.map((section) => (
            <li key={section.id}>
              <button
                onClick={() => onSectionChange(section.id)}
                className={`w-full text-left px-4 py-2 rounded-lg flex items-center transition-colors ${
                  activeSection === section.id
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                <svg className="h-5 w-5 mr-3 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={section.icon} />
                </svg>
                <span>{section.label}</span>
              </button>
            </li>
          ))}
        </ul>
        
        <div className="mt-8 pt-8 border-t border-gray-800">
          <button className="w-full text-left px-4 py-2 rounded-lg flex items-center text-red-400 hover:bg-gray-800">
            <svg className="h-5 w-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Logout</span>
          </button>
        </div>
      </div>
    </div>
  );
};

const ProfileSection: React.FC = () => {
  const [formData, setFormData] = useState({
    firstName: 'Alex',
    lastName: 'Morgan',
    email: 'alex.morgan@example.com',
    phone: '+1 (555) 123-4567',
    dateOfBirth: '05/12/1985',
    address: '123 Trading Street\nSan Francisco, CA 94107\nUnited States',
    taxId: '***-**-7890',
    taxClassification: 'Individual'
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Profile Information</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl p-6 shadow-md">
            <h2 className="text-lg font-medium text-white mb-6">Personal Details</h2>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-1">First Name</label>
                  <input
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => handleInputChange('firstName', e.target.value)}
                    className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-1">Last Name</label>
                  <input
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => handleInputChange('lastName', e.target.value)}
                    className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Email Address</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Phone Number</label>
                <input
                  type="text"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Date of Birth</label>
                <input
                  type="text"
                  value={formData.dateOfBirth}
                  onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Address</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => handleInputChange('address', e.target.value)}
                  rows={3}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              
              <div className="pt-4">
                <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors">
                  Save Changes
                </button>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-xl p-6 shadow-md mt-6">
            <h2 className="text-lg font-medium text-white mb-6">Tax Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Tax Identification Number (SSN/TIN)</label>
                <input
                  type="text"
                  value={formData.taxId}
                  onChange={(e) => handleInputChange('taxId', e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Tax Classification</label>
                <select
                  value={formData.taxClassification}
                  onChange={(e) => handleInputChange('taxClassification', e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                >
                  <option>Individual</option>
                  <option>Business</option>
                  <option>Trust</option>
                  <option>Estate</option>
                </select>
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">W-9 Form</label>
                <div className="flex items-center mt-2">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-2 flex-1 mr-2">
                    <span className="text-gray-400">w9_form_2023.pdf</span>
                  </div>
                  <button className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg transition-colors">
                    Update
                  </button>
                </div>
              </div>
              
              <div className="pt-4">
                <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors">
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div>
          <div className="bg-gray-900 rounded-xl p-6 shadow-md">
            <div className="text-center mb-6">
              <div className="h-24 w-24 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 mx-auto flex items-center justify-center">
                <span className="text-white text-2xl font-bold">AM</span>
              </div>
              <button className="text-purple-400 hover:text-purple-300 mt-4 text-sm transition-colors">
                Change Avatar
              </button>
            </div>
            
            <div className="border-t border-gray-800 pt-6">
              <h3 className="text-lg font-medium text-white mb-4">Account Information</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Member Since</span>
                  <span className="text-white text-sm">January 15, 2023</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Account Type</span>
                  <span className="text-white text-sm">Premium</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Account Status</span>
                  <span className="text-green-400 text-sm">Active</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Account ID</span>
                  <span className="text-white text-sm">ELS-78502</span>
                </div>
              </div>
            </div>
            
            <div className="border-t border-gray-800 pt-6 mt-6">
              <button className="w-full bg-red-900 hover:bg-red-800 text-red-200 px-4 py-2 rounded-lg text-sm transition-colors">
                Deactivate Account
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const SecuritySection: React.FC = () => {
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [twoFactorSettings, setTwoFactorSettings] = useState({
    sms: true,
    authenticatorApp: false,
    email: false,
    securityKey: false
  });

  const handleTwoFactorToggle = (method: string) => {
    setTwoFactorSettings(prev => ({
      ...prev,
      [method]: !prev[method as keyof typeof prev]
    }));
  };

  const loginHistory = [
    { date: 'Feb 28, 2025 10:23 AM', device: 'MacBook Pro (Chrome)', location: 'San Francisco, CA, USA', ip: '192.168.1.1', status: 'Success' },
    { date: 'Feb 27, 2025 3:45 PM', device: 'iPhone 15 Pro (Safari)', location: 'San Francisco, CA, USA', ip: '192.168.1.2', status: 'Success' },
    { date: 'Feb 25, 2025 7:12 PM', device: 'Unknown Device (Firefox)', location: 'New York, NY, USA', ip: '203.0.113.5', status: 'Failed' },
    { date: 'Feb 24, 2025 11:30 AM', device: 'MacBook Pro (Chrome)', location: 'San Francisco, CA, USA', ip: '192.168.1.1', status: 'Success' }
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Security Settings</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl p-6 shadow-md">
            <h2 className="text-lg font-medium text-white mb-6">Change Password</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Current Password</label>
                <input
                  type="password"
                  placeholder="Enter current password"
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">New Password</label>
                <input
                  type="password"
                  placeholder="Enter new password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
                <div className="mt-2">
                  <div className="flex mb-1">
                    <span className="text-xs text-gray-400">Password Strength:</span>
                    <span className="ml-1 text-xs text-green-400">Strong</span>
                  </div>
                  <div className="w-full h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div className="bg-green-500 h-full transition-all duration-300" style={{ width: '85%' }}></div>
                  </div>
                </div>
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Confirm New Password</label>
                <input
                  type="password"
                  placeholder="Confirm new password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-2 w-full text-white focus:outline-none focus:border-purple-500 transition-colors"
                />
              </div>
              
              <div className="pt-4">
                <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors">
                  Update Password
                </button>
              </div>
            </div>
          </div>
          
          <div className="bg-gray-900 rounded-xl p-6 shadow-md mt-6">
            <h2 className="text-lg font-medium text-white mb-6">Two-Factor Authentication</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-medium">SMS Authentication</h3>
                  <p className="text-gray-400 text-sm">Receive a verification code via SMS</p>
                </div>
                <Toggle
                  checked={twoFactorSettings.sms}
                  onChange={() => handleTwoFactorToggle('sms')}
                />
              </div>
              
              <div className="flex items-center justify-between pt-2 pb-2 border-t border-gray-800">
                <div>
                  <h3 className="text-white font-medium">Authenticator App</h3>
                  <p className="text-gray-400 text-sm">Use an authenticator app like Google Authenticator</p>
                </div>
                <Toggle
                  checked={twoFactorSettings.authenticatorApp}
                  onChange={() => handleTwoFactorToggle('authenticatorApp')}
                />
              </div>
              
              <div className="flex items-center justify-between pt-2 pb-2 border-t border-gray-800">
                <div>
                  <h3 className="text-white font-medium">Email Authentication</h3>
                  <p className="text-gray-400 text-sm">Receive a verification code via email</p>
                </div>
                <Toggle
                  checked={twoFactorSettings.email}
                  onChange={() => handleTwoFactorToggle('email')}
                />
              </div>
              
              <div className="flex items-center justify-between pt-2 pb-2 border-t border-gray-800">
                <div>
                  <h3 className="text-white font-medium">Security Key</h3>
                  <p className="text-gray-400 text-sm">Use a physical security key like YubiKey</p>
                </div>
                <Toggle
                  checked={twoFactorSettings.securityKey}
                  onChange={() => handleTwoFactorToggle('securityKey')}
                />
              </div>
            </div>
          </div>
        </div>
        
        <div>
          <div className="bg-gray-900 rounded-xl p-6 shadow-md text-center">
            <div className="w-24 h-24 bg-green-900 rounded-full mx-auto mb-4 flex items-center justify-center">
              <svg className="h-12 w-12 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-white mb-2">Your Account is Secure</h3>
            <p className="text-gray-400 text-sm mb-6">
              Your account security is strong. Keep up the good work by maintaining these security practices.
            </p>
            
            <div className="space-y-4">
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-300 text-sm">Strong Password</span>
                </div>
              </div>
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-300 text-sm">2FA Enabled</span>
                </div>
              </div>
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-gray-300 text-sm">Recent Login Check</span>
                </div>
              </div>
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-yellow-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="text-gray-300 text-sm">Email Backup Not Verified</span>
                </div>
              </div>
            </div>
            
            <button className="mt-6 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
              Run Security Check
            </button>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-900 rounded-xl p-6 shadow-md">
        <h2 className="text-lg font-medium text-white mb-6">Login History</h2>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-800">
            <thead>
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Date & Time
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Device
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Location
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  IP Address
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {loginHistory.map((entry, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {entry.date}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {entry.device}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {entry.location}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {entry.ip}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge 
                      variant={entry.status === 'Success' ? 'success' : 'error'}
                      size="sm"
                    >
                      {entry.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="mt-4 text-center">
          <button className="text-purple-400 hover:text-purple-300 text-sm transition-colors">
            View Full Login History
          </button>
        </div>
      </div>
    </div>
  );
};

// API Access Section
const APISection: React.FC = () => {
  const [apiKey, setApiKey] = useState('elsk_*****************************7a3f');
  const [showKey, setShowKey] = useState(false);
  const [copied, setCopied] = useState(false);
  const fullApiKey = 'elsk_live_abc123def456ghi789jkl012mno345pqr67a3f';

  const handleCopyKey = () => {
    navigator.clipboard.writeText(fullApiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerateKey = () => {
    // In production, this would call the API
    alert('API key regeneration would be confirmed here');
  };

  const apiUsage = [
    { endpoint: '/api/v1/market-data/quote', calls: 1243, lastUsed: '2 min ago' },
    { endpoint: '/api/v1/trading/orders', calls: 89, lastUsed: '15 min ago' },
    { endpoint: '/api/v1/portfolio/positions', calls: 456, lastUsed: '5 min ago' },
    { endpoint: '/api/v1/account/balance', calls: 234, lastUsed: '1 hour ago' },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">API Access</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl p-6 shadow-md">
            <h2 className="text-lg font-medium text-white mb-4">API Key Management</h2>
            <p className="text-gray-400 text-sm mb-6">
              Use your API key to access the Elson Trading API programmatically. Keep your key secure and never share it publicly.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-2">Your API Key</label>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-gray-800 border border-gray-700 rounded-lg p-3 font-mono text-sm text-gray-300">
                    {showKey ? fullApiKey : apiKey}
                  </div>
                  <button
                    onClick={() => setShowKey(!showKey)}
                    className="bg-gray-700 hover:bg-gray-600 text-white p-3 rounded-lg transition-colors"
                    title={showKey ? 'Hide key' : 'Show key'}
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {showKey ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      )}
                    </svg>
                  </button>
                  <button
                    onClick={handleCopyKey}
                    className="bg-gray-700 hover:bg-gray-600 text-white p-3 rounded-lg transition-colors"
                    title="Copy key"
                  >
                    {copied ? (
                      <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              <div className="pt-4 flex space-x-4">
                <button
                  onClick={handleRegenerateKey}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Regenerate Key
                </button>
                <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors">
                  View Documentation
                </button>
              </div>
            </div>
          </div>

          <div className="bg-gray-900 rounded-xl p-6 shadow-md mt-6">
            <h2 className="text-lg font-medium text-white mb-4">API Usage (Last 24 Hours)</h2>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-800">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Endpoint</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Calls</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Last Used</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {apiUsage.map((item, index) => (
                    <tr key={index}>
                      <td className="px-4 py-3 text-sm font-mono text-gray-300">{item.endpoint}</td>
                      <td className="px-4 py-3 text-sm text-gray-300">{item.calls.toLocaleString()}</td>
                      <td className="px-4 py-3 text-sm text-gray-400">{item.lastUsed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div>
          <div className="bg-gray-900 rounded-xl p-6 shadow-md">
            <h3 className="text-lg font-medium text-white mb-4">Rate Limits</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Requests/min</span>
                  <span className="text-white">45/100</span>
                </div>
                <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="bg-purple-500 h-full" style={{ width: '45%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">Daily Requests</span>
                  <span className="text-white">2,022/10,000</span>
                </div>
                <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full" style={{ width: '20%' }}></div>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-800">
              <h4 className="text-sm font-medium text-white mb-3">Quick Links</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-purple-400 hover:text-purple-300 text-sm transition-colors">API Documentation</a>
                </li>
                <li>
                  <a href="#" className="text-purple-400 hover:text-purple-300 text-sm transition-colors">SDK Downloads</a>
                </li>
                <li>
                  <a href="#" className="text-purple-400 hover:text-purple-300 text-sm transition-colors">Webhook Settings</a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Notifications Section
const NotificationsSection: React.FC = () => {
  const [notifications, setNotifications] = useState({
    // Trading Notifications
    orderExecuted: { email: true, push: true, sms: false },
    orderFailed: { email: true, push: true, sms: true },
    priceAlert: { email: false, push: true, sms: false },
    dividendReceived: { email: true, push: false, sms: false },

    // Account Notifications
    loginAlert: { email: true, push: true, sms: true },
    depositComplete: { email: true, push: true, sms: false },
    withdrawalComplete: { email: true, push: true, sms: true },
    securityAlert: { email: true, push: true, sms: true },

    // Education & Marketing
    newCourses: { email: true, push: false, sms: false },
    weeklyDigest: { email: true, push: false, sms: false },
    promotions: { email: false, push: false, sms: false },
    tips: { email: true, push: false, sms: false },
  });

  const toggleNotification = (category: string, channel: 'email' | 'push' | 'sms') => {
    setNotifications(prev => ({
      ...prev,
      [category]: {
        ...prev[category as keyof typeof prev],
        [channel]: !prev[category as keyof typeof prev][channel]
      }
    }));
  };

  const NotificationRow = ({
    label,
    description,
    category
  }: {
    label: string;
    description: string;
    category: keyof typeof notifications;
  }) => (
    <div className="flex items-center justify-between py-4 border-b border-gray-800 last:border-b-0">
      <div className="flex-1">
        <h4 className="text-white font-medium">{label}</h4>
        <p className="text-gray-400 text-sm">{description}</p>
      </div>
      <div className="flex items-center space-x-6">
        <label className="flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={notifications[category].email}
            onChange={() => toggleNotification(category, 'email')}
            className="sr-only"
          />
          <div className={`w-10 h-6 rounded-full transition-colors ${notifications[category].email ? 'bg-purple-600' : 'bg-gray-700'}`}>
            <div className={`w-4 h-4 bg-white rounded-full transform transition-transform mt-1 ${notifications[category].email ? 'translate-x-5' : 'translate-x-1'}`}></div>
          </div>
          <span className="ml-2 text-gray-400 text-xs">Email</span>
        </label>
        <label className="flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={notifications[category].push}
            onChange={() => toggleNotification(category, 'push')}
            className="sr-only"
          />
          <div className={`w-10 h-6 rounded-full transition-colors ${notifications[category].push ? 'bg-purple-600' : 'bg-gray-700'}`}>
            <div className={`w-4 h-4 bg-white rounded-full transform transition-transform mt-1 ${notifications[category].push ? 'translate-x-5' : 'translate-x-1'}`}></div>
          </div>
          <span className="ml-2 text-gray-400 text-xs">Push</span>
        </label>
        <label className="flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={notifications[category].sms}
            onChange={() => toggleNotification(category, 'sms')}
            className="sr-only"
          />
          <div className={`w-10 h-6 rounded-full transition-colors ${notifications[category].sms ? 'bg-purple-600' : 'bg-gray-700'}`}>
            <div className={`w-4 h-4 bg-white rounded-full transform transition-transform mt-1 ${notifications[category].sms ? 'translate-x-5' : 'translate-x-1'}`}></div>
          </div>
          <span className="ml-2 text-gray-400 text-xs">SMS</span>
        </label>
      </div>
    </div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Notification Preferences</h1>

      <div className="space-y-6">
        <div className="bg-gray-900 rounded-xl p-6 shadow-md">
          <h2 className="text-lg font-medium text-white mb-4">Trading Notifications</h2>
          <NotificationRow
            label="Order Executed"
            description="Get notified when your orders are filled"
            category="orderExecuted"
          />
          <NotificationRow
            label="Order Failed"
            description="Get notified when an order fails to execute"
            category="orderFailed"
          />
          <NotificationRow
            label="Price Alerts"
            description="Receive alerts when stocks hit your target prices"
            category="priceAlert"
          />
          <NotificationRow
            label="Dividend Received"
            description="Get notified when dividends are credited"
            category="dividendReceived"
          />
        </div>

        <div className="bg-gray-900 rounded-xl p-6 shadow-md">
          <h2 className="text-lg font-medium text-white mb-4">Account Notifications</h2>
          <NotificationRow
            label="Login Alerts"
            description="Get notified of new login attempts"
            category="loginAlert"
          />
          <NotificationRow
            label="Deposit Complete"
            description="Notification when deposits are processed"
            category="depositComplete"
          />
          <NotificationRow
            label="Withdrawal Complete"
            description="Notification when withdrawals are processed"
            category="withdrawalComplete"
          />
          <NotificationRow
            label="Security Alerts"
            description="Important security-related notifications"
            category="securityAlert"
          />
        </div>

        <div className="bg-gray-900 rounded-xl p-6 shadow-md">
          <h2 className="text-lg font-medium text-white mb-4">Education & Marketing</h2>
          <NotificationRow
            label="New Courses Available"
            description="Learn about new educational content"
            category="newCourses"
          />
          <NotificationRow
            label="Weekly Digest"
            description="Weekly summary of your portfolio performance"
            category="weeklyDigest"
          />
          <NotificationRow
            label="Promotions & Offers"
            description="Special offers and promotional content"
            category="promotions"
          />
          <NotificationRow
            label="Tips & Insights"
            description="Trading tips and market insights"
            category="tips"
          />
        </div>

        <div className="flex justify-end">
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg transition-colors">
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
};

// Devices Section
const DevicesSection: React.FC = () => {
  const [devices] = useState([
    {
      id: '1',
      name: 'MacBook Pro',
      type: 'desktop',
      browser: 'Chrome 121',
      location: 'San Francisco, CA',
      lastActive: 'Active now',
      isCurrent: true,
      ip: '192.168.1.1',
      trusted: true
    },
    {
      id: '2',
      name: 'iPhone 15 Pro',
      type: 'mobile',
      browser: 'Safari iOS',
      location: 'San Francisco, CA',
      lastActive: '2 hours ago',
      isCurrent: false,
      ip: '192.168.1.2',
      trusted: true
    },
    {
      id: '3',
      name: 'Windows Desktop',
      type: 'desktop',
      browser: 'Firefox 122',
      location: 'New York, NY',
      lastActive: '3 days ago',
      isCurrent: false,
      ip: '203.0.113.45',
      trusted: false
    },
    {
      id: '4',
      name: 'iPad Pro',
      type: 'tablet',
      browser: 'Safari iPadOS',
      location: 'San Francisco, CA',
      lastActive: '1 week ago',
      isCurrent: false,
      ip: '192.168.1.5',
      trusted: true
    }
  ]);

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'mobile':
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      case 'tablet':
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        );
      default:
        return (
          <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
    }
  };

  const handleRevokeDevice = (deviceId: string) => {
    alert(`Revoking access for device ${deviceId}`);
  };

  const handleRevokeAll = () => {
    alert('Revoking access for all devices except current');
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Connected Devices</h1>

      <div className="bg-gray-900 rounded-xl p-6 shadow-md mb-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-lg font-medium text-white">Active Sessions</h2>
            <p className="text-gray-400 text-sm">Manage devices that have access to your account</p>
          </div>
          <button
            onClick={handleRevokeAll}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Sign Out All Devices
          </button>
        </div>

        <div className="space-y-4">
          {devices.map((device) => (
            <div
              key={device.id}
              className={`flex items-center justify-between p-4 rounded-lg ${
                device.isCurrent ? 'bg-purple-900/30 border border-purple-500/30' : 'bg-gray-800'
              }`}
            >
              <div className="flex items-center space-x-4">
                <div className={`p-2 rounded-lg ${device.isCurrent ? 'bg-purple-600/30 text-purple-400' : 'bg-gray-700 text-gray-400'}`}>
                  {getDeviceIcon(device.type)}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-white font-medium">{device.name}</h3>
                    {device.isCurrent && (
                      <span className="bg-green-600 text-white text-xs px-2 py-0.5 rounded-full">
                        Current
                      </span>
                    )}
                    {device.trusted && !device.isCurrent && (
                      <span className="bg-blue-600/20 text-blue-400 text-xs px-2 py-0.5 rounded-full">
                        Trusted
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 text-sm">{device.browser} • {device.location}</p>
                  <p className="text-gray-500 text-xs mt-1">IP: {device.ip} • {device.lastActive}</p>
                </div>
              </div>

              {!device.isCurrent && (
                <button
                  onClick={() => handleRevokeDevice(device.id)}
                  className="text-red-400 hover:text-red-300 text-sm transition-colors"
                >
                  Revoke Access
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl p-6 shadow-md">
        <h2 className="text-lg font-medium text-white mb-4">Session Settings</h2>

        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-gray-800">
            <div>
              <h4 className="text-white font-medium">Remember Trusted Devices</h4>
              <p className="text-gray-400 text-sm">Skip 2FA on devices you've marked as trusted</p>
            </div>
            <Toggle checked={true} onChange={() => {}} />
          </div>

          <div className="flex items-center justify-between py-3 border-b border-gray-800">
            <div>
              <h4 className="text-white font-medium">Auto Sign-Out</h4>
              <p className="text-gray-400 text-sm">Automatically sign out after inactivity</p>
            </div>
            <select className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm">
              <option>15 minutes</option>
              <option>30 minutes</option>
              <option>1 hour</option>
              <option>4 hours</option>
              <option>Never</option>
            </select>
          </div>

          <div className="flex items-center justify-between py-3">
            <div>
              <h4 className="text-white font-medium">Login Notifications</h4>
              <p className="text-gray-400 text-sm">Get notified of new device logins</p>
            </div>
            <Toggle checked={true} onChange={() => {}} />
          </div>
        </div>
      </div>
    </div>
  );
};

// Preferences Section
const PreferencesSection: React.FC = () => {
  const [tradingPreferences, setTradingPreferences] = useState({
    defaultOrderType: 'market',
    confirmOrders: true,
    showEducationalTips: true,
    autoRefreshData: true,
    soundEffects: false,
    compactMode: false
  });

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">App Preferences</h1>

      {/* Theme Selector */}
      <ThemeSelector />

      {/* Trading Preferences */}
      <div className="bg-gray-900 rounded-xl p-6 shadow-md mt-6">
        <h3 className="text-lg font-semibold text-white mb-4">Trading Preferences</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-gray-800">
            <div>
              <h4 className="text-white font-medium">Default Order Type</h4>
              <p className="text-gray-400 text-sm">Pre-selected order type when trading</p>
            </div>
            <select
              value={tradingPreferences.defaultOrderType}
              onChange={(e) => setTradingPreferences(prev => ({ ...prev, defaultOrderType: e.target.value }))}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
            >
              <option value="market">Market Order</option>
              <option value="limit">Limit Order</option>
              <option value="stop">Stop Order</option>
            </select>
          </div>

          <div className="flex items-center justify-between py-3 border-b border-gray-800">
            <div>
              <h4 className="text-white font-medium">Confirm Before Trading</h4>
              <p className="text-gray-400 text-sm">Show confirmation dialog before placing orders</p>
            </div>
            <Toggle
              checked={tradingPreferences.confirmOrders}
              onChange={() => setTradingPreferences(prev => ({ ...prev, confirmOrders: !prev.confirmOrders }))}
            />
          </div>

          <div className="flex items-center justify-between py-3 border-b border-gray-800">
            <div>
              <h4 className="text-white font-medium">Show Educational Tips</h4>
              <p className="text-gray-400 text-sm">Display helpful tips and explanations</p>
            </div>
            <Toggle
              checked={tradingPreferences.showEducationalTips}
              onChange={() => setTradingPreferences(prev => ({ ...prev, showEducationalTips: !prev.showEducationalTips }))}
            />
          </div>
        </div>
      </div>

      {/* Display Preferences */}
      <div className="bg-gray-900 rounded-xl p-6 shadow-md mt-6">
        <h3 className="text-lg font-semibold text-white mb-4">Display Settings</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-gray-800">
            <div>
              <h4 className="text-white font-medium">Auto-Refresh Data</h4>
              <p className="text-gray-400 text-sm">Automatically refresh market data</p>
            </div>
            <Toggle
              checked={tradingPreferences.autoRefreshData}
              onChange={() => setTradingPreferences(prev => ({ ...prev, autoRefreshData: !prev.autoRefreshData }))}
            />
          </div>

          <div className="flex items-center justify-between py-3 border-b border-gray-800">
            <div>
              <h4 className="text-white font-medium">Sound Effects</h4>
              <p className="text-gray-400 text-sm">Play sounds for trades and alerts</p>
            </div>
            <Toggle
              checked={tradingPreferences.soundEffects}
              onChange={() => setTradingPreferences(prev => ({ ...prev, soundEffects: !prev.soundEffects }))}
            />
          </div>

          <div className="flex items-center justify-between py-3">
            <div>
              <h4 className="text-white font-medium">Compact Mode</h4>
              <p className="text-gray-400 text-sm">Reduce spacing for more information density</p>
            </div>
            <Toggle
              checked={tradingPreferences.compactMode}
              onChange={() => setTradingPreferences(prev => ({ ...prev, compactMode: !prev.compactMode }))}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end mt-6">
        <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg transition-colors">
          Save Preferences
        </button>
      </div>
    </div>
  );
};

// Subscription Section
const SubscriptionSection: React.FC = () => {
  const [currentPlan] = useState({
    name: 'Premium',
    price: 9.99,
    billingCycle: 'monthly',
    nextBilling: 'March 15, 2025',
    features: [
      'Unlimited trades',
      'Real-time market data',
      'Advanced charting',
      'AI trading signals',
      'Priority support',
      'API access'
    ]
  });

  const plans = [
    {
      name: 'Basic',
      price: 0,
      period: 'Free forever',
      features: ['5 trades/month', 'Delayed quotes (15 min)', 'Basic charts', 'Email support'],
      current: false
    },
    {
      name: 'Premium',
      price: 9.99,
      period: '/month',
      features: ['Unlimited trades', 'Real-time data', 'Advanced charts', 'AI signals', 'Priority support', 'API access'],
      current: true
    },
    {
      name: 'Pro',
      price: 29.99,
      period: '/month',
      features: ['Everything in Premium', 'Options trading', 'Level 2 data', 'Strategy backtesting', 'Dedicated manager', 'Custom alerts'],
      current: false
    }
  ];

  const billingHistory = [
    { date: 'Feb 15, 2025', description: 'Premium Plan - Monthly', amount: '$9.99', status: 'Paid' },
    { date: 'Jan 15, 2025', description: 'Premium Plan - Monthly', amount: '$9.99', status: 'Paid' },
    { date: 'Dec 15, 2024', description: 'Premium Plan - Monthly', amount: '$9.99', status: 'Paid' },
    { date: 'Nov 15, 2024', description: 'Premium Plan - Monthly', amount: '$9.99', status: 'Paid' }
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Subscription Management</h1>

      {/* Current Plan */}
      <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-xl p-6 border border-purple-500/30 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-white">{currentPlan.name} Plan</h2>
              <span className="bg-purple-600 text-white text-xs px-2 py-1 rounded-full">Active</span>
            </div>
            <p className="text-gray-300 mt-1">
              ${currentPlan.price}/{currentPlan.billingCycle} • Next billing: {currentPlan.nextBilling}
            </p>
          </div>
          <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            Cancel Subscription
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-2">
          {currentPlan.features.map((feature, index) => (
            <div key={index} className="flex items-center text-gray-300 text-sm">
              <svg className="h-4 w-4 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              {feature}
            </div>
          ))}
        </div>
      </div>

      {/* Available Plans */}
      <div className="bg-gray-900 rounded-xl p-6 shadow-md mb-6">
        <h2 className="text-lg font-medium text-white mb-6">Available Plans</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-xl p-4 border ${
                plan.current
                  ? 'bg-purple-900/30 border-purple-500/50'
                  : 'bg-gray-800 border-gray-700 hover:border-gray-600'
              } transition-colors`}
            >
              <h3 className="text-lg font-bold text-white">{plan.name}</h3>
              <div className="mt-2">
                <span className="text-3xl font-bold text-white">${plan.price}</span>
                <span className="text-gray-400 text-sm">{plan.period}</span>
              </div>

              <ul className="mt-4 space-y-2">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center text-gray-300 text-sm">
                    <svg className="h-4 w-4 text-purple-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                className={`w-full mt-4 py-2 rounded-lg text-sm transition-colors ${
                  plan.current
                    ? 'bg-purple-600 text-white cursor-default'
                    : 'bg-gray-700 hover:bg-gray-600 text-white'
                }`}
                disabled={plan.current}
              >
                {plan.current ? 'Current Plan' : plan.price === 0 ? 'Downgrade' : 'Upgrade'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Billing History */}
      <div className="bg-gray-900 rounded-xl p-6 shadow-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-white">Billing History</h2>
          <button className="text-purple-400 hover:text-purple-300 text-sm transition-colors">
            Download All Invoices
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-800">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Date</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Description</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Amount</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Invoice</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {billingHistory.map((item, index) => (
                <tr key={index}>
                  <td className="px-4 py-3 text-sm text-gray-300">{item.date}</td>
                  <td className="px-4 py-3 text-sm text-gray-300">{item.description}</td>
                  <td className="px-4 py-3 text-sm text-white font-medium">{item.amount}</td>
                  <td className="px-4 py-3">
                    <Badge variant="success" size="sm">{item.status}</Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-purple-400 hover:text-purple-300 text-sm transition-colors">
                      Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const SettingsPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('profile');

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'profile':
        return <ProfileSection />;
      case 'security':
        return <SecuritySection />;
      case 'api':
        return <APISection />;
      case 'notifications':
        return <NotificationsSection />;
      case 'devices':
        return <DevicesSection />;
      case 'preferences':
        return <PreferencesSection />;
      case 'subscription':
        return <SubscriptionSection />;
      default:
        return <ProfileSection />;
    }
  };

  return (
    <div className="bg-gray-800 min-h-screen flex">
      {/* Settings Sidebar */}
      <SettingsSidebar 
        activeSection={activeSection} 
        onSectionChange={setActiveSection} 
      />
      
      {/* Main Content */}
      <div className="flex-1 p-6">
        {renderActiveSection()}
      </div>
    </div>
  );
};

export default SettingsPage;