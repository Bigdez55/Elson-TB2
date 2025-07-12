import { Component, ErrorInfo, ReactNode } from 'react';
import Button from './Button';
import config from '../../core/config';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error: error,
      errorInfo: null
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // You can also log the error to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    this.setState({
      errorInfo: errorInfo
    });
    
    // Here you could send the error to an analytics service
    // Example: logErrorToService(error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-5 text-center">
          <div className="max-w-md">
            <div className="text-red-500 mb-4">
              <svg 
                className="h-16 w-16 mx-auto" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-white mb-4">Something went wrong</h1>
            <p className="text-gray-300 mb-6">
              We&apos;ve encountered an unexpected error. Please try refreshing the page or contact support if the problem persists.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                onClick={() => window.location.reload()} 
                variant="primary"
              >
                Refresh Page
              </Button>
              <Button 
                onClick={this.handleReset} 
                variant="secondary"
              >
                Try Again
              </Button>
            </div>

            {/* Error details (collapsed by default - can be expanded for debugging) */}
            {config.isDev && (
              <div className="mt-8 text-left">
                <details className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <summary className="cursor-pointer text-gray-300 font-medium">
                    Error Details (Developer Mode)
                  </summary>
                  <div className="mt-4">
                    <p className="text-red-400 text-sm mb-2">{this.state.error?.toString()}</p>
                    <pre className="text-gray-400 text-xs overflow-auto p-2 bg-gray-900 rounded">
                      {this.state.errorInfo?.componentStack}
                    </pre>
                  </div>
                </details>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;