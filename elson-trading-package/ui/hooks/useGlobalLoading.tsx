import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import LoadingSpinner from '../components/common/LoadingSpinner';

interface GlobalLoadingContextType {
  /**
   * Start a global loading operation with an optional ID
   */
  startLoading: (id?: string) => void;
  
  /**
   * End a specific loading operation by ID or the most recent if no ID is provided
   */
  endLoading: (id?: string) => void;
  
  /**
   * Check if a specific loading operation is in progress
   */
  isLoading: (id?: string) => boolean;
  
  /**
   * Current active loading operations
   */
  activeLoadingOperations: string[];
}

// Create context
const GlobalLoadingContext = createContext<GlobalLoadingContextType | undefined>(undefined);

// Provider component
export const GlobalLoadingProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [loadingOperations, setLoadingOperations] = useState<string[]>([]);

  // Generate a unique ID for the loading operation if not provided
  const startLoading = useCallback((id?: string) => {
    const operationId = id || `loading-${Date.now()}`;
    setLoadingOperations(prev => [...prev, operationId]);
    return operationId;
  }, []);

  // End a loading operation by ID
  const endLoading = useCallback((id?: string) => {
    if (id) {
      setLoadingOperations(prev => prev.filter(opId => opId !== id));
    } else if (loadingOperations.length > 0) {
      // If no ID is provided, remove the most recent loading operation
      setLoadingOperations(prev => prev.slice(0, -1));
    }
  }, [loadingOperations]);

  // Check if a specific ID is loading or if any loading is happening
  const isLoading = useCallback((id?: string) => {
    if (id) {
      return loadingOperations.includes(id);
    }
    return loadingOperations.length > 0;
  }, [loadingOperations]);

  const value = {
    startLoading,
    endLoading,
    isLoading,
    activeLoadingOperations: loadingOperations,
  };

  return (
    <GlobalLoadingContext.Provider value={value}>
      {children}
      {loadingOperations.length > 0 && (
        <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50">
          <LoadingSpinner size="large" color="text-purple-600" text="Loading..." />
        </div>
      )}
    </GlobalLoadingContext.Provider>
  );
};

// Hook for using the global loading context
export const useGlobalLoading = (): GlobalLoadingContextType => {
  const context = useContext(GlobalLoadingContext);
  if (context === undefined) {
    throw new Error('useGlobalLoading must be used within a GlobalLoadingProvider');
  }
  return context;
};

// Higher-order component for easily adding loading state to async functions
export const withLoadingState = <P extends object>(
  Component: React.ComponentType<P>,
  loadingId?: string
): React.FC<P> => {
  return (props: P) => {
    const { startLoading, endLoading } = useGlobalLoading();
    
    // Wrap the component's methods with loading state
    const enhancedProps = Object.keys(props).reduce((acc, key) => {
      const prop = props[key as keyof P];
      
      // If the prop is a function, wrap it with loading state
      if (typeof prop === 'function') {
        acc[key as keyof P] = (async (...args: any[]) => {
          const opId = startLoading(loadingId);
          try {
            // @ts-ignore
            return await prop(...args);
          } finally {
            endLoading(opId);
          }
        }) as any;
      } else {
        acc[key as keyof P] = prop;
      }
      
      return acc;
    }, {} as P);
    
    return <Component {...enhancedProps} />;
  };
};