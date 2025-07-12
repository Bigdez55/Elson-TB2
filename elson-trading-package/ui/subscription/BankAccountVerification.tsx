import React, { useState } from 'react';
import { subscriptionService } from '../../services/subscriptionService';

interface BankAccountVerificationProps {
  subscriptionId: number;
  bankAccountId?: string;
  darkMode?: boolean;
  onSuccess: () => void;
  onError: (error: string) => void;
}

const BankAccountVerification: React.FC<BankAccountVerificationProps> = ({
  subscriptionId,
  bankAccountId,
  darkMode = false,
  onSuccess,
  onError
}) => {
  const [amount1, setAmount1] = useState('');
  const [amount2, setAmount2] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Style classes based on dark mode
  const inputClasses = darkMode
    ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500 focus:ring-purple-500 focus:border-purple-500'
    : 'bg-white border-gray-300 text-gray-700 placeholder-gray-400 focus:ring-indigo-500 focus:border-indigo-500';
    
  const labelClasses = darkMode
    ? 'text-gray-300'
    : 'text-gray-700';
    
  const buttonClasses = darkMode
    ? 'bg-purple-600 hover:bg-purple-500 text-white'
    : 'bg-indigo-600 hover:bg-indigo-500 text-white';
  
  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate amounts
    if (!amount1 || !amount2) {
      onError('Please enter both deposit amounts');
      return;
    }
    
    // Convert to cents as integers (Stripe expects amounts in cents)
    const cents1 = Math.round(parseFloat(amount1) * 100);
    const cents2 = Math.round(parseFloat(amount2) * 100);
    
    // Ensure we have valid numbers
    if (isNaN(cents1) || isNaN(cents2)) {
      onError('Please enter valid amounts');
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Call API to verify the amounts
      const result = await subscriptionService.verifyBankAccount(
        subscriptionId,
        [cents1, cents2],
        bankAccountId
      );
      
      if (result.success) {
        onSuccess();
      } else {
        onError(result.message || 'Verification failed');
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'An error occurred during verification');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className={`p-6 ${darkMode ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'} rounded-lg shadow-sm`}>
      <h3 className="text-xl font-semibold mb-4">Verify Your Bank Account</h3>
      
      <div className={`mb-6 p-4 rounded-md ${darkMode ? 'bg-gray-800' : 'bg-blue-50'}`}>
        <h4 className={`text-sm font-medium ${darkMode ? 'text-gray-200' : 'text-blue-800'} mb-2`}>Micro-Deposit Verification</h4>
        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-blue-600'}`}>
          Two small deposits have been sent to your bank account. These deposits typically 
          appear within 1-2 business days with a description like "VERIFICATION".
          Enter the exact amounts below to verify your account.
        </p>
      </div>
      
      <form onSubmit={handleVerify}>
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label htmlFor="amount1" className={`block text-sm font-medium ${labelClasses} mb-1`}>
              First Deposit Amount ($)
            </label>
            <input
              type="text"
              id="amount1"
              className={`w-full px-3 py-2 border rounded-md ${inputClasses}`}
              placeholder="0.32"
              value={amount1}
              onChange={(e) => setAmount1(e.target.value)}
              required
            />
          </div>
          
          <div>
            <label htmlFor="amount2" className={`block text-sm font-medium ${labelClasses} mb-1`}>
              Second Deposit Amount ($)
            </label>
            <input
              type="text"
              id="amount2"
              className={`w-full px-3 py-2 border rounded-md ${inputClasses}`}
              placeholder="0.45"
              value={amount2}
              onChange={(e) => setAmount2(e.target.value)}
              required
            />
          </div>
        </div>
        
        <div className="mt-4">
          <button
            type="submit"
            className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium 
            ${buttonClasses} focus:outline-none focus:ring-2 focus:ring-offset-2 ${darkMode ? 'focus:ring-purple-500' : 'focus:ring-indigo-500'}`}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Verifying...' : 'Verify Bank Account'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default BankAccountVerification;