import React from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  rows?: number;
  maxLength?: number;
  showCharCount?: boolean;
}

const TextArea = React.forwardRef<HTMLTextAreaElement, TextAreaProps>(({
  label,
  error,
  helperText,
  className = '',
  fullWidth = true,
  disabled,
  required,
  rows = 4,
  maxLength,
  showCharCount = false,
  value = '',
  ...props
}, ref) => {
  // Define base textarea styles
  const baseTextAreaStyles = 
    'block rounded-lg border bg-gray-800 text-white transition-colors resize-y ' +
    'focus:ring-2 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';

  // Adjust styles based on error state
  const textAreaStyles = `
    ${baseTextAreaStyles}
    ${error 
      ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
      : 'border-gray-700 focus:border-purple-500 focus:ring-purple-500'}
    px-4 py-3
  `;

  const widthStyle = fullWidth ? 'w-full' : '';
  const currentLength = value.toString().length;

  return (
    <div className={widthStyle}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Textarea element */}
      <textarea
        ref={ref}
        className={`${textAreaStyles} ${className} ${widthStyle}`}
        disabled={disabled}
        aria-invalid={error ? 'true' : 'false'}
        rows={rows}
        maxLength={maxLength}
        {...props}
        value={value}
      />

      {/* Character count */}
      {showCharCount && maxLength && (
        <div className="mt-1 text-right text-sm text-gray-400">
          {currentLength}/{maxLength}
        </div>
      )}

      {/* Error message or helper text */}
      {(error || helperText) && (
        <p className={`mt-1.5 text-sm ${error ? 'text-red-500' : 'text-gray-400'}`}>
          {error || helperText}
        </p>
      )}
    </div>
  );
});

TextArea.displayName = 'TextArea';

export default TextArea;