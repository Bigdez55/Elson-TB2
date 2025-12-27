import { store } from '../store/store';

// WebSocket Events
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  channel?: string;
}

export interface MarketDataUpdate {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
  bid?: number;
  ask?: number;
  last_trade_time?: string;
}

export interface OrderUpdate {
  order_id: string;
  status: string;
  symbol: string;
  trade_type: string;
  quantity: number;
  filled_quantity?: number;
  price?: number;
  filled_price?: number;
  timestamp: string;
  paper_trading: boolean;
}

export interface PositionUpdate {
  symbol: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  timestamp: string;
  paper_trading: boolean;
}

export interface PortfolioUpdate {
  total_value: number;
  cash_balance: number;
  day_pnl: number;
  day_pnl_percent: number;
  timestamp: string;
  paper_trading: boolean;
}

// WebSocket Configuration
interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  channels: string[];
  requireAuth: boolean;
}

// Default configuration
const DEFAULT_CONFIG: WebSocketConfig = {
  url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/v1/streaming/ws',
  reconnectInterval: 5000, // 5 seconds
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000, // 30 seconds
  channels: [],
  requireAuth: true,
};

export enum WebSocketStatus {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  ERROR = 'ERROR',
  RECONNECTING = 'RECONNECTING',
  AUTHENTICATED = 'AUTHENTICATED',
  AUTHORIZATION_FAILED = 'AUTHORIZATION_FAILED',
}

export interface WebSocketState {
  status: WebSocketStatus;
  lastConnected: Date | null;
  reconnectAttempts: number;
  error: string | null;
  subscribedChannels: Set<string>;
  pendingSubscriptions: Set<string>;
}

// Event handlers
export type WebSocketEventHandler = (data: any) => void;

export interface WebSocketEventHandlers {
  onMarketData?: WebSocketEventHandler;
  onOrderUpdate?: WebSocketEventHandler;
  onPositionUpdate?: WebSocketEventHandler;
  onPortfolioUpdate?: WebSocketEventHandler;
  onStatusChange?: (status: WebSocketStatus) => void;
  onError?: (error: string) => void;
  onMessage?: WebSocketEventHandler;
}

class SecureWebSocketService {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private state: WebSocketState;
  private eventHandlers: WebSocketEventHandlers = {};
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private connectionPromise: Promise<void> | null = null;
  private isAuthenticated = false;
  private authToken: string | null = null;

  constructor(config: Partial<WebSocketConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.state = {
      status: WebSocketStatus.DISCONNECTED,
      lastConnected: null,
      reconnectAttempts: 0,
      error: null,
      subscribedChannels: new Set(),
      pendingSubscriptions: new Set(),
    };
  }

  // Public API
  public async connect(): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = this._connect();
    return this.connectionPromise;
  }

  public disconnect(): void {
    this.isAuthenticated = false;
    this.connectionPromise = null;
    this.clearTimers();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.updateState({
      status: WebSocketStatus.DISCONNECTED,
      reconnectAttempts: 0,
    });
  }

  public subscribe(channel: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.isConnectedAndAuthenticated()) {
        this.state.pendingSubscriptions.add(channel);
        resolve(); // Will be processed when connected
        return;
      }

      this.sendMessage({
        type: 'subscribe',
        data: { channel },
        timestamp: new Date().toISOString(),
        channel,
      });

      // Simple acknowledgment - in production you'd wait for server confirmation
      setTimeout(() => {
        this.state.subscribedChannels.add(channel);
        resolve();
      }, 100);
    });
  }

  public unsubscribe(channel: string): Promise<void> {
    return new Promise((resolve) => {
      if (this.state.subscribedChannels.has(channel)) {
        this.sendMessage({
          type: 'unsubscribe',
          data: { channel },
          timestamp: new Date().toISOString(),
          channel,
        });
        this.state.subscribedChannels.delete(channel);
      }
      
      this.state.pendingSubscriptions.delete(channel);
      resolve();
    });
  }

  public subscribeToMarketData(symbols: string[]): Promise<void> {
    const channel = `market_data:${symbols.join(',')}`;
    return this.subscribe(channel);
  }

  public subscribeToOrderUpdates(mode: 'paper' | 'live'): Promise<void> {
    const channel = `orders:${mode}`;
    return this.subscribe(channel);
  }

  public subscribeToPortfolio(mode: 'paper' | 'live'): Promise<void> {
    const channel = `portfolio:${mode}`;
    return this.subscribe(channel);
  }

  public getState(): WebSocketState {
    return { ...this.state };
  }

  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN && this.isAuthenticated;
  }

  // Event handling
  public on(eventType: keyof WebSocketEventHandlers, handler: WebSocketEventHandler | ((status: WebSocketStatus) => void)): void {
    (this.eventHandlers as any)[eventType] = handler;
  }

  public off(eventType: keyof WebSocketEventHandlers): void {
    delete (this.eventHandlers as any)[eventType];
  }

  // Private methods
  private async _connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.updateState({ status: WebSocketStatus.CONNECTING });
        
        // Get auth token
        this.authToken = localStorage.getItem('token');
        if (this.config.requireAuth && !this.authToken) {
          throw new Error('Authentication token required but not found');
        }

        // Create WebSocket connection with auth parameters
        const wsUrl = this.buildWebSocketUrl();
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          this.updateState({
            status: WebSocketStatus.CONNECTED,
            lastConnected: new Date(),
            reconnectAttempts: 0,
            error: null,
          });

          this.startHeartbeat();
          
          // Authenticate if required
          if (this.config.requireAuth) {
            this.authenticate();
          } else {
            this.onAuthenticationComplete();
            resolve();
          }
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
            
            // Resolve connection promise on successful auth
            if (message.type === 'auth_success' && this.connectionPromise) {
              this.onAuthenticationComplete();
              resolve();
            } else if (message.type === 'auth_failed') {
              this.isAuthenticated = false;
              this.updateState({ status: WebSocketStatus.AUTHORIZATION_FAILED });
              reject(new Error('WebSocket authentication failed'));
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
            this.eventHandlers.onError?.('Failed to parse message');
          }
        };

        this.ws.onclose = (event) => {
          this.isAuthenticated = false;
          this.clearTimers();
          
          if (event.wasClean) {
            this.updateState({ status: WebSocketStatus.DISCONNECTED });
          } else {
            this.updateState({
              status: WebSocketStatus.ERROR,
              error: `Connection lost: ${event.reason}`,
            });
            this.handleReconnection();
          }
          
          if (this.connectionPromise && !this.isAuthenticated) {
            reject(new Error(`WebSocket connection failed: ${event.reason}`));
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.updateState({
            status: WebSocketStatus.ERROR,
            error: 'WebSocket connection error',
          });
          reject(new Error('WebSocket connection error'));
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private buildWebSocketUrl(): string {
    const url = new URL(this.config.url);
    
    // Add auth token as query parameter for initial handshake
    if (this.authToken) {
      url.searchParams.set('token', this.authToken);
    }
    
    // Add client info
    url.searchParams.set('client', 'web');
    url.searchParams.set('version', '1.0');
    
    return url.toString();
  }

  private authenticate(): void {
    if (!this.authToken) {
      this.updateState({ status: WebSocketStatus.AUTHORIZATION_FAILED });
      return;
    }

    this.sendMessage({
      type: 'authenticate',
      data: { token: this.authToken },
      timestamp: new Date().toISOString(),
    });
  }

  private onAuthenticationComplete(): void {
    this.isAuthenticated = true;
    this.updateState({ status: WebSocketStatus.AUTHENTICATED });
    this.connectionPromise = null;
    
    // Process pending subscriptions
    this.state.pendingSubscriptions.forEach(channel => {
      this.subscribe(channel);
    });
    this.state.pendingSubscriptions.clear();
  }

  private handleMessage(message: WebSocketMessage): void {
    // Call general message handler
    this.eventHandlers.onMessage?.(message);

    // Handle specific message types
    switch (message.type) {
      case 'market_data':
        this.eventHandlers.onMarketData?.(message.data as MarketDataUpdate);
        break;
      
      case 'order_update':
        this.eventHandlers.onOrderUpdate?.(message.data as OrderUpdate);
        break;
      
      case 'position_update':
        this.eventHandlers.onPositionUpdate?.(message.data as PositionUpdate);
        break;
      
      case 'portfolio_update':
        this.eventHandlers.onPortfolioUpdate?.(message.data as PortfolioUpdate);
        break;
      
      case 'error':
        this.eventHandlers.onError?.(message.data.message || 'Unknown error');
        break;
      
      case 'pong':
        // Heartbeat response - connection is alive
        break;
      
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }

  private sendMessage(message: WebSocketMessage): boolean {
    if (!this.isConnectedAndAuthenticated()) {
      console.warn('Cannot send message: WebSocket not connected or authenticated');
      return false;
    }

    try {
      this.ws!.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.sendMessage({
        type: 'ping',
        data: {},
        timestamp: new Date().toISOString(),
      });
    }, this.config.heartbeatInterval);
  }

  private handleReconnection(): void {
    if (this.state.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.updateState({
        status: WebSocketStatus.ERROR,
        error: 'Max reconnection attempts reached',
      });
      return;
    }

    this.updateState({
      status: WebSocketStatus.RECONNECTING,
      reconnectAttempts: this.state.reconnectAttempts + 1,
    });

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
        this.handleReconnection();
      });
    }, this.config.reconnectInterval);
  }

  private clearTimers(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private updateState(updates: Partial<WebSocketState>): void {
    this.state = { ...this.state, ...updates };
    
    // Notify status change handler
    if (updates.status) {
      this.eventHandlers.onStatusChange?.(updates.status);
    }
  }

  private isConnectedAndAuthenticated(): boolean {
    return this.ws?.readyState === WebSocket.OPEN && 
           (this.isAuthenticated || !this.config.requireAuth);
  }
}

// Singleton instance
export const webSocketService = new SecureWebSocketService();

// Convenience methods for Redux integration
export const connectWebSocket = () => webSocketService.connect();
export const disconnectWebSocket = () => webSocketService.disconnect();

export default webSocketService;