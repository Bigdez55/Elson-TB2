import React, { useEffect, createContext, useContext } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store/store';
import { fetchActiveSubscription } from '../../store/slices/subscriptionSlice';
import { subscriptionService, SubscriptionPlan, BillingCycle, FeatureAccessResponse } from '../../services/subscriptionService';

interface SubscriptionProviderProps {
  children: React.ReactNode;
}

// Define context type for subscription-related helpers
interface SubscriptionContextType {
  currentPlan: SubscriptionPlan;
  isInTrial: boolean;
  daysUntilRenewal: number | null;
  isActive: boolean;
  checkFeatureAccess: (feature: string) => Promise<FeatureAccessResponse>;
  getPlanDetails: (plan: SubscriptionPlan, billingCycle: BillingCycle) => {
    price: number;
    features: string[];
    billingCycle: BillingCycle;
    plan: SubscriptionPlan;
  };
  refreshSubscription: () => void;
}

// Create context
export const SubscriptionContext = createContext<SubscriptionContextType | null>(null);

/**
 * Provider component that loads the user's subscription data on mount
 * and provides helpers for subscription-related functionality
 */
export const SubscriptionProvider: React.FC<SubscriptionProviderProps> = ({ 
  children 
}) => {
  const dispatch = useDispatch();
  const { subscription, loading, error } = useSelector((state: RootState) => state.subscription);
  
  // Load subscription data on mount
  useEffect(() => {
    dispatch(fetchActiveSubscription());
  }, [dispatch]);
  
  // Function to refresh subscription data
  const refreshSubscription = () => {
    dispatch(fetchActiveSubscription());
  };
  
  // Helper values and functions
  const currentPlan = subscription?.plan || SubscriptionPlan.FREE;
  
  const isInTrial = Boolean(
    subscription?.trial_end_date && 
    new Date(subscription.trial_end_date) > new Date()
  );
  
  const daysUntilRenewal = subscription?.end_date 
    ? Math.max(
        0, 
        Math.ceil(
          (new Date(subscription.end_date).getTime() - new Date().getTime()) / 
          (1000 * 60 * 60 * 24)
        )
      ) 
    : null;
  
  const isActive = subscription?.is_active || false;

  // Create context value
  const contextValue: SubscriptionContextType = {
    currentPlan,
    isInTrial,
    daysUntilRenewal,
    isActive,
    checkFeatureAccess: subscriptionService.checkFeatureAccess,
    getPlanDetails: subscriptionService.getPlanDetails,
    refreshSubscription
  };
  
  return (
    <SubscriptionContext.Provider value={contextValue}>
      {children}
    </SubscriptionContext.Provider>
  );
};

/**
 * Hook to use the subscription context
 */
export const useSubscriptionContext = () => {
  const context = useContext(SubscriptionContext);
  
  if (!context) {
    throw new Error('useSubscriptionContext must be used within a SubscriptionProvider');
  }
  
  return context;
};

export default SubscriptionProvider;