import { useState, useEffect, useCallback } from 'react';
import { 
  subscriptionService, 
  Subscription, 
  SubscriptionPlan, 
  BillingCycle,
  FeatureAccessResponse
} from '../services/subscriptionService';

interface UseSubscriptionReturn {
  /**
   * The active subscription, or null if not subscribed
   */
  subscription: Subscription | null;
  
  /**
   * Whether the subscription data is loading
   */
  loading: boolean;
  
  /**
   * Error message if loading the subscription failed
   */
  error: string | null;
  
  /**
   * The user's current subscription plan
   */
  currentPlan: SubscriptionPlan;
  
  /**
   * Check if the user has access to a specific feature
   */
  checkFeatureAccess: (feature: string) => Promise<FeatureAccessResponse>;
  
  /**
   * Whether the user is on a trial
   */
  isInTrial: boolean;
  
  /**
   * Days left in the subscription period
   */
  daysUntilRenewal: number | null;
  
  /**
   * Refresh subscription data
   */
  refreshSubscription: () => Promise<void>;
  
  /**
   * Whether the subscription is in active status
   */
  isActive: boolean;
  
  /**
   * Get details of a plan (pricing, features)
   */
  getPlanDetails: (plan: SubscriptionPlan, billingCycle: BillingCycle) => {
    price: number;
    features: string[];
    billingCycle: BillingCycle;
    plan: SubscriptionPlan;
  };
}

/**
 * Hook for accessing subscription data throughout the application
 */
export const useSubscription = (): UseSubscriptionReturn => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to fetch subscription
  const fetchSubscription = useCallback(async () => {
    try {
      setLoading(true);
      const data = await subscriptionService.getActiveSubscription();
      setSubscription(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching subscription:', err);
      setError('Failed to load subscription. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load subscription on mount
  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  // Determine current plan
  const currentPlan = subscription?.plan || SubscriptionPlan.FREE;
  
  // Check if in trial
  const isInTrial = Boolean(
    subscription?.trial_end_date && 
    new Date(subscription.trial_end_date) > new Date()
  );
  
  // Check days until renewal
  const daysUntilRenewal = subscription?.end_date 
    ? Math.max(
        0, 
        Math.ceil(
          (new Date(subscription.end_date).getTime() - new Date().getTime()) / 
          (1000 * 60 * 60 * 24)
        )
      ) 
    : null;
  
  // Check if active
  const isActive = subscription?.is_active || false;

  // Function to check feature access
  const checkFeatureAccess = useCallback(async (feature: string) => {
    return subscriptionService.checkFeatureAccess(feature);
  }, []);

  return {
    subscription,
    loading,
    error,
    currentPlan,
    checkFeatureAccess,
    isInTrial,
    daysUntilRenewal,
    refreshSubscription: fetchSubscription,
    isActive,
    getPlanDetails: subscriptionService.getPlanDetails
  };
};

export default useSubscription;