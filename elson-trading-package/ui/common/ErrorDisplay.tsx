import React from 'react';
import { Button } from './Button';

interface ErrorDisplayProps {
  /**
   * The error message to display
   */
  error: string | null | unknown;
  
  /**
   * Function to retry the failed operation
   */
  onRetry?: () => void;
  
  /**
   * Function to dismiss the error
   */
  onDismiss?: () => void;
  
  /**
   * Show technical details (for development)
   */
  showDetails?: boolean;
  
  /**
   * Title for the error
   */
  title?: string;
  
  /**
   * Additional CSS class for the container
   */
  className?: string;
  
  /**
   * Variant of the error display
   */
  variant?: 'inline' | 'card' | 'toast' | 'full';
}

/**
 * ErrorDisplay component for displaying errors in a user-friendly way
 * This provides consistency for error handling across the application
 */
const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  showDetails = false,
  title = 'An error occurred',
  className = '',
  variant = 'card',
}) => {
  if (!error) return null;
  
  // Format the error message
  const errorMessage = typeof error === 'string' 
    ? error 
    : error instanceof Error 
      ? error.message 
      : 'An unexpected error occurred';
  
  // Get the error details if available
  const errorDetails = error instanceof Error ? error.stack : JSON.stringify(error);

  // Render different variants
  const renderContent = () => {
    switch (variant) {
      case 'inline':
        return (
          <div className={`text-red-500 ${className}`}>
            <p>{errorMessage}</p>
            {onRetry && (
              <Button
                onClick={onRetry}
                variant="text"
                className="text-purple-400 ml-2 text-sm"
              >
                Retry
              </Button>
            )}
          </div>
        );

      case 'toast':
        return (
          <div className={`bg-red-900 bg-opacity-90 text-white p-4 rounded-lg shadow-lg max-w-md ${className}`}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium">{title}</p>
                <p className="mt-1 text-sm text-red-200">{errorMessage}</p>
                {onRetry && (
                  <div className="mt-2">
                    <Button
                      onClick={onRetry}
                      variant="secondary"
                      className="text-xs"
                    >
                      Try Again
                    </Button>
                  </div>
                )}
              </div>
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="ml-4 flex-shrink-0 text-red-300 hover:text-white focus:outline-none"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        );

      case 'full':
        return (
          <div className={`min-h-[40vh] flex flex-col items-center justify-center text-center p-6 ${className}`}>
            <svg className="h-16 w-16 text-red-500 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
            <p className="text-gray-400 mb-6">{errorMessage}</p>
            <div className="flex space-x-4">
              {onRetry && (
                <Button
                  onClick={onRetry}
                  variant="primary"
                >
                  Try Again
                </Button>
              )}
              {onDismiss && (
                <Button
                  onClick={onDismiss}
                  variant="secondary"
                >
                  Dismiss
                </Button>
              )}
            </div>
            
            {showDetails && (
              <details className="mt-8 text-left w-full max-w-2xl">
                <summary className="cursor-pointer text-gray-400 text-sm">Error Details</summary>
                <pre className="mt-2 p-4 bg-gray-900 rounded text-red-400 text-xs overflow-x-auto">
                  {errorDetails}
                </pre>
              </details>
            )}
          </div>
        );

      case 'card':
      default:
        return (
          <div className={`bg-gray-800 border border-red-900 rounded-lg p-4 ${className}`}>
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-500">{title}</h3>
                <div className="mt-2 text-sm text-gray-300">
                  <p>{errorMessage}</p>
                </div>
                <div className="mt-4">
                  <div className="flex space-x-3">
                    {onRetry && (
                      <Button
                        onClick={onRetry}
                        variant="primary"
                        className="text-sm"
                      >
                        Try Again
                      </Button>
                    )}
                    {onDismiss && (
                      <Button
                        onClick={onDismiss}
                        variant="secondary"
                        className="text-sm"
                      >
                        Dismiss
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {showDetails && (
              <details className="mt-3 text-left">
                <summary className="cursor-pointer text-gray-400 text-xs">Error Details</summary>
                <pre className="mt-2 p-2 bg-gray-900 rounded text-red-400 text-xs overflow-x-auto">
                  {errorDetails}
                </pre>
              </details>
            )}
          </div>
        );
    }
  };

  return renderContent();
};

export default ErrorDisplay;