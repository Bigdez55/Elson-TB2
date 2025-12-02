"""Automated Order Aggregation Script.

This script runs as a scheduled job to automatically aggregate small dollar-based
orders into larger parent orders for more efficient execution. It is designed to
be run at regular intervals (e.g., every 15 minutes) to ensure timely processing
of customer orders while still allowing for beneficial aggregation.
"""

import sys
import os
import logging
import time
from decimal import Decimal
from datetime import datetime, timedelta
import argparse
import schedule

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.db.database import get_db
from app.services.order_aggregator import OrderAggregator
from app.services.market_data import MarketDataService
from app.services.trading_service import TradingService
from app.core.logging import setup_logging
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

def setup_argparse():
    """Set up command line argument parsing."""
    parser = argparse.ArgumentParser(description='Automated Order Aggregation Job')
    parser.add_argument('--run-once', action='store_true', 
                      help='Run once and exit (default is to run as scheduled service)')
    parser.add_argument('--interval', type=int, default=15,
                      help='Interval in minutes between aggregation runs (default: 15)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true',
                      help='Perform dry run without executing orders')
    return parser.parse_args()

def run_aggregation_job(dry_run=False):
    """Run one cycle of the order aggregation process."""
    logger.info("Starting order aggregation job")
    start_time = time.time()
    
    try:
        # Get database session
        db = next(get_db())
        
        # Initialize services
        market_data_service = MarketDataService()
        order_aggregator = OrderAggregator(db, market_data_service)
        trading_service = TradingService(db)
        
        # Run aggregation cycle to create parent orders
        aggregation_result = order_aggregator.run_aggregation_cycle()
        
        if not dry_run and aggregation_result["parent_orders_created"] > 0:
            # Get pending parent orders that need to be executed
            parent_orders = order_aggregator.get_pending_parent_orders()
            logger.info(f"Found {len(parent_orders)} parent orders to execute")
            
            # Execute each parent order
            for parent_order in parent_orders:
                try:
                    logger.info(f"Executing parent order {parent_order.id} for {parent_order.symbol}")
                    result = trading_service.execute_trade(parent_order.id)
                    if result:
                        logger.info(f"Successfully executed parent order {parent_order.id}")
                    else:
                        logger.error(f"Failed to execute parent order {parent_order.id}")
                except Exception as e:
                    logger.error(f"Error executing parent order {parent_order.id}: {str(e)}")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"Order aggregation job completed in {execution_time:.2f} seconds")
        logger.info(f"Aggregation statistics: {aggregation_result}")
        
        return aggregation_result
        
    except Exception as e:
        logger.error(f"Error in order aggregation job: {str(e)}")
        return {"error": str(e)}
    finally:
        # Close database session if needed
        try:
            db.close()
        except:
            pass

def main():
    """Main entry point for the script."""
    args = setup_argparse()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)
    
    logger.info(f"Starting Automated Order Aggregation service "
               f"({'DRY RUN' if args.dry_run else 'LIVE MODE'})")
    
    if args.run_once:
        logger.info("Running single aggregation cycle")
        run_aggregation_job(dry_run=args.dry_run)
    else:
        # Schedule repeated execution
        interval_minutes = args.interval
        logger.info(f"Scheduling aggregation job to run every {interval_minutes} minutes")
        
        # Define the scheduled job
        def scheduled_job():
            run_aggregation_job(dry_run=args.dry_run)
        
        # Schedule the job
        schedule.every(interval_minutes).minutes.do(scheduled_job)
        
        # Run immediately on startup
        run_aggregation_job(dry_run=args.dry_run)
        
        # Keep the script running and executing the scheduled job
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, terminating gracefully")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

if __name__ == "__main__":
    main()