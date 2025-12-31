import React from 'react';

interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'large';
  className?: string;
  color?: 'blue' | 'white' | 'gray' | string;
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = '',
  color = 'blue',
  text,
}) => {
  const sizeClasses: Record<string, string> = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    large: 'w-12 h-12',
  };

  const colorClasses: Record<string, string> = {
    blue: 'border-gray-600 border-t-blue-500',
    white: 'border-gray-300 border-t-white',
    gray: 'border-gray-600 border-t-gray-400',
  };

  // Handle custom color classes (e.g., "text-purple-600")
  const spinnerColor = colorClasses[color] || 'border-gray-300 border-t-current';
  const customColorClass = color?.startsWith('text-') ? color : '';

  return (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      <div
        className={`
          ${sizeClasses[size] || sizeClasses.md}
          ${spinnerColor}
          ${customColorClass}
          border-2 rounded-full animate-spin
        `}
      />
      {text && (
        <p className="text-sm text-gray-600">{text}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;
