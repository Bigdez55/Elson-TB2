from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import stripe
import structlog
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.subscription import PaymentStatus, Subscription, SubscriptionPayment
from app.models.user import User
from app.schemas.subscription import BankAccountInfo, CreditCardInfo

# Initialize Stripe with API key
stripe.api_key = settings.STRIPE_API_KEY

# Get logger
logger = structlog.get_logger(__name__)


class StripeService:
    """Service for handling Stripe payment processing"""

    @staticmethod
    def create_customer(
        user_id: int, email: str, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Stripe customer.

        Args:
            user_id: Internal user ID
            email: User's email address
            name: User's full name (optional)

        Returns:
            Stripe customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email, name=name, metadata={"user_id": str(user_id)}
            )
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def create_payment_method(
        card_info: Optional[CreditCardInfo] = None,
        bank_info: Optional[BankAccountInfo] = None,
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new payment method.

        Args:
            card_info: Credit card information (optional)
            bank_info: Bank account information (optional)
            customer_id: Stripe customer ID to attach the payment method to

        Returns:
            Stripe payment method object
        """
        try:
            if card_info:
                # Create card payment method
                payment_method = stripe.PaymentMethod.create(
                    type="card",
                    card={
                        "number": card_info.card_number,
                        "exp_month": card_info.expiry_month,
                        "exp_year": card_info.expiry_year,
                        "cvc": card_info.cvc,
                    },
                    billing_details={"name": card_info.cardholder_name},
                )
            elif bank_info:
                # Create ACH bank account payment method
                payment_method = stripe.PaymentMethod.create(
                    type="us_bank_account",
                    us_bank_account={
                        "account_number": bank_info.account_number,
                        "routing_number": bank_info.routing_number,
                        "account_type": bank_info.account_type,
                    },
                    billing_details={"name": bank_info.account_holder_name},
                )
            else:
                raise ValueError("Either card_info or bank_info must be provided")

            # Attach to customer if provided
            if customer_id:
                stripe.PaymentMethod.attach(payment_method.id, customer=customer_id)

            return payment_method
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment method: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def create_subscription(
        customer_id: str,
        price_id: str,
        payment_method_id: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Stripe subscription.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            payment_method_id: Stripe payment method ID
            metadata: Additional metadata for the subscription

        Returns:
            Stripe subscription object
        """
        try:
            # Set default payment method for customer
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                expand=["latest_invoice.payment_intent"],
                metadata=metadata or {},
            )

            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def update_subscription(
        subscription_id: str,
        price_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        cancel_at_period_end: Optional[bool] = None,
        proration_behavior: str = "create_prorations",
    ) -> Dict[str, Any]:
        """
        Update an existing Stripe subscription.

        Args:
            subscription_id: Stripe subscription ID
            price_id: New Stripe price ID (for plan changes)
            metadata: New metadata
            cancel_at_period_end: Whether to cancel at period end
            proration_behavior: How to handle proration

        Returns:
            Updated Stripe subscription object
        """
        try:
            update_params = {}

            if price_id:
                update_params["items"] = [
                    {
                        "id": stripe.Subscription.retrieve(subscription_id)["items"][
                            "data"
                        ][0]["id"],
                        "price": price_id,
                    }
                ]
                update_params["proration_behavior"] = proration_behavior

            if metadata:
                update_params["metadata"] = metadata

            if cancel_at_period_end is not None:
                update_params["cancel_at_period_end"] = cancel_at_period_end

            subscription = stripe.Subscription.modify(subscription_id, **update_params)

            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def cancel_subscription(
        subscription_id: str, immediate: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a Stripe subscription.

        Args:
            subscription_id: Stripe subscription ID
            immediate: Whether to cancel immediately (vs. at period end)

        Returns:
            Updated Stripe subscription object
        """
        try:
            if immediate:
                # Cancel immediately
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                # Cancel at period end
                subscription = stripe.Subscription.modify(
                    subscription_id, cancel_at_period_end=True
                )

            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def get_payment_methods(
        customer_id: str, type: str = "card"
    ) -> List[Dict[str, Any]]:
        """
        Get a customer's payment methods.

        Args:
            customer_id: Stripe customer ID
            type: Payment method type (card, bank_account, etc.)

        Returns:
            List of payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(customer=customer_id, type=type)
            return payment_methods.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment methods: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def delete_payment_method(payment_method_id: str) -> Dict[str, Any]:
        """
        Delete a payment method.

        Args:
            payment_method_id: Stripe payment method ID

        Returns:
            Deleted payment method object
        """
        try:
            return stripe.PaymentMethod.detach(payment_method_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to delete payment method: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def create_checkout_session(
        price_id: str,
        customer_id: Optional[str] = None,
        success_url: str = None,
        cancel_url: str = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session.

        Args:
            price_id: Stripe price ID
            customer_id: Optional Stripe customer ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            metadata: Additional metadata

        Returns:
            Checkout session object with URL
        """
        try:
            # Set default URLs if not provided
            success_url = success_url or f"{settings.FRONTEND_URL}/subscription/success"
            cancel_url = cancel_url or f"{settings.FRONTEND_URL}/subscription/cancel"

            session_params = {
                "payment_method_types": ["card"],
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": "subscription",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {},
            }

            if customer_id:
                session_params["customer"] = customer_id

            session = stripe.checkout.Session.create(**session_params)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def handle_webhook_event(
        payload: bytes, sig_header: str, webhook_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify and handle a Stripe webhook event.

        Args:
            payload: Raw request body
            sig_header: Stripe signature header
            webhook_secret: Webhook signing secret (defaults to settings)

        Returns:
            Parsed event object
        """
        webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET

        if not webhook_secret:
            logger.error("Webhook secret not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook secret not configured",
            )

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            return event
        except ValueError as e:
            # Invalid payload
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
            )

    @staticmethod
    def process_subscription_updated(
        db: Session, event_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process a subscription.updated webhook event.

        Args:
            db: Database session
            event_data: Webhook event data

        Returns:
            Success status and message
        """
        try:
            subscription = event_data["object"]

            # Find internal subscription by Stripe ID
            db_subscription = (
                db.query(Subscription)
                .filter(Subscription.provider_subscription_id == subscription["id"])
                .first()
            )

            if not db_subscription:
                return False, f"Subscription not found: {subscription['id']}"

            # Update subscription status
            status = subscription["status"]

            if status == "active":
                db_subscription.is_active = True
            elif status in ["canceled", "unpaid", "incomplete_expired"]:
                db_subscription.is_active = False
                if status == "canceled":
                    db_subscription.canceled_at = datetime.utcnow()
                    db_subscription.auto_renew = False

            # Update end date if needed
            if subscription.get("cancel_at_period_end"):
                db_subscription.auto_renew = False

            db.commit()
            return True, "Subscription updated successfully"

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing subscription.updated: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """
        Get a Stripe subscription by ID.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe subscription object
        """
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def create_invoice(
        customer_id: str,
        subscription_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Stripe invoice for a customer.

        Args:
            customer_id: Stripe customer ID
            subscription_id: Optional Stripe subscription ID
            description: Optional invoice description

        Returns:
            Stripe invoice object
        """
        try:
            invoice_params = {
                "customer": customer_id,
                "auto_advance": False,  # Don't automatically finalize
            }

            if subscription_id:
                invoice_params["subscription"] = subscription_id

            if description:
                invoice_params["description"] = description

            invoice = stripe.Invoice.create(**invoice_params)

            # Add subscription line items if provided
            if subscription_id:
                stripe.InvoiceItem.create(
                    customer=customer_id,
                    subscription=subscription_id,
                    invoice=invoice.id,
                )

            # Finalize the invoice
            invoice = stripe.Invoice.finalize_invoice(invoice.id)

            return invoice
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create invoice: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def pay_invoice(invoice_id: str) -> Dict[str, Any]:
        """
        Attempt to pay a Stripe invoice.

        Args:
            invoice_id: Stripe invoice ID

        Returns:
            Paid invoice object or error details
        """
        try:
            return stripe.Invoice.pay(invoice_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to pay invoice: {str(e)}")
            # Return the error rather than raising an exception
            # so we can handle payment failures gracefully
            return {"error": str(e), "status": "failed", "id": invoice_id}

    @staticmethod
    def process_invoice_paid(
        db: Session, event_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process an invoice.paid webhook event.

        Args:
            db: Database session
            event_data: Webhook event data

        Returns:
            Success status and message
        """
        try:
            invoice = event_data["object"]

            # Find subscription
            if not invoice.get("subscription"):
                return False, "No subscription in invoice"

            db_subscription = (
                db.query(Subscription)
                .filter(
                    Subscription.provider_subscription_id == invoice["subscription"]
                )
                .first()
            )

            if not db_subscription:
                return False, f"Subscription not found: {invoice['subscription']}"

            # Create payment record
            payment = SubscriptionPayment(
                subscription_id=db_subscription.id,
                amount=invoice["amount_paid"] / 100,  # Convert cents to dollars
                status=PaymentStatus.SUCCEEDED,
                provider_payment_id=invoice["id"],
                provider_payment_data=invoice,
            )

            db.add(payment)

            # Update subscription end date based on invoice data when available
            if (
                invoice.get("lines", {}).get("data")
                and len(invoice["lines"]["data"]) > 0
            ):
                line_item = invoice["lines"]["data"][0]
                period_end = line_item.get("period", {}).get("end")
                if period_end:
                    # Convert Unix timestamp to datetime
                    new_end_date = datetime.fromtimestamp(period_end)
                    db_subscription.end_date = new_end_date
                else:
                    # Fallback: use billing cycle
                    if db_subscription.billing_cycle == "monthly":
                        db_subscription.end_date = datetime.utcnow() + timedelta(
                            days=30
                        )
                    else:
                        db_subscription.end_date = datetime.utcnow() + timedelta(
                            days=365
                        )
            else:
                # Fallback if no line items
                if db_subscription.billing_cycle == "monthly":
                    db_subscription.end_date = datetime.utcnow() + timedelta(days=30)
                else:
                    db_subscription.end_date = datetime.utcnow() + timedelta(days=365)

            # Ensure subscription is active
            db_subscription.is_active = True

            db.commit()
            return True, "Payment recorded successfully"

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing invoice.paid: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def process_payment_failed(
        db: Session, event_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process an invoice.payment_failed webhook event.

        Args:
            db: Database session
            event_data: Webhook event data

        Returns:
            Success status and message
        """
        try:
            invoice = event_data["object"]

            # Find subscription
            if not invoice.get("subscription"):
                return False, "No subscription in invoice"

            db_subscription = (
                db.query(Subscription)
                .filter(
                    Subscription.provider_subscription_id == invoice["subscription"]
                )
                .first()
            )

            if not db_subscription:
                return False, f"Subscription not found: {invoice['subscription']}"

            # Create failed payment record
            payment = SubscriptionPayment(
                subscription_id=db_subscription.id,
                amount=invoice.get("amount_due", 0) / 100,  # Convert cents to dollars
                status=PaymentStatus.FAILED,
                provider_payment_id=invoice["id"],
                provider_payment_data=invoice,
            )

            db.add(payment)

            # Get retry count from invoice attempt count
            retry_count = invoice.get("attempt_count", 1) - 1

            # If we've exceeded retry attempts (Stripe default is 3), mark subscription inactive
            max_retries = 3
            if retry_count >= max_retries:
                logger.warning(
                    f"Payment failed after {retry_count} retries for subscription {db_subscription.id}"
                )
                db_subscription.is_active = False

                # We don't set auto_renew to False to allow reactivation if customer updates payment method

                # Log the next steps
                logger.info(
                    f"Subscription {db_subscription.id} marked inactive due to payment failures"
                )
            else:
                logger.info(
                    f"Payment failed (attempt {retry_count+1}/{max_retries+1}) for subscription {db_subscription.id}"
                )

            db.commit()

            # Return success status with attempt information
            return (
                True,
                f"Failed payment recorded (attempt {retry_count+1}/{max_retries+1})",
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing payment failure: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def process_payment_method_updated(
        db: Session, event_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process a payment_method.updated webhook event.

        Args:
            db: Database session
            event_data: Webhook event data

        Returns:
            Success status and message
        """
        try:
            payment_method = event_data["object"]
            customer_id = payment_method.get("customer")

            if not customer_id:
                return False, "No customer linked to payment method"

            # Find all subscriptions for this customer
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if not user:
                return False, f"No user found for Stripe customer {customer_id}"

            # Update payment method details for subscriptions using this payment method
            subscriptions = (
                db.query(Subscription)
                .filter(
                    Subscription.user_id == user.id,
                    Subscription.payment_method_id == payment_method["id"],
                )
                .all()
            )

            if not subscriptions:
                return True, "No subscriptions found using this payment method"

            for subscription in subscriptions:
                # Update payment method details
                card_details = payment_method.get("card", {})
                if card_details:
                    # Encrypt the updated card information
                    payment_details = {
                        "card_number": f"**** **** **** {card_details.get('last4', '****')}",
                        "expiry": f"{card_details.get('exp_month', '**')}/{card_details.get('exp_year', '****')}",
                        "brand": card_details.get("brand", "unknown"),
                        "stripe_payment_method_id": payment_method["id"],
                    }

                    # Encrypt updated payment details
                    try:
                        from app.core.encryption import AES256Encryptor

                        encryptor = AES256Encryptor()
                        encrypted_details = encryptor.encrypt(payment_details)
                        subscription.encrypted_payment_details = encrypted_details
                    except Exception as enc_err:
                        logger.error(
                            f"Failed to encrypt updated payment details: {str(enc_err)}"
                        )

            db.commit()
            return (
                True,
                f"Updated payment method for {len(subscriptions)} subscriptions",
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing payment method update: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def create_paypal_order(
        customer_id: str,
        price_id: str,
        return_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a PayPal order for subscription payment.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            return_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            metadata: Additional metadata for the order

        Returns:
            PayPal order object with redirect URL
        """
        try:
            # Create a Checkout Session with PayPal as the payment method
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["paypal"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=return_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )

            return {
                "id": checkout_session.id,
                "url": checkout_session.url,
                "expires_at": checkout_session.expires_at,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create PayPal order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def create_bank_account_token(
        bank_info: BankAccountInfo, customer_id: str
    ) -> Dict[str, Any]:
        """
        Create a bank account token for ACH payments and attach to customer.
        This is used for the older Stripe ACH flow.

        Args:
            bank_info: Bank account information
            customer_id: Stripe customer ID

        Returns:
            Bank account token
        """
        try:
            # Create bank account token
            bank_token = stripe.Token.create(
                bank_account={
                    "country": "US",
                    "currency": "usd",
                    "account_holder_name": bank_info.account_holder_name,
                    "account_holder_type": "individual",
                    "routing_number": bank_info.routing_number,
                    "account_number": bank_info.account_number,
                    "account_type": bank_info.account_type,
                }
            )

            # Add bank account to customer
            bank_account = stripe.Customer.create_source(
                customer_id, source=bank_token.id
            )

            return bank_account
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create bank account token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def verify_bank_account(
        customer_id: str, bank_account_id: str, amounts: List[int]
    ) -> Dict[str, Any]:
        """
        Verify a bank account by confirming the micro-deposit amounts.

        Args:
            customer_id: Stripe customer ID
            bank_account_id: Stripe bank account ID
            amounts: List of micro-deposit amounts in cents (usually two deposits)

        Returns:
            Verified bank account
        """
        try:
            bank_account = stripe.Customer.verify_source(
                customer_id, bank_account_id, amounts=amounts
            )
            return bank_account
        except stripe.error.StripeError as e:
            logger.error(f"Failed to verify bank account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment service error: {str(e)}",
            )

    @staticmethod
    def process_bank_account_verification(
        db: Session, event_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process a bank account verification event.

        Args:
            db: Database session
            event_data: Webhook event data

        Returns:
            Success status and message
        """
        try:
            bank_account = event_data["object"]

            # Find subscriptions using this bank account
            db_subscriptions = (
                db.query(Subscription)
                .filter(Subscription.payment_method_id == bank_account["id"])
                .all()
            )

            if not db_subscriptions:
                return True, "No subscriptions found using this bank account"

            for subscription in db_subscriptions:
                if bank_account["status"] == "verified":
                    # Update subscription status if bank account is verified
                    subscription.is_active = True
                    logger.info(
                        f"Bank account verified for subscription {subscription.id}"
                    )
                elif bank_account["status"] == "verification_failed":
                    # Mark subscription as inactive if verification failed
                    subscription.is_active = False
                    logger.warning(
                        f"Bank account verification failed for subscription {subscription.id}"
                    )

                # Update payment details
                payment_details = {
                    "payment_type": "bank_account",
                    "bank_account_id": bank_account["id"],
                    "last4": bank_account.get("last4"),
                    "bank_name": bank_account.get("bank_name"),
                    "status": bank_account["status"],
                }

                # Encrypt payment details
                try:
                    from app.core.encryption import AES256Encryptor

                    encryptor = AES256Encryptor()
                    encrypted_details = encryptor.encrypt(payment_details)
                    subscription.encrypted_payment_details = encrypted_details
                except Exception as enc_err:
                    logger.error(
                        f"Failed to encrypt bank account details: {str(enc_err)}"
                    )

            db.commit()
            return (
                True,
                f"Processed bank account verification for {len(db_subscriptions)} subscriptions",
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing bank account verification: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def process_paypal_webhook(
        db: Session, event_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process a checkout.session.completed webhook event for PayPal payments.

        Args:
            db: Database session
            event_data: Webhook event data

        Returns:
            Success status and message
        """
        try:
            session = event_data["object"]

            # Skip non-PayPal payments
            payment_method_types = session.get("payment_method_types", [])
            if "paypal" not in payment_method_types:
                return True, "Not a PayPal payment"

            # Get subscription details from metadata
            metadata = session.get("metadata", {})
            subscription_id = metadata.get("subscription_id")

            if not subscription_id:
                return False, "No subscription ID in metadata"

            # Find subscription in database
            db_subscription = (
                db.query(Subscription)
                .filter(Subscription.id == int(subscription_id))
                .first()
            )

            if not db_subscription:
                return False, f"Subscription not found: {subscription_id}"

            # Update payment method details
            payment_details = {
                "payment_type": "paypal",
                "checkout_session_id": session.get("id"),
                "customer_email": session.get("customer_details", {}).get("email"),
                "paypal_email": session.get("customer_details", {}).get("email"),
            }

            # Get PayPal specific details when available
            customer_details = session.get("customer_details", {})
            if customer_details and customer_details.get("email"):
                # Store PayPal payer ID if it's in the metadata or session
                # In a real integration, this would come from the PayPal API directly
                payer_id = metadata.get("paypal_payer_id")
                if payer_id:
                    db_subscription.paypal_payer_id = payer_id
                    payment_details["paypal_payer_id"] = payer_id

                # For agreement ID, this would also normally come from PayPal's API
                # but we'll store the subscription ID for now as a reference
                if session.get("subscription"):
                    db_subscription.paypal_agreement_id = session["subscription"]
                    payment_details["paypal_agreement_id"] = session["subscription"]

            # Encrypt payment details
            try:
                from app.core.encryption import AES256Encryptor

                encryptor = AES256Encryptor()
                encrypted_details = encryptor.encrypt(payment_details)
                db_subscription.encrypted_payment_details = encrypted_details
                db_subscription.payment_method_type = "paypal"
            except Exception as enc_err:
                logger.error(
                    f"Failed to encrypt PayPal payment details: {str(enc_err)}"
                )

            # Update subscription with Stripe subscription ID
            if session.get("subscription"):
                db_subscription.provider_subscription_id = session["subscription"]

                # Get subscription details from Stripe to get proper renewal date
                try:
                    stripe_subscription = stripe.Subscription.retrieve(
                        session["subscription"]
                    )
                    if stripe_subscription.get("current_period_end"):
                        end_date = datetime.fromtimestamp(
                            stripe_subscription["current_period_end"]
                        )
                        db_subscription.end_date = end_date
                    else:
                        # Default to billing cycle if we can't get the end date
                        now = datetime.utcnow()
                        if db_subscription.billing_cycle == "monthly":
                            db_subscription.end_date = now + timedelta(days=30)
                        else:
                            db_subscription.end_date = now + timedelta(days=365)
                except stripe.error.StripeError as stripe_err:
                    logger.error(
                        f"Failed to retrieve Stripe subscription details: {str(stripe_err)}"
                    )
                    # Continue with default end date calculation below

            # Create payment record
            if session.get("amount_total"):
                payment = SubscriptionPayment(
                    subscription_id=db_subscription.id,
                    amount=session["amount_total"] / 100,  # Convert cents to dollars
                    status=PaymentStatus.SUCCEEDED,
                    provider_payment_id=session.get("id"),
                    provider_payment_data=session,
                )
                db.add(payment)

            # Calculate end date if not already set from Stripe subscription
            if not db_subscription.end_date:
                now = datetime.utcnow()
                if db_subscription.billing_cycle == "monthly":
                    db_subscription.end_date = now + timedelta(days=30)
                else:
                    db_subscription.end_date = now + timedelta(days=365)

            # Ensure subscription is active
            db_subscription.is_active = True

            db.commit()
            logger.info(
                f"PayPal subscription successfully processed for user {db_subscription.user_id}, "
                + f"subscription ID: {db_subscription.id}, end date: {db_subscription.end_date}"
            )
            return True, "PayPal subscription processed successfully"

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing PayPal webhook: {str(e)}")
            return False, f"Error: {str(e)}"
