"""
Script to run the order reconciliation service.

This script is designed to be run as a scheduled task (e.g., Kubernetes CronJob)
to periodically reconcile trade status between the application database and
broker records.
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.reconciliation.order_reconciliation import OrderReconciliationService
from app.services.notifications import NotificationService
from app.core.alerts_manager import alert_manager
from app.core.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

async def run_reconciliation(hours: int = 24, deep_reconciliation: bool = False) -> None:
    """
    Run the order reconciliation service.
    
    Args:
        hours: Number of hours to look back for trades to reconcile
        deep_reconciliation: Whether to perform a deep reconciliation of all positions
    """
    logger.info(f"Starting order reconciliation (hours={hours}, deep={deep_reconciliation})")
    start_time = datetime.utcnow()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize services
        notification_service = NotificationService(db)
        reconciliation_service = OrderReconciliationService(db, notification_service)
        
        # Run reconciliation
        results = await reconciliation_service.reconcile_recent_orders(hours)
        logger.info(f"Order reconciliation completed: {results}")
        
        # Run deep reconciliation if requested
        if deep_reconciliation:
            logger.info("Starting deep position reconciliation")
            position_results = await reconciliation_service.reconcile_all_active_positions()
            logger.info(f"Position reconciliation completed: {position_results}")
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Reconciliation completed in {execution_time:.2f} seconds")
        
        # Send alert if there were significant mismatches
        if results.get("mismatch_count", 0) > 10 or results.get("error_count", 0) > 5:
            alert_manager.send_alert(
                title="High number of order reconciliation issues",
                message=f"Reconciliation found {results.get('mismatch_count')} mismatches and {results.get('error_count')} errors",
                level="warning"
            )
            
    except Exception as e:
        logger.error(f"Error during reconciliation: {str(e)}", exc_info=True)
        alert_manager.send_alert(
            title="Order reconciliation failed",
            message=f"Error during reconciliation: {str(e)}",
            level="error"
        )
        sys.exit(1)
    finally:
        db.close()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run order reconciliation")
    parser.add_argument("--hours", type=int, default=24, 
                        help="Number of hours to look back for trades")
    parser.add_argument("--deep", action="store_true", 
                        help="Perform deep reconciliation of all positions")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_reconciliation(args.hours, args.deep))