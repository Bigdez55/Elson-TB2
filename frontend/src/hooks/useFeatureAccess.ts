import { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store/store';
import { checkFeatureAccess } from '../store/slices/subscriptionSlice';
import { SubscriptionPlan } from '../services/subscriptionService';

/**
 * Hook to check if the current user has access to a specific feature
 *
 * @param feature The feature to check access for
 * @returns Object with hasAccess, isLoading, requiredPlan, and error
 */
export function useFeatureAccess(feature: string) {
  const dispatch = useDispatch();
  const { featureAccess } = useSelector((state: RootState) => state.subscription);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requiredPlan, setRequiredPlan] = useState<SubscriptionPlan | null>(null);

  useEffect(() => {
    const checkAccess = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Check if we already have the access data in the store
        if (feature in featureAccess) {
          setIsLoading(false);
          return;
        }

        // Fetch access from the API
        const resultAction = await dispatch(checkFeatureAccess(feature) as any);

        if (checkFeatureAccess.fulfilled.match(resultAction)) {
          // Set the required plan if access was denied
          if (!resultAction.payload.has_access && resultAction.payload.required_plan) {
            setRequiredPlan(resultAction.payload.required_plan);
          }
        } else if (checkFeatureAccess.rejected.match(resultAction)) {
          setError(resultAction.error.message || 'Failed to check feature access');
        }
      } catch (err: any) {
        setError(err.message || 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    checkAccess();
  }, [dispatch, feature, featureAccess]);

  const hasAccess = Boolean(featureAccess[feature]);

  return {
    hasAccess,
    isLoading,
    requiredPlan,
    error
  };
}

export default useFeatureAccess;
