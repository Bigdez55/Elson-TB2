import React, { useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store/store';
import { removeToast, Toast, ToastType } from '../../store/slices/toastSlice';

// Icon components for each toast type
const SuccessIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path
      fillRule="evenodd"
      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
      clipRule="evenodd"
    />
  </svg>
);

const ErrorIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path
      fillRule="evenodd"
      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
      clipRule="evenodd"
    />
  </svg>
);

const WarningIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path
      fillRule="evenodd"
      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
      clipRule="evenodd"
    />
  </svg>
);

const InfoIcon = () => (
  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
    <path
      fillRule="evenodd"
      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
      clipRule="evenodd"
    />
  </svg>
);

const CloseIcon = () => (
  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
    <path
      fillRule="evenodd"
      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
      clipRule="evenodd"
    />
  </svg>
);

// Toast styling configurations
const toastStyles: Record<ToastType, { bg: string; icon: string; border: string }> = {
  success: {
    bg: 'bg-green-900/90',
    icon: 'text-green-400',
    border: 'border-green-500',
  },
  error: {
    bg: 'bg-red-900/90',
    icon: 'text-red-400',
    border: 'border-red-500',
  },
  warning: {
    bg: 'bg-yellow-900/90',
    icon: 'text-yellow-400',
    border: 'border-yellow-500',
  },
  info: {
    bg: 'bg-blue-900/90',
    icon: 'text-blue-400',
    border: 'border-blue-500',
  },
};

const iconComponents: Record<ToastType, React.FC> = {
  success: SuccessIcon,
  error: ErrorIcon,
  warning: WarningIcon,
  info: InfoIcon,
};

// Position styling
const positionStyles: Record<string, string> = {
  'top-right': 'top-4 right-4',
  'top-left': 'top-4 left-4',
  'bottom-right': 'bottom-4 right-4',
  'bottom-left': 'bottom-4 left-4',
  'top-center': 'top-4 left-1/2 -translate-x-1/2',
  'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
};

interface ToastItemProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onDismiss }) => {
  const styles = toastStyles[toast.type];
  const Icon = iconComponents[toast.type];

  useEffect(() => {
    if (toast.duration && toast.duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(toast.id);
      }, toast.duration);

      return () => clearTimeout(timer);
    }
  }, [toast.id, toast.duration, onDismiss]);

  return (
    <div
      className={`
        ${styles.bg} ${styles.border}
        border-l-4 rounded-lg shadow-lg p-4 mb-3
        min-w-[300px] max-w-[400px]
        transform transition-all duration-300 ease-in-out
        animate-slide-in
      `}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start">
        <div className={`flex-shrink-0 ${styles.icon}`}>
          <Icon />
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-white">{toast.title}</p>
          {toast.message && (
            <p className="mt-1 text-sm text-gray-300">{toast.message}</p>
          )}
          {toast.action && (
            <button
              onClick={toast.action.onClick}
              className="mt-2 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
            >
              {toast.action.label}
            </button>
          )}
        </div>
        <button
          onClick={() => onDismiss(toast.id)}
          className="ml-4 flex-shrink-0 text-gray-400 hover:text-white transition-colors"
          aria-label="Dismiss notification"
        >
          <CloseIcon />
        </button>
      </div>

      {/* Progress bar for auto-dismiss */}
      {toast.duration && toast.duration > 0 && (
        <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full ${styles.icon.replace('text-', 'bg-')} animate-progress`}
            style={{
              animationDuration: `${toast.duration}ms`,
            }}
          />
        </div>
      )}
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const dispatch = useDispatch();
  const { toasts, position } = useSelector((state: RootState) => state.toast);

  const handleDismiss = useCallback(
    (id: string) => {
      dispatch(removeToast(id));
    },
    [dispatch]
  );

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div
      className={`fixed ${positionStyles[position]} z-50 pointer-events-none`}
      aria-label="Notifications"
    >
      <div className="pointer-events-auto">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={handleDismiss} />
        ))}
      </div>
    </div>
  );
};

// Custom hook for easy toast dispatching
export const useToast = () => {
  const dispatch = useDispatch();

  const success = useCallback(
    (title: string, message?: string) => {
      dispatch({
        type: 'toast/addToast',
        payload: { type: 'success', title, message },
      });
    },
    [dispatch]
  );

  const error = useCallback(
    (title: string, message?: string) => {
      dispatch({
        type: 'toast/addToast',
        payload: { type: 'error', title, message, duration: 8000 },
      });
    },
    [dispatch]
  );

  const warning = useCallback(
    (title: string, message?: string) => {
      dispatch({
        type: 'toast/addToast',
        payload: { type: 'warning', title, message },
      });
    },
    [dispatch]
  );

  const info = useCallback(
    (title: string, message?: string) => {
      dispatch({
        type: 'toast/addToast',
        payload: { type: 'info', title, message },
      });
    },
    [dispatch]
  );

  const dismiss = useCallback(
    (id: string) => {
      dispatch(removeToast(id));
    },
    [dispatch]
  );

  const dismissAll = useCallback(() => {
    dispatch({ type: 'toast/clearAllToasts' });
  }, [dispatch]);

  return {
    success,
    error,
    warning,
    info,
    dismiss,
    dismissAll,
  };
};

export default ToastContainer;
