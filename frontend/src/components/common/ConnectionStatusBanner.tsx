import React, { useState, useEffect } from 'react';
import { useAppSelector } from '../../store/hooks';
import { selectWebSocketStatus, selectConnectionError, selectIsConnected } from '../../store/slices/websocketSlice';
import { WebSocketStatus } from '../../services/websocketService';
import { WebSocketIndicator } from './WebSocketStatus';

interface ConnectionStatusBannerProps {
  className?: string;
  showWhenConnected?: boolean;
  autoHide?: boolean;
  autoHideDelay?: number;
}

export const ConnectionStatusBanner: React.FC<ConnectionStatusBannerProps> = ({
  className = '',
  showWhenConnected = false,
  autoHide = true,
  autoHideDelay = 3000,
}) => {
  const status = useAppSelector(selectWebSocketStatus);
  const error = useAppSelector(selectConnectionError);
  const isConnected = useAppSelector(selectIsConnected);
  const [isVisible, setIsVisible] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);

  // Auto-hide logic for successful connections
  useEffect(() => {
    if (autoHide && isConnected && status === WebSocketStatus.AUTHENTICATED) {
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, autoHideDelay);

      return () => clearTimeout(timer);
    }
  }, [autoHide, autoHideDelay, isConnected, status]);

  // Reset visibility when status changes to non-connected states
  useEffect(() => {
    if (!isConnected) {
      setIsVisible(true);
      setIsMinimized(false);
    }
  }, [isConnected]);

  // Don't show banner for certain states
  const shouldShow = () => {
    // Always hide if not visible
    if (!isVisible) return false;

    // Hide when connected if showWhenConnected is false
    if (isConnected && !showWhenConnected) return false;

    // Show for all non-disconnected states
    return status !== WebSocketStatus.DISCONNECTED;
  };

  const getBannerStyle = () => {
    switch (status) {
      case WebSocketStatus.AUTHENTICATED:
        return {
          bg: 'bg-green-900',
          border: 'border-green-600',
          text: 'text-green-100',
          icon: 'text-green-400',
        };
      case WebSocketStatus.CONNECTED:
        return {
          bg: 'bg-yellow-900',
          border: 'border-yellow-600',
          text: 'text-yellow-100',
          icon: 'text-yellow-400',
        };
      case WebSocketStatus.CONNECTING:
        return {
          bg: 'bg-blue-900',
          border: 'border-blue-600',
          text: 'text-blue-100',
          icon: 'text-blue-400',
        };
      case WebSocketStatus.RECONNECTING:
        return {
          bg: 'bg-orange-900',
          border: 'border-orange-600',
          text: 'text-orange-100',
          icon: 'text-orange-400',
        };
      case WebSocketStatus.ERROR:
      case WebSocketStatus.AUTHORIZATION_FAILED:
        return {
          bg: 'bg-red-900',
          border: 'border-red-600',
          text: 'text-red-100',
          icon: 'text-red-400',
        };
      default:
        return {
          bg: 'bg-gray-900',
          border: 'border-gray-600',
          text: 'text-gray-100',
          icon: 'text-gray-400',
        };
    }
  };

  const getStatusMessage = () => {
    switch (status) {
      case WebSocketStatus.AUTHENTICATED:
        return 'Connected to live market data';
      case WebSocketStatus.CONNECTED:
        return 'Connected, authenticating...';
      case WebSocketStatus.CONNECTING:
        return 'Connecting to market data...';
      case WebSocketStatus.RECONNECTING:
        return 'Connection lost, reconnecting...';
      case WebSocketStatus.AUTHORIZATION_FAILED:
        return 'Authentication failed. Please refresh and sign in again.';
      case WebSocketStatus.ERROR:
        return error || 'Connection error occurred';
      default:
        return 'Market data unavailable';
    }
  };

  const handleDismiss = () => {
    setIsVisible(false);
  };

  const handleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  if (!shouldShow()) {
    return null;
  }

  const style = getBannerStyle();

  return (
    <div className={`fixed top-0 left-0 right-0 z-50 ${style.bg} ${style.border} border-b transition-all duration-300 ${isMinimized ? 'py-1' : 'py-2'} ${className}`}>
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between">
          {/* Status content */}
          <div className="flex items-center space-x-3">
            <WebSocketIndicator status={status} size="md" className={style.icon} />
            
            {!isMinimized && (
              <div className="flex-1">
                <div className={`text-sm font-medium ${style.text}`}>
                  {getStatusMessage()}
                </div>
                {error && status === WebSocketStatus.ERROR && !isMinimized && (
                  <div className="text-xs opacity-75 mt-1">
                    {error}
                  </div>
                )}
              </div>
            )}

            {isMinimized && (
              <div className={`text-xs font-medium ${style.text}`}>
                Market Data: {isConnected ? 'Live' : 'Offline'}
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-2">
            {/* Minimize/Expand button */}
            <button
              onClick={handleMinimize}
              className={`${style.text} hover:opacity-75 transition-opacity`}
              title={isMinimized ? 'Expand' : 'Minimize'}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMinimized ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                )}
              </svg>
            </button>

            {/* Dismiss button (only for successful connections or errors) */}
            {(isConnected || status === WebSocketStatus.ERROR) && (
              <button
                onClick={handleDismiss}
                className={`${style.text} hover:opacity-75 transition-opacity`}
                title="Dismiss"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Additional info for errors */}
        {status === WebSocketStatus.AUTHORIZATION_FAILED && !isMinimized && (
          <div className="mt-2 text-xs opacity-75">
            This may be due to an expired session or network issues. Try refreshing the page.
          </div>
        )}
      </div>
    </div>
  );
};

// Compact status indicator for toolbar/navbar
export const CompactConnectionStatus: React.FC<{ className?: string }> = ({ 
  className = '' 
}) => {
  const status = useAppSelector(selectWebSocketStatus);
  const isConnected = useAppSelector(selectIsConnected);

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <WebSocketIndicator status={status} size="sm" />
      <span className="text-xs text-gray-400">
        {isConnected ? 'Live' : 'Offline'}
      </span>
    </div>
  );
};

export default ConnectionStatusBanner;