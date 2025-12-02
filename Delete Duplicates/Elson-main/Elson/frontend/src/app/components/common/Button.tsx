// frontend/src/app/components/common/Button.tsx
import React, { useMemo } from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className = '',
  fullWidth = false,
  loading = false,
  leftIcon,
  rightIcon,
  disabled,
  ...props 
}) => {
  // Check for touch device - moved up before use
  const isTouch = useMemo(() => {
    if (typeof window !== 'undefined') {
      return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    return false;
  }, []);

  const baseStyles = `rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-opacity-50 flex items-center justify-center ${isTouch ? 'active:translate-y-0.5' : ''}`;
  
  const variantStyles: Record<string, string> = {
    primary: 'bg-purple-600 hover:bg-purple-700 text-white focus:ring-purple-500',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-white focus:ring-gray-500',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
    outline: 'bg-transparent border border-purple-600 text-purple-500 hover:bg-purple-600 hover:bg-opacity-10 focus:ring-purple-500',
    ghost: 'bg-transparent hover:bg-gray-700 text-gray-300 hover:text-white focus:ring-gray-500'
  };
  
  const sizeStyles: Record<string, string> = {
    xs: 'px-2 py-1 text-xs',
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  const widthStyles = fullWidth ? 'w-full' : '';
  const disabledStyles = disabled || loading ? 'opacity-60 cursor-not-allowed' : '';

  // Loading spinner
  const loadingSpinner = (
    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  );

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${widthStyles} ${disabledStyles} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading && loadingSpinner}
      {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
      {children}
      {!loading && rightIcon && <span className="ml-2">{rightIcon}</span>}
    </button>
  );
};

export default Button;