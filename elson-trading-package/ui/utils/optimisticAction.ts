import { useState } from 'react';
import { Dispatch } from 'redux';
import { handleError } from './errorHandling';

export interface OptimisticActionOptions<T, R> {
  // The initial state
  initialState: T;
  
  // The optimistic update function to apply immediately
  optimisticUpdate: (currentState: T) => T;
  
  // The actual API call to perform
  apiCall: () => Promise<R>;
  
  // Function to update the state based on API response
  onSuccess?: (response: R, currentState: T) => T;
  
  // Function to handle failure (rollback and error handling)
  onError?: (error: any, currentState: T) => T;
  
  // Redux dispatch for error handling
  dispatch?: Dispatch;
  
  // Context description for error messages
  context?: string;
}

/**
 * Hook to handle optimistic updates with API calls, rollbacks, and error handling
 */
export function useOptimisticAction<T, R = any>(options: OptimisticActionOptions<T, R>) {
  const [state, setState] = useState<T>(options.initialState);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<any>(null);
  
  const executeAction = async () => {
    // Clear previous errors
    setError(null);
    setIsLoading(true);
    
    // Store the previous state for rollback
    const previousState = state;
    
    try {
      // Apply optimistic update
      const optimisticState = options.optimisticUpdate(previousState);
      setState(optimisticState);
      
      // Execute the actual API call
      const response = await options.apiCall();
      
      // Apply success updates if provided
      if (options.onSuccess) {
        const finalState = options.onSuccess(response, optimisticState);
        setState(finalState);
      }
      
      setIsLoading(false);
      return response;
    } catch (error) {
      // Handle error with dispatch if provided
      if (options.dispatch) {
        handleError(error, options.dispatch, options.context || 'optimistic action');
      }
      
      // Store the error
      setError(error);
      
      // Apply error updates/rollback if provided
      if (options.onError) {
        const errorState = options.onError(error, state);
        setState(errorState);
      } else {
        // Default rollback to previous state
        setState(previousState);
      }
      
      setIsLoading(false);
      throw error;
    }
  };
  
  return {
    state,
    setState,
    isLoading,
    error,
    executeAction,
    reset: () => setState(options.initialState)
  };
}

/**
 * Function to perform an optimistic update with API call
 */
export async function performOptimisticAction<T, R = any>(
  options: OptimisticActionOptions<T, R>,
  stateSetter: (state: T) => void
): Promise<R | undefined> {
  // Store the previous state for rollback
  const previousState = options.initialState;
  
  try {
    // Apply optimistic update
    const optimisticState = options.optimisticUpdate(previousState);
    stateSetter(optimisticState);
    
    // Execute the actual API call
    const response = await options.apiCall();
    
    // Apply success updates if provided
    if (options.onSuccess) {
      const finalState = options.onSuccess(response, optimisticState);
      stateSetter(finalState);
    }
    
    return response;
  } catch (error) {
    // Handle error with dispatch if provided
    if (options.dispatch) {
      handleError(error, options.dispatch, options.context || 'optimistic action');
    }
    
    // Apply error updates/rollback if provided
    if (options.onError) {
      const errorState = options.onError(error, options.initialState);
      stateSetter(errorState);
    } else {
      // Default rollback to previous state
      stateSetter(previousState);
    }
    
    return undefined;
  }
}