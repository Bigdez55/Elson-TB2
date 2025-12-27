import React, { useState } from 'react';
import {
  useGetDevicesQuery,
  useGetSessionsQuery,
  useRevokeDeviceMutation,
  useTerminateSessionsMutation,
  useTrustDeviceMutation,
  useUpdateDeviceNameMutation,
  DeviceInfo,
  SecuritySession,
} from '../../services/deviceManagementApi';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Badge } from '../common/Badge';

interface DeviceManagementProps {
  className?: string;
}

export const DeviceManagement: React.FC<DeviceManagementProps> = ({ className = '' }) => {
  const [editingDevice, setEditingDevice] = useState<string | null>(null);
  const [newDeviceName, setNewDeviceName] = useState('');

  // API hooks
  const { data: devices, isLoading: isDevicesLoading, refetch: refetchDevices } = useGetDevicesQuery();
  const { data: sessions, isLoading: isSessionsLoading, refetch: refetchSessions } = useGetSessionsQuery();
  
  const [revokeDevice] = useRevokeDeviceMutation();
  const [terminateSessions] = useTerminateSessionsMutation();
  const [trustDevice] = useTrustDeviceMutation();
  const [updateDeviceName] = useUpdateDeviceNameMutation();

  const formatLastUsed = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType) {
      case 'desktop':
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'mobile':
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a1 1 0 001-1V4a1 1 0 00-1-1H8a1 1 0 00-1 1v16a1 1 0 001 1z" />
          </svg>
        );
      case 'tablet':
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
        );
    }
  };

  const handleRevokeDevice = async (deviceId: string) => {
    if (window.confirm('Are you sure you want to revoke access for this device? This will terminate all sessions on this device.')) {
      try {
        await revokeDevice({ device_id: deviceId }).unwrap();
        refetchDevices();
        refetchSessions();
      } catch (error) {
        console.error('Failed to revoke device:', error);
        alert('Failed to revoke device access');
      }
    }
  };

  const handleTrustDevice = async (deviceId: string) => {
    try {
      await trustDevice({ device_id: deviceId }).unwrap();
      refetchDevices();
    } catch (error) {
      console.error('Failed to trust device:', error);
      alert('Failed to trust device');
    }
  };

  const handleTerminateSession = async (sessionId: string) => {
    if (window.confirm('Are you sure you want to terminate this session?')) {
      try {
        await terminateSessions({ session_ids: [sessionId] }).unwrap();
        refetchSessions();
      } catch (error) {
        console.error('Failed to terminate session:', error);
        alert('Failed to terminate session');
      }
    }
  };

  const handleTerminateAllSessions = async () => {
    if (window.confirm('Are you sure you want to terminate all other sessions? You will remain logged in on this device.')) {
      try {
        await terminateSessions({ terminate_all: true, exclude_current: true }).unwrap();
        refetchSessions();
      } catch (error) {
        console.error('Failed to terminate sessions:', error);
        alert('Failed to terminate sessions');
      }
    }
  };

  const handleSaveDeviceName = async (deviceId: string) => {
    if (!newDeviceName.trim()) return;
    
    try {
      await updateDeviceName({ device_id: deviceId, name: newDeviceName }).unwrap();
      setEditingDevice(null);
      setNewDeviceName('');
      refetchDevices();
    } catch (error) {
      console.error('Failed to update device name:', error);
      alert('Failed to update device name');
    }
  };

  const startEditingDevice = (device: DeviceInfo) => {
    setEditingDevice(device.device_id);
    setNewDeviceName(device.device_name);
  };

  if (isDevicesLoading || isSessionsLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <LoadingSpinner size="md" />
        <span className="ml-3 text-gray-400">Loading device information...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Registered Devices */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Registered Devices</h3>
          <Badge variant="neutral" size="sm">
            {devices?.length || 0} devices
          </Badge>
        </div>

        {devices && devices.length > 0 ? (
          <div className="space-y-4">
            {devices.map((device) => (
              <div
                key={device.device_id}
                className="bg-gray-700 rounded-lg p-4 border border-gray-600"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="text-gray-400 mt-1">
                      {getDeviceIcon(device.device_type)}
                    </div>
                    
                    <div className="flex-1">
                      {editingDevice === device.device_id ? (
                        <div className="flex items-center space-x-2 mb-2">
                          <input
                            type="text"
                            value={newDeviceName}
                            onChange={(e) => setNewDeviceName(e.target.value)}
                            className="bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-purple-500"
                            onKeyPress={(e) => e.key === 'Enter' && handleSaveDeviceName(device.device_id)}
                          />
                          <button
                            onClick={() => handleSaveDeviceName(device.device_id)}
                            className="text-green-400 hover:text-green-300 text-sm"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingDevice(null)}
                            className="text-gray-400 hover:text-gray-300 text-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="text-white font-medium">{device.device_name}</h4>
                          <button
                            onClick={() => startEditingDevice(device)}
                            className="text-gray-400 hover:text-gray-300"
                            title="Edit device name"
                          >
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                        </div>
                      )}
                      
                      <div className="text-sm text-gray-400 space-y-1">
                        <div>{device.browser} on {device.os}</div>
                        <div>Last used: {formatLastUsed(device.last_used)}</div>
                        {device.location && (
                          <div>Location: {device.location.city}, {device.location.country}</div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 mt-3">
                        {device.is_current && (
                          <Badge variant="success" size="sm">Current Device</Badge>
                        )}
                        {device.is_trusted ? (
                          <Badge variant="info" size="sm">Trusted</Badge>
                        ) : (
                          <Badge variant="warning" size="sm">Untrusted</Badge>
                        )}
                        <Badge variant="neutral" size="sm">{device.device_type}</Badge>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {!device.is_trusted && (
                      <button
                        onClick={() => handleTrustDevice(device.device_id)}
                        className="text-green-400 hover:text-green-300 text-sm px-3 py-1 rounded border border-green-400 hover:border-green-300 transition-colors"
                      >
                        Trust
                      </button>
                    )}
                    
                    {!device.is_current && (
                      <button
                        onClick={() => handleRevokeDevice(device.device_id)}
                        className="text-red-400 hover:text-red-300 text-sm px-3 py-1 rounded border border-red-400 hover:border-red-300 transition-colors"
                      >
                        Revoke
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-400 text-center py-8">
            No registered devices found
          </div>
        )}
      </div>

      {/* Active Sessions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Active Sessions</h3>
          <div className="flex items-center space-x-3">
            <Badge variant="neutral" size="sm">
              {sessions?.length || 0} sessions
            </Badge>
            <button
              onClick={handleTerminateAllSessions}
              className="text-red-400 hover:text-red-300 text-sm px-3 py-1 rounded border border-red-400 hover:border-red-300 transition-colors"
            >
              Terminate All Others
            </button>
          </div>
        </div>

        {sessions && sessions.length > 0 ? (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className="bg-gray-700 rounded-lg p-4 border border-gray-600"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="text-gray-400 mt-1">
                      {getDeviceIcon(session.device_info.device_type)}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="text-white font-medium">{session.device_info.device_name}</h4>
                        {session.is_current && (
                          <Badge variant="success" size="sm">Current Session</Badge>
                        )}
                      </div>
                      
                      <div className="text-sm text-gray-400 space-y-1">
                        <div>{session.device_info.browser} on {session.device_info.os}</div>
                        <div>IP: {session.ip_address}</div>
                        {session.location && (
                          <div>Location: {session.location.city}, {session.location.country}</div>
                        )}
                        <div>Created: {new Date(session.created_at).toLocaleString()}</div>
                        <div>Last activity: {formatLastUsed(session.last_activity)}</div>
                        <div>Expires: {new Date(session.expires_at).toLocaleString()}</div>
                      </div>
                    </div>
                  </div>

                  {!session.is_current && (
                    <button
                      onClick={() => handleTerminateSession(session.session_id)}
                      className="text-red-400 hover:text-red-300 text-sm px-3 py-1 rounded border border-red-400 hover:border-red-300 transition-colors"
                    >
                      Terminate
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-400 text-center py-8">
            No active sessions found
          </div>
        )}
      </div>
    </div>
  );
};

export default DeviceManagement;