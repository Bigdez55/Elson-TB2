// Validate email format
export const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };
  
  // Validate password strength
  export const isValidPassword = (password: string): boolean => {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/;
    return passwordRegex.test(password);
  };
  
  // Validate trade amount
  export const isValidTradeAmount = (amount: number): boolean => {
    return amount > 0 && Number.isFinite(amount);
  };
  
  // Validate trading symbol
  export const isValidSymbol = (symbol: string): boolean => {
    // Basic symbol format validation (e.g., BTC/USD)
    const symbolRegex = /^[A-Z0-9]{2,8}\/[A-Z0-9]{2,8}$/;
    return symbolRegex.test(symbol);
  };
  
  // Validate numeric input with optional decimal places
  export const isValidNumber = (value: string, decimals = 2): boolean => {
    const numberRegex = new RegExp(`^\\d*\\.?\\d{0,${decimals}}$`);
    return numberRegex.test(value);
  };