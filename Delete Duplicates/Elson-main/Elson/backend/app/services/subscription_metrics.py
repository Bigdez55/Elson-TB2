from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json
from sqlalchemy import func, text, and_, or_, desc, extract
from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionPayment, PaymentStatus
from app.models.user import User, SubscriptionPlan, BillingCycle
from app.core.logging import get_logger

logger = get_logger(__name__)

class SubscriptionMetricsService:
    """Service for calculating and reporting subscription metrics"""
    
    @staticmethod
    def get_mrr(db: Session, date: Optional[datetime] = None) -> float:
        """
        Calculate Monthly Recurring Revenue (MRR) for a given date.
        
        Args:
            db: Database session
            date: Date to calculate MRR for. Defaults to current date.
            
        Returns:
            MRR value
        """
        if date is None:
            date = datetime.utcnow()
            
        # Get all active subscriptions on the given date
        active_subscriptions = db.query(Subscription).filter(
            Subscription.is_active == True,
            Subscription.start_date <= date,
            or_(
                Subscription.end_date.is_(None),
                Subscription.end_date > date
            )
        ).all()
        
        # Calculate MRR
        mrr = 0.0
        for sub in active_subscriptions:
            # For monthly subscriptions, just add the price
            if sub.billing_cycle == BillingCycle.MONTHLY:
                mrr += sub.price
            # For annual subscriptions, divide by 12
            elif sub.billing_cycle == BillingCycle.ANNUALLY:
                mrr += sub.price / 12
                
        return mrr
    
    @staticmethod
    def get_arr(db: Session, date: Optional[datetime] = None) -> float:
        """
        Calculate Annual Recurring Revenue (ARR) for a given date.
        
        Args:
            db: Database session
            date: Date to calculate ARR for. Defaults to current date.
            
        Returns:
            ARR value
        """
        # Simply multiply MRR by 12
        mrr = SubscriptionMetricsService.get_mrr(db, date)
        return mrr * 12
    
    @staticmethod
    def get_mrr_history(db: Session, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get MRR history for the past N months.
        
        Args:
            db: Database session
            months: Number of months to include
            
        Returns:
            List of MRR values by month
        """
        now = datetime.utcnow()
        result = []
        
        for i in range(months, -1, -1):
            date = (now - timedelta(days=i * 30)).replace(day=1)
            mrr = SubscriptionMetricsService.get_mrr(db, date)
            
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "mrr": mrr
            })
            
        return result
    
    @staticmethod
    def get_active_subscriptions_by_plan(db: Session) -> Dict[str, int]:
        """
        Get count of active subscriptions by plan.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary of plan names to counts
        """
        now = datetime.utcnow()
        
        # Query for active subscriptions grouped by plan
        result = db.query(
            Subscription.plan,
            func.count(Subscription.id).label("count")
        ).filter(
            Subscription.is_active == True,
            or_(
                Subscription.end_date.is_(None),
                Subscription.end_date > now
            )
        ).group_by(Subscription.plan).all()
        
        # Convert to dictionary
        plan_counts = {
            plan.value: count for plan, count in result
        }
        
        # Add free plan count
        total_users = db.query(func.count(User.id)).scalar()
        subscribed_users = db.query(func.count(User.id)).join(
            Subscription, User.id == Subscription.user_id
        ).filter(
            Subscription.is_active == True,
            or_(
                Subscription.end_date.is_(None),
                Subscription.end_date > now
            )
        ).scalar()
        
        plan_counts["free"] = total_users - subscribed_users
        
        return plan_counts
    
    @staticmethod
    def calculate_churn_rate(db: Session, period_days: int = 30) -> Dict[str, float]:
        """
        Calculate churn rate for a given period.
        
        Args:
            db: Database session
            period_days: Number of days to calculate churn for
            
        Returns:
            Dictionary with churn metrics
        """
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)
        
        # Get subscriptions at start of period
        subs_at_start = db.query(func.count(Subscription.id)).filter(
            Subscription.is_active == True,
            Subscription.start_date <= period_start,
            or_(
                Subscription.end_date.is_(None),
                Subscription.end_date > period_start
            )
        ).scalar()
        
        # Get canceled subscriptions during period
        canceled_subs = db.query(func.count(Subscription.id)).filter(
            Subscription.canceled_at.between(period_start, now)
        ).scalar()
        
        # Calculate churn rate
        churn_rate = 0.0
        if subs_at_start > 0:
            churn_rate = (canceled_subs / subs_at_start) * 100
            
        return {
            "period_days": period_days,
            "subscriptions_at_start": subs_at_start,
            "canceled_subscriptions": canceled_subs,
            "churn_rate_percent": churn_rate
        }
    
    @staticmethod
    def get_monthly_revenue(db: Session, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get monthly revenue from subscription payments.
        
        Args:
            db: Database session
            months: Number of months to include
            
        Returns:
            List of monthly revenue data
        """
        now = datetime.utcnow()
        result = []
        
        # Get payments by month
        query = db.query(
            extract('year', SubscriptionPayment.payment_date).label('year'),
            extract('month', SubscriptionPayment.payment_date).label('month'),
            func.sum(SubscriptionPayment.amount).label('revenue')
        ).filter(
            SubscriptionPayment.status == PaymentStatus.SUCCEEDED,
            SubscriptionPayment.payment_date >= now - timedelta(days=months * 30)
        ).group_by(
            extract('year', SubscriptionPayment.payment_date),
            extract('month', SubscriptionPayment.payment_date)
        ).order_by(
            extract('year', SubscriptionPayment.payment_date),
            extract('month', SubscriptionPayment.payment_date)
        ).all()
        
        # Format results
        for row in query:
            date = datetime(int(row.year), int(row.month), 1)
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "revenue": float(row.revenue)
            })
        
        return result
    
    @staticmethod
    def get_ltv_estimates(db: Session) -> Dict[str, float]:
        """
        Estimate lifetime value (LTV) for subscribers.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with LTV estimates by plan
        """
        # Calculate average subscription lifetime
        now = datetime.utcnow()
        
        # Get completed subscriptions
        completed_subs = db.query(
            Subscription.plan,
            Subscription.start_date,
            Subscription.canceled_at
        ).filter(
            Subscription.is_active == False,
            Subscription.canceled_at.isnot(None)
        ).all()
        
        # Calculate average lifetime by plan
        lifetime_days = defaultdict(list)
        for sub in completed_subs:
            days = (sub.canceled_at - sub.start_date).days
            lifetime_days[sub.plan].append(days)
        
        # Calculate average lifetime and LTV
        ltv_estimates = {}
        for plan, days_list in lifetime_days.items():
            if days_list:
                avg_days = sum(days_list) / len(days_list)
                
                # Calculate average monthly price for this plan
                monthly_subs = db.query(func.avg(Subscription.price)).filter(
                    Subscription.plan == plan,
                    Subscription.billing_cycle == BillingCycle.MONTHLY
                ).scalar() or 0
                
                annual_subs = db.query(func.avg(Subscription.price)).filter(
                    Subscription.plan == plan,
                    Subscription.billing_cycle == BillingCycle.ANNUALLY
                ).scalar() or 0
                
                # Calculate weighted average monthly revenue
                monthly_count = db.query(func.count(Subscription.id)).filter(
                    Subscription.plan == plan,
                    Subscription.billing_cycle == BillingCycle.MONTHLY
                ).scalar() or 0
                
                annual_count = db.query(func.count(Subscription.id)).filter(
                    Subscription.plan == plan,
                    Subscription.billing_cycle == BillingCycle.ANNUALLY
                ).scalar() or 0
                
                total_count = monthly_count + annual_count
                
                if total_count > 0:
                    avg_monthly_revenue = (
                        (monthly_subs * monthly_count) + 
                        ((annual_subs / 12) * annual_count)
                    ) / total_count
                    
                    # LTV = Average Monthly Revenue * Average Lifetime (in months)
                    ltv = avg_monthly_revenue * (avg_days / 30)
                    ltv_estimates[plan.value] = ltv
        
        return ltv_estimates
    
    @staticmethod
    def get_conversion_rate(db: Session, days: int = 30) -> Dict[str, float]:
        """
        Calculate conversion rate from free to paid plans.
        
        Args:
            db: Database session
            days: Number of days to calculate conversion for
            
        Returns:
            Dictionary with conversion metrics
        """
        now = datetime.utcnow()
        period_start = now - timedelta(days=days)
        
        # Get users created in period
        new_users = db.query(func.count(User.id)).filter(
            User.created_at.between(period_start, now)
        ).scalar()
        
        # Get users who subscribed in period
        new_subscribers = db.query(func.count(User.id)).join(
            Subscription, User.id == Subscription.user_id
        ).filter(
            User.created_at.between(period_start, now),
            Subscription.start_date.between(period_start, now)
        ).scalar()
        
        # Calculate conversion rate
        conversion_rate = 0.0
        if new_users > 0:
            conversion_rate = (new_subscribers / new_users) * 100
            
        return {
            "period_days": days,
            "new_users": new_users,
            "new_subscribers": new_subscribers,
            "conversion_rate_percent": conversion_rate
        }
    
    @staticmethod
    def get_subscription_dashboard_data(db: Session) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for subscriptions.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with dashboard metrics
        """
        # Get current MRR/ARR
        current_mrr = SubscriptionMetricsService.get_mrr(db)
        current_arr = current_mrr * 12
        
        # Get MRR from 30 days ago for growth calculation
        date_30_days_ago = datetime.utcnow() - timedelta(days=30)
        mrr_30_days_ago = SubscriptionMetricsService.get_mrr(db, date_30_days_ago)
        
        # Calculate MRR growth
        mrr_growth = 0.0
        if mrr_30_days_ago > 0:
            mrr_growth = ((current_mrr - mrr_30_days_ago) / mrr_30_days_ago) * 100
        
        # Get subscribers by plan
        subscribers_by_plan = SubscriptionMetricsService.get_active_subscriptions_by_plan(db)
        
        # Get churn rate
        churn_data = SubscriptionMetricsService.calculate_churn_rate(db)
        
        # Get conversion rate
        conversion_data = SubscriptionMetricsService.get_conversion_rate(db)
        
        # Get MRR history
        mrr_history = SubscriptionMetricsService.get_mrr_history(db, months=6)
        
        # Get LTV estimates
        ltv_estimates = SubscriptionMetricsService.get_ltv_estimates(db)
        
        return {
            "current_mrr": current_mrr,
            "current_arr": current_arr,
            "mrr_growth_percent": mrr_growth,
            "subscribers_by_plan": subscribers_by_plan,
            "total_subscribers": sum(count for plan, count in subscribers_by_plan.items() if plan != "free"),
            "churn_rate": churn_data,
            "conversion_rate": conversion_data,
            "mrr_history": mrr_history,
            "ltv_estimates": ltv_estimates
        }