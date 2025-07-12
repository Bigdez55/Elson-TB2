import React from 'react';

type BadgeVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info';
type BadgeSize = 'xs' | 'sm' | 'md';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
  rounded?: boolean;
}

const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'sm',
  className = '',
  rounded = false,
}) => {
  // Base styles
  const baseStyles = 'inline-flex items-center justify-center font-medium';
  
  // Variant styles
  const variantStyles = {
    primary: 'bg-purple-900 text-purple-300',
    secondary: 'bg-gray-700 text-gray-300',
    success: 'bg-green-900 text-green-300',
    warning: 'bg-yellow-900 text-yellow-300',
    danger: 'bg-red-900 text-red-300',
    info: 'bg-blue-900 text-blue-300',
  };
  
  // Size styles
  const sizeStyles = {
    xs: 'text-xs px-1.5 py-0.5',
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-2.5 py-1',
  };
  
  // Rounded styles
  const roundedStyles = rounded ? 'rounded-full' : 'rounded';

  return (
    <span 
      className={`
        ${baseStyles} 
        ${variantStyles[variant]} 
        ${sizeStyles[size]} 
        ${roundedStyles} 
        ${className}
      `}
    >
      {children}
    </span>
  );
};

export default Badge;