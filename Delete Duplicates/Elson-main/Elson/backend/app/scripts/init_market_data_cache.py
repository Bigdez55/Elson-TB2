"""
Script to initialize the market data cache.

This script preloads market data for common stocks and indices to ensure 
that the application has data available even if market data sources are temporarily unavailable.
It's designed to be run at application startup.
"""

import asyncio
import logging
import sys
from typing import List, Dict, Any

from app.services.market_data import MarketDataService
from app.core.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Symbols to preload
COMMON_STOCKS = [
    # Major indices
    "SPY", "QQQ", "DIA", "IWM", 
    # Large cap tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    # Financial
    "JPM", "BAC", "WFC", "GS", "V", "MA",
    # Other sectors
    "JNJ", "PG", "KO", "PEP", "WMT", "HD", "MCD",
    # Popular among new investors
    "F", "GM", "GE", "DIS", "NFLX", "AMD", "INTC"
]

async def init_market_data_cache() -> None:
    """Initialize the market data cache with common stocks."""
    logger.info("Starting market data cache initialization")
    
    try:
        # Initialize market data service
        market_data_service = MarketDataService()
        await market_data_service.setup()
        
        # Get market hours first (required for other operations)
        try:
            market_hours = await market_data_service.get_market_hours("US")
            logger.info(f"Market hours loaded: market is {'open' if market_hours.get('is_open') else 'closed'}")
        except Exception as e:
            logger.error(f"Error fetching market hours: {str(e)}")
        
        # Preload quotes for common stocks in batches
        batch_size = 10
        for i in range(0, len(COMMON_STOCKS), batch_size):
            batch = COMMON_STOCKS[i:i+batch_size]
            logger.info(f"Loading batch {i//batch_size + 1}: {', '.join(batch)}")
            
            try:
                quotes = await market_data_service.get_batch_quotes(batch, force_refresh=True)
                success_count = sum(1 for q in quotes.values() if "error" not in q)
                logger.info(f"Successfully loaded {success_count}/{len(batch)} quotes")
            except Exception as e:
                logger.error(f"Error loading batch {i//batch_size + 1}: {str(e)}")
        
        # Check cache quality metrics
        metrics = await market_data_service.get_data_quality_metrics()
        logger.info(f"Cache quality metrics: {metrics}")
        
        # Close connections
        await market_data_service.close()
        logger.info("Market data cache initialization completed")
        
    except Exception as e:
        logger.error(f"Error during market data cache initialization: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_market_data_cache())