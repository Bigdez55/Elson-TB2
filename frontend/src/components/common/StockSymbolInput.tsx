import React, { useState, useCallback } from 'react';

interface StockSymbolInputProps {
  label?: string;
  value: string;
  onChange: (symbol: string) => void;
  required?: boolean;
  darkMode?: boolean;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export const StockSymbolInput: React.FC<StockSymbolInputProps> = ({
  label,
  value,
  onChange,
  required = false,
  darkMode = false,
  placeholder = 'Enter symbol (e.g., AAPL)',
  className = '',
  disabled = false,
}) => {
  const [inputValue, setInputValue] = useState(value);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value.toUpperCase();
    setInputValue(newValue);
  }, []);

  const handleBlur = useCallback(() => {
    onChange(inputValue);
  }, [inputValue, onChange]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onChange(inputValue);
    }
  }, [inputValue, onChange]);

  React.useEffect(() => {
    setInputValue(value);
  }, [value]);

  const baseClasses = darkMode
    ? 'bg-gray-700 text-white border-gray-600 placeholder-gray-400'
    : 'bg-white text-gray-900 border-gray-300 placeholder-gray-500';

  return (
    <div className={`${className}`}>
      {label && (
        <label className={`block text-sm font-medium mb-1 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        type="text"
        value={inputValue}
        onChange={handleChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className={`
          w-full px-3 py-2 rounded-md border
          ${baseClasses}
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      />
    </div>
  );
};

export default StockSymbolInput;
