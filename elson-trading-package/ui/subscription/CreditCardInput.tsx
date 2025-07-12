import React, { useState } from 'react';
import { validateCardNumber, validateExpiryDate, validateCVC } from '../../utils/validation';

export interface CreditCardValues {
  card_number: string;
  expiry_month: number;
  expiry_year: number;
  cvc: string;
  cardholder_name: string;
}

interface CreditCardInputProps {
  values: CreditCardValues;
  onChange: (values: CreditCardValues) => void;
  showBillingAddress?: boolean;
}

export const CreditCardInput: React.FC<CreditCardInputProps> = ({
  values,
  onChange,
  showBillingAddress = false
}) => {
  const [errors, setErrors] = useState<Partial<Record<keyof CreditCardValues, string>>>({});
  
  // Format credit card number with spaces
  const formatCardNumber = (value: string) => {
    return value
      .replace(/\s/g, '')
      .replace(/(.{4})/g, '$1 ')
      .trim();
  };
  
  // Format expiry date
  const handleExpiryChange = (value: string) => {
    // Remove non-digits
    const cleaned = value.replace(/\D/g, '');
    
    // Split into month and year
    if (cleaned.length >= 2) {
      const month = parseInt(cleaned.substring(0, 2), 10);
      const year = cleaned.length > 2 ? parseInt(cleaned.substring(2, 4), 10) : 0;
      
      // Validate month (1-12)
      const validMonth = month > 0 && month <= 12 ? month : 0;
      
      // Update state
      onChange({
        ...values,
        expiry_month: validMonth,
        expiry_year: year ? 2000 + year : 0
      });
    } else if (cleaned.length === 1) {
      onChange({
        ...values,
        expiry_month: parseInt(cleaned, 10),
        expiry_year: 0
      });
    } else {
      onChange({
        ...values,
        expiry_month: 0,
        expiry_year: 0
      });
    }
  };
  
  // Validate card number - now using the utility function
  
  // Validate input field
  const validateField = (field: keyof CreditCardValues) => {
    let errorMessage = '';
    
    switch (field) {
      case 'card_number':
        const cleanedNumber = values.card_number.replace(/\D/g, '');
        if (!cleanedNumber) {
          errorMessage = 'Card number is required';
        } else if (cleanedNumber.length < 13) {
          errorMessage = 'Card number is too short';
        } else if (!validateCardNumber(cleanedNumber)) {
          errorMessage = 'Invalid card number';
        }
        break;
        
      case 'expiry_month':
      case 'expiry_year':
        if (!values.expiry_month || !values.expiry_year) {
          errorMessage = 'Expiry date is required';
        } else if (!validateExpiryDate(values.expiry_month, values.expiry_year)) {
          errorMessage = 'Card has expired';
        }
        break;
        
      case 'cvc':
        if (!values.cvc) {
          errorMessage = 'CVC is required';
        } else if (!validateCVC(values.cvc)) {
          errorMessage = 'Invalid CVC';
        }
        break;
        
      case 'cardholder_name':
        if (!values.cardholder_name) {
          errorMessage = 'Cardholder name is required';
        }
        break;
    }
    
    setErrors(prev => ({
      ...prev,
      [field]: errorMessage
    }));
    
    return !errorMessage;
  };
  
  return (
    <div className="space-y-4">
      {/* Card number */}
      <div>
        <label htmlFor="card_number" className="block text-sm font-medium text-gray-700 mb-1">
          Card Number
        </label>
        <input
          type="text"
          id="card_number"
          placeholder="1234 5678 9012 3456"
          className={`w-full border ${errors.card_number ? 'border-red-500' : 'border-gray-300'} rounded-md p-2`}
          value={values.card_number}
          onChange={(e) => {
            const formatted = formatCardNumber(e.target.value);
            onChange({
              ...values,
              card_number: formatted
            });
          }}
          onBlur={() => validateField('card_number')}
          maxLength={19}
        />
        {errors.card_number && (
          <p className="text-sm text-red-600 mt-1">{errors.card_number}</p>
        )}
      </div>
      
      {/* Expiry date and CVC */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="expiry_date" className="block text-sm font-medium text-gray-700 mb-1">
            Expiry Date (MM/YY)
          </label>
          <input
            type="text"
            id="expiry_date"
            placeholder="MM/YY"
            className={`w-full border ${errors.expiry_month || errors.expiry_year ? 'border-red-500' : 'border-gray-300'} rounded-md p-2`}
            value={`${values.expiry_month.toString().padStart(2, '0')}${values.expiry_year ? '/' + values.expiry_year.toString().substring(2, 4) : ''}`}
            onChange={(e) => handleExpiryChange(e.target.value)}
            onBlur={() => validateField('expiry_month')}
            maxLength={5}
          />
          {(errors.expiry_month || errors.expiry_year) && (
            <p className="text-sm text-red-600 mt-1">{errors.expiry_month || errors.expiry_year}</p>
          )}
        </div>
        
        <div>
          <label htmlFor="cvc" className="block text-sm font-medium text-gray-700 mb-1">
            CVC
          </label>
          <input
            type="text"
            id="cvc"
            placeholder="123"
            className={`w-full border ${errors.cvc ? 'border-red-500' : 'border-gray-300'} rounded-md p-2`}
            value={values.cvc}
            onChange={(e) => {
              // Only allow digits
              const value = e.target.value.replace(/\D/g, '');
              onChange({
                ...values,
                cvc: value
              });
            }}
            onBlur={() => validateField('cvc')}
            maxLength={4}
          />
          {errors.cvc && (
            <p className="text-sm text-red-600 mt-1">{errors.cvc}</p>
          )}
        </div>
      </div>
      
      {/* Cardholder name */}
      <div>
        <label htmlFor="cardholder_name" className="block text-sm font-medium text-gray-700 mb-1">
          Cardholder Name
        </label>
        <input
          type="text"
          id="cardholder_name"
          placeholder="John Doe"
          className={`w-full border ${errors.cardholder_name ? 'border-red-500' : 'border-gray-300'} rounded-md p-2`}
          value={values.cardholder_name}
          onChange={(e) => {
            onChange({
              ...values,
              cardholder_name: e.target.value
            });
          }}
          onBlur={() => validateField('cardholder_name')}
        />
        {errors.cardholder_name && (
          <p className="text-sm text-red-600 mt-1">{errors.cardholder_name}</p>
        )}
      </div>
      
      {/* Billing address (optionally shown) */}
      {showBillingAddress && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Billing Address</h4>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="street" className="block text-sm font-medium text-gray-700 mb-1">
                Street Address
              </label>
              <input
                type="text"
                id="street"
                className="w-full border border-gray-300 rounded-md p-2"
                placeholder="123 Main St"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                  City
                </label>
                <input
                  type="text"
                  id="city"
                  className="w-full border border-gray-300 rounded-md p-2"
                  placeholder="New York"
                />
              </div>
              
              <div>
                <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
                  State/Province
                </label>
                <input
                  type="text"
                  id="state"
                  className="w-full border border-gray-300 rounded-md p-2"
                  placeholder="NY"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="zip" className="block text-sm font-medium text-gray-700 mb-1">
                  ZIP/Postal Code
                </label>
                <input
                  type="text"
                  id="zip"
                  className="w-full border border-gray-300 rounded-md p-2"
                  placeholder="10001"
                />
              </div>
              
              <div>
                <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">
                  Country
                </label>
                <select
                  id="country"
                  className="w-full border border-gray-300 rounded-md p-2"
                >
                  <option value="US">United States</option>
                  <option value="CA">Canada</option>
                  <option value="UK">United Kingdom</option>
                  <option value="AU">Australia</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Payment card brands */}
      <div className="flex space-x-2 mt-2">
        <img 
          src="/visa.svg" 
          alt="Visa" 
          className="h-6"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="12" viewBox="0 0 40 12"><rect width="40" height="12" fill="%23f5f5f5"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="8" fill="%23666666">Visa</text></svg>';
          }}
        />
        <img 
          src="/mastercard.svg" 
          alt="Mastercard" 
          className="h-6"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="12" viewBox="0 0 40 12"><rect width="40" height="12" fill="%23f5f5f5"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="8" fill="%23666666">MC</text></svg>';
          }}
        />
        <img 
          src="/amex.svg" 
          alt="American Express" 
          className="h-6"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="12" viewBox="0 0 40 12"><rect width="40" height="12" fill="%23f5f5f5"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="8" fill="%23666666">Amex</text></svg>';
          }}
        />
        <img 
          src="/discover.svg" 
          alt="Discover" 
          className="h-6"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="12" viewBox="0 0 40 12"><rect width="40" height="12" fill="%23f5f5f5"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="8" fill="%23666666">Disc</text></svg>';
          }}
        />
      </div>
      
      <div className="text-xs text-gray-500 flex items-center">
        <svg className="h-4 w-4 text-gray-400 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        Secure payment processed using 256-bit encryption
      </div>
    </div>
  );
};

export default CreditCardInput;