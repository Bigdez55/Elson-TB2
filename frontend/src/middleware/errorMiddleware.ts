import { Middleware, isRejectedWithValue } from '@reduxjs/toolkit';

/**
 * Redux middleware for handling async action errors
 * Logs rejected actions and can trigger global error handling
 */
export const errorMiddleware: Middleware = () => (next) => (action) => {
  // Check if action is a rejected async thunk
  if (isRejectedWithValue(action)) {
    // Log the error for debugging
    console.error('Async action rejected:', {
      type: action.type,
      payload: action.payload,
      error: action.error,
    });

    // Could dispatch to a global error slice or show toast notification here
    // For now, just log and pass through
  }

  return next(action);
};

export default errorMiddleware;
