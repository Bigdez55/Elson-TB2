export const isValidNumber = (value: string): boolean => {
  const num = parseFloat(value);
  return !isNaN(num) && isFinite(num);
};

export const isPositiveNumber = (value: string): boolean => {
  const num = parseFloat(value);
  return isValidNumber(value) && num > 0;
};

export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidSymbol = (symbol: string): boolean => {
  // Basic symbol validation - alphanumeric and some special characters
  const symbolRegex = /^[A-Z0-9/.-]+$/i;
  return symbolRegex.test(symbol) && symbol.length >= 1 && symbol.length <= 10;
};

export const validateOrderAmount = (amount: string, balance: number): string | null => {
  if (!amount || amount.trim() === '') {
    return 'Amount is required';
  }
  
  if (!isValidNumber(amount)) {
    return 'Please enter a valid number';
  }
  
  const numAmount = parseFloat(amount);
  if (numAmount <= 0) {
    return 'Amount must be greater than 0';
  }
  
  if (numAmount > balance) {
    return 'Insufficient balance';
  }
  
  return null;
};

export const validatePrice = (price: string): string | null => {
  if (!price || price.trim() === '') {
    return 'Price is required';
  }
  
  if (!isValidNumber(price)) {
    return 'Please enter a valid price';
  }
  
  const numPrice = parseFloat(price);
  if (numPrice <= 0) {
    return 'Price must be greater than 0';
  }
  
  return null;
};