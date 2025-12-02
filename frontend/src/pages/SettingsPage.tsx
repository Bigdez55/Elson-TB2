import React, { useState } from 'react';
import { Toggle } from '../components/common/Toggle';
import { Badge } from '../components/common/Badge';

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

// Placeholder sections for other settings pages
const APISection: React.FC = () => (
  <div>
    <h1 className="text-2xl font-bold text-white mb-6">API Access</h1>
    <div className="bg-gray-900 rounded-xl p-6">
      <p className="text-gray-300">API Access settings will be implemented here.</p>
    </div>
  </div>
);

const NotificationsSection: React.FC = () => (
  <div>
    <h1 className="text-2xl font-bold text-white mb-6">Notification Preferences</h1>
    <div className="bg-gray-900 rounded-xl p-6">
      <p className="text-gray-300">Notification preferences will be implemented here.</p>
    </div>
  </div>
);

const DevicesSection: React.FC = () => (
  <div>
    <h1 className="text-2xl font-bold text-white mb-6">Connected Devices</h1>
    <div className="bg-gray-900 rounded-xl p-6">
      <p className="text-gray-300">Device management will be implemented here.</p>
    </div>
  </div>
);

const PreferencesSection: React.FC = () => (
  <div>
    <h1 className="text-2xl font-bold text-white mb-6">App Preferences</h1>
    <div className="bg-gray-900 rounded-xl p-6">
      <p className="text-gray-300">App preferences will be implemented here.</p>
    </div>
  </div>
);

const SubscriptionSection: React.FC = () => (
  <div>
    <h1 className="text-2xl font-bold text-white mb-6">Subscription Management</h1>
    <div className="bg-gray-900 rounded-xl p-6">
      <p className="text-gray-300">Subscription management will be implemented here.</p>
    </div>
  </div>
);

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