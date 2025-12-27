/**
 * Execution Bot Entry Point
 *
 * Run with: npx ts-node index.ts
 *
 * This is the "Body" of the Brain & Body architecture.
 * It listens for signals from the Python ML engine (Brain) via Redis
 * and executes trades on the exchange.
 */

import Redis from 'ioredis';
import { ExecutionBot, createExecutionBot, ExecutionBotConfig } from './executionBot';

// Configuration from environment
const config: Partial<ExecutionBotConfig> = {
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    password: process.env.REDIS_PASSWORD,
  },
  paperTrading: process.env.PAPER_TRADING !== 'false',
  initialBalance: parseFloat(process.env.INITIAL_BALANCE || '10000'),
  minConfidence: parseFloat(process.env.MIN_CONFIDENCE || '0.6'),
  maxPositionSize: parseFloat(process.env.MAX_POSITION_SIZE || '10'),
  maxDailyLoss: parseFloat(process.env.MAX_DAILY_LOSS || '5'),
};

async function main() {
  console.log('═'.repeat(60));
  console.log('  ELSON TRADING EXECUTION BOT');
  console.log('  The "Body" of the Brain & Body Architecture');
  console.log('═'.repeat(60));

  // Create Redis client
  const redis = new Redis({
    host: config.redis?.host,
    port: config.redis?.port,
    password: config.redis?.password,
    retryDelayOnFailover: 100,
    maxRetriesPerRequest: 3,
  });

  // Handle Redis errors
  redis.on('error', (err) => {
    console.error('Redis error:', err.message);
  });

  redis.on('connect', () => {
    console.log('✅ Connected to Redis');
  });

  // Create and start bot
  const bot = await createExecutionBot(config);

  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n\nReceived SIGINT, shutting down gracefully...');
    await bot.stop();
    await redis.quit();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    console.log('\n\nReceived SIGTERM, shutting down gracefully...');
    await bot.stop();
    await redis.quit();
    process.exit(0);
  });

  // Start the bot
  try {
    // Cast to satisfy type (ioredis matches our interface)
    await bot.start(redis as any);

    // Print status periodically
    setInterval(() => {
      const portfolio = bot.getPortfolio();
      const stats = bot.getStats();

      console.log('\n📊 Status Update:');
      console.log(`   Signals Processed: ${stats.signalCount}`);
      console.log(`   Balance: $${portfolio.balance.toFixed(2)}`);
      console.log(`   Equity: $${portfolio.equity.toFixed(2)}`);
      console.log(`   Daily P&L: $${portfolio.daily_pnl.toFixed(2)} (${portfolio.daily_pnl_pct.toFixed(2)}%)`);
      console.log(`   Open Positions: ${portfolio.positions.length}`);

      if (portfolio.positions.length > 0) {
        portfolio.positions.forEach((pos) => {
          console.log(`     - ${pos.symbol}: ${pos.quantity.toFixed(4)} @ $${pos.entry_price.toFixed(2)} (P&L: $${pos.unrealized_pnl.toFixed(2)})`);
        });
      }
    }, 60000); // Every minute

  } catch (error) {
    console.error('Failed to start bot:', error);
    process.exit(1);
  }
}

// Run if executed directly
main().catch(console.error);

export { ExecutionBot, createExecutionBot };
export * from './types/signals';
