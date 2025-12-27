/**
 * Trading Signal Types
 *
 * Shared type definitions for the Brain & Body architecture.
 * These types define the contract between Python (Brain) and TypeScript (Body).
 */

/**
 * Trading signal actions
 */
export type SignalAction = 'BUY' | 'SELL' | 'HOLD' | 'CLOSE' | 'SCALE_IN' | 'SCALE_OUT';

/**
 * Signal source identifiers
 */
export type SignalSource =
  | 'lstm_predictor'
  | 'cnn_predictor'
  | 'transformer'
  | 'sentiment'
  | 'quantum'
  | 'rl_agent'
  | 'technical'
  | 'ensemble'
  | 'golden_cross'
  | 'rsi'
  | 'macd'
  | 'bollinger';

/**
 * Trading signal payload from Python Brain
 */
export interface TradingSignal {
  // Core signal data
  symbol: string;
  action: SignalAction;
  price: number;
  timestamp: number;

  // Signal metadata
  strategy: string;
  source: SignalSource;
  confidence: number; // 0.0 to 1.0

  // Optional fields
  quantity?: number;
  stop_loss?: number;
  take_profit?: number;

  // Risk management
  risk_score?: number;
  position_size_pct?: number;

  // Additional context
  indicators?: Record<string, number>;
  reasoning?: string;

  // Signal ID for tracking
  signal_id?: string;
}

/**
 * Alert types for non-trading notifications
 */
export interface TradeAlert {
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  data?: Record<string, unknown>;
  timestamp: number;
}

/**
 * Engine heartbeat status
 */
export interface EngineHeartbeat {
  status: 'alive' | 'degraded' | 'dead';
  timestamp: number;
  engine: string;
  metrics?: {
    signals_per_minute?: number;
    latency_ms?: number;
    memory_usage_mb?: number;
  };
}

/**
 * Execution result from the Body
 */
export interface ExecutionResult {
  success: boolean;
  signal_id: string;
  order_id?: string;
  executed_price?: number;
  executed_quantity?: number;
  fees?: number;
  error?: string;
  timestamp: number;
}

/**
 * Position state
 */
export interface Position {
  symbol: string;
  side: 'long' | 'short' | 'flat';
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

/**
 * Portfolio state
 */
export interface PortfolioState {
  balance: number;
  equity: number;
  positions: Position[];
  open_orders: number;
  daily_pnl: number;
  daily_pnl_pct: number;
}

/**
 * Redis channel names
 */
export const REDIS_CHANNELS = {
  SIGNALS: 'trade_signals',
  ALERTS: 'trade_alerts',
  HEARTBEAT: 'engine_heartbeat',
  EXECUTION: 'execution_results',
} as const;

/**
 * Signal validation
 */
export function isValidSignal(signal: unknown): signal is TradingSignal {
  if (typeof signal !== 'object' || signal === null) return false;

  const s = signal as Record<string, unknown>;

  return (
    typeof s.symbol === 'string' &&
    typeof s.action === 'string' &&
    ['BUY', 'SELL', 'HOLD', 'CLOSE', 'SCALE_IN', 'SCALE_OUT'].includes(s.action as string) &&
    typeof s.price === 'number' &&
    typeof s.timestamp === 'number' &&
    typeof s.strategy === 'string' &&
    typeof s.source === 'string' &&
    typeof s.confidence === 'number' &&
    s.confidence >= 0 &&
    s.confidence <= 1
  );
}

/**
 * Calculate signal strength (for UI display)
 */
export function getSignalStrength(signal: TradingSignal): 'weak' | 'moderate' | 'strong' {
  if (signal.confidence >= 0.8) return 'strong';
  if (signal.confidence >= 0.6) return 'moderate';
  return 'weak';
}

/**
 * Format signal for logging
 */
export function formatSignal(signal: TradingSignal): string {
  const strength = getSignalStrength(signal);
  return `[${strength.toUpperCase()}] ${signal.action} ${signal.symbol} @ $${signal.price.toFixed(2)} (${signal.strategy})`;
}
