import { useState, useEffect, useCallback } from 'react';

type ConnectionStatus = 'online' | 'offline' | 'reconnecting';

interface ConnectionStatusOptions {
  onStatusChange?: (status: ConnectionStatus) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

/**
 * Hook to monitor network connection status and handle reconnection
 */
export function useConnectionStatus(options: ConnectionStatusOptions = {}) {
  const {
    onStatusChange,
    reconnectInterval = 5000,
    maxReconnectAttempts = 3
  } = options;
  
  const [status, setStatus] = useState<ConnectionStatus>(navigator.onLine ? 'online' : 'offline');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastOnlineTime, setLastOnlineTime] = useState<Date | null>(navigator.onLine ? new Date() : null);
  
  // Update status
  const updateStatus = useCallback((newStatus: ConnectionStatus) => {
    setStatus(newStatus);
    
    if (newStatus === 'online') {
      setLastOnlineTime(new Date());
      setReconnectAttempts(0);
    }
    
    if (onStatusChange) {
      onStatusChange(newStatus);
    }
  }, [onStatusChange]);

  // Check connection by fetching a tiny resource
  const checkConnection = useCallback(async () => {
    try {
      // Small image fetch to quickly test connectivity
      const timestamp = new Date().getTime();
      const response = await fetch(`/favicon.ico?${timestamp}`, {
        method: 'HEAD',
        cache: 'no-cache'
      });
      
      return response.ok;
    } catch (error) {
      return false;
    }
  }, []);

  // Attempt to reconnect
  const attemptReconnect = useCallback(async () => {
    if (status !== 'offline' && status !== 'reconnecting') return;
    
    updateStatus('reconnecting');
    
    if (reconnectAttempts >= maxReconnectAttempts) {
      // Give up after max attempts
      updateStatus('offline');
      return;
    }
    
    // Try to reconnect
    try {
      const isConnected = await checkConnection();
      
      if (isConnected) {
        updateStatus('online');
      } else {
        setReconnectAttempts(prev => prev + 1);
        setTimeout(attemptReconnect, reconnectInterval);
      }
    } catch (error) {
      setReconnectAttempts(prev => prev + 1);
      setTimeout(attemptReconnect, reconnectInterval);
    }
  }, [status, reconnectAttempts, maxReconnectAttempts, checkConnection, reconnectInterval, updateStatus]);

  // Handle online event
  const handleOnline = useCallback(() => {
    updateStatus('online');
  }, [updateStatus]);

  // Handle offline event
  const handleOffline = useCallback(async () => {
    // Double-check with fetch to confirm it's really offline
    // as the browser's online/offline events aren't always reliable
    const isReallyConnected = await checkConnection();
    
    if (!isReallyConnected) {
      updateStatus('offline');
      attemptReconnect();
    }
  }, [updateStatus, attemptReconnect, checkConnection]);

  // Set up event listeners
  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Initial check on mount
    if (!navigator.onLine) {
      attemptReconnect();
    }
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline, attemptReconnect]);

  return {
    status,
    isOnline: status === 'online',
    isOffline: status === 'offline',
    isReconnecting: status === 'reconnecting',
    reconnectAttempts,
    lastOnlineTime,
    checkConnection,
    attemptReconnect
  };
}

export default useConnectionStatus;