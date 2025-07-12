import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { subscriptionService, Subscription, SubscriptionPlan } from '../../services/subscriptionService';
import { formatCurrency } from '../../utils/formatters';
import { Button } from '../common/Button';
import { SubscriptionStatus } from './SubscriptionStatus';

export const SubscriptionSettings: React.FC = () => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelImmediate, setCancelImmediate] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchSubscription = async () => {
      setIsLoading(true);
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
  
  const handleCancelDialogOpen = () => {
    setCancelDialogOpen(true);
  };
  
  const handleCancelDialogClose = () => {
    setCancelDialogOpen(false);
    setCancelReason('');
    setCancelImmediate(false);
  };
  
  const handleCancelSubscription = async () => {
    if (!subscription) return;
    
    setIsCancelling(true);
    try {
      const updatedSubscription = await subscriptionService.cancelSubscription(subscription.id, {
        reason: cancelReason,
        immediate: cancelImmediate
      });
      setSubscription(updatedSubscription);
      handleCancelDialogClose();
    } catch (err: any) {
      console.error('Error cancelling subscription:', err);
      setError(err.message || 'Failed to cancel subscription');
    } finally {
      setIsCancelling(false);
    }
  };
  
  const renderCancelDialog = () => {
    if (!cancelDialogOpen) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6">
          <h3 className="text-lg font-medium mb-4">Cancel Subscription</h3>
          <p className="text-gray-700 mb-4">
            Are you sure you want to cancel your {subscription?.plan === SubscriptionPlan.PREMIUM ? 'Premium' : 'Family'} subscription?
          </p>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Could you tell us why you're cancelling? (Optional)
            </label>
            <textarea
              rows={3}
              className="w-full border border-gray-300 rounded-md p-2 text-sm"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Your feedback helps us improve our service"
            />
          </div>
          
          <div className="mb-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                checked={cancelImmediate}
                onChange={(e) => setCancelImmediate(e.target.checked)}
              />
              <span className="ml-2 text-sm text-gray-700">
                Cancel immediately (otherwise, service continues until the end of the billing period)
              </span>
            </label>
          </div>
          
          <div className="flex justify-end space-x-3">
            <Button
              onClick={handleCancelDialogClose}
              className="bg-white text-gray-700 border border-gray-300"
            >
              Keep Subscription
            </Button>
            <Button
              onClick={handleCancelSubscription}
              className="bg-red-600 text-white hover:bg-red-700"
              disabled={isCancelling}
            >
              {isCancelling ? 'Cancelling...' : 'Cancel Subscription'}
            </Button>
          </div>
        </div>
      </div>
    );
  };
  
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-20 bg-gray-200 rounded"></div>
        <div className="h-40 bg-gray-200 rounded"></div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-medium mb-4">Subscription Management</h2>
        
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {/* Subscription status card */}
        <SubscriptionStatus />
        
        {/* No subscription section */}
        {!subscription && (
          <div className="mt-8">
            <h3 className="text-lg font-medium mb-2">Premium Features</h3>
            <p className="text-gray-700 mb-4">
              Upgrade to Premium or Family plan to unlock advanced features:
            </p>
            <ul className="list-disc pl-5 mb-4 space-y-1 text-gray-700">
              <li>Unlimited recurring investments</li>
              <li>AI-powered trading recommendations</li>
              <li>Tax-loss harvesting</li>
              <li>High-yield savings (5.00% APY)</li>
              <li>Fractional shares trading</li>
              <li>Advanced market data</li>
            </ul>
            <Button
              onClick={handleUpgrade}
              className="w-full justify-center bg-indigo-600 text-white"
            >
              View Pricing & Plans
            </Button>
          </div>
        )}
        
        {/* Active subscription management */}
        {subscription && (
          <div className="mt-8">
            <h3 className="text-lg font-medium mb-4">Manage Your Subscription</h3>
            
            {/* Auto-renewal toggle */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
              <div>
                <h4 className="font-medium">Auto-Renewal</h4>
                <p className="text-sm text-gray-600">
                  {subscription.auto_renew 
                    ? 'Your subscription will automatically renew at the end of the billing period' 
                    : 'Your subscription will expire at the end of the billing period'}
                </p>
              </div>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={subscription.auto_renew}
                  onChange={async () => {
                    try {
                      const updated = await subscriptionService.updateSubscription(
                        subscription.id, { auto_renew: !subscription.auto_renew }
                      );
                      setSubscription(updated);
                    } catch (err: any) {
                      setError(err.message || 'Failed to update auto-renewal setting');
                    }
                  }}
                  className="sr-only"
                  id="auto-renewal-toggle"
                />
                <label
                  htmlFor="auto-renewal-toggle"
                  className={`block w-14 h-7 rounded-full transition-colors duration-300 ease-in-out ${
                    subscription.auto_renew ? 'bg-indigo-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`block w-5 h-5 mt-1 ml-1 bg-white rounded-full shadow transition-transform duration-300 ease-in-out ${
                      subscription.auto_renew ? 'transform translate-x-7' : ''
                    }`}
                  />
                </label>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Change plan */}
              <div>
                <h4 className="font-medium mb-2">Change Plan</h4>
                <p className="text-sm text-gray-600 mb-3">
                  {subscription.plan === SubscriptionPlan.PREMIUM
                    ? 'Upgrade to Family plan for custodial accounts and family features'
                    : 'You are currently on our highest tier plan'}
                </p>
                <Button
                  onClick={handleUpgrade}
                  className="w-full justify-center"
                  disabled={subscription.plan === SubscriptionPlan.FAMILY}
                >
                  {subscription.plan === SubscriptionPlan.PREMIUM
                    ? 'Upgrade to Family'
                    : 'View Plans'}
                </Button>
              </div>
              
              {/* Cancel subscription */}
              <div>
                <h4 className="font-medium mb-2">Cancel Subscription</h4>
                <p className="text-sm text-gray-600 mb-3">
                  You can cancel your subscription at any time
                </p>
                <Button
                  onClick={handleCancelDialogOpen}
                  className="w-full justify-center bg-white border border-red-600 text-red-600 hover:bg-red-50"
                >
                  Cancel Subscription
                </Button>
              </div>
            </div>
            
            {/* Billing history */}
            <div className="mt-8">
              <h4 className="font-medium mb-3">Billing History</h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <th className="pb-2">Date</th>
                      <th className="pb-2">Amount</th>
                      <th className="pb-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {subscription.payments?.length > 0 ? (
                      subscription.payments.map((payment) => (
                        <tr key={payment.id}>
                          <td className="py-2 text-sm">
                            {new Date(payment.payment_date).toLocaleDateString()}
                          </td>
                          <td className="py-2 text-sm">
                            {formatCurrency(payment.amount)}
                          </td>
                          <td className="py-2 text-sm">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              payment.status === 'succeeded' ? 'bg-green-100 text-green-800' : 
                              payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 
                              'bg-red-100 text-red-800'
                            }`}>
                              {payment.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3} className="py-4 text-sm text-gray-500 text-center">
                          No payment history available
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Render cancel confirmation dialog */}
      {renderCancelDialog()}
    </div>
  );
};

export default SubscriptionSettings;