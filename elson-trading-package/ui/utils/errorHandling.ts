import { AxiosError } from 'axios';
import { setError } from '../store/slices/alertsSlice';
import { addNotification } from '../store/slices/notificationsSlice';
import { Dispatch } from 'redux';

// Error severity levels
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

// Error sources
export enum ErrorSource {
  NETWORK = 'network',
  API = 'api',
  CLIENT = 'client',
  UNKNOWN = 'unknown'
}

// Specific error types
export enum ErrorType {
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  VALIDATION = 'validation',
  NOT_FOUND = 'not_found',
  TIMEOUT = 'timeout',
  RATE_LIMIT = 'rate_limit',
  SERVER = 'server',
  UNKNOWN = 'unknown'
}

export interface ErrorDetails {
  message: string;
  severity: ErrorSeverity;
  source: ErrorSource;
  type: ErrorType;
  statusCode?: number;
  field?: string;
  retry?: boolean;
  details?: any;
}

/**
 * Process and handle errors in a consistent way
 * @param error - The error object
 * @param dispatch - Redux dispatch function
 * @param context - Additional context for the error
 * @param showToast - Whether to show toast notification (default: true)
 * @returns Processed error details
 */
export const handleError = (
  error: unknown,
  dispatch: Dispatch,
  context = 'operation',
  showToast = true
): ErrorDetails => {
  // Default error structure
  const errorDetails: ErrorDetails = {
    message: `An unexpected error occurred during ${context}`,
    severity: ErrorSeverity.ERROR,
    source: ErrorSource.UNKNOWN,
    type: ErrorType.UNKNOWN,
    retry: false
  };

  // Process different types of errors
  if (error instanceof Error) {
    errorDetails.message = error.message;
    
    // Handle Axios errors
    if (isAxiosError(error)) {
      errorDetails.source = ErrorSource.API;
      const status = error.response?.status;
      errorDetails.statusCode = status;

      if (status) {
        // Handle different status codes
        if (status === 401) {
          errorDetails.type = ErrorType.AUTHENTICATION;
          errorDetails.message = 'Your session has expired. Please log in again.';
          errorDetails.retry = false;
        } else if (status === 403) {
          errorDetails.type = ErrorType.AUTHORIZATION;
          errorDetails.message = 'You do not have permission to perform this action.';
          errorDetails.retry = false;
        } else if (status === 404) {
          errorDetails.type = ErrorType.NOT_FOUND;
          errorDetails.message = 'The requested resource could not be found.';
          errorDetails.retry = true;
        } else if (status === 422) {
          errorDetails.type = ErrorType.VALIDATION;
          errorDetails.message = error.response?.data?.message || 'Validation failed. Please check your input.';
          errorDetails.details = error.response?.data?.details;
          errorDetails.retry = true;
        } else if (status === 429) {
          errorDetails.type = ErrorType.RATE_LIMIT;
          errorDetails.message = 'Rate limit exceeded. Please try again later.';
          errorDetails.retry = true;
        } else if (status >= 500) {
          errorDetails.type = ErrorType.SERVER;
          errorDetails.message = 'Server error. Please try again later.';
          errorDetails.retry = true;
        }
      } else if (error.message === 'Network Error') {
        errorDetails.source = ErrorSource.NETWORK;
        errorDetails.message = 'Network error. Please check your connection and try again.';
        errorDetails.retry = true;
      } else if (error.code === 'ECONNABORTED') {
        errorDetails.source = ErrorSource.NETWORK;
        errorDetails.type = ErrorType.TIMEOUT;
        errorDetails.message = 'The request timed out. Please try again.';
        errorDetails.retry = true;
      }
    } else {
      errorDetails.source = ErrorSource.CLIENT;
    }
  } else if (typeof error === 'string') {
    errorDetails.message = error;
    errorDetails.source = ErrorSource.CLIENT;
  } else if (error && typeof error === 'object') {
    const errorObj = error as any;
    errorDetails.message = errorObj.message || errorDetails.message;
    errorDetails.details = errorObj;
  }

  // Dispatch error to redux state
  dispatch(setError(errorDetails.message));
  
  // Create toast notification for errors if requested
  if (showToast) {
    dispatch(addNotification({
      type: 'error',
      message: errorDetails.message,
      timestamp: new Date().toISOString(),
      read: false
    }));
  }

  // Log error for debugging
  console.error(`[${errorDetails.source.toUpperCase()}] [${errorDetails.type.toUpperCase()}]:`, errorDetails.message, error);
  
  return errorDetails;
};

/**
 * Type guard for Axios errors
 */
function isAxiosError(error: any): error is AxiosError {
  return error && error.isAxiosError === true;
}

/**
 * Creates a retry function that can be used after an error
 * @param operation - Function to retry
 * @param maxRetries - Maximum number of retry attempts 
 * @param delay - Delay between retries in ms
 * @returns A function that can be called to retry the operation
 */
export const createRetryFunction = (
  operation: () => Promise<any>,
  maxRetries = 3,
  delay = 1000
): (() => Promise<any>) => {
  let attempts = 0;
  
  const retry = async (): Promise<any> => {
    try {
      attempts++;
      return await operation();
    } catch (error) {
      if (attempts < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay));
        return retry();
      }
      throw error;
    }
  };
  
  return retry;
};

/**
 * Higher-order function to add error handling to async functions
 * @param fn - Async function to wrap with error handling
 * @param dispatch - Redux dispatch function
 * @param context - Error context description
 * @param showToast - Whether to show toast notifications
 * @returns Wrapped function with error handling
 */
export const withErrorHandling = <T extends (...args: any[]) => Promise<any>>(
  fn: T,
  dispatch: Dispatch,
  context = 'operation',
  showToast = true
): ((...args: Parameters<T>) => Promise<ReturnType<T> | undefined>) => {
  return async (...args: Parameters<T>): Promise<ReturnType<T> | undefined> => {
    try {
      return await fn(...args);
    } catch (error) {
      handleError(error, dispatch, context, showToast);
      return undefined;
    }
  };
};

/**
 * Creates a standardized error message based on the error type
 */
export const createErrorMessage = (type: ErrorType, context?: string): string => {
  const contextStr = context ? ` while ${context}` : '';
  
  switch (type) {
    case ErrorType.AUTHENTICATION:
      return `Authentication error${contextStr}. Please log in again.`;
    case ErrorType.AUTHORIZATION:
      return `You don't have permission${contextStr}.`;
    case ErrorType.VALIDATION:
      return `Validation error${contextStr}. Please check your input.`;
    case ErrorType.NOT_FOUND:
      return `The requested resource was not found${contextStr}.`;
    case ErrorType.TIMEOUT:
      return `Request timed out${contextStr}. Please try again.`;
    case ErrorType.RATE_LIMIT:
      return `Rate limit exceeded${contextStr}. Please try again later.`;
    case ErrorType.SERVER:
      return `Server error occurred${contextStr}. Please try again later.`;
    case ErrorType.UNKNOWN:
    default:
      return `An unexpected error occurred${contextStr}.`;
  }
};