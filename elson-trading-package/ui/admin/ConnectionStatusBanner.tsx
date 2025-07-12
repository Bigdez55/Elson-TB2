import React from 'react';
import { FiWifi, FiWifiOff, FiRefreshCw } from 'react-icons/fi';
import Button from '../common/Button';
import useConnectionStatus from '../../hooks/useConnectionStatus';

interface ConnectionStatusBannerProps {
  onRetry?: () => void;
}

const ConnectionStatusBanner: React.FC<ConnectionStatusBannerProps> = ({ 
  onRetry 
}) => {
  const { 
    isOnline, 
    isOffline, 
    isReconnecting, 
    reconnectAttempts,
    attemptReconnect 
  } = useConnectionStatus();
  
  // Do not render if online
  if (isOnline) return null;
  
  const handleRetry = () => {
    attemptReconnect();
    if (onRetry) {
      onRetry();
    }
  };

  return (
    <div className={`py-2 px-4 text-sm flex items-center justify-between
      ${isOffline ? 'bg-red-900 bg-opacity-60 text-red-200' : ''}
      ${isReconnecting ? 'bg-yellow-900 bg-opacity-60 text-yellow-200' : ''}
    `}>
      <div className="flex items-center">
        {isOffline && <FiWifiOff className="mr-2" />}
        {isReconnecting && <FiWifi className="mr-2 animate-pulse" />}
        
        <span>
          {isOffline && "You're currently offline. Some features may be unavailable."}
          {isReconnecting && `Attempting to reconnect (Attempt ${reconnectAttempts})...`}
        </span>
      </div>
      
      <Button
        variant="outline"
        size="xs"
        onClick={handleRetry}
        leftIcon={<FiRefreshCw className={isReconnecting ? 'animate-spin' : ''} />}
      >
        {isReconnecting ? 'Reconnecting...' : 'Retry Connection'}
      </Button>
    </div>
  );
};

export default ConnectionStatusBanner;