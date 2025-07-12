import React, { lazy, Suspense, ComponentType } from 'react';
import { LoadingSpinner } from './LoadingSpinner';

interface LazyLoadProps {
  /**
   * The loading component to display while the lazy component is loading
   */
  fallback?: React.ReactNode;
  
  /**
   * Custom error component to display when loading fails
   */
  errorComponent?: React.ReactNode;
  
  /**
   * Additional props to pass to the component
   */
  [key: string]: any;
}

/**
 * Creates a lazily loaded component with standardized loading state
 * 
 * @param importFunc - A function that returns a dynamic import promise
 * @returns A React component that will be lazily loaded
 */
export function createLazyComponent<P = {}>(
  importFunc: () => Promise<{ default: ComponentType<P> }>,
  displayName?: string
) {
  const LazyComponent = lazy(importFunc);
  
  const LazyLoadComponent: React.FC<P & LazyLoadProps> = ({ 
    fallback = <div className="p-4 flex justify-center">
      <LoadingSpinner size="large" color="text-purple-600" />
    </div>,
    errorComponent = <div className="p-4 text-red-500 text-center">
      Failed to load component
    </div>,
    ...props 
  }) => {
    return (
      <Suspense fallback={fallback}>
        <ErrorBoundary fallback={errorComponent}>
          <LazyComponent {...props as P} />
        </ErrorBoundary>
      </Suspense>
    );
  };
  
  if (displayName) {
    LazyLoadComponent.displayName = `LazyLoad(${displayName})`;
  }
  
  return LazyLoadComponent;
}

interface ErrorBoundaryProps {
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Error boundary component to catch errors in lazy loaded components
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('LazyLoad component error:', error, errorInfo);
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return this.props.fallback || <div>Something went wrong.</div>;
    }
    
    return this.props.children;
  }
}

export default createLazyComponent;