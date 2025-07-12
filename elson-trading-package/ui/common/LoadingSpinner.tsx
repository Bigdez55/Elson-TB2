import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  className?: string;
  fullScreen?: boolean;
  text?: string;
}

/**
 * A loading spinner component with configurable size and color
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  color = 'text-purple-600',
  className = '',
  fullScreen = false,
  text
}) => {
  // Map size prop to actual size values
  const sizeClasses = {
    small: 'w-4 h-4 border-2',
    medium: 'w-8 h-8 border-4',
    large: 'w-12 h-12 border-4',
  };

  // Text size based on spinner size
  const textSizes = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base',
  };

  const spinner = (
    <div className="flex flex-col justify-center items-center">
      <div 
        className={`
          ${sizeClasses[size]} 
          ${color} 
          ${className}
          rounded-full 
          border-t-transparent 
          animate-spin
        `}
      />
      {text && (
        <p className={`mt-2 ${textSizes[size]} text-gray-400`}>{text}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-50">
        {spinner}
      </div>
    );
  }

  return (
    <div className="flex justify-center items-center">
      {spinner}
    </div>
  );
};

export default LoadingSpinner;