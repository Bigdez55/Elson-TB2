#!/usr/bin/env python
"""
Script to process subscription renewals.
Should be run daily as a scheduled task.
"""

import logging
import sys
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

# Add the parent directory to sys.path
sys.path.append("..")

from app.db.database import SessionLocal
from app.models.subscription import Subscription
from app.models.user import User, SubscriptionPlan, BillingCycle
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import SubscriptionPaymentCreate, PaymentStatus
from app.core.alerts import send_alert

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("subscription_renewals.log")
    ]
)
logger = logging.getLogger("subscription_renewals")

def get_renewals_due(db: Session, days_ahead: int = 0) -> list:
    """
    Get subscriptions that need renewal.
    
    Args:
        db: Database session
        days_ahead: Process renewals this many days ahead (for pre-processing)
        
    Returns:
        List of subscription IDs due for renewal
    """
    now = datetime.utcnow()
    target_date = now + timedelta(days=days_ahead)
    
    # Find active subscriptions set to auto-renew that expire within the target date
    subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.is_active == True,
            Subscription.auto_renew == True,
            Subscription.end_date <= target_date
        )
        .all()
    )
    
    return [sub.id for sub in subscriptions]

def process_renewals(subscription_ids: list, db: Session) -> dict:
    """
    Process renewals for given subscription IDs.
    
    Args:
        subscription_ids: List of subscription IDs to renew
        db: Database session
        
    Returns:
        Dictionary with results
    """
    results = {
        "total": len(subscription_ids),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    for sub_id in subscription_ids:
        logger.info(f"Processing renewal for subscription {sub_id}")
        try:
            success = SubscriptionService.process_renewal(db, sub_id)
            if success:
                results["successful"] += 1
                logger.info(f"Successfully renewed subscription {sub_id}")
            else:
                results["failed"] += 1
                error_msg = f"Failed to renew subscription {sub_id}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        except Exception as e:
            results["failed"] += 1
            error_msg = f"Error renewing subscription {sub_id}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
    
    return results

def send_renewal_notifications(subscription_ids: list, db: Session) -> None:
    """
    Send notifications to users for upcoming renewals.
    
    Args:
        subscription_ids: List of subscription IDs with upcoming renewals
        db: Database session
    """
    from app.services.notifications import NotificationService
    
    for sub_id in subscription_ids:
        try:
            # Get subscription
            subscription = db.query(Subscription).filter(Subscription.id == sub_id).first()
            if not subscription:
                continue
                
            # Calculate days until renewal
            days_left = (subscription.end_date - datetime.utcnow()).days
            
            # Get user email
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if not user or not user.email:
                continue
                
            # Send notification email
            plan_name = subscription.plan.value.capitalize()
            price = subscription.price
            
            subject = f"Your Elson {plan_name} Plan Renews in {days_left} Days"
            message = f"""
            Dear {user.first_name or 'Valued Customer'},
            
            Your Elson {plan_name} subscription will renew automatically in {days_left} days.
            
            Subscription details:
            - Plan: {plan_name}
            - Billing Cycle: {subscription.billing_cycle.value.capitalize()}
            - Price: ${price:.2f}
            - Renewal Date: {subscription.end_date.strftime('%Y-%m-%d')}
            
            If you would like to make any changes to your subscription, please log in to your account.
            
            Thank you for choosing Elson Wealth!
            
            The Elson Team
            """
            
            NotificationService.send_email(
                recipient=user.email,
                subject=subject,
                body=message
            )
            
            logger.info(f"Sent renewal notification to user {user.id} for subscription {sub_id}")
            
        except Exception as e:
            logger.error(f"Error sending notification for subscription {sub_id}: {str(e)}")

def main():
    """Main function to process subscription renewals"""
    logger.info("Starting subscription renewal process")
    
    db = SessionLocal()
    try:
        # Get subscriptions due for renewal today
        logger.info("Finding subscriptions due for renewal today")
        renewals_due = get_renewals_due(db)
        logger.info(f"Found {len(renewals_due)} subscriptions due for renewal")
        
        # Process renewals
        if renewals_due:
            results = process_renewals(renewals_due, db)
            
            # Log summary
            logger.info(f"Renewal summary: {results['successful']} successful, {results['failed']} failed")
            
            # Send alert if too many failures
            if results["failed"] > 0 and results["failed"] / results["total"] > 0.1:
                error_details = "\n".join(results["errors"][:10])
                if len(results["errors"]) > 10:
                    error_details += f"\n...and {len(results['errors']) - 10} more errors"
                    
                send_alert(
                    title="High subscription renewal failure rate",
                    message=f"Renewal process encountered {results['failed']} failures out of {results['total']} renewals.\n\nErrors:\n{error_details}",
                    level="error"
                )
        
        # Find subscriptions due for renewal in 3 days and send notifications
        logger.info("Finding subscriptions due for renewal in 3 days")
        upcoming_renewals = get_renewals_due(db, days_ahead=3)
        logger.info(f"Found {len(upcoming_renewals)} subscriptions due for renewal in 3 days")
        
        if upcoming_renewals:
            logger.info("Sending renewal notifications")
            send_renewal_notifications(upcoming_renewals, db)
        
    except Exception as e:
        logger.error(f"Error in renewal process: {str(e)}")
        send_alert(
            title="Subscription renewal process error",
            message=f"The subscription renewal process encountered an error: {str(e)}",
            level="critical"
        )
    finally:
        db.close()
    
    logger.info("Subscription renewal process completed")

if __name__ == "__main__":
    main()