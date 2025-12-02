import React from 'react';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  disabled = false,
  label,
  description,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: {
      toggle: 'w-8 h-4',
      knob: 'w-3 h-3',
      transform: 'translate-x-4',
    },
    md: {
      toggle: 'w-12 h-6',
      knob: 'w-5 h-5',
      transform: 'translate-x-6',
    },
    lg: {
      toggle: 'w-14 h-7',
      knob: 'w-6 h-6',
      transform: 'translate-x-7',
    },
  };

  const currentSize = sizeClasses[size];

  return (
    <div className="flex items-center justify-between">
      {(label || description) && (
        <div className="flex-1 mr-4">
          {label && <h3 className="text-white font-medium">{label}</h3>}
          {description && <p className="text-gray-400 text-sm">{description}</p>}
        </div>
      )}
      <button
        type="button"
        onClick={() => !disabled && onChange(!checked)}
        disabled={disabled}
        className={`
          relative inline-flex items-center ${currentSize.toggle} rounded-full transition-colors duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900
          ${checked ? 'bg-purple-600' : 'bg-gray-600'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <span
          className={`
            inline-block ${currentSize.knob} rounded-full bg-white transform transition-transform duration-300 ease-in-out
            ${checked ? currentSize.transform : 'translate-x-0.5'}
          `}
        />
      </button>
    </div>
  );
};

interface ToggleGroupProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const ToggleGroup: React.FC<ToggleGroupProps> = ({
  title,
  children,
  className = '',
}) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {title && <h3 className="text-white font-medium mb-3">{title}</h3>}
      <div className="space-y-3">
        {children}
      </div>
    </div>
  );
};