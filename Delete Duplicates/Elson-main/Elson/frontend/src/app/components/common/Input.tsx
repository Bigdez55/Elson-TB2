import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  fullWidth?: boolean;
  actionIcon?: React.ReactNode;
  onActionClick?: () => void;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  startIcon,
  endIcon,
  className = '',
  fullWidth = true,
  disabled,
  required,
  actionIcon,
  onActionClick,
  ...props
}, ref) => {
  // Define base input styles
  const baseInputStyles = 
    'block rounded-lg border bg-gray-800 text-white transition-colors ' +
    'focus:ring-2 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';

  // Adjust styles based on error state
  const inputStyles = `
    ${baseInputStyles}
    ${error 
      ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
      : 'border-gray-700 focus:border-purple-500 focus:ring-purple-500'}
    ${startIcon ? 'pl-10' : 'pl-4'}
    ${endIcon || actionIcon ? 'pr-10' : 'pr-4'}
    py-2.5
  `;

  const widthStyle = fullWidth ? 'w-full' : '';

  return (
    <div className={widthStyle}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Input wrapper for icons */}
      <div className="relative">
        {/* Start Icon */}
        {startIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
            {startIcon}
          </div>
        )}

        {/* Input element */}
        <input
          ref={ref}
          className={`${inputStyles} ${className} ${widthStyle}`}
          disabled={disabled}
          aria-invalid={error ? 'true' : 'false'}
          {...props}
        />

        {/* End Icon (non-clickable) */}
        {endIcon && !actionIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-gray-400">
            {endIcon}
          </div>
        )}

        {/* Action Icon (clickable) */}
        {actionIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <button
              type="button"
              className="text-gray-400 hover:text-purple-500 focus:outline-none transition-colors"
              onClick={onActionClick}
              tabIndex={-1}
            >
              {actionIcon}
            </button>
          </div>
        )}
      </div>

      {/* Error message or helper text */}
      {(error || helperText) && (
        <p className={`mt-1.5 text-sm ${error ? 'text-red-500' : 'text-gray-400'}`}>
          {error || helperText}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;