// Backend API User interface
export interface User {
  id: number;
  email: string;
  full_name?: string;
  risk_tolerance: string;
  trading_style: string;
  is_active: boolean;
  is_verified: boolean;
  role?: string;
  created_at?: string;
  updated_at?: string;
}

// Auth state interface
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Backend API Asset interface
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

// Legacy Asset interface
export interface AssetLegacy {
  symbol: string;
  amount: number;
  currentPrice: number;
  averagePrice: number;
  totalValue: number;
}

// Backend API Trade interface
export interface Trade {
  id: number;
  symbol: string;
  trade_type: string;
  order_type: string;
  quantity: number;
  price?: number | null;
  status: string;
  created_at: string;
  updated_at?: string;
  executed_at?: string | null;
  executed_price?: number | null;
  notes?: string;
}

// Legacy Trade interface
export interface TradeLegacy {
  id: string;
  symbol: string;
  type: 'BUY' | 'SELL';
  amount: number;
  price: number;
  status: 'PENDING' | 'COMPLETED' | 'CANCELLED' | 'FAILED';
  timestamp: string;
  fee?: number;
}

// Backend API TradeOrderRequest interface
export interface TradeOrderRequest {
  symbol: string;
  trade_type: string;
  order_type: string;
  quantity: number;
  limit_price?: number;
  stop_price?: number;
  strategy?: string;
  notes?: string;
}

// Legacy OrderData interface
export interface OrderData {
  symbol: string;
  type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
  side: 'BUY' | 'SELL';
  amount: number;
  price?: number;
  stopPrice?: number;
}

// Backend API Portfolio interface
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

// Backend API Holding interface
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

// Backend API PortfolioSummary interface
export interface PortfolioSummary {
  portfolio: Portfolio;
  holdings: Holding[];
  total_positions: number;
  largest_position?: Holding;
  best_performer?: Holding;
  worst_performer?: Holding;
}

// Frontend Portfolio state (legacy - will be deprecated)
export interface PortfolioLegacy {
  assets: Asset[];
  totalValue: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
}

// Backend API Quote interface
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

// Legacy MarketQuote interface
export interface MarketQuote {
  symbol: string;
  price: number;
  timestamp: number;
  volume?: number;
  high24h?: number;
  low24h?: number;
  change24h?: number;
  bid?: number;
  ask?: number;
}

export interface WatchlistItem {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

// Backend API TradingStats interface
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

export interface TradingState {
  portfolio: {
    assets: AssetLegacy[];
    totalValue: number;
    loading: boolean;
    error: string | null;
  };
  history: {
    trades: TradeLegacy[];
    loading: boolean;
    error: string | null;
  };
  watchlist: {
    items: WatchlistItem[];
    loading: boolean;
    error: string | null;
  };
  orders: {
    pending: TradeLegacy[];
    loading: boolean;
    error: string | null;
  };
}

// Roundup transaction interface
export interface RoundupTransaction {
  id: number;
  original_amount: number;
  roundup_amount: number;
  transaction_amount: number;
  transaction_date: string;
  description?: string;
  source?: string;
  status: 'pending' | 'invested' | 'cancelled';
  created_at: string;
  source_type?: string;
  source_description?: string;
}

// Recurring investment interface
export interface RecurringInvestment {
  id?: number;
  symbol: string;
  amount: number;
  investment_amount?: number;
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly' | string;
  day_of_week?: number;
  day_of_month?: number;
  next_execution_date?: string;
  next_investment_date?: string;
  start_date?: string;
  execution_count?: number;
  last_execution_date?: string;
  status?: 'active' | 'paused' | 'cancelled';
  is_active?: boolean;
  created_at?: string;
}

// Roundup summary interface
export interface RoundupSummary {
  total_roundups: number;
  total_amount: number;
  pending_amount: number;
  invested_amount: number;
  transaction_count: number;
  average_roundup: number;
  total_investments: number;
  last_investment_date?: string;
}