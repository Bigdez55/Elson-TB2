import React from 'react';
import LoadingSpinner from './LoadingSpinner';

interface LoadingStateProps {
  /**
   * The loading state
   */
  isLoading: boolean;
  
  /**
   * The error message, if any
   */
  error?: string | null;
  
  /**
   * Content to display when loading
   */
  children: React.ReactNode;
  
  /**
   * Custom loading component
   */
  loadingComponent?: React.ReactNode;
  
  /**
   * Custom error component
   */
  errorComponent?: React.ReactNode;
  
  /**
   * Show skeleton while loading
   */
  skeleton?: React.ReactNode;
  
  /**
   * Retry function for error states
   */
  onRetry?: () => void;
  
  /**
   * Additional CSS class for the container
   */
  className?: string;
  
  /**
   * If true, loading and error states won't cover the whole content area
   */
  inline?: boolean;
}

/**
 * A standardized component for handling loading and error states
 * This provides a consistent UX across the application
 */
const LoadingState: React.FC<LoadingStateProps> = ({
  isLoading,
  error,
  children,
  loadingComponent,
  errorComponent,
  skeleton,
  onRetry,
  className = '',
  inline = false,
}) => {
  // If we're loading and have a skeleton, show that instead of the spinner
  if (isLoading && skeleton) {
    return <div className={className}>{skeleton}</div>;
  }
  
  // If loading and no skeleton, show loading spinner or custom loading component
  if (isLoading) {
    if (loadingComponent) {
      return <div className={className}>{loadingComponent}</div>;
    }
    
    return (
      <div className={`${className} ${inline ? '' : 'min-h-[200px] flex items-center justify-center'}`}>
        <LoadingSpinner size="large" color="text-purple-600" text="Loading..." />
      </div>
    );
  }
  
  // If there's an error, show error state
  if (error) {
    if (errorComponent) {
      return <div className={className}>{errorComponent}</div>;
    }
    
    return (
      <div className={`${className} ${inline ? '' : 'min-h-[200px]'} bg-gray-800 p-6 rounded-lg`}>
        <div className="text-red-500 flex flex-col items-center justify-center text-center">
          <svg 
            className="h-12 w-12 mb-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
          <h3 className="text-xl font-bold mb-2">Error loading data</h3>
          <p className="text-gray-400 mb-4">{error}</p>
          {onRetry && (
            <button 
              onClick={onRetry}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }
  
  // No loading or error, show children
  return <>{children}</>;
};

export default LoadingState;