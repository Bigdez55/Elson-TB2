import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFeatureAccess } from '../../hooks/useFeatureAccess';
import { Button } from './Button';
import { SubscriptionPlan } from '../../services/subscriptionService';

interface FeatureGateProps {
  featureName: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * A component that conditionally renders its children based on feature access
 * If the user doesn't have access to the feature, displays a message prompting them to upgrade
 */
export const FeatureGate: React.FC<FeatureGateProps> = ({ 
  featureName, 
  children,
  fallback
}) => {
  const { hasAccess, isLoading, requiredPlan } = useFeatureAccess(featureName);
  const navigate = useNavigate();
  
  // While checking access, render nothing or a placeholder
  if (isLoading) {
    return <div className="animate-pulse h-8 bg-gray-200 rounded w-full"></div>;
  }
  
  // If the user has access, render the children
  if (hasAccess) {
    return <>{children}</>;
  }
  
  // If a fallback is provided, render it
  if (fallback) {
    return <>{fallback}</>;
  }
  
  // Otherwise, render the upgrade message
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
      <div className="mb-3">
        <PremiumIcon className="h-10 w-10 mx-auto text-indigo-600" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">Premium Feature</h3>
      <p className="text-sm text-gray-600 mb-3">
        {requiredPlan === SubscriptionPlan.PREMIUM 
          ? 'This feature requires a Premium subscription.'
          : requiredPlan === SubscriptionPlan.FAMILY
            ? 'This feature requires a Family subscription.'
            : 'You need to upgrade your subscription to access this feature.'}
      </p>
      <Button
        onClick={() => navigate('/pricing')}
        className="bg-indigo-600 text-white hover:bg-indigo-700"
      >
        Upgrade Now
      </Button>
    </div>
  );
};

// Premium icon component
const PremiumIcon = ({ className = '' }) => (
  <svg 
    className={className} 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="currentColor"
  >
    <path d="M9.68 13.69L12 11.93l2.31 1.76-.88-2.85L15.75 9h-2.84L12 6.19 11.09 9H8.25l2.31 1.84-.88 2.85zM20 10c0-4.42-3.58-8-8-8s-8 3.58-8 8c0 3.54 2.29 6.53 5.47 7.59.01 0 .01-.01.01-.01.26.11.53.2.81.28C11.3 17.96 11.65 18 12 18s.7-.04 1.04-.14c.27-.08.54-.17.8-.28.01 0 .01.01.01.01C17.71 16.53 20 13.54 20 10zm-8 6c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6z"/>
  </svg>
);

export default FeatureGate;