import React, { useState } from 'react';
import {
  useGetSecurityAlertsQuery,
  useGetLoginHistoryQuery,
  useMarkAlertAsReadMutation,
  useDismissAlertMutation,
  SecurityAlert,
  LoginAttempt,
} from '../../services/deviceManagementApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Badge } from '../common/Badge';
import DeviceManagement from './DeviceManagement';
import TwoFactorAuth from './TwoFactorAuth';
import SecuritySettings from './SecuritySettings';
import BiometricManagement from './BiometricManagement';

interface SecurityDashboardProps {
  className?: string;
}

export const SecurityDashboard: React.FC<SecurityDashboardProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'devices' | '2fa' | 'biometric' | 'settings'>('overview');

  // API hooks
  const { data: alerts, isLoading: isAlertsLoading, refetch: refetchAlerts } = useGetSecurityAlertsQuery({});
  const { data: loginHistory, isLoading: isHistoryLoading } = useGetLoginHistoryQuery({ limit: 10 });
  
  const [markAsRead] = useMarkAlertAsReadMutation();
  const [dismissAlert] = useDismissAlertMutation();

  const unreadAlerts = alerts?.filter(alert => !alert.is_read) || [];
  const recentFailedLogins = loginHistory?.filter(attempt => !attempt.success).slice(0, 5) || [];

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-900';
      case 'high': return 'text-orange-400 bg-orange-900';
      case 'medium': return 'text-yellow-400 bg-yellow-900';
      case 'low': return 'text-blue-400 bg-blue-900';
      default: return 'text-gray-400 bg-gray-900';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'suspicious_login':
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'new_device':
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a1 1 0 001-1V4a1 1 0 00-1-1H8a1 1 0 00-1 1v16a1 1 0 001 1z" />
          </svg>
        );
      case 'unusual_activity':
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 1.182C4.77 15.916 3 13.658 3 11c0-4.418 4.03-8 9-8s9 3.582 9 8c0 2.658-1.77 4.916-3 7.182" />
          </svg>
        );
    }
  };

  const handleMarkAsRead = async (alertId: string) => {
    try {
      await markAsRead({ alert_id: alertId }).unwrap();
      refetchAlerts();
    } catch (error) {
      console.error('Failed to mark alert as read:', error);
    }
  };

  const handleDismissAlert = async (alertId: string) => {
    try {
      await dismissAlert({ alert_id: alertId }).unwrap();
      refetchAlerts();
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', badge: unreadAlerts.length > 0 ? unreadAlerts.length : undefined },
    { id: 'devices', label: 'Devices & Sessions' },
    { id: '2fa', label: 'Two-Factor Auth' },
    { id: 'biometric', label: 'Biometric' },
    { id: 'settings', label: 'Security Settings' },
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Security Dashboard</h2>
        {unreadAlerts.length > 0 && (
          <Badge variant="error" size="sm">
            {unreadAlerts.length} alert{unreadAlerts.length !== 1 ? 's' : ''}
          </Badge>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
              }`}
            >
              <span className="flex items-center space-x-2">
                <span>{tab.label}</span>
                {tab.badge && (
                  <Badge variant="error" size="sm">
                    {tab.badge}
                  </Badge>
                )}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Security Alerts */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Security Alerts</h3>
              
              {isAlertsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2 text-gray-400">Loading alerts...</span>
                </div>
              ) : alerts && alerts.length > 0 ? (
                <div className="space-y-3">
                  {alerts.slice(0, 5).map((alert) => (
                    <div
                      key={alert.id}
                      className={`border rounded-lg p-4 ${
                        alert.is_read ? 'border-gray-600 bg-gray-700' : 'border-orange-500 bg-orange-900 bg-opacity-20'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <div className={`mt-1 ${getSeverityColor(alert.severity).split(' ')[0]}`}>
                            {getAlertIcon(alert.type)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <h4 className="text-white font-medium text-sm">{alert.title}</h4>
                              <Badge 
                                variant={
                                  alert.severity === 'critical' ? 'error' :
                                  alert.severity === 'high' ? 'warning' :
                                  'neutral'
                                } 
                                size="sm"
                              >
                                {alert.severity}
                              </Badge>
                            </div>
                            <p className="text-gray-400 text-sm">{alert.description}</p>
                            <div className="text-xs text-gray-500 mt-2">
                              {formatTimestamp(alert.created_at)}
                              {alert.location && ` • ${alert.location}`}
                              {alert.ip_address && ` • ${alert.ip_address}`}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {!alert.is_read && (
                            <button
                              onClick={() => handleMarkAsRead(alert.id)}
                              className="text-blue-400 hover:text-blue-300 text-xs"
                            >
                              Mark Read
                            </button>
                          )}
                          <button
                            onClick={() => handleDismissAlert(alert.id)}
                            className="text-gray-400 hover:text-gray-300"
                          >
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-green-400 mb-2">
                    <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-gray-400">No security alerts</p>
                  <p className="text-gray-500 text-sm">Your account security looks good!</p>
                </div>
              )}
            </div>

            {/* Recent Login Activity */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Recent Login Activity</h3>
              
              {isHistoryLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2 text-gray-400">Loading login history...</span>
                </div>
              ) : loginHistory && loginHistory.length > 0 ? (
                <div className="space-y-3">
                  {loginHistory.slice(0, 8).map((attempt) => (
                    <div
                      key={attempt.id}
                      className={`flex items-center justify-between p-3 rounded border ${
                        attempt.success 
                          ? 'border-gray-600 bg-gray-700' 
                          : 'border-red-600 bg-red-900 bg-opacity-20'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={attempt.success ? 'text-green-400' : 'text-red-400'}>
                          {attempt.success ? (
                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          ) : (
                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          )}
                        </div>
                        <div>
                          <div className="text-white text-sm">
                            {attempt.success ? 'Successful login' : 'Failed login attempt'}
                          </div>
                          <div className="text-gray-400 text-xs">
                            {attempt.ip_address}
                            {attempt.location && ` • ${attempt.location.city}, ${attempt.location.country}`}
                            {attempt.failure_reason && ` • ${attempt.failure_reason}`}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <span className="text-gray-500 text-xs">
                          {formatTimestamp(attempt.timestamp)}
                        </span>
                        {attempt.blocked && (
                          <Badge variant="error" size="sm">Blocked</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-400 text-center py-8">
                  No login history available
                </div>
              )}
            </div>

            {/* Failed Login Summary */}
            {recentFailedLogins.length > 0 && (
              <div className="bg-red-900 bg-opacity-20 border border-red-700 rounded-lg p-4">
                <h4 className="text-red-300 font-medium mb-2">Recent Failed Login Attempts</h4>
                <p className="text-red-400 text-sm mb-3">
                  {recentFailedLogins.length} failed login attempts in the last 30 days.
                </p>
                <div className="space-y-1">
                  {recentFailedLogins.map((attempt) => (
                    <div key={attempt.id} className="text-red-300 text-xs">
                      {formatTimestamp(attempt.timestamp)} - {attempt.ip_address}
                      {attempt.location && ` (${attempt.location.city}, ${attempt.location.country})`}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'devices' && <DeviceManagement />}
        {activeTab === '2fa' && <TwoFactorAuth />}
        {activeTab === 'biometric' && <BiometricManagement />}
        {activeTab === 'settings' && <SecuritySettings />}
      </div>
    </div>
  );
};

export default SecurityDashboard;