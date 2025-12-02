import React from 'react';

interface PayPalPaymentInputProps {
  darkMode?: boolean;
}

/**
 * PayPal payment input component
 * Just a visual representation - actual payment is handled through PayPal redirect
 */
export const PayPalPaymentInput: React.FC<PayPalPaymentInputProps> = ({ darkMode = false }) => {
  // Logic here is minimal since PayPal handles the actual payment UI
  
  // Select appropriate component styles based on dark mode
  const containerClasses = darkMode 
    ? "bg-gray-800 border border-gray-700 rounded-lg p-4 text-center"
    : "bg-gray-50 border border-gray-200 rounded-lg p-4 text-center";
    
  const textClasses = darkMode 
    ? "text-gray-300 mb-4"
    : "text-gray-700 mb-4";
    
  const securityClasses = darkMode
    ? "text-xs text-gray-500 flex items-center justify-center mt-4"
    : "text-xs text-gray-500 flex items-center justify-center mt-4";
    
  const iconClasses = darkMode
    ? "h-4 w-4 text-gray-400 mr-1"
    : "h-4 w-4 text-gray-400 mr-1";
  
  return (
    <div className={containerClasses}>
      <p className={textClasses}>
        You will be redirected to PayPal to complete your payment.
      </p>
      <img 
        src="/paypal_logo.svg" 
        alt="PayPal" 
        className="h-10 mx-auto"
      />
      
      <div className={securityClasses}>
        <svg className={iconClasses} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        PayPal securely handles your payment information
      </div>
      
      <div className="mt-4 text-sm">
        <ul className={darkMode ? "text-gray-400" : "text-gray-600"}>
          <li className="flex items-center">
            <svg className="h-4 w-4 mr-1 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            No Elson account required for payment
          </li>
          <li className="flex items-center">
            <svg className="h-4 w-4 mr-1 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Pay with your PayPal balance or linked cards
          </li>
          <li className="flex items-center">
            <svg className="h-4 w-4 mr-1 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Purchase protection on eligible payments
          </li>
        </ul>
      </div>
    </div>
  );
};

export default PayPalPaymentInput;