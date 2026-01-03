import React from 'react';

export type ErrorType = 'network' | 'auth' | 'notFound' | 'server' | 'validation' | 'generic';

interface ErrorDisplayProps {
  type?: ErrorType;
  title?: string;
  message?: string;
  error?: Error | string | null;
  onRetry?: () => void;
  onGoBack?: () => void;
  onGoHome?: () => void;
  compact?: boolean;
  className?: string;
}

const errorConfigs: Record<ErrorType, { icon: React.ReactNode; defaultTitle: string; defaultMessage: string; color: string }> = {
  network: {
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a5 5 0 01-7.07-7.07m7.07 7.07l-2.829-2.829" />
      </svg>
    ),
    defaultTitle: 'Connection Error',
    defaultMessage: 'Unable to connect to the server. Please check your internet connection and try again.',
    color: 'text-yellow-400',
  },
  auth: {
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
    defaultTitle: 'Authentication Required',
    defaultMessage: 'You need to be logged in to access this content. Please sign in and try again.',
    color: 'text-purple-400',
  },
  notFound: {
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    defaultTitle: 'Not Found',
    defaultMessage: "The content you're looking for doesn't exist or has been moved.",
    color: 'text-gray-400',
  },
  server: {
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    defaultTitle: 'Server Error',
    defaultMessage: 'Something went wrong on our end. Our team has been notified and is working on a fix.',
    color: 'text-red-400',
  },
  validation: {
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    defaultTitle: 'Invalid Request',
    defaultMessage: 'The request could not be processed. Please check your input and try again.',
    color: 'text-orange-400',
  },
  generic: {
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    defaultTitle: 'Something Went Wrong',
    defaultMessage: 'An unexpected error occurred. Please try again later.',
    color: 'text-red-400',
  },
};

/**
 * ErrorDisplay Component
 * A consistent error display component for the entire application
 */
export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  type = 'generic',
  title,
  message,
  error,
  onRetry,
  onGoBack,
  onGoHome,
  compact = false,
  className = '',
}) => {
  const config = errorConfigs[type];
  const displayTitle = title || config.defaultTitle;
  const displayMessage = message || (error ? (typeof error === 'string' ? error : error.message) : config.defaultMessage);

  if (compact) {
    return (
      <div className={`bg-red-900/20 border border-red-500/30 rounded-lg p-4 ${className}`}>
        <div className="flex items-start space-x-3">
          <div className={`flex-shrink-0 ${config.color}`}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">{displayTitle}</p>
            <p className="text-sm text-gray-400 mt-1">{displayMessage}</p>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex-shrink-0 text-sm text-purple-400 hover:text-purple-300 transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}>
      <div className={`${config.color} mb-4`}>{config.icon}</div>
      <h2 className="text-xl font-semibold text-white mb-2 text-center">{displayTitle}</h2>
      <p className="text-gray-400 text-center max-w-md mb-6">{displayMessage}</p>

      <div className="flex flex-wrap justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Try Again</span>
          </button>
        )}
        {onGoBack && (
          <button
            onClick={onGoBack}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Go Back</span>
          </button>
        )}
        {onGoHome && (
          <button
            onClick={onGoHome}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <span>Go Home</span>
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Inline Error Message
 * For form validation and inline errors
 */
export const InlineError: React.FC<{ message: string; className?: string }> = ({ message, className = '' }) => (
  <div className={`flex items-center space-x-1 text-red-400 text-sm mt-1 ${className}`}>
    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span>{message}</span>
  </div>
);

/**
 * Error Boundary Fallback Component
 * Use with React Error Boundaries
 */
export const ErrorBoundaryFallback: React.FC<{
  error: Error;
  resetErrorBoundary?: () => void;
}> = ({ error, resetErrorBoundary }) => (
  <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
    <ErrorDisplay
      type="generic"
      title="Application Error"
      message="An unexpected error occurred in the application."
      error={error}
      onRetry={resetErrorBoundary}
      onGoHome={() => window.location.href = '/'}
    />
  </div>
);

/**
 * Empty State Component
 * For when there's no data to display
 */
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  message,
  action,
  className = '',
}) => (
  <div className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}>
    {icon ? (
      <div className="text-gray-500 mb-4">{icon}</div>
    ) : (
      <div className="text-gray-500 mb-4">
        <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
      </div>
    )}
    <h3 className="text-lg font-medium text-white mb-2 text-center">{title}</h3>
    <p className="text-gray-400 text-center max-w-sm mb-6">{message}</p>
    {action && (
      <button
        onClick={action.onClick}
        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
      >
        {action.label}
      </button>
    )}
  </div>
);

export default ErrorDisplay;
