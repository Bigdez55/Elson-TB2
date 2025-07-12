import React, { useState, useEffect } from 'react';
import { validateRoutingNumber, validateAccountNumber } from '../../utils/validation';

export interface BankAccountValues {
  account_number: string;
  routing_number: string;
  account_type: string;
  account_holder_name: string;
}

interface BankAccountInputProps {
  values?: BankAccountValues;
  onChange: (values: BankAccountValues) => void;
  darkMode?: boolean;
}

const BankAccountInput: React.FC<BankAccountInputProps> = ({
  values = {
    account_number: '',
    routing_number: '',
    account_type: 'checking',
    account_holder_name: ''
  },
  onChange,
  darkMode = false
}) => {
  const [accountNumber, setAccountNumber] = useState(values.account_number);
  const [routingNumber, setRoutingNumber] = useState(values.routing_number);
  const [accountType, setAccountType] = useState(values.account_type);
  const [accountHolder, setAccountHolder] = useState(values.account_holder_name);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Update parent component when local state changes
  useEffect(() => {
    onChange({
      account_number: accountNumber,
      routing_number: routingNumber,
      account_type: accountType,
      account_holder_name: accountHolder
    });
  }, [accountNumber, routingNumber, accountType, accountHolder, onChange]);
  
  // Validate on blur
  const validateField = (field: string, value: string) => {
    const newErrors = { ...errors };
    
    switch (field) {
      case 'account_number':
        if (!value) {
          newErrors.account_number = 'Account number is required';
        } else if (!validateAccountNumber(value)) {
          newErrors.account_number = 'Invalid account number';
        } else {
          delete newErrors.account_number;
        }
        break;
        
      case 'routing_number':
        if (!value) {
          newErrors.routing_number = 'Routing number is required';
        } else if (!validateRoutingNumber(value)) {
          newErrors.routing_number = 'Invalid routing number';
        } else {
          delete newErrors.routing_number;
        }
        break;
        
      case 'account_holder_name':
        if (!value) {
          newErrors.account_holder_name = 'Account holder name is required';
        } else if (value.length < 3) {
          newErrors.account_holder_name = 'Please enter full name';
        } else {
          delete newErrors.account_holder_name;
        }
        break;
    }
    
    setErrors(newErrors);
  };
  
  // Style classes based on dark mode
  const inputClasses = darkMode
    ? 'bg-gray-800 border-gray-700 text-white placeholder-gray-500 focus:ring-purple-500 focus:border-purple-500'
    : 'bg-white border-gray-300 text-gray-700 placeholder-gray-400 focus:ring-indigo-500 focus:border-indigo-500';
    
  const labelClasses = darkMode
    ? 'text-gray-300'
    : 'text-gray-700';
    
  const errorClasses = darkMode
    ? 'text-red-400 text-sm mt-1'
    : 'text-red-500 text-sm mt-1';
  
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="routing_number" className={`block text-sm font-medium ${labelClasses} mb-1`}>
          Routing Number
        </label>
        <input
          type="text"
          id="routing_number"
          maxLength={9}
          className={`w-full px-3 py-2 border rounded-md ${inputClasses} ${errors.routing_number ? (darkMode ? 'border-red-600' : 'border-red-500') : ''}`}
          value={routingNumber}
          onChange={(e) => setRoutingNumber(e.target.value.replace(/\D/g, ''))}
          onBlur={() => validateField('routing_number', routingNumber)}
          placeholder="123456789"
        />
        {errors.routing_number && <div className={errorClasses}>{errors.routing_number}</div>}
        <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
          The 9-digit routing number from your bank
        </p>
      </div>
      
      <div>
        <label htmlFor="account_number" className={`block text-sm font-medium ${labelClasses} mb-1`}>
          Account Number
        </label>
        <input
          type="text"
          id="account_number"
          className={`w-full px-3 py-2 border rounded-md ${inputClasses} ${errors.account_number ? (darkMode ? 'border-red-600' : 'border-red-500') : ''}`}
          value={accountNumber}
          onChange={(e) => setAccountNumber(e.target.value.replace(/\D/g, ''))}
          onBlur={() => validateField('account_number', accountNumber)}
          placeholder="Your account number"
        />
        {errors.account_number && <div className={errorClasses}>{errors.account_number}</div>}
      </div>
      
      <div>
        <label htmlFor="account_type" className={`block text-sm font-medium ${labelClasses} mb-1`}>
          Account Type
        </label>
        <select
          id="account_type"
          className={`w-full px-3 py-2 border rounded-md ${inputClasses}`}
          value={accountType}
          onChange={(e) => setAccountType(e.target.value)}
        >
          <option value="checking">Checking</option>
          <option value="savings">Savings</option>
        </select>
      </div>
      
      <div>
        <label htmlFor="account_holder_name" className={`block text-sm font-medium ${labelClasses} mb-1`}>
          Account Holder Name
        </label>
        <input
          type="text"
          id="account_holder_name"
          className={`w-full px-3 py-2 border rounded-md ${inputClasses} ${errors.account_holder_name ? (darkMode ? 'border-red-600' : 'border-red-500') : ''}`}
          value={accountHolder}
          onChange={(e) => setAccountHolder(e.target.value)}
          onBlur={() => validateField('account_holder_name', accountHolder)}
          placeholder="Name on account"
        />
        {errors.account_holder_name && <div className={errorClasses}>{errors.account_holder_name}</div>}
      </div>
      
      <div className={`mt-4 p-4 border rounded-md ${darkMode ? 'bg-gray-900 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
        <h4 className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-800'} mb-2`}>Bank Account Information</h4>
        <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          By providing your bank information, you authorize Elson Wealth to send instructions to your bank to debit your account for subscription charges. Your account must have these transaction rights enabled.
        </p>
      </div>
    </div>
  );
};

export default BankAccountInput;