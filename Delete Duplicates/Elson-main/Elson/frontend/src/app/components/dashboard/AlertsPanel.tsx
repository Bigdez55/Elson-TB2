import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchAlerts, dismissAlert } from '../../store/slices/alertsSlice';
import { formatDateTime } from '../../utils/formatters';
import Button from '../common/Button';

interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
  read: boolean;
  symbol?: string;
}

const AlertCard: React.FC<{ alert: Alert; onDismiss: (id: string) => void }> = ({
  alert,
  onDismiss,
}) => {
  const bgColorClass = {
    info: 'bg-blue-900/50',
    warning: 'bg-yellow-900/50',
    error: 'bg-red-900/50',
    success: 'bg-green-900/50',
  }[alert.type];

  const iconClass = {
    info: 'info-circle',
    warning: 'exclamation-triangle',
    error: 'exclamation-circle',
    success: 'check-circle',
  }[alert.type];

  return (
    <div className={`p-4 rounded-lg mb-3 ${bgColorClass} relative ${!alert.read ? 'border-l-4 border-primary-500' : ''}`}>
      <div className="flex justify-between items-start">
        <div className="flex items-start space-x-3">
          <div className={`mt-1 ${
            alert.type === 'error' ? 'text-red-400' :
            alert.type === 'warning' ? 'text-yellow-400' :
            alert.type === 'success' ? 'text-green-400' :
            'text-blue-400'
          }`}>
            <i className={`fas fa-${iconClass} text-lg`}></i>
          </div>
          <div>
            <p className="font-medium">{alert.message}</p>
            <div className="flex items-center mt-1 space-x-2 text-sm text-gray-400">
              <span>{formatDateTime(alert.timestamp)}</span>
              {alert.symbol && (
                <>
                  <span>•</span>
                  <span>{alert.symbol}</span>
                </>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={() => onDismiss(alert.id)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <i className="fas fa-times"></i>
        </button>
      </div>
    </div>
  );
};

const AlertsPanel: React.FC = () => {
  const dispatch = useDispatch();
  const { alerts, loading, error } = useSelector((state: any) => state.alerts);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    dispatch(fetchAlerts());

    // Poll for new alerts
    const interval = setInterval(() => {
      dispatch(fetchAlerts());
    }, 30000);

    return () => clearInterval(interval);
  }, [dispatch]);

  const handleDismiss = (alertId: string) => {
    dispatch(dismissAlert(alertId));
  };

  const handleDismissAll = () => {
    alerts.forEach((alert: Alert) => {
      dispatch(dismissAlert(alert.id));
    });
  };

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter((alert: Alert) => !alert.read);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Alerts</h2>
        <div className="flex space-x-2">
          <Button
            variant={filter === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All
          </Button>
          <Button
            variant={filter === 'unread' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter('unread')}
          >
            Unread
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDismissAll}
          >
            Dismiss All
          </Button>
        </div>
      </div>

      {loading && alerts.length === 0 ? (
        <div className="text-gray-400 text-center py-8">Loading alerts...</div>
      ) : error ? (
        <div className="text-red-500 text-center py-8">Error loading alerts: {error}</div>
      ) : filteredAlerts.length === 0 ? (
        <div className="text-gray-400 text-center py-8">No alerts to display</div>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert: Alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onDismiss={handleDismiss}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertsPanel;