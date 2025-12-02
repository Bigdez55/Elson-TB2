import React, { useMemo } from 'react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  fullScreen?: boolean;
}

const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  text = 'Loading...',
  fullScreen = false
}) => {
  // Check if we're on mobile using a custom hook
  const isMobile = useMobile();
  
  // Adjust size for mobile if needed
  const adjustedSize = isMobile && size === 'lg' ? 'md' : size;
  
  // Size variations for the spinner
  const spinnerSizes: Record<string, string> = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  // Text sizes that correspond to spinner sizes
  const textSizes: Record<string, string> = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center" role="status" aria-live="polite">
      <svg
        className={`animate-spin ${spinnerSizes[adjustedSize]} text-purple-500`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {text && (
        <span className={`mt-2 ${textSizes[adjustedSize]} text-gray-400`}>
          {text}
        </span>
      )}
      <span className="sr-only">Loading</span>
    </div>
  );

  if (fullScreen) {
    return (
      <div 
        className="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 z-50 transition-opacity"
        aria-modal="true"
      >
        {spinner}
      </div>
    );
  }

  return spinner;
};

// Custom hook for detecting mobile viewport
function useMobile(): boolean {
  return useMemo(() => {
    if (typeof window !== 'undefined') {
      // Check for mobile viewport width (< 640px for standard tailwind sm breakpoint)
      return window.innerWidth < 640;
    }
    return false;
  }, []);
}

export default Loading;