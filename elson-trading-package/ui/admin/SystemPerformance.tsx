import React, { useState, useEffect, useCallback } from 'react';
import { 
  FiActivity, FiServer, FiCpu, FiHardDrive, 
  FiDatabase, FiRefreshCw, FiX, FiWifiOff
} from 'react-icons/fi';
import Card from '../common/Card';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import adminService from '../../services/adminService';
import { useDispatch } from 'react-redux';
import { addNotification } from '../../store/slices/notificationsSlice';
import AdminErrorBoundary from './AdminErrorBoundary';
import { handleError } from '../../utils/errorHandling';
import useConnectionStatus from '../../hooks/useConnectionStatus';

interface ServerStats {
  cpu: {
    usage: number;
    cores: number;
    load: number[];
  };
  memory: {
    total: number;
    used: number;
    free: number;
    usage: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    usage: number;
  };
  network: {
    rx_bytes: number;
    tx_bytes: number;
    rx_packets: number;
    tx_packets: number;
    rx_errors: number;
    tx_errors: number;
  };
  uptime: number;
}

interface DatabaseStats {
  connections: number;
  active_queries: number;
  slow_queries: number;
  query_execution_time: number;
  replication_lag?: number;
  database_size: number;
  read_operations: number;
  write_operations: number;
  cache_hit_ratio: number;
}

interface ServiceStats {
  name: string;
  status: 'operational' | 'degraded' | 'outage' | 'maintenance';
  response_time: number;
  error_rate: number;
  resource_usage: number;
  instance_count: number;
}

interface SystemPerformanceData {
  timestamp: string;
  server: ServerStats;
  database: DatabaseStats;
  services: ServiceStats[];
}

const SystemPerformance: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [performanceData, setPerformanceData] = useState<SystemPerformanceData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshingData, setRefreshingData] = useState<boolean>(false);
  
  const dispatch = useDispatch();

  // Connection status hook to handle offline/online states
  const { isOnline, status: connectionStatus } = useConnectionStatus({
    onStatusChange: (status) => {
      if (status === 'online' && connectionStatus === 'offline') {
        // Auto-refresh data when coming back online
        fetchPerformanceData(true);
      }
    }
  });

  // Fetch performance data
  const fetchPerformanceData = useCallback(async (forceRefresh = false) => {
    if (refreshingData && !forceRefresh) return;
    
    // Don't try to fetch if we're offline
    if (!isOnline && !forceRefresh) {
      dispatch(addNotification({
        type: 'warning',
        message: 'You appear to be offline. Using cached performance data.',
        timestamp: new Date().toISOString(),
        read: false
      }));
      return;
    }
    
    if (forceRefresh) {
      setRefreshingData(true);
    } else {
      setLoading(true);
    }
    
    try {
      const data = await adminService.getSystemPerformance();
      setPerformanceData(data);
      
      if (forceRefresh) {
        dispatch(addNotification({
          type: 'success',
          message: 'System performance data refreshed successfully.',
          timestamp: new Date().toISOString(),
          read: false
        }));
      }
    } catch (error) {
      handleError(error, dispatch, 'fetching system performance data');
    } finally {
      setLoading(false);
      setRefreshingData(false);
    }
  }, [dispatch, refreshingData, isOnline]);

  // Fetch performance data on mount
  useEffect(() => {
    fetchPerformanceData();
    
    // Set up auto-refresh every 30 seconds if online
    const intervalId = setInterval(() => {
      if (isOnline) {
        fetchPerformanceData(true);
      }
    }, 30000);
    
    return () => clearInterval(intervalId);
  }, [fetchPerformanceData, isOnline]);

  // Format bytes into human-readable format
  const formatBytes = (bytes: number, decimals = 2): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  // Format uptime into days, hours, minutes
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / (24 * 60 * 60));
    const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60));
    const minutes = Math.floor((seconds % (60 * 60)) / 60);
    
    const parts = [];
    if (days > 0) parts.push(`${days} day${days !== 1 ? 's' : ''}`);
    if (hours > 0) parts.push(`${hours} hour${hours !== 1 ? 's' : ''}`);
    if (minutes > 0) parts.push(`${minutes} minute${minutes !== 1 ? 's' : ''}`);
    
    return parts.join(', ');
  };

  // Get status color
  const getStatusColor = (status: ServiceStats['status']) => {
    switch (status) {
      case 'operational':
        return 'bg-green-900 bg-opacity-30 text-green-400';
      case 'degraded':
        return 'bg-yellow-900 bg-opacity-30 text-yellow-400';
      case 'outage':
        return 'bg-red-900 bg-opacity-30 text-red-400';
      case 'maintenance':
        return 'bg-blue-900 bg-opacity-30 text-blue-400';
      default:
        return 'bg-gray-800 text-gray-400';
    }
  };

  // Get usage color based on percentage
  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-600';
    if (percentage >= 75) return 'bg-yellow-600';
    if (percentage >= 50) return 'bg-blue-600';
    return 'bg-green-600';
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Resource usage progress bar
  const ResourceUsageBar: React.FC<{ percentage: number }> = ({ percentage }) => {
    return (
      <div className="w-full h-2 bg-gray-800 rounded-full">
        <div 
          className={`h-2 rounded-full ${getUsageColor(percentage)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  };

  // Restart service handler
  const handleRestartService = async (serviceName: string) => {
    if (!isOnline) {
      dispatch(addNotification({
        type: 'error',
        message: 'Cannot restart services while offline.',
        timestamp: new Date().toISOString(),
        read: false
      }));
      return;
    }
    
    try {
      // Show pending notification
      dispatch(addNotification({
        type: 'info',
        message: `Restarting service ${serviceName}...`,
        timestamp: new Date().toISOString(),
        read: false
      }));
      
      await adminService.restartService(serviceName);
      
      // Show success notification
      dispatch(addNotification({
        type: 'success',
        message: `Service ${serviceName} restart initiated successfully.`,
        timestamp: new Date().toISOString(),
        read: false
      }));
      
      // Refresh after a short delay to show updated status
      setTimeout(() => {
        fetchPerformanceData(true);
      }, 3000);
    } catch (error) {
      handleError(error, dispatch, `restarting service ${serviceName}`);
    }
  };

  return (
    <AdminErrorBoundary>
      <Card title="System Performance" className="min-h-[400px]">
      <div className="absolute top-3 right-3">
        <button 
          className="p-1.5 rounded-md text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          onClick={onClose}
        >
          <FiX size={20} />
        </button>
      </div>

      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-400">
          {performanceData ? (
            <span>Last updated: {formatTimestamp(performanceData.timestamp)}</span>
          ) : (
            <span>Loading data...</span>
          )}
        </div>
        
        <Button 
          variant="secondary" 
          leftIcon={<FiRefreshCw className={refreshingData ? 'animate-spin' : ''} />}
          onClick={() => fetchPerformanceData(true)}
          disabled={refreshingData}
        >
          {refreshingData ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>
      
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="large" />
        </div>
      ) : !isOnline && !performanceData ? (
        <div className="text-center py-12">
          <FiWifiOff className="mx-auto text-4xl text-gray-500 mb-3" />
          <h3 className="text-xl font-medium text-gray-300">You&apos;re offline</h3>
          <p className="text-gray-400 mt-1">Connect to the internet to view system performance</p>
          <Button 
            variant="primary" 
            size="sm" 
            className="mt-4"
            onClick={() => fetchPerformanceData(true)}
            leftIcon={<FiRefreshCw />}
          >
            Try Again
          </Button>
        </div>
      ) : !performanceData ? (
        <div className="text-center py-12">
          <FiActivity className="mx-auto text-4xl text-gray-500 mb-3" />
          <h3 className="text-xl font-medium text-gray-300">No performance data available</h3>
          <p className="text-gray-400 mt-1">Try refreshing to fetch the latest data</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Server Stats */}
          <div>
            <h3 className="text-lg font-medium flex items-center mb-3">
              <FiServer className="mr-2 text-blue-400" />
              Server Resources
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* CPU Usage */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between mb-2">
                  <div className="flex items-center">
                    <FiCpu className="mr-2 text-blue-400" />
                    <span className="font-medium">CPU Usage</span>
                  </div>
                  <span className="text-lg font-semibold">
                    {performanceData.server.cpu.usage.toFixed(1)}%
                  </span>
                </div>
                <ResourceUsageBar percentage={performanceData.server.cpu.usage} />
                <div className="mt-2 text-sm text-gray-400">
                  <div>Cores: {performanceData.server.cpu.cores}</div>
                  <div>
                    Load: {performanceData.server.cpu.load.map(l => l.toFixed(2)).join(', ')}
                  </div>
                </div>
              </div>
              
              {/* Memory Usage */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between mb-2">
                  <div className="flex items-center">
                    <FiServer className="mr-2 text-green-400" />
                    <span className="font-medium">Memory Usage</span>
                  </div>
                  <span className="text-lg font-semibold">
                    {performanceData.server.memory.usage.toFixed(1)}%
                  </span>
                </div>
                <ResourceUsageBar percentage={performanceData.server.memory.usage} />
                <div className="mt-2 text-sm text-gray-400">
                  <div>
                    Used: {formatBytes(performanceData.server.memory.used)} / 
                    {formatBytes(performanceData.server.memory.total)}
                  </div>
                  <div>
                    Free: {formatBytes(performanceData.server.memory.free)}
                  </div>
                </div>
              </div>
              
              {/* Disk Usage */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between mb-2">
                  <div className="flex items-center">
                    <FiHardDrive className="mr-2 text-purple-400" />
                    <span className="font-medium">Disk Usage</span>
                  </div>
                  <span className="text-lg font-semibold">
                    {performanceData.server.disk.usage.toFixed(1)}%
                  </span>
                </div>
                <ResourceUsageBar percentage={performanceData.server.disk.usage} />
                <div className="mt-2 text-sm text-gray-400">
                  <div>
                    Used: {formatBytes(performanceData.server.disk.used)} / 
                    {formatBytes(performanceData.server.disk.total)}
                  </div>
                  <div>
                    Free: {formatBytes(performanceData.server.disk.free)}
                  </div>
                </div>
              </div>
              
              {/* Network */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <FiActivity className="mr-2 text-yellow-400" />
                  <span className="font-medium">Network Traffic</span>
                </div>
                <div className="text-sm text-gray-400 grid grid-cols-2 gap-2">
                  <div>RX: {formatBytes(performanceData.server.network.rx_bytes)}</div>
                  <div>TX: {formatBytes(performanceData.server.network.tx_bytes)}</div>
                  <div>RX Packets: {performanceData.server.network.rx_packets.toLocaleString()}</div>
                  <div>TX Packets: {performanceData.server.network.tx_packets.toLocaleString()}</div>
                  <div>RX Errors: {performanceData.server.network.rx_errors}</div>
                  <div>TX Errors: {performanceData.server.network.tx_errors}</div>
                </div>
              </div>
            </div>
            
            <div className="mt-2 text-sm text-gray-400">
              <span>Server uptime: {formatUptime(performanceData.server.uptime)}</span>
            </div>
          </div>
          
          {/* Database Stats */}
          <div>
            <h3 className="text-lg font-medium flex items-center mb-3">
              <FiDatabase className="mr-2 text-green-400" />
              Database Performance
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Connection Pool */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm font-medium mb-2">Connection Pool</div>
                <div className="text-xl font-semibold">
                  {performanceData.database.connections}
                </div>
                <div className="text-xs text-gray-400 mt-1">Active connections</div>
              </div>
              
              {/* Query Stats */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm font-medium mb-2">Query Performance</div>
                <div className="text-xl font-semibold">
                  {performanceData.database.query_execution_time.toFixed(2)} ms
                </div>
                <div className="text-xs text-gray-400 mt-1">Avg. execution time</div>
              </div>
              
              {/* Cache Hit Ratio */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm font-medium mb-2">Cache Hit Ratio</div>
                <div className="text-xl font-semibold">
                  {(performanceData.database.cache_hit_ratio * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-400 mt-1">Higher is better</div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm font-medium mb-2">Database Operations</div>
                <div className="text-sm text-gray-400 flex justify-between">
                  <span>Read ops: {performanceData.database.read_operations.toLocaleString()}</span>
                  <span>Write ops: {performanceData.database.write_operations.toLocaleString()}</span>
                </div>
                <div className="text-sm text-gray-400 flex justify-between mt-1">
                  <span>Active queries: {performanceData.database.active_queries}</span>
                  <span>Slow queries: {performanceData.database.slow_queries}</span>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-sm font-medium mb-2">Database Info</div>
                <div className="text-sm text-gray-400">
                  <div>Size: {formatBytes(performanceData.database.database_size)}</div>
                  {performanceData.database.replication_lag !== undefined && (
                    <div>Replication lag: {performanceData.database.replication_lag.toFixed(2)} seconds</div>
                  )}
                </div>
              </div>
            </div>
          </div>
          
          {/* Service Status */}
          <div>
            <h3 className="text-lg font-medium flex items-center mb-3">
              <FiActivity className="mr-2 text-purple-400" />
              Service Status
            </h3>
            
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-left text-gray-400 text-sm border-b border-gray-800">
                    <th className="pb-2 font-medium">Service</th>
                    <th className="pb-2 font-medium">Status</th>
                    <th className="pb-2 font-medium">Response Time</th>
                    <th className="pb-2 font-medium">Error Rate</th>
                    <th className="pb-2 font-medium">Instances</th>
                    <th className="pb-2 font-medium">Resource Usage</th>
                    <th className="pb-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {performanceData.services.map((service, index) => (
                    <tr 
                      key={index} 
                      className={`border-b border-gray-800 ${
                        service.status !== 'operational' ? 'bg-gray-850' : ''
                      }`}
                    >
                      <td className="py-3 pr-4">{service.name}</td>
                      <td className="py-3 pr-4">
                        <span className={`inline-block px-2 py-1 rounded-full text-xs ${getStatusColor(service.status)}`}>
                          {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        {service.response_time.toFixed(2)} ms
                      </td>
                      <td className="py-3 pr-4">
                        {(service.error_rate * 100).toFixed(2)}%
                      </td>
                      <td className="py-3 pr-4">
                        {service.instance_count}
                      </td>
                      <td className="py-3 pr-4 w-1/6">
                        <div className="flex items-center">
                          <div className="w-full mr-2">
                            <ResourceUsageBar percentage={service.resource_usage * 100} />
                          </div>
                          <span className="text-xs whitespace-nowrap">
                            {(service.resource_usage * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-3">
                        <Button 
                          variant="secondary" 
                          size="xs"
                          onClick={() => handleRestartService(service.name)}
                          disabled={service.status === 'maintenance'}
                        >
                          Restart
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </Card>
    </AdminErrorBoundary>
  );
};

export default SystemPerformance;