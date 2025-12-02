import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import Toast from './Toast';

export interface ToastOptions {
  type: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  toasts: (ToastOptions & { id: string })[];
  removeToast: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ 
  position = 'top-right',
  toasts,
  removeToast
}) => {
  const [domReady, setDomReady] = useState(false);

  // Position styles map
  const positionStyles = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
    'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2'
  };

  // Wait for client-side render to access document
  useEffect(() => {
    setDomReady(true);
  }, []);

  if (!domReady) {
    return null;
  }

  // Create a portal for our toasts
  return ReactDOM.createPortal(
    <div className={`fixed ${positionStyles[position]} z-50 flex flex-col items-end space-y-2`}>
      {toasts.map(toast => (
        <Toast 
          key={toast.id} 
          id={toast.id}
          type={toast.type}
          title={toast.title}
          message={toast.message}
          duration={toast.duration} 
          onClose={removeToast} 
        />
      ))}
    </div>,
    document.body
  );
};

export default ToastContainer;