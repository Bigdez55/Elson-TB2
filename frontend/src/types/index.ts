// Auth types
export interface User {
  id: number;
  email: string;
  full_name?: string;
  risk_tolerance: string;
  trading_style: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Trading types
export enum TradeType {
  BUY = 'buy',
  SELL = 'sell'
}

export enum OrderType {
  MARKET = 'market',
  LIMIT = 'limit',
  STOP_LOSS = 'stop_loss',
  STOP_LIMIT = 'stop_limit'
}

export enum TradeStatus {
  PENDING = 'pending',
  FILLED = 'filled',
  PARTIALLY_FILLED = 'partially_filled',
  CANCELLED = 'cancelled',
  REJECTED = 'rejected'
}

export interface Trade {
  id: number;
  symbol: string;
  trade_type: TradeType;
  order_type: OrderType;
  quantity: number;
  price?: number;
  filled_quantity: number;
  filled_price?: number;
  status: TradeStatus;
  total_cost?: number;
  commission: number;
  fees: number;
  strategy?: string;
  notes?: string;
  is_paper_trade: boolean;
  created_at: string;
  executed_at?: string;
}

export interface TradeOrderRequest {
  symbol: string;
  trade_type: TradeType;
  order_type: OrderType;
  quantity: number;
  limit_price?: number;
  stop_price?: number;
  strategy?: string;
  notes?: string;
}

// Market data types
export interface Quote {
  symbol: string;
  open: number;
  high: number;
  low: number;
  price: number;
  volume: number;
  change?: number;
  change_percent?: number;
  previous_close?: number;
  source: string;
  timestamp?: string;
}

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  asset_type: string;
  exchange?: string;
  sector?: string;
  industry?: string;
  is_tradable: boolean;
}

// Portfolio types
export interface Holding {
  id: number;
  symbol: string;
  asset_type: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_gain_loss: number;
  unrealized_gain_loss_percentage: number;
  target_allocation_percentage?: number;
  current_allocation_percentage?: number;
}

export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  total_value: number;
  cash_balance: number;
  invested_amount: number;
  total_return: number;
  total_return_percentage: number;
  auto_rebalance: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface PortfolioSummary {
  portfolio: Portfolio;
  holdings: Holding[];
  total_positions: number;
  largest_position?: Holding;
  best_performer?: Holding;
  worst_performer?: Holding;
}

// API response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Trading stats
export interface TradingStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_profit_loss: number;
  average_profit_loss: number;
  largest_win: number;
  largest_loss: number;
  total_commission: number;
}