import React, { createContext, useContext, useState, useCallback } from 'react';
import ToastContainer, { ToastOptions } from './ToastContainer';

interface ToastContextType {
  showToast: (options: ToastOptions) => string;
  hideToast: (id: string) => void;
  clearAllToasts: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToastContext = () => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
};

interface ToastProviderProps {
  children: React.ReactNode;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

let toastCounter = 0;

export const ToastProvider: React.FC<ToastProviderProps> = ({ 
  children, 
  position = 'top-right' 
}) => {
  const [toasts, setToasts] = useState<(ToastOptions & { id: string })[]>([]);

  const showToast = useCallback((options: ToastOptions) => {
    const id = `toast-${toastCounter++}`;
    const newToast = {
      id,
      ...options
    };
    
    setToasts(prevToasts => [...prevToasts, newToast]);
    return id;
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const value = {
    showToast,
    hideToast,
    clearAllToasts
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer 
        position={position}
        toasts={toasts}
        removeToast={hideToast}
      />
    </ToastContext.Provider>
  );
};

export default ToastProvider;