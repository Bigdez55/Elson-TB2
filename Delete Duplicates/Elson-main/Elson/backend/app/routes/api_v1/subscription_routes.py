from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.database import get_db
from app.routes.deps import get_current_user, get_current_admin_user
from app.services.subscription_service import SubscriptionService
from app.services.subscription_metrics import SubscriptionMetricsService
from app.models.user import User, SubscriptionPlan
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse,
    SubscriptionPaymentResponse, SubscriptionWithPaymentCreate,
    CancelSubscription, ChangeSubscriptionPlan,
    FeatureAccessCheck, FeatureAccessResponse
)
from app.services.stripe_service import StripeService

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)

@router.get("/", response_model=List[SubscriptionResponse])
def get_user_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all subscriptions for the current user"""
    subscriptions = SubscriptionService.get_user_subscriptions(db, current_user.id)
    return subscriptions

@router.get("/active", response_model=Optional[SubscriptionResponse])
def get_active_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the user's active subscription if any"""
    subscription = SubscriptionService.get_active_subscription(db, current_user.id)
    if not subscription:
        return None
    return subscription

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int = Path(..., title="The ID of the subscription to get"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific subscription by ID"""
    subscription = SubscriptionService.get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Only allow users to see their own subscriptions (admins can see all)
    if subscription.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this subscription"
        )
        
    return subscription

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription (admin only)"""
    # Only admins can create subscriptions for other users
    if subscription_data.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create subscriptions for other users"
        )
    
    subscription = SubscriptionService.create_subscription(db, subscription_data)
    return subscription

@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe(
    subscription_data: SubscriptionWithPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Subscribe to a plan with payment information"""
    # Create subscription for current user
    subscription_create = SubscriptionCreate(
        user_id=current_user.id,
        plan=subscription_data.plan,
        billing_cycle=subscription_data.billing_cycle,
        price=subscription_data.price,
        auto_renew=subscription_data.auto_renew,
        trial_days=subscription_data.trial_days
    )
    
    # Check if user already has an active subscription
    existing_subscription = SubscriptionService.get_active_subscription(db, current_user.id)
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )
    
    # Create the subscription
    subscription = SubscriptionService.create_subscription(db, subscription_create)
    
    # Process payment
    success, message, payment, additional_data = SubscriptionService.process_payment(
        db, subscription.id, subscription_data.payment_method
    )
    
    if not success:
        # Clean up the subscription if payment fails
        db.delete(subscription)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment failed: {message}"
        )
    
    # For PayPal payments, return redirect URL
    if subscription_data.payment_method.type == PaymentMethod.PAYPAL and additional_data:
        return {
            "id": subscription.id,
            "redirect_url": additional_data.get("redirect_url"),
            "session_id": additional_data.get("session_id"),
            "message": message
        }
    
    # Return regular subscription for other payment methods
    return subscription

@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_data: SubscriptionUpdate,
    subscription_id: int = Path(..., title="The ID of the subscription to update"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a subscription (admin only)"""
    # Check if subscription exists
    existing_subscription = SubscriptionService.get_subscription(db, subscription_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Only allow admins to update subscriptions
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update subscriptions"
        )
    
    updated_subscription = SubscriptionService.update_subscription(
        db, subscription_id, subscription_data
    )
    return updated_subscription

@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    cancel_data: CancelSubscription,
    subscription_id: int = Path(..., title="The ID of the subscription to cancel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a subscription"""
    # Check if subscription exists
    existing_subscription = SubscriptionService.get_subscription(db, subscription_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check if user is authorized to cancel this subscription
    if existing_subscription.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this subscription"
        )
    
    # Cancel the subscription
    updated_subscription = SubscriptionService.cancel_subscription(
        db, subscription_id, cancel_data.immediate
    )
    return updated_subscription

@router.post("/{subscription_id}/change-plan", response_model=SubscriptionResponse)
def change_subscription_plan(
    change_data: ChangeSubscriptionPlan,
    subscription_id: int = Path(..., title="The ID of the subscription to change"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change a subscription's plan"""
    # Check if subscription exists
    existing_subscription = SubscriptionService.get_subscription(db, subscription_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check if user is authorized to change this subscription
    if existing_subscription.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to change this subscription"
        )
    
    # Change the plan
    updated_subscription = SubscriptionService.change_plan(
        db, 
        subscription_id, 
        change_data.new_plan,
        change_data.new_billing_cycle,
        change_data.prorate
    )
    return updated_subscription

@router.post("/check-feature", response_model=FeatureAccessResponse)
def check_feature_access(
    feature_check: FeatureAccessCheck,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if the current user has access to a specific feature"""
    has_access, required_plan = SubscriptionService.check_feature_access(
        db, current_user.id, feature_check.feature
    )
    
    return FeatureAccessResponse(
        feature=feature_check.feature,
        has_access=has_access,
        required_plan=required_plan
    )

@router.get("/user/{user_id}/active", response_model=Optional[SubscriptionResponse])
def get_user_active_subscription(
    user_id: int = Path(..., title="The ID of the user to get the subscription for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a user's active subscription (admin only)"""
    # Only admins can access other users' subscriptions
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's subscription"
        )
    
    subscription = SubscriptionService.get_active_subscription(db, user_id)
    return subscription

# Metrics Endpoints (Admin Only)

@router.get("/metrics/dashboard", response_model=Dict[str, Any])
def get_subscription_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get comprehensive subscription metrics dashboard data (admin only)"""
    return SubscriptionMetricsService.get_subscription_dashboard_data(db)

@router.get("/metrics/mrr", response_model=float)
def get_mrr(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get current Monthly Recurring Revenue (admin only)"""
    return SubscriptionMetricsService.get_mrr(db)

@router.get("/metrics/arr", response_model=float)
def get_arr(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get current Annual Recurring Revenue (admin only)"""
    return SubscriptionMetricsService.get_arr(db)

@router.get("/metrics/mrr-history", response_model=List[Dict[str, Any]])
def get_mrr_history(
    months: int = Query(6, ge=1, le=36, description="Number of months to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get MRR history for the past N months (admin only)"""
    return SubscriptionMetricsService.get_mrr_history(db, months)

@router.get("/metrics/subscribers-by-plan", response_model=Dict[str, int])
def get_subscribers_by_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get count of active subscribers by plan (admin only)"""
    return SubscriptionMetricsService.get_active_subscriptions_by_plan(db)

@router.get("/metrics/churn-rate", response_model=Dict[str, Any])
def get_churn_rate(
    period_days: int = Query(30, ge=7, le=365, description="Number of days to calculate churn for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get churn rate for a given period (admin only)"""
    return SubscriptionMetricsService.calculate_churn_rate(db, period_days)

@router.get("/metrics/monthly-revenue", response_model=List[Dict[str, Any]])
def get_monthly_revenue(
    months: int = Query(12, ge=1, le=36, description="Number of months to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get monthly revenue data (admin only)"""
    return SubscriptionMetricsService.get_monthly_revenue(db, months)

@router.get("/metrics/ltv-estimates", response_model=Dict[str, float])
def get_ltv_estimates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get lifetime value estimates by plan (admin only)"""
    return SubscriptionMetricsService.get_ltv_estimates(db)

@router.get("/metrics/conversion-rate", response_model=Dict[str, Any])
def get_conversion_rate(
    days: int = Query(30, ge=7, le=365, description="Number of days to calculate conversion for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get conversion rate from free to paid plans (admin only)"""
    return SubscriptionMetricsService.get_conversion_rate(db, days)

# Feature Access and Verification Endpoints

@router.post("/{subscription_id}/verify-bank-account")
def verify_bank_account(
    amounts: List[int] = Body(..., description="List of micro-deposit amounts in cents"),
    bank_account_id: Optional[str] = Body(None, description="Bank account ID (if using older token-based flow)"),
    subscription_id: int = Path(..., title="The ID of the subscription to verify"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify a bank account for ACH payments by confirming micro-deposit amounts.
    
    This endpoint allows users to verify their bank account by providing the exact
    amounts of the micro-deposits sent by Stripe. Amounts should be provided in cents.
    """
    # Check if subscription exists and belongs to the user
    subscription = SubscriptionService.get_subscription(db, subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to verify this subscription's bank account"
        )
    
    # Check if subscription uses bank account payment method
    if subscription.payment_method_type != "bank_account":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This subscription does not use a bank account payment method"
        )
    
    # Determine which bank account ID to use
    account_id = bank_account_id or subscription.payment_method_id
    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No bank account ID available for verification"
        )
    
    try:
        # Get the user's Stripe customer ID
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user or not user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have a payment provider account"
            )
        
        # Verify the bank account
        bank_account = StripeService.verify_bank_account(
            customer_id=user.stripe_customer_id,
            bank_account_id=account_id,
            amounts=amounts
        )
        
        # Update subscription status based on verification
        if bank_account.get("status") == "verified":
            subscription.is_active = True
            
            # Update payment details
            try:
                from app.core.encryption import AES256Encryptor
                
                # Get current encrypted payment details
                encryptor = AES256Encryptor()
                payment_details = encryptor.decrypt(subscription.encrypted_payment_details)
                
                # Update verification status
                payment_details["verification_status"] = "verified"
                
                # Re-encrypt updated details
                encrypted_details = encryptor.encrypt(payment_details)
                subscription.encrypted_payment_details = encrypted_details
            except Exception as e:
                # Continue even if encryption fails
                from app.core.logging import get_logger
                logger = get_logger(__name__)
                logger.error(f"Error updating encrypted payment details: {str(e)}")
        
        db.commit()
        
        return {"success": True, "status": bank_account.get("status")}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bank account verification failed: {str(e)}"
        )