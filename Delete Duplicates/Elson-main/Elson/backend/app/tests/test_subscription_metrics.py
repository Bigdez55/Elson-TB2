import pytest
import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionPayment, PaymentStatus
from app.models.user import User, SubscriptionPlan, BillingCycle
from app.services.subscription_metrics import SubscriptionMetricsService


class TestSubscriptionMetricsService:
    """Tests for the SubscriptionMetricsService class"""
    
    def test_get_mrr(self, db_session: Session):
        """Test calculating Monthly Recurring Revenue"""
        # Mock the database query results
        mock_subscriptions = [
            MagicMock(
                billing_cycle=BillingCycle.MONTHLY,
                price=9.99
            ),
            MagicMock(
                billing_cycle=BillingCycle.MONTHLY,
                price=9.99
            ),
            MagicMock(
                billing_cycle=BillingCycle.ANNUALLY,
                price=95.88  # $7.99/month annual plan
            )
        ]
        
        # Configure the mock query
        db_session.query.return_value.filter.return_value.all.return_value = mock_subscriptions
        
        # Call the service
        mrr = SubscriptionMetricsService.get_mrr(db_session)
        
        # Expected MRR: 2 monthly subscriptions at $9.99 each + 1 annual at $95.88/12
        expected_mrr = (9.99 * 2) + (95.88 / 12)
        
        # Assertions (we use round to handle floating point precision)
        assert round(mrr, 2) == round(expected_mrr, 2)
    
    def test_get_arr(self, db_session: Session):
        """Test calculating Annual Recurring Revenue"""
        # Mock the get_mrr method
        with patch.object(SubscriptionMetricsService, 'get_mrr', return_value=100.0):
            # Call the service
            arr = SubscriptionMetricsService.get_arr(db_session)
            
            # Expected ARR: MRR * 12
            assert arr == 1200.0
    
    def test_get_active_subscriptions_by_plan(self, db_session: Session):
        """Test getting active subscriptions by plan"""
        # Mock query for subscriptions by plan
        plan_counts = [
            (SubscriptionPlan.PREMIUM, 10),
            (SubscriptionPlan.FAMILY, 5)
        ]
        db_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = plan_counts
        
        # Mock total users and subscribed users
        db_session.query.return_value.scalar.side_effect = [20, 15]  # 20 total users, 15 with subscriptions
        
        # Call the service
        result = SubscriptionMetricsService.get_active_subscriptions_by_plan(db_session)
        
        # Expected result
        expected = {
            'premium': 10,
            'family': 5,
            'free': 5  # 20 total - 15 subscribed
        }
        
        # Assertions
        assert result == expected
    
    def test_calculate_churn_rate(self, db_session: Session):
        """Test calculating churn rate"""
        # Mock subs at start and canceled subs
        db_session.query.return_value.filter.return_value.scalar.side_effect = [100, 5]
        
        # Call the service
        result = SubscriptionMetricsService.calculate_churn_rate(db_session, 30)
        
        # Expected result
        expected = {
            'period_days': 30,
            'subscriptions_at_start': 100,
            'canceled_subscriptions': 5,
            'churn_rate_percent': 5.0  # (5/100) * 100 = 5%
        }
        
        # Assertions
        assert result == expected
    
    def test_get_subscription_dashboard_data(self, db_session: Session):
        """Test getting subscription dashboard data"""
        # Mock various metrics methods
        with patch.multiple(
            SubscriptionMetricsService,
            get_mrr=MagicMock(return_value=1000.0),
            get_mrr_history=MagicMock(return_value=[{'date': '2025-01-01', 'mrr': 900.0}]),
            get_active_subscriptions_by_plan=MagicMock(return_value={'premium': 50, 'family': 25, 'free': 100}),
            calculate_churn_rate=MagicMock(return_value={'churn_rate_percent': 3.5}),
            get_conversion_rate=MagicMock(return_value={'conversion_rate_percent': 12.0}),
            get_ltv_estimates=MagicMock(return_value={'premium': 200.0, 'family': 350.0})
        ):
            # Call the service
            result = SubscriptionMetricsService.get_subscription_dashboard_data(db_session)
            
            # Assert that result contains expected keys
            assert 'current_mrr' in result
            assert 'current_arr' in result
            assert 'mrr_growth_percent' in result
            assert 'subscribers_by_plan' in result
            assert 'total_subscribers' in result
            assert 'churn_rate' in result
            assert 'conversion_rate' in result
            assert 'mrr_history' in result
            assert 'ltv_estimates' in result
            
            # Check some specific values
            assert result['current_mrr'] == 1000.0
            assert result['current_arr'] == 12000.0
            assert result['total_subscribers'] == 75  # 50 premium + 25 family