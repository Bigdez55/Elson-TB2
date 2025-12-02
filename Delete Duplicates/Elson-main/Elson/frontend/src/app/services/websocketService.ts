import { io, Socket } from 'socket.io-client';
import { store } from '../store/store';
import { updateMarketData, updateOrderBook } from '../store/slices/marketSlice';
import { updateOrder, updatePosition } from '../store/slices/tradingSlice';
import { addNotification } from '../store/slices/notificationsSlice';
import { triggerAlert } from '../store/slices/alertsSlice';
import config from '../core/config';

class WebSocketService {
  private socket: Socket | null = null;
  private subscriptions: Set<string> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect() {
    if (this.socket?.connected) return;

    this.socket = io(config.websocketUrl, {
      auth: {
        token: localStorage.getItem('token'),
      },
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers() {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', this.handleConnect);
    this.socket.on('disconnect', this.handleDisconnect);
    this.socket.on('error', this.handleError);

    // Market data events
    this.socket.on('ticker', this.handleTickerUpdate);
    this.socket.on('orderbook', this.handleOrderBookUpdate);
    this.socket.on('trade', this.handleTradeUpdate);

    // Trading events
    this.socket.on('order', this.handleOrderUpdate);
    this.socket.on('position', this.handlePositionUpdate);
    this.socket.on('alert', this.handleAlertTrigger);
  }

  private handleConnect = () => {
    this.reconnectAttempts = 0;
    this.resubscribe();
  };

  private handleDisconnect = (reason: string) => {
    console.warn('WebSocket disconnected:', reason);
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
    }
  };

  private handleError = (error: Error) => {
    console.error('WebSocket error:', error);
    store.dispatch(
      addNotification({
        type: 'error',
        message: 'WebSocket connection error',
        timestamp: new Date().toISOString(),
      })
    );
  };

  private handleTickerUpdate = (data: any) => {
    store.dispatch(updateMarketData(data));
  };

  private handleOrderBookUpdate = (data: any) => {
    store.dispatch(updateOrderBook(data));
  };

  private handleTradeUpdate = (data: any) => {
    // Handle incoming trade data
  };

  private handleOrderUpdate = (data: any) => {
    store.dispatch(updateOrder(data));
    if (data.status === 'FILLED' || data.status === 'CANCELED') {
      store.dispatch(
        addNotification({
          type: data.status === 'FILLED' ? 'success' : 'info',
          message: `Order ${data.id} ${data.status.toLowerCase()}`,
          timestamp: new Date().toISOString(),
        })
      );
    }
  };

  private handlePositionUpdate = (data: any) => {
    store.dispatch(updatePosition(data));
  };

  private handleAlertTrigger = (data: any) => {
    store.dispatch(triggerAlert(data));
    store.dispatch(
      addNotification({
        type: 'warning',
        message: `Alert triggered: ${data.message}`,
        timestamp: new Date().toISOString(),
      })
    );
  };

  subscribe(channel: string, params?: any) {
    if (!this.socket?.connected) {
      this.connect();
    }
    const subscriptionKey = params ? `${channel}:${JSON.stringify(params)}` : channel;
    if (!this.subscriptions.has(subscriptionKey)) {
      this.socket?.emit('subscribe', { channel, ...params });
      this.subscriptions.add(subscriptionKey);
    }
  }

  unsubscribe(channel: string, params?: any) {
    const subscriptionKey = params ? `${channel}:${JSON.stringify(params)}` : channel;
    if (this.subscriptions.has(subscriptionKey)) {
      this.socket?.emit('unsubscribe', { channel, ...params });
      this.subscriptions.delete(subscriptionKey);
    }
  }

  private resubscribe() {
    this.subscriptions.forEach(subscriptionKey => {
      const [channel, paramsStr] = subscriptionKey.split(':');
      const params = paramsStr ? JSON.parse(paramsStr) : undefined;
      this.socket?.emit('subscribe', { channel, ...params });
    });
  }

  disconnect() {
    this.subscriptions.clear();
    this.socket?.disconnect();
    this.socket = null;
  }
}

export const wsService = new WebSocketService();
export default wsService;