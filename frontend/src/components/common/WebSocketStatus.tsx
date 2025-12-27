import React from 'react';
import { WebSocketStatus as WSStatus } from '../../services/websocketService';

interface WebSocketStatusProps {
  status: WSStatus;
  lastConnected?: Date | null;
  reconnectAttempts?: number;
  error?: string | null;
  className?: string;
  showDetails?: boolean;
}

export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({
  status,
  lastConnected,
  reconnectAttempts = 0,
  error,
  className = '',
  showDetails = false,
}) => {
  const getStatusInfo = () => {
    switch (status) {
      case WSStatus.CONNECTED:
        return {
          text: 'Connected',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-900',
          icon: (
            <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          ),
        };
      case WSStatus.AUTHENTICATED:
        return {
          text: 'Live',
          color: 'text-green-400',
          bgColor: 'bg-green-900',
          icon: (
            <div className="h-3 w-3 bg-green-400 rounded-full animate-pulse" />
          ),
        };
      case WSStatus.CONNECTING:
        return {
          text: 'Connecting',
          color: 'text-blue-400',
          bgColor: 'bg-blue-900',
          icon: (
            <svg className="h-3 w-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          ),
        };
      case WSStatus.RECONNECTING:
        return {
          text: `Reconnecting (${reconnectAttempts})`,
          color: 'text-orange-400',
          bgColor: 'bg-orange-900',
          icon: (
            <svg className="h-3 w-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          ),
        };
      case WSStatus.AUTHORIZATION_FAILED:
        return {
          text: 'Auth Failed',
          color: 'text-red-400',
          bgColor: 'bg-red-900',
          icon: (
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m0 0v2m0-2h2m-2 0h-2M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
        };
      case WSStatus.ERROR:
        return {
          text: 'Error',
          color: 'text-red-400',
          bgColor: 'bg-red-900',
          icon: (
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ),
        };
      case WSStatus.DISCONNECTED:
      default:
        return {
          text: 'Offline',
          color: 'text-gray-400',
          bgColor: 'bg-gray-700',
          icon: (
            <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18.364 5.636l-12.728 12.728M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
            </svg>
          ),
        };
    }
  };

  const statusInfo = getStatusInfo();

  const formatLastConnected = (date: Date | null) => {
    if (!date) return 'Never';
    
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    return date.toLocaleDateString();
  };

  if (!showDetails) {
    return (
      <div className={`inline-flex items-center space-x-2 px-2 py-1 rounded-full text-xs font-medium bg-opacity-20 ${statusInfo.bgColor} ${statusInfo.color} ${className}`}>
        {statusInfo.icon}
        <span>{statusInfo.text}</span>
      </div>
    );
  }

  return (
    <div className={`bg-gray-800 rounded-lg p-3 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm font-medium">Connection Status</span>
        <div className={`inline-flex items-center space-x-2 px-2 py-1 rounded-full text-xs font-medium bg-opacity-20 ${statusInfo.bgColor} ${statusInfo.color}`}>
          {statusInfo.icon}
          <span>{statusInfo.text}</span>
        </div>
      </div>
      
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-500">Last Connected:</span>
          <span className="text-gray-300">{formatLastConnected(lastConnected || null)}</span>
        </div>
        
        {reconnectAttempts > 0 && (
          <div className="flex justify-between">
            <span className="text-gray-500">Reconnect Attempts:</span>
            <span className="text-gray-300">{reconnectAttempts}</span>
          </div>
        )}
        
        {error && (
          <div className="mt-2 p-2 bg-red-900 bg-opacity-20 border border-red-700 rounded">
            <div className="text-red-300 text-xs font-medium mb-1">Error Details:</div>
            <div className="text-red-400 text-xs break-words">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
};

interface WebSocketIndicatorProps {
  status: WSStatus;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const WebSocketIndicator: React.FC<WebSocketIndicatorProps> = ({
  status,
  className = '',
  size = 'sm',
}) => {
  const getIndicatorClass = () => {
    const baseClass = 'rounded-full border-2 border-gray-800';
    const sizeClass = {
      sm: 'h-2 w-2',
      md: 'h-3 w-3',
      lg: 'h-4 w-4',
    }[size];

    const statusClass = {
      [WSStatus.AUTHENTICATED]: 'bg-green-400 animate-pulse',
      [WSStatus.CONNECTED]: 'bg-yellow-400',
      [WSStatus.CONNECTING]: 'bg-blue-400 animate-pulse',
      [WSStatus.RECONNECTING]: 'bg-orange-400 animate-pulse',
      [WSStatus.AUTHORIZATION_FAILED]: 'bg-red-400',
      [WSStatus.ERROR]: 'bg-red-400',
      [WSStatus.DISCONNECTED]: 'bg-gray-500',
    }[status] || 'bg-gray-500';

    return `${baseClass} ${sizeClass} ${statusClass}`;
  };

  return (
    <div className={`${getIndicatorClass()} ${className}`} title={status} />
  );
};

export default WebSocketStatus;