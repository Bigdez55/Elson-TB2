from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
import stripe
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.subscription import Subscription, SubscriptionPayment, SubscriptionHistory, PaymentStatus, PaymentMethod
from app.models.user import User, SubscriptionPlan, BillingCycle
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionPaymentCreate,
    SubscriptionHistoryCreate, ChangeType,
    PaymentMethodCreate, CreditCardInfo, BankAccountInfo
)
from app.core.encryption import AES256Encryptor
from app.core.config import settings
from app.services.stripe_service import StripeService
from app.core.logging import get_logger

# Initialize encryption
encryptor = AES256Encryptor()

# Get logger
logger = get_logger(__name__)

# Pricing configuration
PRICING = {
    SubscriptionPlan.PREMIUM: {
        BillingCycle.MONTHLY: 9.99,
        BillingCycle.ANNUALLY: 95.88  # $7.99/month billed annually
    },
    SubscriptionPlan.FAMILY: {
        BillingCycle.MONTHLY: 19.99,
        BillingCycle.ANNUALLY: 191.88  # $15.99/month billed annually
    }
}

class SubscriptionService:
    """Service for managing user subscriptions and payments"""
    
    @staticmethod
    def get_subscription(db: Session, subscription_id: int) -> Optional[Subscription]:
        """Get a subscription by ID"""
        return db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    @staticmethod
    def get_user_subscriptions(db: Session, user_id: int) -> List[Subscription]:
        """Get all subscriptions for a user"""
        return db.query(Subscription).filter(Subscription.user_id == user_id).all()
    
    @staticmethod
    def get_active_subscription(db: Session, user_id: int) -> Optional[Subscription]:
        """Get a user's active subscription if any"""
        from sqlalchemy import or_
        now = datetime.utcnow()
        return (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                or_(Subscription.end_date.is_(None), Subscription.end_date > now)
            )
            .order_by(Subscription.created_at.desc())
            .first()
        )
    
    @staticmethod
    def create_history_entry(
        db: Session,
        subscription_id: int,
        change_type: ChangeType,
        change_data: Optional[Dict[str, Any]] = None
    ) -> SubscriptionHistory:
        """Create a subscription history entry for audit and tracking"""
        history_entry = SubscriptionHistory(
            subscription_id=subscription_id,
            change_type=change_type,
            change_data=change_data,
            changed_at=datetime.utcnow()
        )
        
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        return history_entry

    @staticmethod
    def create_subscription(
        db: Session, 
        subscription_data: SubscriptionCreate
    ) -> Subscription:
        """Create a new subscription"""
        # Calculate dates
        now = datetime.utcnow()
        start_date = now
        
        # Set end date based on billing cycle
        if subscription_data.billing_cycle == BillingCycle.MONTHLY:
            end_date = now + timedelta(days=30)
        else:  # ANNUALLY
            end_date = now + timedelta(days=365)
        
        # Set trial period if specified
        trial_end_date = None
        if subscription_data.trial_days:
            trial_end_date = now + timedelta(days=subscription_data.trial_days)
        
        # Verify price matches the plan and billing cycle
        expected_price = PRICING.get(subscription_data.plan, {}).get(subscription_data.billing_cycle)
        if expected_price and subscription_data.price != expected_price:
            subscription_data.price = expected_price
        
        # Create the subscription
        db_subscription = Subscription(
            user_id=subscription_data.user_id,
            plan=subscription_data.plan,
            billing_cycle=subscription_data.billing_cycle,
            price=subscription_data.price,
            start_date=start_date,
            end_date=end_date,
            auto_renew=subscription_data.auto_renew,
            trial_end_date=trial_end_date,
            payment_method_id=subscription_data.payment_method_id,
            payment_method_type=subscription_data.payment_method_type,
            # PayPal specific fields
            paypal_agreement_id=subscription_data.paypal_agreement_id,
            paypal_payer_id=subscription_data.paypal_payer_id,
            is_active=True
        )
        
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        
        # Create history entry for subscription creation
        SubscriptionService.create_history_entry(
            db=db,
            subscription_id=db_subscription.id,
            change_type=ChangeType.CREATED,
            change_data={
                "plan": db_subscription.plan.value,
                "billing_cycle": db_subscription.billing_cycle.value,
                "price": db_subscription.price,
                "payment_method_type": db_subscription.payment_method_type.value if db_subscription.payment_method_type else None,
                "is_paypal": db_subscription.payment_method_type == PaymentMethod.PAYPAL,
                "trial_days": subscription_data.trial_days
            }
        )
        
        return db_subscription
    
    @staticmethod
    def update_subscription(
        db: Session, 
        subscription_id: int, 
        subscription_data: SubscriptionUpdate
    ) -> Optional[Subscription]:
        """Update an existing subscription"""
        db_subscription = SubscriptionService.get_subscription(db, subscription_id)
        if not db_subscription:
            return None
        
        # Track changes for history entry
        old_values = {}
        new_values = {}
        
        # Update fields
        update_data = subscription_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(db_subscription, key):
                old_values[key] = getattr(db_subscription, key)
                if isinstance(old_values[key], enum.Enum):
                    old_values[key] = old_values[key].value
                
                setattr(db_subscription, key, value)
                
                new_values[key] = value
                if isinstance(new_values[key], enum.Enum):
                    new_values[key] = new_values[key].value
        
        db.commit()
        db.refresh(db_subscription)
        
        # Create history entry for subscription update
        if old_values:
            SubscriptionService.create_history_entry(
                db=db,
                subscription_id=db_subscription.id,
                change_type=ChangeType.UPDATED,
                change_data={
                    "old_values": old_values,
                    "new_values": new_values
                }
            )
        
        return db_subscription
    
    @staticmethod
    def cancel_subscription(
        db: Session, 
        subscription_id: int, 
        immediate: bool = False,
        reason: Optional[str] = None
    ) -> Optional[Subscription]:
        """Cancel a subscription"""
        db_subscription = SubscriptionService.get_subscription(db, subscription_id)
        if not db_subscription:
            return None
        
        try:
            # If we have a Stripe subscription ID, cancel it in Stripe
            if db_subscription.provider_subscription_id:
                logger.info(f"Canceling Stripe subscription: {db_subscription.provider_subscription_id}")
                
                # Cancel in Stripe
                StripeService.cancel_subscription(
                    subscription_id=db_subscription.provider_subscription_id,
                    immediate=immediate
                )
            
            # Update local subscription record
            if immediate:
                # Immediate cancellation
                db_subscription.is_active = False
            else:
                # Cancel at end of billing period (just let it expire)
                db_subscription.auto_renew = False
            
            db_subscription.canceled_at = datetime.utcnow()
            db.commit()
            db.refresh(db_subscription)
            
            # Create history entry for cancellation
            SubscriptionService.create_history_entry(
                db=db,
                subscription_id=db_subscription.id,
                change_type=ChangeType.CANCELLED,
                change_data={
                    "immediate": immediate,
                    "reason": reason,
                    "provider_subscription_id": db_subscription.provider_subscription_id,
                    "is_paypal": db_subscription.payment_method_type == PaymentMethod.PAYPAL
                }
            )
            
            return db_subscription
            
        except stripe.error.StripeError as e:
            db.rollback()
            logger.error(f"Stripe error canceling subscription: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel subscription: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error canceling subscription: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel subscription: {str(e)}"
            )
    
    @staticmethod
    def change_plan(
        db: Session, 
        subscription_id: int, 
        new_plan: SubscriptionPlan,
        new_billing_cycle: Optional[BillingCycle] = None,
        prorate: bool = True
    ) -> Optional[Subscription]:
        """Change a subscription's plan"""
        db_subscription = SubscriptionService.get_subscription(db, subscription_id)
        if not db_subscription:
            return None
        
        try:
            # Store old plan info for logging
            old_plan = db_subscription.plan
            old_cycle = db_subscription.billing_cycle
            
            # Update plan
            db_subscription.plan = new_plan
            
            # Update billing cycle if specified
            if new_billing_cycle:
                db_subscription.billing_cycle = new_billing_cycle
            
            # Update price based on plan and billing cycle
            db_subscription.price = PRICING.get(new_plan, {}).get(db_subscription.billing_cycle, db_subscription.price)
            
            # If we have a Stripe subscription, update it there
            if db_subscription.provider_subscription_id:
                # Get Stripe price ID from settings
                plan_key = db_subscription.plan.value.lower()
                cycle_key = db_subscription.billing_cycle.value.lower()
                
                # Get new price ID from settings
                new_price_id = settings.STRIPE_PRICE_IDS.get(plan_key, {}).get(cycle_key)
                
                if not new_price_id:
                    logger.error(f"Could not find Stripe price ID for plan {db_subscription.plan} and cycle {db_subscription.billing_cycle}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid subscription plan or billing cycle"
                    )
                
                # Update in Stripe
                logger.info(f"Changing plan in Stripe: {db_subscription.provider_subscription_id} to {new_price_id}")
                
                # Set proration behavior
                proration_behavior = "create_prorations" if prorate else "none"
                
                # Update the subscription in Stripe
                stripe_subscription = StripeService.update_subscription(
                    subscription_id=db_subscription.provider_subscription_id,
                    price_id=new_price_id,
                    metadata={
                        "subscription_id": str(db_subscription.id),
                        "plan": db_subscription.plan.value,
                        "billing_cycle": db_subscription.billing_cycle.value
                    },
                    proration_behavior=proration_behavior
                )
                
                # Log the change
                logger.info(f"Plan changed from {old_plan.value}/{old_cycle.value} to {new_plan.value}/{db_subscription.billing_cycle.value}")
                
                # Update local end date based on Stripe response
                if stripe_subscription.get("current_period_end"):
                    # Convert Unix timestamp to datetime
                    end_date = datetime.fromtimestamp(stripe_subscription["current_period_end"])
                    db_subscription.end_date = end_date
                
            # If no Stripe subscription, handle proration manually
            elif prorate and db_subscription.end_date:
                # Calculate remaining days in current cycle
                now = datetime.utcnow()
                days_left = max(0, (db_subscription.end_date - now).days)
                
                # Calculate total days based on actual months/years, not fixed values
                if old_cycle == BillingCycle.MONTHLY:
                    start_of_cycle = db_subscription.end_date - timedelta(days=30)  # Approximate
                    days_in_old_cycle = (db_subscription.end_date - start_of_cycle).days
                else:  # ANNUALLY
                    start_of_cycle = db_subscription.end_date - timedelta(days=365)  # Approximate
                    days_in_old_cycle = (db_subscription.end_date - start_of_cycle).days
                
                # Only prorate if there are days left
                if days_left > 0:
                    # Calculate new end date based on remaining value and new price
                    old_price = PRICING.get(old_plan, {}).get(old_cycle, 0)
                    if old_price <= 0 or db_subscription.price <= 0:
                        # Handle edge case where prices aren't positive
                        logger.warning(f"Invalid prices for proration: old_price={old_price}, new_price={db_subscription.price}")
                        db_subscription.end_date = now + timedelta(days=days_left)
                    else:
                        # Calculate remaining value and apply to new cycle
                        remaining_value = (days_left / days_in_old_cycle) * old_price
                        
                        # Calculate days in new cycle based on pricing
                        if db_subscription.billing_cycle == BillingCycle.MONTHLY:
                            days_in_new_cycle = (remaining_value / db_subscription.price) * 30
                        else:  # ANNUALLY
                            days_in_new_cycle = (remaining_value / db_subscription.price) * 365
                        
                        # Ensure we always give at least one day
                        days_in_new_cycle = max(1, round(days_in_new_cycle))
                        
                        # Update end date
                        db_subscription.end_date = now + timedelta(days=days_in_new_cycle)
                        
                        logger.info(f"Prorated subscription: remaining={days_left} days, value=${remaining_value:.2f}, " +
                                   f"new days={days_in_new_cycle}, new end date={db_subscription.end_date}")
            
            db.commit()
            db.refresh(db_subscription)
            
            # Add history entry for plan change
            SubscriptionService.create_history_entry(
                db=db,
                subscription_id=db_subscription.id,
                change_type=ChangeType.PLAN_CHANGED,
                change_data={
                    "old_plan": old_plan.value,
                    "new_plan": new_plan.value,
                    "old_cycle": old_cycle.value,
                    "new_cycle": db_subscription.billing_cycle.value,
                    "old_price": PRICING.get(old_plan, {}).get(old_cycle),
                    "new_price": db_subscription.price,
                    "prorate": prorate
                }
            )
            
            return db_subscription
            
        except stripe.error.StripeError as e:
            db.rollback()
            logger.error(f"Stripe error changing plan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to change subscription plan: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error changing plan: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to change subscription plan: {str(e)}"
            )
    
    @staticmethod
    def create_payment(
        db: Session, 
        payment_data: SubscriptionPaymentCreate
    ) -> SubscriptionPayment:
        """Create a new payment record"""
        db_payment = SubscriptionPayment(
            subscription_id=payment_data.subscription_id,
            amount=payment_data.amount,
            status=payment_data.status,
            provider_payment_id=payment_data.provider_payment_id,
            provider_payment_data=payment_data.provider_payment_data,
        )
        
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        
        # Create history entry for payment
        change_type = ChangeType.PAYMENT_SUCCEEDED if payment_data.status == PaymentStatus.SUCCEEDED else ChangeType.PAYMENT_FAILED
        
        SubscriptionService.create_history_entry(
            db=db,
            subscription_id=payment_data.subscription_id,
            change_type=change_type,
            change_data={
                "payment_id": db_payment.id,
                "amount": payment_data.amount,
                "status": payment_data.status.value,
                "provider_payment_id": payment_data.provider_payment_id
            }
        )
        
        return db_payment
    
    @staticmethod
    def process_payment(
        db: Session,
        subscription_id: int,
        payment_method: PaymentMethodCreate
    ) -> Tuple[bool, str, Optional[SubscriptionPayment], Optional[Dict[str, Any]]]:
        """Process a payment for a subscription"""
        db_subscription = SubscriptionService.get_subscription(db, subscription_id)
        if not db_subscription:
            return False, "Subscription not found", None, None
        
        try:
            # Get user information for Stripe customer creation
            user = db.query(User).filter(User.id == db_subscription.user_id).first()
            if not user:
                return False, "User not found", None, None
            
            # Create or retrieve Stripe customer
            if not user.stripe_customer_id:
                # Create new Stripe customer
                customer = StripeService.create_customer(
                    user_id=user.id,
                    email=user.email,
                    name=f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else None
                )
                user.stripe_customer_id = customer["id"]
                db.commit()
            
            # Process based on payment method type
            if payment_method.type == PaymentMethod.CREDIT_CARD and payment_method.credit_card:
                # Create Stripe payment method
                card_info = payment_method.credit_card
                stripe_payment_method = StripeService.create_payment_method(
                    card_info=card_info,
                    customer_id=user.stripe_customer_id
                )
                
                # Store secure reference to payment method
                payment_details = {
                    "card_number": card_info.card_number[-4:],  # Store only last 4 digits
                    "expiry": f"{card_info.expiry_month}/{card_info.expiry_year}",
                    "cardholder": card_info.cardholder_name,
                    "stripe_payment_method_id": stripe_payment_method["id"]
                }
                encrypted_details = encryptor.encrypt(payment_details)
                db_subscription.encrypted_payment_details = encrypted_details
                db_subscription.payment_method_type = PaymentMethod.CREDIT_CARD
                db_subscription.payment_method_id = stripe_payment_method["id"]
                
                # Get Stripe price ID from settings
                plan_key = db_subscription.plan.value.lower()
                cycle_key = db_subscription.billing_cycle.value.lower()
                
                # Get price ID from settings
                price_id = settings.STRIPE_PRICE_IDS.get(plan_key, {}).get(cycle_key)
                
                if not price_id:
                    return False, "Invalid subscription plan or billing cycle", None, None
                
                # Create Stripe subscription
                stripe_subscription = StripeService.create_subscription(
                    customer_id=user.stripe_customer_id,
                    price_id=price_id,
                    payment_method_id=stripe_payment_method["id"],
                    metadata={
                        "subscription_id": str(db_subscription.id),
                        "user_id": str(user.id),
                        "plan": db_subscription.plan.value,
                        "billing_cycle": db_subscription.billing_cycle.value
                    }
                )
                
                # Store Stripe subscription ID
                db_subscription.provider_subscription_id = stripe_subscription["id"]
                
                # Create payment record based on invoice
                latest_invoice = stripe_subscription.get("latest_invoice", {})
                payment_intent = latest_invoice.get("payment_intent", {})
                
                payment_data = SubscriptionPaymentCreate(
                    subscription_id=subscription_id,
                    amount=db_subscription.price,
                    status=PaymentStatus.SUCCEEDED if payment_intent.get("status") == "succeeded" else PaymentStatus.PENDING,
                    provider_payment_id=latest_invoice.get("id"),
                    provider_payment_data=latest_invoice
                )
                db_payment = SubscriptionService.create_payment(db, payment_data)
                
                db.commit()
                return True, "Payment processed successfully", db_payment, None
                
            elif payment_method.type == PaymentMethod.BANK_ACCOUNT and payment_method.bank_account:
                # Bank account payment through Stripe ACH
                bank_info = payment_method.bank_account
                
                # Try modern Stripe ACH method first (using PaymentMethod API)
                try:
                    # Create Stripe payment method
                    stripe_payment_method = StripeService.create_payment_method(
                        bank_info=bank_info,
                        customer_id=user.stripe_customer_id
                    )
                    
                    # Store secure reference to bank account
                    payment_details = {
                        "account_number": f"****{bank_info.account_number[-4:]}",
                        "routing_number": f"****{bank_info.routing_number[-4:]}",
                        "account_type": bank_info.account_type,
                        "account_holder": bank_info.account_holder_name,
                        "payment_method_id": stripe_payment_method["id"],
                        "verification_status": "pending"
                    }
                    encrypted_details = encryptor.encrypt(payment_details)
                    db_subscription.encrypted_payment_details = encrypted_details
                    db_subscription.payment_method_type = PaymentMethod.BANK_ACCOUNT
                    db_subscription.payment_method_id = stripe_payment_method["id"]
                    
                    # Get Stripe price ID from settings
                    plan_key = db_subscription.plan.value.lower()
                    cycle_key = db_subscription.billing_cycle.value.lower()
                    price_id = settings.STRIPE_PRICE_IDS.get(plan_key, {}).get(cycle_key)
                    
                    if not price_id:
                        return False, "Invalid subscription plan or billing cycle", None, None
                    
                    # Create Stripe subscription with pending payment
                    # Note: ACH requires customer confirmation before charging
                    stripe_subscription = StripeService.create_subscription(
                        customer_id=user.stripe_customer_id,
                        price_id=price_id,
                        payment_method_id=stripe_payment_method["id"],
                        metadata={
                            "subscription_id": str(db_subscription.id),
                            "user_id": str(user.id),
                            "plan": db_subscription.plan.value,
                            "billing_cycle": db_subscription.billing_cycle.value
                        }
                    )
                    
                    # Store Stripe subscription ID
                    db_subscription.provider_subscription_id = stripe_subscription["id"]
                    
                    # Create payment record
                    payment_data = SubscriptionPaymentCreate(
                        subscription_id=subscription_id,
                        amount=db_subscription.price,
                        status=PaymentStatus.PENDING,
                        provider_payment_id=stripe_subscription.get("latest_invoice", {}).get("id"),
                        provider_payment_data=stripe_subscription.get("latest_invoice", {})
                    )
                    db_payment = SubscriptionService.create_payment(db, payment_data)
                    
                    db.commit()
                    
                    # Return information for bank account verification
                    return True, "Bank account payment method created successfully", db_payment, {
                        "requires_verification": True,
                        "verification_method": "microdeposits",
                        "estimated_arrival_days": 1,
                        "subscription_id": db_subscription.id
                    }
                    
                except Exception as e:
                    logger.error(f"Error creating ACH payment method: {str(e)}")
                    
                    # Fall back to older token-based ACH method if modern method fails
                    try:
                        # Create bank account token and attach to customer
                        bank_account = StripeService.create_bank_account_token(
                            bank_info=bank_info,
                            customer_id=user.stripe_customer_id
                        )
                        
                        # Store secure reference to bank account
                        payment_details = {
                            "account_number": f"****{bank_info.account_number[-4:]}",
                            "routing_number": f"****{bank_info.routing_number[-4:]}",
                            "account_type": bank_info.account_type,
                            "account_holder": bank_info.account_holder_name,
                            "bank_account_id": bank_account["id"],
                            "verification_status": "pending"
                        }
                        encrypted_details = encryptor.encrypt(payment_details)
                        db_subscription.encrypted_payment_details = encrypted_details
                        db_subscription.payment_method_type = PaymentMethod.BANK_ACCOUNT
                        db_subscription.payment_method_id = bank_account["id"]
                        
                        # Create pending payment record
                        payment_data = SubscriptionPaymentCreate(
                            subscription_id=subscription_id,
                            amount=db_subscription.price,
                            status=PaymentStatus.PENDING,
                            provider_payment_id=bank_account["id"]
                        )
                        db_payment = SubscriptionService.create_payment(db, payment_data)
                        
                        db.commit()
                        
                        # Return information for bank account verification
                        return True, "Bank account payment method created successfully", db_payment, {
                            "requires_verification": True,
                            "verification_method": "microdeposits",
                            "estimated_arrival_days": 1,
                            "bank_account_id": bank_account["id"],
                            "subscription_id": db_subscription.id
                        }
                        
                    except Exception as token_error:
                        logger.error(f"Error with fallback ACH method: {str(token_error)}")
                        return False, f"Bank account processing failed: {str(token_error)}", None, None
                
                # This code should never be reached if either method succeeds or fails
                logger.error("Unexpected flow in ACH processing")
                return False, "Unexpected error in bank account processing", None, None
                
            elif payment_method.type == PaymentMethod.PAYPAL:
                # PayPal payment through Stripe checkout
                
                # Get frontend URLs from settings
                frontend_url = settings.FRONTEND_URL
                return_url = f"{frontend_url}/subscription/success?subscription_id={subscription_id}"
                cancel_url = f"{frontend_url}/subscription/cancel?subscription_id={subscription_id}"
                
                # Get Stripe price ID from settings
                plan_key = db_subscription.plan.value.lower()
                cycle_key = db_subscription.billing_cycle.value.lower()
                price_id = settings.STRIPE_PRICE_IDS.get(plan_key, {}).get(cycle_key)
                
                if not price_id:
                    return False, "Invalid subscription plan or billing cycle", None, None
                
                # Create PayPal checkout session
                paypal_order = StripeService.create_paypal_order(
                    customer_id=user.stripe_customer_id,
                    price_id=price_id,
                    return_url=return_url,
                    cancel_url=cancel_url,
                    metadata={
                        "subscription_id": str(db_subscription.id),
                        "user_id": str(user.id),
                        "plan": db_subscription.plan.value,
                        "billing_cycle": db_subscription.billing_cycle.value
                    }
                )
                
                # Store temporary payment method information
                payment_details = {
                    "payment_type": "paypal",
                    "checkout_session_id": paypal_order.get("id"),
                    "expires_at": paypal_order.get("expires_at")
                }
                encrypted_details = encryptor.encrypt(payment_details)
                db_subscription.encrypted_payment_details = encrypted_details
                db_subscription.payment_method_type = PaymentMethod.PAYPAL
                
                # We'll get the full PayPal details after PayPal checkout via webhook,
                # but we can store the metadata here for our reference
                paypal_metadata = metadata or {}
                if "subscription_id" in paypal_metadata:
                    # This will be populated with the actual PayPal agreement ID 
                    # by the webhook handler when the checkout is completed
                    db_subscription.paypal_agreement_id = None
                    
                    # If successful, this will get the actual PayPal payer ID
                    # from PayPal when the checkout is completed
                    db_subscription.paypal_payer_id = None
                
                # Create pending payment record
                payment_data = SubscriptionPaymentCreate(
                    subscription_id=subscription_id,
                    amount=db_subscription.price,
                    status=PaymentStatus.PENDING,
                    provider_payment_id=paypal_order.get("id")
                )
                db_payment = SubscriptionService.create_payment(db, payment_data)
                
                db.commit()
                
                # Return PayPal redirect URL
                return True, "PayPal checkout initiated", db_payment, {
                    "redirect_url": paypal_order.get("url"),
                    "session_id": paypal_order.get("id")
                }
                
            else:
                return False, "Unsupported payment method", None, None
                
        except stripe.error.StripeError as e:
            db.rollback()
            logger.error(f"Stripe error processing payment: {str(e)}")
            return False, f"Payment processing failed: {str(e)}", None, None
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing payment: {str(e)}")
            return False, f"Payment processing failed: {str(e)}", None, None
    
    @staticmethod
    def process_renewal(db: Session, subscription_id: int) -> bool:
        """Process a subscription renewal"""
        from datetime import datetime
        
        db_subscription = SubscriptionService.get_subscription(db, subscription_id)
        if not db_subscription:
            logger.error(f"Renewal failed: Subscription {subscription_id} not found")
            return False
        
        now = datetime.utcnow()
        
        # Check if renewal is needed
        if not db_subscription.is_active:
            logger.info(f"Renewal skipped: Subscription {subscription_id} is not active")
            return False
            
        if not db_subscription.auto_renew:
            logger.info(f"Renewal skipped: Subscription {subscription_id} is not set to auto-renew")
            return False
            
        if db_subscription.end_date and db_subscription.end_date > now:
            # Not yet time to renew
            logger.info(f"Renewal skipped: Subscription {subscription_id} end date is still in the future ({db_subscription.end_date})")
            return False
        
        try:
            # Process Stripe renewal if subscription is linked to Stripe
            if db_subscription.provider_subscription_id:
                logger.info(f"Processing Stripe renewal for subscription {subscription_id}")
                
                try:
                    # Fetch Stripe subscription to make sure it's still active
                    stripe_subscription = StripeService.get_subscription(db_subscription.provider_subscription_id)
                    
                    if stripe_subscription.get("status") != "active":
                        logger.warning(f"Stripe subscription {db_subscription.provider_subscription_id} is not active")
                        # Update local status
                        db_subscription.is_active = False
                        db.commit()
                        return False
                    
                    # Check payment method type - handle PayPal differently
                    if db_subscription.payment_method_type == PaymentMethod.PAYPAL:
                        logger.info(f"Processing PayPal subscription renewal for subscription {subscription_id}")
                        
                        # For PayPal, the renewal is typically handled automatically by Stripe's recurring billing
                        # So we just need to check the current period end from the subscription
                        if stripe_subscription.get("current_period_end"):
                            # Convert Unix timestamp to datetime
                            new_end_date = datetime.fromtimestamp(stripe_subscription["current_period_end"])
                            db_subscription.end_date = new_end_date
                            
                            # Create a payment record for tracking
                            payment_data = SubscriptionPaymentCreate(
                                subscription_id=subscription_id,
                                amount=db_subscription.price,
                                status=PaymentStatus.SUCCEEDED,
                                provider_payment_id=f"paypal_renewal_{now.strftime('%Y%m%d%H%M%S')}",
                                provider_payment_data={"stripe_subscription_id": stripe_subscription["id"]}
                            )
                            SubscriptionService.create_payment(db, payment_data)
                            
                            logger.info(f"Successfully updated PayPal subscription {subscription_id}, new end date: {db_subscription.end_date}")
                            db.commit()
                            return True
                        else:
                            logger.error(f"Could not determine end date for PayPal subscription {subscription_id}")
                            return False
                    
                    # For credit card payments, create and pay an invoice
                    # Create an invoice to charge the customer
                    invoice = StripeService.create_invoice(
                        customer_id=stripe_subscription.get("customer"),
                        subscription_id=db_subscription.provider_subscription_id
                    )
                    
                    # Attempt to collect payment
                    paid_invoice = StripeService.pay_invoice(invoice.get("id"))
                    
                    # Update local records based on Stripe response
                    if paid_invoice.get("status") == "paid":
                        # Calculate new end date based on Stripe billing period
                        if paid_invoice.get("lines", {}).get("data") and len(paid_invoice["lines"]["data"]) > 0:
                            line_item = paid_invoice["lines"]["data"][0]
                            period_end = line_item.get("period", {}).get("end")
                            if period_end:
                                # Convert Unix timestamp to datetime
                                new_end_date = datetime.fromtimestamp(period_end)
                                db_subscription.end_date = new_end_date
                            else:
                                # Fallback: calculate based on billing cycle
                                if db_subscription.billing_cycle == BillingCycle.MONTHLY:
                                    db_subscription.end_date = now + timedelta(days=30)
                                else:  # ANNUALLY
                                    db_subscription.end_date = now + timedelta(days=365)
                        
                        # Create payment record
                        payment_data = SubscriptionPaymentCreate(
                            subscription_id=subscription_id,
                            amount=db_subscription.price,
                            status=PaymentStatus.SUCCEEDED,
                            provider_payment_id=paid_invoice.get("id"),
                            provider_payment_data=paid_invoice
                        )
                        SubscriptionService.create_payment(db, payment_data)
                        
                        logger.info(f"Successfully renewed Stripe subscription {subscription_id}, new end date: {db_subscription.end_date}")
                        db.commit()
                        return True
                    else:
                        # Payment failed
                        payment_data = SubscriptionPaymentCreate(
                            subscription_id=subscription_id,
                            amount=db_subscription.price,
                            status=PaymentStatus.FAILED,
                            provider_payment_id=paid_invoice.get("id"),
                            provider_payment_data=paid_invoice
                        )
                        SubscriptionService.create_payment(db, payment_data)
                        
                        logger.error(f"Failed to collect payment for Stripe subscription {subscription_id}")
                        db.commit()
                        return False
                        
                except stripe.error.StripeError as e:
                    logger.error(f"Stripe error during renewal: {str(e)}")
                    db.rollback()
                    return False
            
            # No Stripe subscription, handle renewal locally
            else:
                logger.info(f"Processing local renewal for subscription {subscription_id}")
                
                # Calculate new end date
                if db_subscription.billing_cycle == BillingCycle.MONTHLY:
                    new_end_date = now + timedelta(days=30)
                else:  # ANNUALLY
                    new_end_date = now + timedelta(days=365)
                
                # Update subscription
                db_subscription.end_date = new_end_date
                
                # Create payment record
                payment_data = SubscriptionPaymentCreate(
                    subscription_id=subscription_id,
                    amount=db_subscription.price,
                    status=PaymentStatus.SUCCEEDED
                )
                SubscriptionService.create_payment(db, payment_data)
                
                logger.info(f"Successfully renewed local subscription {subscription_id}, new end date: {db_subscription.end_date}")
                db.commit()
                return True
            
        except Exception as e:
            logger.error(f"Error renewing subscription {subscription_id}: {str(e)}")
            db.rollback()
            return False
    
    @staticmethod
    def get_subscription_history(db: Session, subscription_id: int) -> List[SubscriptionHistory]:
        """Get the history entries for a subscription"""
        return db.query(SubscriptionHistory).filter(
            SubscriptionHistory.subscription_id == subscription_id
        ).order_by(SubscriptionHistory.changed_at.desc()).all()
    
    @staticmethod
    def check_feature_access(db: Session, user_id: int, feature: str) -> Tuple[bool, Optional[SubscriptionPlan]]:
        """Check if a user has access to a specific feature"""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, None
        
        # Admin has access to everything
        if user.role == "admin":
            return True, None
        
        # Get active subscription
        subscription = SubscriptionService.get_active_subscription(db, user_id)
        
        # Map features to required subscription plans
        feature_requirements = {
            # Free tier features
            "basic_trading": None,
            "paper_trading": None,
            "basic_education": None,
            "market_data_basic": None,
            "portfolio_tracking": None,
            
            # Premium tier features
            "advanced_trading": SubscriptionPlan.PREMIUM,
            "fractional_shares": SubscriptionPlan.PREMIUM,
            "ai_recommendations": SubscriptionPlan.PREMIUM,
            "unlimited_recurring_investments": SubscriptionPlan.PREMIUM,
            "tax_loss_harvesting": SubscriptionPlan.PREMIUM,
            "advanced_education": SubscriptionPlan.PREMIUM,
            "market_data_advanced": SubscriptionPlan.PREMIUM,
            "high_yield_savings": SubscriptionPlan.PREMIUM,
            "retirement_accounts": SubscriptionPlan.PREMIUM,
            "api_access": SubscriptionPlan.PREMIUM,
            
            # Family tier features
            "custodial_accounts": SubscriptionPlan.FAMILY,
            "guardian_approval": SubscriptionPlan.FAMILY,
            "family_challenges": SubscriptionPlan.FAMILY,
            "educational_games": SubscriptionPlan.FAMILY,
            "multiple_retirement_accounts": SubscriptionPlan.FAMILY,
        }
        
        # Free tier features are available to everyone
        required_plan = feature_requirements.get(feature)
        if required_plan is None:
            return True, None
        
        # Check subscription
        if not subscription:
            return False, required_plan
        
        # Premium subscribers can access premium features
        if required_plan == SubscriptionPlan.PREMIUM:
            return subscription.plan in (SubscriptionPlan.PREMIUM, SubscriptionPlan.FAMILY), required_plan
        
        # Family subscribers can access family features
        if required_plan == SubscriptionPlan.FAMILY:
            return subscription.plan == SubscriptionPlan.FAMILY, required_plan
        
        return False, required_plan