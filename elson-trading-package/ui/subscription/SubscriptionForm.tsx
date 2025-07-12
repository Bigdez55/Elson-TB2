import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { fetchActiveSubscription } from '../../store/slices/subscriptionSlice';
import { subscriptionService, SubscriptionPlan, BillingCycle } from '../../services/subscriptionService';
import { formatCurrency } from '../../utils/formatters';
import { validateSubscriptionForm } from '../../utils/validation';
import { Button } from '../common/Button';
import { CreditCardInput } from './CreditCardInput';
import { PayPalPaymentInput } from './PayPalPaymentInput';
import BankAccountInput from './BankAccountInput';

// Dark mode theme prop
interface SubscriptionFormProps {
  darkMode?: boolean;
}

interface PaymentMethod {
  type: 'credit_card' | 'bank_account' | 'paypal' | 'apple_pay' | 'google_pay';
  credit_card?: {
    card_number: string;
    expiry_month: number;
    expiry_year: number;
    cvc: string;
    cardholder_name: string;
    billing_address?: {
      street: string;
      city: string;
      state: string;
      zip: string;
      country: string;
    };
  };
  bank_account?: {
    account_number: string;
    routing_number: string;
    account_type: string;
    account_holder_name: string;
  };
  save_for_future: boolean;
}

const SubscriptionForm: React.FC<SubscriptionFormProps> = ({ darkMode = false }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
  // Get plan and billing cycle from location state or default to premium monthly
  const { plan = SubscriptionPlan.PREMIUM, billingCycle = BillingCycle.MONTHLY } = 
    (location.state as { plan?: SubscriptionPlan; billingCycle?: BillingCycle }) || {};
  
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan>(plan);
  const [selectedBillingCycle, setSelectedBillingCycle] = useState<BillingCycle>(billingCycle);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>({
    type: 'credit_card',
    save_for_future: true
  });
  const [cardDetails, setCardDetails] = useState({
    card_number: '',
    expiry_month: 0,
    expiry_year: 0,
    cvc: '',
    cardholder_name: ''
  });
  const [bankDetails, setBankDetails] = useState({
    account_number: '',
    routing_number: '',
    account_type: 'checking',
    account_holder_name: ''
  });
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Get pricing
  const pricing = subscriptionService.getPlanDetails(selectedPlan, selectedBillingCycle);
  
  // Calculate savings when paying annually
  const monthlyCost = subscriptionService.getPlanDetails(selectedPlan, BillingCycle.MONTHLY).price;
  const annualCost = subscriptionService.getPlanDetails(selectedPlan, BillingCycle.ANNUALLY).price;
  const annualSavings = (monthlyCost * 12 - annualCost).toFixed(2);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Use our validation utility for the whole form
    const formErrors = validateSubscriptionForm(
      selectedPlan,
      selectedBillingCycle,
      agreeToTerms,
      paymentMethod.type,
      paymentMethod.type === 'credit_card' ? cardDetails : undefined,
      paymentMethod.type === 'bank_account' ? bankDetails : undefined
    );
    
    // Check if we have any errors
    if (Object.keys(formErrors).length > 0) {
      // Get the first error message to display
      const firstError = Object.values(formErrors)[0];
      setError(firstError);
      return;
    }
    
    setIsProcessing(true);
    setError(null);
    
    try {
      // Prepare payment method data based on selected type
      let completePaymentMethod: PaymentMethod;
      
      if (paymentMethod.type === 'credit_card') {
        completePaymentMethod = {
          ...paymentMethod,
          credit_card: cardDetails
        };
      } else if (paymentMethod.type === 'bank_account') {
        completePaymentMethod = {
          ...paymentMethod,
          bank_account: bankDetails
        };
      } else {
        // PayPal or other methods don't need additional details
        completePaymentMethod = paymentMethod;
      }
      
      // Subscribe to plan
      const response = await subscriptionService.subscribe({
        plan: selectedPlan,
        billing_cycle: selectedBillingCycle,
        price: pricing.price,
        auto_renew: true,
        payment_method: completePaymentMethod
      });
      
      // Handle PayPal redirects
      if (paymentMethod.type === 'paypal' && response.redirect_url) {
        // Store subscription ID in session storage for retrieval after redirect
        sessionStorage.setItem('pendingSubscriptionId', response.id.toString());
        
        // Redirect to PayPal
        window.location.href = response.redirect_url;
        return;
      }
      
      // For credit card payments, refresh subscription data and redirect to success page
      await dispatch(fetchActiveSubscription());
      navigate('/settings?tab=subscription&subscribed=true');
    } catch (err: any) {
      console.error('Subscription error:', err);
      setError(err.message || 'Failed to process subscription. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Dark mode version
  if (darkMode) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="bg-gray-900 rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Complete Your Subscription</h2>
          
          {error && (
            <div className="mb-6 bg-red-900 text-red-100 p-4 rounded-md border border-red-800">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            {/* Plan selection */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-white mb-4">1. Select Your Plan</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div 
                  className={`border rounded-lg p-4 cursor-pointer ${
                    selectedPlan === SubscriptionPlan.PREMIUM 
                      ? 'border-purple-500 bg-gray-800' 
                      : 'border-gray-700 bg-gray-800'
                  }`}
                  onClick={() => setSelectedPlan(SubscriptionPlan.PREMIUM)}
                >
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium text-white">Premium Plan</h4>
                    <div className="h-5 w-5 rounded-full border border-purple-500 flex items-center justify-center">
                      {selectedPlan === SubscriptionPlan.PREMIUM && (
                        <div className="h-3 w-3 bg-purple-500 rounded-full"></div>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">Advanced trading features</p>
                  <ul className="text-sm text-gray-300 space-y-1 mb-2">
                    <li>• Unlimited recurring investments</li>
                    <li>• Advanced market data</li>
                    <li>• AI trading recommendations</li>
                  </ul>
                </div>
                
                <div 
                  className={`border rounded-lg p-4 cursor-pointer ${
                    selectedPlan === SubscriptionPlan.FAMILY 
                      ? 'border-purple-500 bg-gray-800' 
                      : 'border-gray-700 bg-gray-800'
                  }`}
                  onClick={() => setSelectedPlan(SubscriptionPlan.FAMILY)}
                >
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium text-white">Family Plan</h4>
                    <div className="h-5 w-5 rounded-full border border-purple-500 flex items-center justify-center">
                      {selectedPlan === SubscriptionPlan.FAMILY && (
                        <div className="h-3 w-3 bg-purple-500 rounded-full"></div>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">Premium + family features</p>
                  <ul className="text-sm text-gray-300 space-y-1 mb-2">
                    <li>• Everything in Premium plan</li>
                    <li>• Up to 5 custodial accounts</li>
                    <li>• Family investment challenges</li>
                  </ul>
                </div>
              </div>
            </div>
            
            {/* Billing cycle selection */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-white mb-4">2. Select Billing Cycle</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div 
                  className={`border rounded-lg p-4 cursor-pointer ${
                    selectedBillingCycle === BillingCycle.MONTHLY 
                      ? 'border-purple-500 bg-gray-800' 
                      : 'border-gray-700 bg-gray-800'
                  }`}
                  onClick={() => setSelectedBillingCycle(BillingCycle.MONTHLY)}
                >
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium text-white">Monthly</h4>
                    <div className="h-5 w-5 rounded-full border border-purple-500 flex items-center justify-center">
                      {selectedBillingCycle === BillingCycle.MONTHLY && (
                        <div className="h-3 w-3 bg-purple-500 rounded-full"></div>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-300">
                    {formatCurrency(
                      subscriptionService.getPlanDetails(selectedPlan, BillingCycle.MONTHLY).price
                    )}/month
                  </p>
                  <p className="text-sm text-gray-400">Billed monthly</p>
                </div>
                
                <div 
                  className={`border rounded-lg p-4 cursor-pointer ${
                    selectedBillingCycle === BillingCycle.ANNUALLY 
                      ? 'border-purple-500 bg-gray-800' 
                      : 'border-gray-700 bg-gray-800'
                  }`}
                  onClick={() => setSelectedBillingCycle(BillingCycle.ANNUALLY)}
                >
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium text-white">Annual</h4>
                    <div className="h-5 w-5 rounded-full border border-purple-500 flex items-center justify-center">
                      {selectedBillingCycle === BillingCycle.ANNUALLY && (
                        <div className="h-3 w-3 bg-purple-500 rounded-full"></div>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-300">
                    {formatCurrency(
                      subscriptionService.getPlanDetails(selectedPlan, BillingCycle.ANNUALLY).price / 12
                    )}/month
                  </p>
                  <p className="text-sm text-gray-400">Billed annually ({formatCurrency(
                    subscriptionService.getPlanDetails(selectedPlan, BillingCycle.ANNUALLY).price
                  )})</p>
                  <p className="text-sm font-medium text-green-400">Save ${annualSavings}/year</p>
                </div>
              </div>
            </div>
            
            {/* Payment method */}
            <div className="mb-8">
              <h3 className="text-lg font-medium text-white mb-4">3. Payment Method</h3>
              
              <div className="mb-4">
                <div className="flex flex-wrap gap-2 mb-4">
                  <button
                    type="button"
                    onClick={() => setPaymentMethod({ ...paymentMethod, type: 'credit_card' })}
                    className={`px-4 py-2 border rounded-md ${
                      paymentMethod.type === 'credit_card' 
                        ? 'border-purple-500 bg-gray-800 text-white'
                        : 'border-gray-700 text-gray-300'
                    }`}
                  >
                    Credit Card
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod({ ...paymentMethod, type: 'bank_account' })}
                    className={`px-4 py-2 border rounded-md ${
                      paymentMethod.type === 'bank_account' 
                        ? 'border-purple-500 bg-gray-800 text-white'
                        : 'border-gray-700 text-gray-300'
                    }`}
                  >
                    Bank Account (ACH)
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod({ ...paymentMethod, type: 'paypal' })}
                    className={`px-4 py-2 border rounded-md ${
                      paymentMethod.type === 'paypal' 
                        ? 'border-purple-500 bg-gray-800 text-white'
                        : 'border-gray-700 text-gray-300'
                    }`}
                  >
                    PayPal
                  </button>
                </div>
                
                {paymentMethod.type === 'credit_card' && (
                  <CreditCardInput 
                    values={cardDetails}
                    onChange={setCardDetails}
                    darkMode={true}
                  />
                )}
                
                {paymentMethod.type === 'bank_account' && (
                  <BankAccountInput 
                    values={bankDetails}
                    onChange={setBankDetails}
                    darkMode={true}
                  />
                )}
                
                {paymentMethod.type === 'paypal' && (
                  <PayPalPaymentInput darkMode={true} />
                )}
                
                <div className="mt-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={paymentMethod.save_for_future}
                      onChange={() => setPaymentMethod({ 
                        ...paymentMethod, 
                        save_for_future: !paymentMethod.save_for_future 
                      })}
                      className="h-4 w-4 text-purple-600 focus:ring-purple-500 bg-gray-800 border-gray-600 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-300">
                      Save payment information for future transactions
                    </span>
                  </label>
                </div>
              </div>
            </div>
            
            {/* Order summary */}
            <div className="mb-8 bg-gray-800 p-4 rounded-lg border border-gray-700">
              <h3 className="text-lg font-medium text-white mb-4">Order Summary</h3>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-gray-300">
                    {selectedPlan === SubscriptionPlan.PREMIUM ? 'Premium' : 'Family'} Plan
                    ({selectedBillingCycle === BillingCycle.MONTHLY ? 'Monthly' : 'Annual'})
                  </span>
                  <span className="font-medium text-white">
                    {formatCurrency(pricing.price)}
                  </span>
                </div>
                
                {selectedBillingCycle === BillingCycle.ANNUALLY && (
                  <div className="flex justify-between text-green-400">
                    <span>Annual Discount</span>
                    <span>-${annualSavings}</span>
                  </div>
                )}
                
                <div className="border-t border-gray-700 pt-2 flex justify-between font-medium">
                  <span className="text-white">Total</span>
                  <span className="text-white">{formatCurrency(pricing.price)}</span>
                </div>
              </div>
              <p className="text-sm text-gray-400">
                {selectedBillingCycle === BillingCycle.MONTHLY 
                  ? 'You will be charged monthly until you cancel.' 
                  : 'You will be charged annually until you cancel.'}
              </p>
            </div>
            
            {/* Terms and conditions */}
            <div className="mb-8">
              <label className="flex items-start">
                <input
                  type="checkbox"
                  checked={agreeToTerms}
                  onChange={() => setAgreeToTerms(!agreeToTerms)}
                  className="h-4 w-4 mt-1 text-purple-600 focus:ring-purple-500 bg-gray-800 border-gray-600 rounded"
                />
                <span className="ml-2 text-sm text-gray-300">
                  I agree to the <a href="/terms" className="text-purple-400 hover:text-purple-300">Terms of Service</a> and
                  <a href="/privacy" className="text-purple-400 hover:text-purple-300"> Privacy Policy</a>. 
                  I understand that my subscription will automatically renew and my payment method will be charged
                  at the end of each billing period unless I cancel.
                </span>
              </label>
            </div>
            
            {/* Submit button */}
            <div className="flex justify-between items-center">
              <button
                type="button"
                onClick={() => navigate('/pricing')}
                className="text-gray-400 hover:text-white"
              >
                Back to Plans
              </button>
              <Button
                type="submit"
                className="px-8 py-3 bg-purple-600 hover:bg-purple-500 text-white"
                disabled={isProcessing || !agreeToTerms}
              >
                {isProcessing ? 'Processing...' : `Subscribe - ${formatCurrency(pricing.price)}`}
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Light mode version (default)
  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-2xl font-bold mb-6">Complete Your Subscription</h2>
        
        {error && (
          <div className="mb-6 bg-red-50 text-red-700 p-4 rounded-md border border-red-100">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          {/* Plan selection */}
          <div className="mb-8">
            <h3 className="text-lg font-medium mb-4">1. Select Your Plan</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div 
                className={`border rounded-lg p-4 cursor-pointer ${
                  selectedPlan === SubscriptionPlan.PREMIUM 
                    ? 'border-indigo-500 bg-indigo-50' 
                    : 'border-gray-200'
                }`}
                onClick={() => setSelectedPlan(SubscriptionPlan.PREMIUM)}
              >
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">Premium Plan</h4>
                  <div className="h-5 w-5 rounded-full border border-indigo-500 flex items-center justify-center">
                    {selectedPlan === SubscriptionPlan.PREMIUM && (
                      <div className="h-3 w-3 bg-indigo-500 rounded-full"></div>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">Advanced trading features</p>
                <ul className="text-sm text-gray-700 space-y-1 mb-2">
                  <li>• Unlimited recurring investments</li>
                  <li>• Advanced market data</li>
                  <li>• AI trading recommendations</li>
                </ul>
              </div>
              
              <div 
                className={`border rounded-lg p-4 cursor-pointer ${
                  selectedPlan === SubscriptionPlan.FAMILY 
                    ? 'border-indigo-500 bg-indigo-50' 
                    : 'border-gray-200'
                }`}
                onClick={() => setSelectedPlan(SubscriptionPlan.FAMILY)}
              >
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">Family Plan</h4>
                  <div className="h-5 w-5 rounded-full border border-indigo-500 flex items-center justify-center">
                    {selectedPlan === SubscriptionPlan.FAMILY && (
                      <div className="h-3 w-3 bg-indigo-500 rounded-full"></div>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">Premium + family features</p>
                <ul className="text-sm text-gray-700 space-y-1 mb-2">
                  <li>• Everything in Premium plan</li>
                  <li>• Up to 5 custodial accounts</li>
                  <li>• Family investment challenges</li>
                </ul>
              </div>
            </div>
          </div>
          
          {/* Billing cycle selection */}
          <div className="mb-8">
            <h3 className="text-lg font-medium mb-4">2. Select Billing Cycle</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div 
                className={`border rounded-lg p-4 cursor-pointer ${
                  selectedBillingCycle === BillingCycle.MONTHLY 
                    ? 'border-indigo-500 bg-indigo-50' 
                    : 'border-gray-200'
                }`}
                onClick={() => setSelectedBillingCycle(BillingCycle.MONTHLY)}
              >
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">Monthly</h4>
                  <div className="h-5 w-5 rounded-full border border-indigo-500 flex items-center justify-center">
                    {selectedBillingCycle === BillingCycle.MONTHLY && (
                      <div className="h-3 w-3 bg-indigo-500 rounded-full"></div>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  {formatCurrency(
                    subscriptionService.getPlanDetails(selectedPlan, BillingCycle.MONTHLY).price
                  )}/month
                </p>
                <p className="text-sm text-gray-500">Billed monthly</p>
              </div>
              
              <div 
                className={`border rounded-lg p-4 cursor-pointer ${
                  selectedBillingCycle === BillingCycle.ANNUALLY 
                    ? 'border-indigo-500 bg-indigo-50' 
                    : 'border-gray-200'
                }`}
                onClick={() => setSelectedBillingCycle(BillingCycle.ANNUALLY)}
              >
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">Annual</h4>
                  <div className="h-5 w-5 rounded-full border border-indigo-500 flex items-center justify-center">
                    {selectedBillingCycle === BillingCycle.ANNUALLY && (
                      <div className="h-3 w-3 bg-indigo-500 rounded-full"></div>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  {formatCurrency(
                    subscriptionService.getPlanDetails(selectedPlan, BillingCycle.ANNUALLY).price / 12
                  )}/month
                </p>
                <p className="text-sm text-gray-500">Billed annually ({formatCurrency(
                  subscriptionService.getPlanDetails(selectedPlan, BillingCycle.ANNUALLY).price
                )})</p>
                <p className="text-sm font-medium text-green-600">Save ${annualSavings}/year</p>
              </div>
            </div>
          </div>
          
          {/* Payment method */}
          <div className="mb-8">
            <h3 className="text-lg font-medium mb-4">3. Payment Method</h3>
            
            <div className="mb-4">
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  type="button"
                  onClick={() => setPaymentMethod({ ...paymentMethod, type: 'credit_card' })}
                  className={`px-4 py-2 border rounded-md ${
                    paymentMethod.type === 'credit_card' 
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-300 text-gray-700'
                  }`}
                >
                  Credit Card
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod({ ...paymentMethod, type: 'bank_account' })}
                  className={`px-4 py-2 border rounded-md ${
                    paymentMethod.type === 'bank_account' 
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-300 text-gray-700'
                  }`}
                >
                  Bank Account (ACH)
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod({ ...paymentMethod, type: 'paypal' })}
                  className={`px-4 py-2 border rounded-md ${
                    paymentMethod.type === 'paypal' 
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-300 text-gray-700'
                  }`}
                >
                  PayPal
                </button>
              </div>
              
              {paymentMethod.type === 'credit_card' && (
                <CreditCardInput 
                  values={cardDetails}
                  onChange={setCardDetails}
                />
              )}
              
              {paymentMethod.type === 'bank_account' && (
                <BankAccountInput 
                  values={bankDetails}
                  onChange={setBankDetails}
                  darkMode={false}
                />
              )}
              
              {paymentMethod.type === 'paypal' && (
                <PayPalPaymentInput darkMode={false} />
              )}
              
              <div className="mt-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={paymentMethod.save_for_future}
                    onChange={() => setPaymentMethod({ 
                      ...paymentMethod, 
                      save_for_future: !paymentMethod.save_for_future 
                    })}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Save payment information for future transactions
                  </span>
                </label>
              </div>
            </div>
          </div>
          
          {/* Order summary */}
          <div className="mb-8 bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium mb-4">Order Summary</h3>
            <div className="space-y-2 mb-4">
              <div className="flex justify-between">
                <span className="text-gray-700">
                  {selectedPlan === SubscriptionPlan.PREMIUM ? 'Premium' : 'Family'} Plan
                  ({selectedBillingCycle === BillingCycle.MONTHLY ? 'Monthly' : 'Annual'})
                </span>
                <span className="font-medium">
                  {formatCurrency(pricing.price)}
                </span>
              </div>
              
              {selectedBillingCycle === BillingCycle.ANNUALLY && (
                <div className="flex justify-between text-green-600">
                  <span>Annual Discount</span>
                  <span>-${annualSavings}</span>
                </div>
              )}
              
              <div className="border-t border-gray-200 pt-2 flex justify-between font-medium">
                <span>Total</span>
                <span>{formatCurrency(pricing.price)}</span>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              {selectedBillingCycle === BillingCycle.MONTHLY 
                ? 'You will be charged monthly until you cancel.' 
                : 'You will be charged annually until you cancel.'}
            </p>
          </div>
          
          {/* Terms and conditions */}
          <div className="mb-8">
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={agreeToTerms}
                onChange={() => setAgreeToTerms(!agreeToTerms)}
                className="h-4 w-4 mt-1 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                I agree to the <a href="/terms" className="text-indigo-600 hover:text-indigo-500">Terms of Service</a> and
                <a href="/privacy" className="text-indigo-600 hover:text-indigo-500"> Privacy Policy</a>. 
                I understand that my subscription will automatically renew and my payment method will be charged
                at the end of each billing period unless I cancel.
              </span>
            </label>
          </div>
          
          {/* Submit button */}
          <div className="flex justify-between items-center">
            <button
              type="button"
              onClick={() => navigate('/pricing')}
              className="text-gray-600 hover:text-gray-900"
            >
              Back to Plans
            </button>
            <Button
              type="submit"
              className="px-8 py-3 bg-indigo-600 text-white"
              disabled={isProcessing || !agreeToTerms}
            >
              {isProcessing ? 'Processing...' : `Subscribe - ${formatCurrency(pricing.price)}`}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SubscriptionForm;