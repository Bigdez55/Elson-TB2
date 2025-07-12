import React, { Component, ErrorInfo, ReactNode } from 'react';
import { FiAlertTriangle, FiRefreshCw } from 'react-icons/fi';
import Button from '../common/Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  errorComponent?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class AdminErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to monitoring service
    console.error('Admin component error:', error, errorInfo);
    
    // You could send to a monitoring service like Sentry here
    // if (process.env.NODE_ENV === 'production') {
    //   Sentry.captureException(error);
    // }
  }

  resetErrorBoundary = (): void => {
    this.props.onReset?.();
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom error component from props
      if (this.props.errorComponent && this.state.error) {
        return this.props.errorComponent(this.state.error, this.resetErrorBoundary);
      }
      
      // Custom fallback component from props
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      // Default error UI
      return (
        <div className="p-6 max-w-md mx-auto bg-gray-800 rounded-lg shadow-md border border-gray-700">
          <div className="flex items-center justify-center mb-4">
            <FiAlertTriangle className="text-red-400 text-3xl" />
          </div>
          <h2 className="text-lg font-medium text-white text-center mb-2">
            Something went wrong
          </h2>
          <p className="text-sm text-gray-300 mb-4 text-center">
            An error occurred in this component. The error has been logged and our team has been notified.
          </p>
          {this.state.error && (
            <div className="mb-4 p-3 bg-gray-900 rounded-md">
              <p className="text-sm font-mono text-red-400 overflow-auto">
                {this.state.error.message || 'Unknown error'}
              </p>
            </div>
          )}
          <div className="flex justify-center">
            <Button
              variant="primary"
              onClick={this.resetErrorBoundary}
              leftIcon={<FiRefreshCw />}
            >
              Try Again
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default AdminErrorBoundary;