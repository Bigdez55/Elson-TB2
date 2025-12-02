import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '../../app/components/common/Button';
import { subscriptionService } from '../../app/services/subscriptionService';

const SubscriptionCancel: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  useEffect(() => {
    const cleanupSubscription = async () => {
      try {
        // Get subscription ID from query params or session storage
        const subscriptionId = searchParams.get('subscription_id') || 
                              sessionStorage.getItem('pendingSubscriptionId');
        
        if (subscriptionId) {
          // Clean up the pending subscription since it was canceled
          await subscriptionService.cancelPendingSubscription(parseInt(subscriptionId, 10));
          
          // Clear the session storage data
          sessionStorage.removeItem('pendingSubscriptionId');
        }
      } catch (err) {
        console.error('Error cleaning up canceled subscription:', err);
      }
    };
    
    cleanupSubscription();
  }, [searchParams]);
  
  return (
    <div className="max-w-md mx-auto mt-12">
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-4 text-yellow-500">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold mb-2">Subscription Payment Canceled</h2>
        <p className="text-gray-600 mb-6">
          Your subscription payment was canceled. No charges were made to your account.
        </p>
        <div className="flex flex-col space-y-3">
          <Button onClick={() => navigate('/pricing')} className="w-full">
            Try Again
          </Button>
          <Button onClick={() => navigate('/dashboard')} className="w-full bg-gray-100 text-gray-800 hover:bg-gray-200">
            Go to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionCancel;