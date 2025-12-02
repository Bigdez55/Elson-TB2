import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { subscriptionService, Subscription, SubscriptionPlan } from '../../services/subscriptionService';
import { formatCurrency } from '../../utils/formatters';
import { Button } from '../common/Button';

interface SubscriptionStatusProps {
  onManageSubscription?: () => void;
}

export const SubscriptionStatus: React.FC<SubscriptionStatusProps> = ({ 
  onManageSubscription 
}) => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchSubscription = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await subscriptionService.getActiveSubscription();
        setSubscription(data);
      } catch (err: any) {
        console.error('Error fetching subscription:', err);
        setError(err.message || 'Failed to load subscription data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSubscription();
  }, []);
  
  const handleUpgrade = () => {
    navigate('/pricing');
  };
  
  const handleManageSubscription = () => {
    if (onManageSubscription) {
      onManageSubscription();
    } else {
      navigate('/settings?tab=subscription');
    }
  };
  
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };
  
  const daysUntilRenewal = (endDate?: string) => {
    if (!endDate) return null;
    
    const end = new Date(endDate);
    const now = new Date();
    const diffTime = end.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays > 0 ? diffDays : 0;
  };
  
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="text-red-600 mb-2">Error loading subscription data</div>
        <Button
          onClick={() => window.location.reload()}
          className="bg-gray-200 text-gray-800 text-sm"
        >
          Retry
        </Button>
      </div>
    );
  }
  
  // Free plan (no subscription)
  if (!subscription) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="text-lg font-medium">Free Plan</h3>
            <p className="text-gray-600 text-sm">Basic investing features</p>
          </div>
          <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-xs font-medium">
            CURRENT PLAN
          </span>
        </div>
        
        <div className="mb-4">
          <p className="text-sm text-gray-700">
            You're currently on the Free plan with access to basic trading features.
            Upgrade to Premium or Family plans for advanced features.
          </p>
        </div>
        
        <div>
          <Button
            onClick={handleUpgrade}
            className="w-full justify-center bg-indigo-600 text-white"
          >
            Upgrade Plan
          </Button>
        </div>
      </div>
    );
  }
  
  // Premium or Family plan
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-medium capitalize">
            {subscription.plan === SubscriptionPlan.PREMIUM ? 'Premium' : 'Family Premium'} Plan
          </h3>
          <p className="text-gray-600 text-sm capitalize">
            {subscription.billing_cycle} billing
          </p>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          subscription.status === 'Active' ? 'bg-green-100 text-green-800' : 
          subscription.status === 'Trial' ? 'bg-blue-100 text-blue-800' : 
          'bg-orange-100 text-orange-800'
        }`}>
          {subscription.status.toUpperCase()}
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm mb-4">
        <div className="text-gray-600">Current Period:</div>
        <div>
          {formatDate(subscription.start_date)} - {formatDate(subscription.end_date)}
        </div>
        
        {subscription.status === 'Trial' && subscription.trial_end_date && (
          <>
            <div className="text-gray-600">Trial Ends:</div>
            <div>{formatDate(subscription.trial_end_date)}</div>
          </>
        )}
        
        <div className="text-gray-600">Auto-Renewal:</div>
        <div>{subscription.auto_renew ? 'Enabled' : 'Disabled'}</div>
        
        {subscription.end_date && subscription.auto_renew && (
          <>
            <div className="text-gray-600">Next Billing:</div>
            <div>
              {formatDate(subscription.end_date)}
              {daysUntilRenewal(subscription.end_date) !== null && (
                <span className="text-xs text-gray-500 ml-2">
                  (in {daysUntilRenewal(subscription.end_date)} days)
                </span>
              )}
            </div>
          </>
        )}
        
        <div className="text-gray-600">Amount:</div>
        <div>{formatCurrency(subscription.price)}</div>
      </div>
      
      <div className="flex space-x-2">
        <Button
          onClick={handleManageSubscription}
          className="flex-1 justify-center bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
        >
          Manage
        </Button>
        
        {subscription.plan === SubscriptionPlan.PREMIUM && (
          <Button
            onClick={handleUpgrade}
            className="flex-1 justify-center bg-indigo-600 text-white"
          >
            Upgrade to Family
          </Button>
        )}
      </div>
    </div>
  );
};

export default SubscriptionStatus;