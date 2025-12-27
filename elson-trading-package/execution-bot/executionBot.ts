/**
 * Execution Bot - The "Body" of the Trading System
 *
 * This bot listens to trading signals from Redis and executes trades.
 * It's the high-speed execution layer that connects to exchange APIs.
 *
 * Architecture:
 *   Python Engine (Brain) ➝ Redis ➝ TypeScript Bot (Body) ➝ Exchange
 */

import {
  TradingSignal,
  TradeAlert,
  EngineHeartbeat,
  ExecutionResult,
  PortfolioState,
  Position,
  REDIS_CHANNELS,
  isValidSignal,
  formatSignal,
  getSignalStrength,
} from './types/signals';

// Redis client type (ioredis)
interface RedisClient {
  subscribe(channel: string, callback?: (err: Error | null, count: number) => void): Promise<number>;
  on(event: 'message', callback: (channel: string, message: string) => void): void;
  publish(channel: string, message: string): Promise<number>;
  quit(): Promise<string>;
}

/**
 * Configuration for the execution bot
 */
export interface ExecutionBotConfig {
  // Redis connection
  redis: {
    host: string;
    port: number;
    password?: string;
  };

  // Trading limits
  maxPositionSize: number; // Max position as % of portfolio
  maxDailyLoss: number; // Max daily loss as % of portfolio
  minConfidence: number; // Minimum signal confidence to execute

  // Paper trading mode
  paperTrading: boolean;
  initialBalance: number;

  // Execution settings
  slippageTolerance: number; // Max acceptable slippage %
  retryAttempts: number;
}

/**
 * Mock exchange executor for paper trading
 */
class PaperTradingExecutor {
  private balance: number;
  private positions: Map<string, Position> = new Map();
  private executionHistory: ExecutionResult[] = [];
  private dailyPnL: number = 0;

  constructor(initialBalance: number) {
    this.balance = initialBalance;
  }

  async executeOrder(
    signal: TradingSignal,
    maxPositionPct: number
  ): Promise<ExecutionResult> {
    const timestamp = Date.now();
    const signalId = signal.signal_id || `${signal.symbol}_${timestamp}`;

    try {
      // Simulate execution latency
      await this.simulateLatency();

      // Calculate position size
      const positionValue = this.balance * (maxPositionPct / 100);
      const quantity = positionValue / signal.price;

      if (signal.action === 'BUY') {
        return this.executeBuy(signal, quantity, signalId, timestamp);
      } else if (signal.action === 'SELL') {
        return this.executeSell(signal, signalId, timestamp);
      } else if (signal.action === 'CLOSE') {
        return this.closePosition(signal, signalId, timestamp);
      }

      return {
        success: false,
        signal_id: signalId,
        error: `Unsupported action: ${signal.action}`,
        timestamp,
      };
    } catch (error) {
      return {
        success: false,
        signal_id: signalId,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp,
      };
    }
  }

  private async executeBuy(
    signal: TradingSignal,
    quantity: number,
    signalId: string,
    timestamp: number
  ): Promise<ExecutionResult> {
    const existingPosition = this.positions.get(signal.symbol);

    if (existingPosition && existingPosition.side === 'long') {
      // Already long, skip
      return {
        success: false,
        signal_id: signalId,
        error: 'Already in long position',
        timestamp,
      };
    }

    // Simulate slippage (0.1% average)
    const executedPrice = signal.price * (1 + (Math.random() - 0.5) * 0.002);
    const cost = quantity * executedPrice;
    const fees = cost * 0.001; // 0.1% fee

    if (cost + fees > this.balance) {
      return {
        success: false,
        signal_id: signalId,
        error: 'Insufficient funds',
        timestamp,
      };
    }

    // Execute
    this.balance -= cost + fees;

    const position: Position = {
      symbol: signal.symbol,
      side: 'long',
      quantity,
      entry_price: executedPrice,
      current_price: executedPrice,
      unrealized_pnl: 0,
      unrealized_pnl_pct: 0,
    };

    this.positions.set(signal.symbol, position);

    const result: ExecutionResult = {
      success: true,
      signal_id: signalId,
      order_id: `ORD_${timestamp}`,
      executed_price: executedPrice,
      executed_quantity: quantity,
      fees,
      timestamp,
    };

    this.executionHistory.push(result);
    console.log(`\n✅ EXECUTED BUY: ${quantity.toFixed(4)} ${signal.symbol} @ $${executedPrice.toFixed(2)}`);
    console.log(`   Fees: $${fees.toFixed(2)} | Remaining Balance: $${this.balance.toFixed(2)}`);

    return result;
  }

  private async executeSell(
    signal: TradingSignal,
    signalId: string,
    timestamp: number
  ): Promise<ExecutionResult> {
    const position = this.positions.get(signal.symbol);

    if (!position || position.side !== 'long') {
      return {
        success: false,
        signal_id: signalId,
        error: 'No long position to sell',
        timestamp,
      };
    }

    // Simulate slippage
    const executedPrice = signal.price * (1 - (Math.random() - 0.5) * 0.002);
    const saleValue = position.quantity * executedPrice;
    const fees = saleValue * 0.001;

    // Calculate P&L
    const pnl = saleValue - (position.quantity * position.entry_price) - fees;
    this.dailyPnL += pnl;
    this.balance += saleValue - fees;

    this.positions.delete(signal.symbol);

    const result: ExecutionResult = {
      success: true,
      signal_id: signalId,
      order_id: `ORD_${timestamp}`,
      executed_price: executedPrice,
      executed_quantity: position.quantity,
      fees,
      timestamp,
    };

    this.executionHistory.push(result);
    console.log(`\n✅ EXECUTED SELL: ${position.quantity.toFixed(4)} ${signal.symbol} @ $${executedPrice.toFixed(2)}`);
    console.log(`   P&L: $${pnl.toFixed(2)} | New Balance: $${this.balance.toFixed(2)}`);

    return result;
  }

  private async closePosition(
    signal: TradingSignal,
    signalId: string,
    timestamp: number
  ): Promise<ExecutionResult> {
    return this.executeSell(signal, signalId, timestamp);
  }

  private async simulateLatency(): Promise<void> {
    // Simulate 10-50ms execution latency
    const latency = 10 + Math.random() * 40;
    return new Promise((resolve) => setTimeout(resolve, latency));
  }

  getPortfolioState(): PortfolioState {
    let equity = this.balance;
    const positions: Position[] = [];

    this.positions.forEach((pos) => {
      equity += pos.quantity * pos.current_price;
      positions.push({ ...pos });
    });

    return {
      balance: this.balance,
      equity,
      positions,
      open_orders: 0,
      daily_pnl: this.dailyPnL,
      daily_pnl_pct: (this.dailyPnL / (equity - this.dailyPnL)) * 100,
    };
  }

  updatePrices(prices: Record<string, number>): void {
    this.positions.forEach((pos, symbol) => {
      if (prices[symbol]) {
        pos.current_price = prices[symbol];
        pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity;
        pos.unrealized_pnl_pct = ((pos.current_price - pos.entry_price) / pos.entry_price) * 100;
      }
    });
  }
}

/**
 * Main Execution Bot class
 */
export class ExecutionBot {
  private config: ExecutionBotConfig;
  private redis: RedisClient | null = null;
  private executor: PaperTradingExecutor;
  private isRunning: boolean = false;
  private signalCount: number = 0;
  private lastHeartbeat: number = 0;

  constructor(config: ExecutionBotConfig) {
    this.config = config;
    this.executor = new PaperTradingExecutor(config.initialBalance);
  }

  /**
   * Start the execution bot
   */
  async start(redisClient: RedisClient): Promise<void> {
    this.redis = redisClient;
    this.isRunning = true;

    console.log('🤖 Execution Bot Starting...');
    console.log(`   Mode: ${this.config.paperTrading ? 'Paper Trading' : 'Live Trading'}`);
    console.log(`   Initial Balance: $${this.config.initialBalance.toLocaleString()}`);
    console.log(`   Min Confidence: ${this.config.minConfidence * 100}%`);

    try {
      // Subscribe to channels
      await this.redis.subscribe(REDIS_CHANNELS.SIGNALS);
      await this.redis.subscribe(REDIS_CHANNELS.ALERTS);
      await this.redis.subscribe(REDIS_CHANNELS.HEARTBEAT);

      console.log(`\n🎧 Listening on Redis channels...`);

      // Handle incoming messages
      this.redis.on('message', (channel, message) => {
        this.handleMessage(channel, message);
      });

      // Start heartbeat monitor
      this.startHeartbeatMonitor();

    } catch (error) {
      console.error('Failed to start execution bot:', error);
      throw error;
    }
  }

  /**
   * Stop the execution bot
   */
  async stop(): Promise<void> {
    this.isRunning = false;
    if (this.redis) {
      await this.redis.quit();
    }
    console.log('\n🛑 Execution Bot Stopped');
    console.log('   Final Portfolio:', this.executor.getPortfolioState());
  }

  /**
   * Handle incoming Redis messages
   */
  private handleMessage(channel: string, message: string): void {
    try {
      const data = JSON.parse(message);

      switch (channel) {
        case REDIS_CHANNELS.SIGNALS:
          this.handleSignal(data);
          break;
        case REDIS_CHANNELS.ALERTS:
          this.handleAlert(data as TradeAlert);
          break;
        case REDIS_CHANNELS.HEARTBEAT:
          this.handleHeartbeat(data as EngineHeartbeat);
          break;
        default:
          console.warn(`Unknown channel: ${channel}`);
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  }

  /**
   * Handle trading signal
   */
  private async handleSignal(data: unknown): Promise<void> {
    if (!isValidSignal(data)) {
      console.warn('Invalid signal received:', data);
      return;
    }

    const signal = data as TradingSignal;
    this.signalCount++;

    console.log(`\n⚡ SIGNAL RECEIVED #${this.signalCount}`);
    console.log(`   ${formatSignal(signal)}`);
    console.log(`   Confidence: ${(signal.confidence * 100).toFixed(1)}%`);

    // Check confidence threshold
    if (signal.confidence < this.config.minConfidence) {
      console.log(`   ⏭️ Skipped: Confidence below threshold (${this.config.minConfidence * 100}%)`);
      return;
    }

    // Check daily loss limit
    const portfolio = this.executor.getPortfolioState();
    const lossLimit = this.config.initialBalance * (this.config.maxDailyLoss / 100);

    if (portfolio.daily_pnl < -lossLimit) {
      console.log(`   ⏭️ Skipped: Daily loss limit reached ($${lossLimit.toFixed(2)})`);
      return;
    }

    // Execute the signal
    if (signal.action === 'HOLD') {
      console.log('   ⏸️ HOLD signal - No action taken');
      return;
    }

    const result = await this.executor.executeOrder(signal, this.config.maxPositionSize);

    // Publish execution result
    if (this.redis) {
      await this.redis.publish(
        REDIS_CHANNELS.EXECUTION,
        JSON.stringify(result)
      );
    }
  }

  /**
   * Handle alert message
   */
  private handleAlert(alert: TradeAlert): void {
    const icons: Record<string, string> = {
      info: 'ℹ️',
      warning: '⚠️',
      error: '❌',
      success: '✅',
    };

    console.log(`\n${icons[alert.type] || '📢'} ALERT: ${alert.message}`);
  }

  /**
   * Handle engine heartbeat
   */
  private handleHeartbeat(heartbeat: EngineHeartbeat): void {
    this.lastHeartbeat = heartbeat.timestamp;

    if (heartbeat.status !== 'alive') {
      console.warn(`\n⚠️ Engine Status: ${heartbeat.status}`);
    }
  }

  /**
   * Monitor for engine heartbeat
   */
  private startHeartbeatMonitor(): void {
    setInterval(() => {
      const now = Date.now() / 1000;
      const timeSinceHeartbeat = now - this.lastHeartbeat;

      if (this.lastHeartbeat > 0 && timeSinceHeartbeat > 30) {
        console.warn(`\n⚠️ No heartbeat from Python engine for ${timeSinceHeartbeat.toFixed(0)}s`);
      }
    }, 10000); // Check every 10 seconds
  }

  /**
   * Get current portfolio state
   */
  getPortfolio(): PortfolioState {
    return this.executor.getPortfolioState();
  }

  /**
   * Get signal statistics
   */
  getStats(): { signalCount: number; lastHeartbeat: number } {
    return {
      signalCount: this.signalCount,
      lastHeartbeat: this.lastHeartbeat,
    };
  }
}

/**
 * Create and start the execution bot
 */
export async function createExecutionBot(
  config: Partial<ExecutionBotConfig> = {}
): Promise<ExecutionBot> {
  const defaultConfig: ExecutionBotConfig = {
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      password: process.env.REDIS_PASSWORD,
    },
    maxPositionSize: 10, // 10% of portfolio per position
    maxDailyLoss: 5, // 5% max daily loss
    minConfidence: 0.6, // 60% minimum confidence
    paperTrading: true,
    initialBalance: 10000,
    slippageTolerance: 0.5, // 0.5% slippage tolerance
    retryAttempts: 3,
  };

  const finalConfig = { ...defaultConfig, ...config };
  return new ExecutionBot(finalConfig);
}

// Export types
export type { TradingSignal, ExecutionResult, PortfolioState, Position };
