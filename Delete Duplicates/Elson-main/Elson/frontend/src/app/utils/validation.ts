/**
 * Validation utility functions for forms
 */

import { CreditCardValues } from '../components/subscription/CreditCardInput';
import { BankAccountValues } from '../components/subscription/BankAccountInput';

/**
 * Validates a credit card number using the Luhn algorithm
 */
export const validateCardNumber = (number: string): boolean => {
  const digits = number.replace(/\D/g, '');
  if (digits.length < 13 || digits.length > 19) {
    return false;
  }
  
  // Luhn algorithm
  let sum = 0;
  let shouldDouble = false;
  
  // Loop from right to left
  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = parseInt(digits.charAt(i), 10);
    
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  
  return sum % 10 === 0;
};

/**
 * Validates a credit card expiry date
 */
export const validateExpiryDate = (month: number, year: number): boolean => {
  if (!month || !year) {
    return false;
  }
  
  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth() + 1; // JS months are 0-based
  
  // Check if the card has expired
  if (year < currentYear || (year === currentYear && month < currentMonth)) {
    return false;
  }
  
  return true;
};

/**
 * Validates a credit card CVC/CVV
 */
export const validateCVC = (cvc: string): boolean => {
  const digits = cvc.replace(/\D/g, '');
  // Most cards have 3 digits, Amex has 4
  return digits.length >= 3 && digits.length <= 4;
};

/**
 * Complete credit card validation
 */
export const validateCreditCard = (card: CreditCardValues): Record<string, string> => {
  const errors: Record<string, string> = {};
  
  // Validate card number
  if (!card.card_number) {
    errors.card_number = 'Card number is required';
  } else if (!validateCardNumber(card.card_number)) {
    errors.card_number = 'Invalid card number';
  }
  
  // Validate expiry date
  if (!card.expiry_month || !card.expiry_year) {
    errors.expiry = 'Expiry date is required';
  } else if (!validateExpiryDate(card.expiry_month, card.expiry_year)) {
    errors.expiry = 'Card has expired';
  }
  
  // Validate CVC
  if (!card.cvc) {
    errors.cvc = 'CVC is required';
  } else if (!validateCVC(card.cvc)) {
    errors.cvc = 'Invalid CVC';
  }
  
  // Validate cardholder name
  if (!card.cardholder_name) {
    errors.cardholder_name = 'Cardholder name is required';
  } else if (card.cardholder_name.length < 3) {
    errors.cardholder_name = 'Please enter full name';
  }
  
  return errors;
};

/**
 * Validates if a PayPal email is potentially valid
 * This is just a basic check as PayPal will handle the actual validation
 */
export const validatePayPalEmail = (email: string): boolean => {
  if (!email) return false;
  
  // Basic email regex
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validates a routing number using the ABA standard
 * U.S. routing numbers are 9 digits and use a checksum algorithm
 */
export const validateRoutingNumber = (routingNumber: string): boolean => {
  // Ensure it's exactly 9 digits
  const digits = routingNumber.replace(/\D/g, '');
  if (digits.length !== 9) {
    return false;
  }
  
  // ABA routing number checksum validation
  let sum = 0;
  for (let i = 0; i < digits.length; i++) {
    let value = parseInt(digits.charAt(i), 10);
    
    // Apply ABA routing number checksum weights (3-7-1 formula)
    if (i % 3 === 0) {
      value *= 3;
    } else if (i % 3 === 1) {
      value *= 7;
    } else {
      value *= 1;
    }
    
    sum += value;
  }
  
  // Valid routing numbers are divisible by 10
  return sum !== 0 && sum % 10 === 0;
};

/**
 * Validates a bank account number
 * This is a basic validation; we rely on Stripe's API for actual verification
 */
export const validateAccountNumber = (accountNumber: string): boolean => {
  const digits = accountNumber.replace(/\D/g, '');
  
  // Account numbers are typically between 6-17 digits
  return digits.length >= 6 && digits.length <= 17;
};

/**
 * Complete bank account validation
 */
export const validateBankAccount = (bankAccount: BankAccountValues): Record<string, string> => {
  const errors: Record<string, string> = {};
  
  // Validate account number
  if (!bankAccount.account_number) {
    errors.account_number = 'Account number is required';
  } else if (!validateAccountNumber(bankAccount.account_number)) {
    errors.account_number = 'Invalid account number';
  }
  
  // Validate routing number
  if (!bankAccount.routing_number) {
    errors.routing_number = 'Routing number is required';
  } else if (!validateRoutingNumber(bankAccount.routing_number)) {
    errors.routing_number = 'Invalid routing number';
  }
  
  // Validate account holder name
  if (!bankAccount.account_holder_name) {
    errors.account_holder_name = 'Account holder name is required';
  } else if (bankAccount.account_holder_name.length < 3) {
    errors.account_holder_name = 'Please enter full name';
  }
  
  // Validate account type
  if (!bankAccount.account_type) {
    errors.account_type = 'Account type is required';
  }
  
  return errors;
};

/**
 * Validates subscription form data
 */
export const validateSubscriptionForm = (
  plan: string,
  billingCycle: string,
  agreeToTerms: boolean,
  paymentMethod: string,
  creditCardData?: CreditCardValues,
  bankAccountData?: BankAccountValues
): Record<string, string> => {
  const errors: Record<string, string> = {};
  
  // Validate plan selection
  if (!plan) {
    errors.plan = 'Please select a subscription plan';
  }
  
  // Validate billing cycle
  if (!billingCycle) {
    errors.billingCycle = 'Please select a billing cycle';
  }
  
  // Validate terms agreement
  if (!agreeToTerms) {
    errors.agreeToTerms = 'You must agree to the terms and conditions';
  }
  
  // Validate payment method
  if (!paymentMethod) {
    errors.paymentMethod = 'Please select a payment method';
  }
  
  // Validate credit card data if credit card is selected
  if (paymentMethod === 'credit_card' && creditCardData) {
    const cardErrors = validateCreditCard(creditCardData);
    Object.keys(cardErrors).forEach(key => {
      errors[`card_${key}`] = cardErrors[key];
    });
  }
  
  // Validate bank account data if bank account is selected
  if (paymentMethod === 'bank_account' && bankAccountData) {
    const bankErrors = validateBankAccount(bankAccountData);
    Object.keys(bankErrors).forEach(key => {
      errors[`bank_${key}`] = bankErrors[key];
    });
  }
  
  return errors;
};