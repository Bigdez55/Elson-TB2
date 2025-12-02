import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { fetchActiveSubscription } from '../../app/store/slices/subscriptionSlice';
import { Button } from '../../app/components/common/Button';

const SubscriptionSuccess: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [isVerifying, setIsVerifying] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const verifySubscription = async () => {
      try {
        // Get subscription ID from query params or session storage
        const subscriptionId = searchParams.get('subscription_id') || 
                              sessionStorage.getItem('pendingSubscriptionId');
        
        if (!subscriptionId) {
          setError('Subscription information not found. Please contact support.');
          setIsVerifying(false);
          return;
        }
        
        // Clear the session storage data
        sessionStorage.removeItem('pendingSubscriptionId');
        
        // Fetch updated subscription data to confirm it's active
        await dispatch(fetchActiveSubscription());
        
        // Success - no need to do anything else
        setIsVerifying(false);
      } catch (err) {
        console.error('Failed to verify subscription:', err);
        setError('Failed to verify subscription status. Please check your account dashboard.');
        setIsVerifying(false);
      }
    };
    
    verifySubscription();
  }, [dispatch, searchParams]);
  
  const handleContinue = () => {
    navigate('/dashboard');
  };
  
  return (
    <div className="max-w-md mx-auto mt-12">
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        {isVerifying ? (
          <div>
            <div className="mb-4">
              <svg className="animate-spin h-10 w-10 text-indigo-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <h2 className="text-xl font-bold mb-2">Verifying Your Subscription</h2>
            <p className="text-gray-600">Please wait while we confirm your subscription details...</p>
          </div>
        ) : error ? (
          <div>
            <div className="mb-4 text-red-500">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold mb-2">Subscription Verification Failed</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="flex flex-col space-y-3">
              <Button onClick={() => navigate('/settings?tab=subscription')} className="w-full">
                View Subscription Settings
              </Button>
              <Button onClick={() => navigate('/support')} className="w-full bg-gray-100 text-gray-800 hover:bg-gray-200">
                Contact Support
              </Button>
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-4 text-green-500">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-2">Subscription Activated!</h2>
            <p className="text-gray-600 mb-6">
              Thank you for subscribing to Elson Wealth. Your subscription is now active, and you have full access to all premium features.
            </p>
            <Button onClick={handleContinue} className="w-full">
              Continue to Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionSuccess;