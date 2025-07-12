import React, { useState, useEffect, useCallback } from 'react';
import { 
  FiList, FiSearch, FiRefreshCw, FiDownload, 
  FiInfo, FiAlertTriangle, FiAlertCircle, FiX, FiWifiOff 
} from 'react-icons/fi';
import Card from '../common/Card';
import Button from '../common/Button';
import Input from '../common/Input';
import Select from '../common/Select';
import LoadingSpinner from '../common/LoadingSpinner';
import adminService from '../../services/adminService';
import { useDispatch } from 'react-redux';
import { addNotification } from '../../store/slices/notificationsSlice';
import AdminErrorBoundary from './AdminErrorBoundary';
import { handleError } from '../../utils/errorHandling';
import useConnectionStatus from '../../hooks/useConnectionStatus';

interface LogEntry {
  id: string;
  timestamp: string;
  service: string;
  severity: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  message: string;
  details?: any;
}

interface LogFilterOptions {
  service: string;
  severity: string;
  search: string;
  limit: number;
}

const SystemLogs: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshingData, setRefreshingData] = useState<boolean>(false);
  const [services, setServices] = useState<string[]>([]);
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  const [filterOptions, setFilterOptions] = useState<LogFilterOptions>({
    service: '',
    severity: '',
    search: '',
    limit: 100
  });

  const dispatch = useDispatch();

  // Connection status hook to handle offline/online states
  const { isOnline, status: connectionStatus } = useConnectionStatus({
    onStatusChange: (status) => {
      if (status === 'online' && connectionStatus === 'offline') {
        // Auto-refresh data when coming back online
        fetchLogs(true);
      }
    }
  });

  // Fetch logs
  const fetchLogs = useCallback(async (forceRefresh = false) => {
    if (refreshingData && !forceRefresh) return;
    
    // Don't try to fetch if we're offline
    if (!isOnline && !forceRefresh) {
      dispatch(addNotification({
        type: 'warning',
        message: 'You appear to be offline. Using cached logs.',
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
      const logs = await adminService.getSystemLogs(
        filterOptions.service !== '' ? filterOptions.service : undefined,
        filterOptions.severity !== '' ? filterOptions.severity : undefined,
        filterOptions.limit
      );
      
      // Parse logs and extract unique services
      setLogs(logs);
      const uniqueServices = [...new Set(logs.map(log => log.service))];
      setServices(uniqueServices);
      
      if (forceRefresh) {
        dispatch(addNotification({
          type: 'success',
          message: 'System logs refreshed successfully.',
          timestamp: new Date().toISOString(),
          read: false
        }));
      }
    } catch (error) {
      handleError(error, dispatch, 'fetching system logs');
      
      // Show a recoverable error UI if there's no data yet
      if (logs.length === 0) {
        dispatch(addNotification({
          type: 'error',
          message: 'Failed to load system logs. Please try again.',
          timestamp: new Date().toISOString(),
          read: false
        }));
      }
    } finally {
      setLoading(false);
      setRefreshingData(false);
    }
  }, [dispatch, filterOptions, refreshingData, isOnline, logs.length]);

  // Fetch logs on mount and when filter options change
  useEffect(() => {
    fetchLogs();
  }, [fetchLogs, filterOptions.service, filterOptions.severity, filterOptions.limit]);

  // Filter logs based on search
  const filteredLogs = logs.filter(log => {
    if (!filterOptions.search) return true;
    
    const search = filterOptions.search.toLowerCase();
    return (
      log.message.toLowerCase().includes(search) ||
      log.service.toLowerCase().includes(search) ||
      (log.details && JSON.stringify(log.details).toLowerCase().includes(search))
    );
  });

  // Handle filter changes
  const handleFilterChange = <K extends keyof LogFilterOptions>(
    name: K, 
    value: LogFilterOptions[K]
  ) => {
    setFilterOptions(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Get severity badge
  const getSeverityBadge = (severity: LogEntry['severity']) => {
    switch (severity) {
      case 'debug':
        return 'bg-gray-800 text-gray-300';
      case 'info':
        return 'bg-blue-900 bg-opacity-30 text-blue-400';
      case 'warning':
        return 'bg-yellow-900 bg-opacity-30 text-yellow-400';
      case 'error':
        return 'bg-red-900 bg-opacity-30 text-red-400';
      case 'critical':
        return 'bg-red-900 bg-opacity-50 text-red-300 font-medium';
      default:
        return 'bg-gray-800 text-gray-400';
    }
  };

  // Get severity icon
  const getSeverityIcon = (severity: LogEntry['severity']) => {
    switch (severity) {
      case 'debug':
        return <FiInfo className="text-gray-400" />;
      case 'info':
        return <FiInfo className="text-blue-400" />;
      case 'warning':
        return <FiAlertTriangle className="text-yellow-400" />;
      case 'error':
      case 'critical':
        return <FiAlertCircle className="text-red-400" />;
      default:
        return <FiInfo className="text-gray-400" />;
    }
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

  // Toggle log expansion
  const toggleLogExpansion = (logId: string) => {
    setExpandedLog(expandedLog === logId ? null : logId);
  };

  return (
    <AdminErrorBoundary>
      <Card title="System Logs" className="min-h-[400px]">
      <div className="absolute top-3 right-3">
        <button 
          className="p-1.5 rounded-md text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          onClick={onClose}
        >
          <FiX size={20} />
        </button>
      </div>

      <div className="flex flex-wrap gap-4 mb-4">
        <div className="flex-grow min-w-[240px]">
          <Input
            placeholder="Search logs..."
            value={filterOptions.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            startIcon={<FiSearch />}
            fullWidth
          />
        </div>
        
        <div className="flex space-x-2">
          <Button 
            variant="secondary" 
            leftIcon={<FiRefreshCw className={refreshingData ? 'animate-spin' : ''} />}
            onClick={() => fetchLogs(true)}
            disabled={refreshingData}
          >
            {refreshingData ? 'Refreshing...' : 'Refresh'}
          </Button>
          
          <Button 
            variant="outline" 
            leftIcon={<FiDownload />}
          >
            Export Logs
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <Select
          label="Service"
          placeholder="All Services"
          options={[
            { value: '', label: 'All Services' },
            ...services.map(service => ({ value: service, label: service }))
          ]}
          value={filterOptions.service}
          onChange={(value) => handleFilterChange('service', value)}
        />
        
        <Select
          label="Severity"
          placeholder="All Levels"
          options={[
            { value: '', label: 'All Levels' },
            { value: 'debug', label: 'Debug' },
            { value: 'info', label: 'Info' },
            { value: 'warning', label: 'Warning' },
            { value: 'error', label: 'Error' },
            { value: 'critical', label: 'Critical' }
          ]}
          value={filterOptions.severity}
          onChange={(value) => handleFilterChange('severity', value)}
        />
        
        <Select
          label="Limit"
          options={[
            { value: '50', label: 'Last 50 entries' },
            { value: '100', label: 'Last 100 entries' },
            { value: '200', label: 'Last 200 entries' },
            { value: '500', label: 'Last 500 entries' }
          ]}
          value={filterOptions.limit.toString()}
          onChange={(value) => handleFilterChange('limit', parseInt(value))}
        />
      </div>
      
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="large" />
        </div>
      ) : !isOnline && logs.length === 0 ? (
        <div className="text-center py-12">
          <FiWifiOff className="mx-auto text-4xl text-gray-500 mb-3" />
          <h3 className="text-xl font-medium text-gray-300">You&apos;re offline</h3>
          <p className="text-gray-400 mt-1">Connect to the internet to view system logs</p>
          <Button 
            variant="primary" 
            size="sm" 
            className="mt-4"
            onClick={() => fetchLogs(true)}
            leftIcon={<FiRefreshCw />}
          >
            Try Again
          </Button>
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="text-center py-12">
          <FiList className="mx-auto text-4xl text-gray-500 mb-3" />
          <h3 className="text-xl font-medium text-gray-300">No logs found</h3>
          <p className="text-gray-400 mt-1">Try adjusting your search or filter criteria</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredLogs.map((log) => (
            <div 
              key={log.id} 
              className="border border-gray-800 rounded-lg overflow-hidden"
            >
              <div 
                className={`p-3 cursor-pointer ${expandedLog === log.id ? 'bg-gray-800' : 'hover:bg-gray-850'}`}
                onClick={() => toggleLogExpansion(log.id)}
              >
                <div className="flex flex-wrap justify-between items-start gap-2">
                  <div className="flex items-start">
                    <div className="mr-3 mt-1">{getSeverityIcon(log.severity)}</div>
                    <div>
                      <div className="font-medium">{log.message}</div>
                      <div className="text-sm text-gray-400 mt-1">
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs mr-2 ${getSeverityBadge(log.severity)}`}>
                          {log.severity.toUpperCase()}
                        </span>
                        <span className="mr-2">{log.service}</span>
                        <span>{formatTimestamp(log.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {expandedLog === log.id && log.details && (
                <div className="p-3 border-t border-gray-800 bg-gray-850">
                  <div className="text-sm font-medium text-gray-300 mb-1">Details:</div>
                  <pre className="text-xs text-gray-400 bg-gray-800 p-3 rounded overflow-auto">
                    {JSON.stringify(log.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
    </AdminErrorBoundary>
  );
};

export default SystemLogs;