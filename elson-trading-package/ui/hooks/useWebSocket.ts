import { useEffect, useCallback } from 'react';
import wsService from '../services/websocketService';

interface WebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export const useWebSocket = (
  channels: string | string[],
  params?: Record<string, any>,
  options: WebSocketOptions = {}
) => {
  const channelsArray = Array.isArray(channels) ? channels : [channels];

  useEffect(() => {
    // Subscribe to all channels
    channelsArray.forEach(channel => {
      wsService.subscribe(channel, params);
    });

    // Cleanup on unmount
    return () => {
      channelsArray.forEach(channel => {
        wsService.unsubscribe(channel, params);
      });
    };
  }, [JSON.stringify(channelsArray), JSON.stringify(params)]);

  const reconnect = useCallback(() => {
    wsService.connect();
  }, []);

  return {
    reconnect,
  };
};

export default useWebSocket;