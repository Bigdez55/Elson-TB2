import React, { useMemo } from 'react';

interface Option {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  options: Option[];
  label?: string;
  error?: string;
  helperText?: string;
  onChange?: (value: string) => void;
  fullWidth?: boolean;
  startIcon?: React.ReactNode;
  placeholder?: string;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({
  options,
  label,
  error,
  helperText,
  className = '',
  disabled,
  required,
  onChange,
  fullWidth = true,
  startIcon,
  placeholder,
  ...props
}, ref) => {
  // Handle change events
  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    onChange?.(event.target.value);
  };

  // Check for touch device
  const isTouch = useMemo(() => {
    if (typeof window !== 'undefined') {
      return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    return false;
  }, []);

  // Base styles for the select element
  const baseSelectStyles = 
    'block rounded-lg border bg-gray-800 text-white transition-colors ' +
    'focus:ring-2 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed ' +
    `appearance-none ${isTouch ? 'text-base' : ''}`;

  // Combine styles based on error state
  const selectStyles = `
    ${baseSelectStyles}
    ${error 
      ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
      : 'border-gray-700 focus:border-purple-500 focus:ring-purple-500'}
    ${startIcon ? 'pl-10' : 'pl-4'}
    pr-10 ${isTouch ? 'py-3' : 'py-2.5'}
  `.trim();

  const widthStyle = fullWidth ? 'w-full' : '';
  const placeholderSelected = !props.value && placeholder;

  return (
    <div className={widthStyle}>
      {/* Label */}
      {label && (
        <label 
          className="block text-sm font-medium text-gray-300 mb-1.5" 
          htmlFor={props.id || props.name}
        >
          {label}
          {required && <span className="text-red-500 ml-1" aria-hidden="true">*</span>}
        </label>
      )}

      {/* Select wrapper for custom arrow */}
      <div className="relative">
        {/* Start Icon */}
        {startIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400" aria-hidden="true">
            {startIcon}
          </div>
        )}

        <select
          ref={ref}
          className={`${selectStyles} ${className} ${widthStyle}`}
          disabled={disabled}
          onChange={handleChange}
          required={required}
          aria-invalid={!!error}
          aria-describedby={props.id ? `${props.id}-helper` : undefined}
          {...props}
        >
          {placeholder && (
            <option value="" disabled selected={placeholderSelected}>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option 
              key={option.value} 
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>

        {/* Custom arrow icon */}
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none" aria-hidden="true">
          <svg
            className="h-4 w-4 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {/* Error message or helper text */}
      {(error || helperText) && (
        <p 
          className={`mt-1.5 text-sm ${error ? 'text-red-500' : 'text-gray-400'}`}
          id={props.id ? `${props.id}-helper` : undefined}
        >
          {error || helperText}
        </p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export default Select;