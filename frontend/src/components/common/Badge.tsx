import React from 'react';

type ColorVariant = 'success' | 'warning' | 'error' | 'info' | 'premium' | 'neutral' | 'green' | 'red' | 'yellow' | 'blue' | 'gray';

interface BadgeProps {
  children: React.ReactNode;
  variant?: ColorVariant;
  color?: ColorVariant;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant,
  color,
  size = 'sm',
  className = '',
}) => {
  const effectiveVariant = variant || color || 'neutral';

  const variantClasses: Record<ColorVariant, string> = {
    success: 'bg-green-900 text-green-300 bg-opacity-40',
    green: 'bg-green-900 text-green-300 bg-opacity-40',
    warning: 'bg-yellow-900 text-yellow-300 bg-opacity-40',
    yellow: 'bg-yellow-900 text-yellow-300 bg-opacity-40',
    error: 'bg-red-900 text-red-300 bg-opacity-40',
    red: 'bg-red-900 text-red-300 bg-opacity-40',
    info: 'bg-blue-900 text-blue-300 bg-opacity-40',
    blue: 'bg-blue-900 text-blue-300 bg-opacity-40',
    premium: 'bg-gradient-to-r from-yellow-400 to-red-500 text-white',
    neutral: 'bg-gray-800 text-gray-300',
    gray: 'bg-gray-800 text-gray-300',
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  return (
    <span
      className={`
        inline-flex items-center rounded-full font-medium
        ${variantClasses[effectiveVariant]}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {children}
    </span>
  );
};

interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'pending' | 'success' | 'failed';
  children?: React.ReactNode;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, children }) => {
  const statusConfig = {
    active: { variant: 'success' as const, text: 'Active' },
    inactive: { variant: 'neutral' as const, text: 'Inactive' },
    pending: { variant: 'warning' as const, text: 'Pending' },
    success: { variant: 'success' as const, text: 'Success' },
    failed: { variant: 'error' as const, text: 'Failed' },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size="sm">
      {children || config.text}
    </Badge>
  );
};