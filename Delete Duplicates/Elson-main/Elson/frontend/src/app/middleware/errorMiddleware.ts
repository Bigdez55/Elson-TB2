import { Middleware, isRejectedWithValue } from '@reduxjs/toolkit';
import { logout } from '../store/slices/userSlice';

/**
 * Middleware for handling errors from rejected Redux API calls
 * This provides consistent error handling across the application
 */
export const errorMiddleware: Middleware = ({ dispatch }) => (next) => (action) => {
  // Check if the action is a rejected action from an API call
  if (isRejectedWithValue(action)) {
    const { payload, error } = action;
    
    // Extract the error message
    const errorMessage = payload || error?.message || 'An unknown error occurred';
    
    // Log the error
    console.error('API Error:', errorMessage, action);
    
    // Handle authentication errors (401 Unauthorized)
    if (
      action.meta?.baseQueryMeta?.response?.status === 401 ||
      (typeof payload === 'string' && 
        (payload.includes('Unauthorized') || 
         payload.includes('token') || 
         payload.includes('auth')))
    ) {
      console.warn('Authentication error detected, logging out user.');
      dispatch(logout());
      
      // Could also redirect to login page or show a specific message
      // dispatch(showNotification({ type: 'error', message: 'Your session has expired. Please log in again.' }));
    }
    
    // Handle server errors (500)
    if (action.meta?.baseQueryMeta?.response?.status >= 500) {
      // Could show a server error notification
      // dispatch(showNotification({ type: 'error', message: 'Server error. Please try again later.' }));
    }
    
    // Handle rate limiting (429)
    if (action.meta?.baseQueryMeta?.response?.status === 429) {
      // Could show a rate limit notification
      // dispatch(showNotification({ type: 'warning', message: 'Rate limit exceeded. Please try again later.' }));
    }
    
    // Add analytics or error reporting here if needed
    // reportErrorToAnalytics(errorMessage, action);
  }
  
  return next(action);
};

/**
 * Function to create a consistent error message from various error formats
 */
export const formatErrorMessage = (error: unknown): string => {
  if (!error) {
    return 'An unknown error occurred';
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'object') {
    // Check for API error response formats
    const errorObj = error as any;
    
    if (errorObj.message) {
      return errorObj.message;
    }
    
    if (errorObj.error) {
      return typeof errorObj.error === 'string' ? errorObj.error : 'API Error';
    }
    
    if (errorObj.data?.message) {
      return errorObj.data.message;
    }
    
    if (errorObj.status && errorObj.statusText) {
      return `${errorObj.status}: ${errorObj.statusText}`;
    }
  }
  
  return 'An unknown error occurred';
};

/**
 * Create a retry function with exponential backoff
 */
export const createRetryHandler = (
  fn: (...args: any[]) => Promise<any>,
  maxRetries = 3,
  baseDelay = 500
) => {
  return async (...args: any[]) => {
    let lastError;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await fn(...args);
      } catch (error) {
        lastError = error;
        
        // If this is not the last attempt, wait before retrying
        if (attempt < maxRetries - 1) {
          // Exponential backoff with jitter
          const delay = baseDelay * Math.pow(2, attempt) * (0.5 + Math.random() * 0.5);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    // If we've exhausted all retries, throw the last error
    throw lastError;
  };
};