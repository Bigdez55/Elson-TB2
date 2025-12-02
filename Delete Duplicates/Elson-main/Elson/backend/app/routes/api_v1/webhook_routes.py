from fastapi import APIRouter, Depends, Request, Response, HTTPException, status, Body
from sqlalchemy.orm import Session
import json
from datetime import datetime, timedelta

from app.db.database import get_db
from app.services.stripe_service import StripeService
from app.core.config import settings
from app.core.logging import get_logger
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter()
logger = get_logger(__name__)

@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Handle Stripe webhook events.
    
    This endpoint receives webhook events from Stripe and processes them accordingly.
    Events include subscription creations, updates, and payment notifications.
    """
    # Get the signature from headers
    stripe_signature = request.headers.get("stripe-signature")
    if not stripe_signature:
        logger.error("Stripe webhook received without signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe signature is missing"
        )
    
    # Get the raw payload
    payload = await request.body()
    
    try:
        # Verify and parse the event
        event = StripeService.handle_webhook_event(
            payload=payload,
            sig_header=stripe_signature
        )
        
        # Log the event type
        event_type = event.get("type", "unknown")
        logger.info(f"Processing Stripe webhook event: {event_type}")
        
        # Process different event types
        if event_type == "customer.subscription.created":
            # New subscription created - log only, creation is handled in our API
            logger.info(f"New subscription created: {event.data.object.id}")
            
        elif event_type == "customer.subscription.updated":
            # Subscription updated
            success, message = StripeService.process_subscription_updated(
                db=db,
                event_data=event.data
            )
            if not success:
                logger.error(f"Failed to process subscription update: {message}")
                
        elif event_type == "customer.subscription.deleted":
            # Subscription canceled
            success, message = StripeService.process_subscription_updated(
                db=db,
                event_data=event.data
            )
            if not success:
                logger.error(f"Failed to process subscription deletion: {message}")
                
        elif event_type == "invoice.paid":
            # Payment succeeded
            success, message = StripeService.process_invoice_paid(
                db=db,
                event_data=event.data
            )
            if not success:
                logger.error(f"Failed to process invoice payment: {message}")
                
        elif event_type == "invoice.payment_failed":
            # Payment failed
            success, message = StripeService.process_payment_failed(
                db=db,
                event_data=event.data
            )
            if not success:
                logger.error(f"Failed to process payment failure: {message}")
            else:
                # Send notification to user about payment failure
                from app.services.notifications import NotificationService
                
                try:
                    # Get subscription and user info
                    invoice = event.data.object
                    subscription_id = invoice.get("subscription")
                    if subscription_id:
                        db_subscription = db.query(Subscription).filter(
                            Subscription.provider_subscription_id == subscription_id
                        ).first()
                        
                        if db_subscription and db_subscription.user_id:
                            user = db.query(User).filter(User.id == db_subscription.user_id).first()
                            if user and user.email:
                                # Get retry count from invoice
                                retry_count = invoice.get("attempt_count", 1) - 1
                                max_retries = 3
                                
                                subject = "Payment Failed for Your Elson Subscription"
                                body = f"""
                                Dear {user.first_name or 'Valued Customer'},
                                
                                We were unable to process your payment for your Elson subscription.
                                
                                Subscription: {db_subscription.plan.value.capitalize()}
                                Amount: ${invoice.get('amount_due', 0) / 100:.2f}
                                
                                {"This was attempt " + str(retry_count+1) + " of " + str(max_retries+1) + ". We will try again soon." if retry_count < max_retries else "We have tried to charge your payment method multiple times without success. Your subscription has been suspended."}
                                
                                To update your payment method, please log in to your account.
                                
                                Thank you,
                                The Elson Team
                                """
                                
                                NotificationService.send_email(
                                    recipient=user.email,
                                    subject=subject,
                                    body=body
                                )
                                
                                logger.info(f"Payment failure notification sent to user {user.id}")
                except Exception as e:
                    logger.error(f"Failed to send payment failure notification: {str(e)}")
            
        elif event_type == "payment_method.attached" or event_type == "payment_method.updated":
            # Payment method added or updated
            success, message = StripeService.process_payment_method_updated(
                db=db,
                event_data=event.data
            )
            if not success:
                logger.error(f"Failed to process payment method update: {message}")
                
        elif event_type == "bank_account.verified" or event_type == "bank_account.verification_failed":
            # Bank account verification status changed
            success, message = StripeService.process_bank_account_verification(
                db=db,
                event_data=event.data
            )
            if not success:
                logger.error(f"Failed to process bank account verification: {message}")
            else:
                # Send email to user about verification result
                from app.services.notifications import NotificationService
                
                try:
                    # Get bank account details
                    bank_account = event.data.object
                    
                    # Find subscriptions using this bank account
                    db_subscriptions = db.query(Subscription).filter(
                        Subscription.payment_method_id == bank_account["id"]
                    ).all()
                    
                    if db_subscriptions:
                        for db_subscription in db_subscriptions:
                            user = db.query(User).filter(User.id == db_subscription.user_id).first()
                            if user and user.email:
                                # Is the account verified or verification failed?
                                if bank_account["status"] == "verified":
                                    subject = "Your Bank Account Has Been Verified"
                                    body = f"""
                                    Dear {user.first_name or 'Valued Customer'},
                                    
                                    Your bank account has been successfully verified for your Elson subscription!
                                    
                                    Subscription: {db_subscription.plan.value.capitalize()}
                                    Billing Cycle: {db_subscription.billing_cycle.value.capitalize()}
                                    Amount: ${db_subscription.price:.2f}
                                    Bank: {bank_account.get('bank_name', 'Your bank')}
                                    Last 4: {bank_account.get('last4', 'xxxx')}
                                    
                                    Your subscription is now active and you have full access to all plan features.
                                    
                                    Thank you for choosing Elson Wealth!
                                    
                                    The Elson Team
                                    """
                                else:
                                    subject = "Bank Account Verification Failed"
                                    body = f"""
                                    Dear {user.first_name or 'Valued Customer'},
                                    
                                    We were unable to verify your bank account for your Elson subscription.
                                    
                                    This could be due to incorrect micro-deposit verification or bank account details.
                                    
                                    Please log in to your account to update your payment method or contact customer support for assistance.
                                    
                                    The Elson Team
                                    """
                                
                                NotificationService.send_email(
                                    recipient=user.email,
                                    subject=subject,
                                    body=body
                                )
                except Exception as e:
                    logger.error(f"Failed to send bank account verification notification: {str(e)}")
                    
        elif event_type == "payment_intent.succeeded":
            # Check if this is an ACH payment intent
            payment_intent = event.data.object
            payment_method_type = payment_intent.get("payment_method_types", [])[0] if payment_intent.get("payment_method_types") else None
            
            if payment_method_type == "us_bank_account":
                # Process successful ACH payment
                invoice_id = payment_intent.get("invoice")
                if invoice_id:
                    # This is a subscription payment, process it like an invoice.paid event
                    try:
                        # Fetch the invoice to get the subscription ID
                        import stripe
                        stripe.api_key = settings.STRIPE_API_KEY
                        invoice = stripe.Invoice.retrieve(invoice_id)
                        
                        if invoice:
                            # Create a modified event data with the invoice
                            modified_event = {"object": invoice}
                            
                            # Process like a regular invoice payment
                            success, message = StripeService.process_invoice_paid(
                                db=db,
                                event_data=modified_event
                            )
                            if not success:
                                logger.error(f"Failed to process ACH payment: {message}")
                    except Exception as e:
                        logger.error(f"Error processing ACH payment: {str(e)}")
                        
        elif event_type == "checkout.session.completed":
            # Handle PayPal checkout completion
            payment_method_types = event.data.object.get("payment_method_types", [])
            
            if "paypal" in payment_method_types:
                # PayPal checkout completed
                success, message = StripeService.process_paypal_webhook(
                    db=db,
                    event_data=event.data
                )
                if not success:
                    logger.error(f"Failed to process PayPal checkout: {message}")
                else:
                    # Send success email to user
                    from app.services.notifications import NotificationService
                    
                    try:
                        # Get subscription details from metadata
                        metadata = event.data.object.get("metadata", {})
                        subscription_id = metadata.get("subscription_id")
                        
                        if subscription_id:
                            db_subscription = db.query(Subscription).filter(
                                Subscription.id == int(subscription_id)
                            ).first()
                            
                            if db_subscription and db_subscription.user_id:
                                user = db.query(User).filter(User.id == db_subscription.user_id).first()
                                if user and user.email:
                                    subject = "Your Elson Subscription is Active!"
                                    body = f"""
                                    Dear {user.first_name or 'Valued Customer'},
                                    
                                    Thank you for subscribing to Elson Wealth! Your PayPal payment has been processed successfully.
                                    
                                    Subscription: {db_subscription.plan.value.capitalize()}
                                    Billing Cycle: {db_subscription.billing_cycle.value.capitalize()}
                                    Amount: ${db_subscription.price:.2f}
                                    
                                    Your subscription is now active and you have full access to all plan features.
                                    
                                    Thank you for choosing Elson Wealth!
                                    
                                    The Elson Team
                                    """
                                    
                                    NotificationService.send_email(
                                        recipient=user.email,
                                        subject=subject,
                                        body=body
                                    )
                                    
                                    logger.info(f"PayPal subscription confirmation sent to user {user.id}")
                    except Exception as e:
                        logger.error(f"Failed to send PayPal confirmation email: {str(e)}")
            else:
                # Regular checkout session (not PayPal)
                logger.info(f"Non-PayPal checkout session completed: {event.data.object.id}")
            
        else:
            # Log unhandled event types
            logger.info(f"Unhandled Stripe webhook event type: {event_type}")
            
        # Return a success response to acknowledge receipt
        return {"status": "success", "message": f"Webhook received: {event_type}"}
        
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}")
        # Still return 200 OK to prevent Stripe from retrying
        return {"status": "error", "message": str(e)}