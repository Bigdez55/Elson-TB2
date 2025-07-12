import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import Button from './Button';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOutsideClick?: boolean;
  closeOnEsc?: boolean;
  hideCloseButton?: boolean;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeOnOutsideClick = true,
  closeOnEsc = true,
  hideCloseButton = false,
}) => {
  // Create a ref to the modal content
  const modalRef = useRef<HTMLDivElement>(null);

  // Size variations
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-4xl',
  };

  // Handle clicks outside the modal
  const handleOutsideClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnOutsideClick && modalRef.current && !modalRef.current.contains(e.target as Node)) {
      onClose();
    }
  };

  // Handle ESC key press to close the modal
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (closeOnEsc && isOpen && e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      // Prevent scrolling on the body when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
      // Restore scrolling when modal is closed
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, onClose, closeOnEsc]);

  // If modal is closed, don't render anything
  if (!isOpen) return null;

  // Create a portal to render the modal at the end of the document body
  return createPortal(
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm transition-opacity"
      onClick={handleOutsideClick}
    >
      <div 
        ref={modalRef}
        className={`bg-gray-900 border border-gray-800 rounded-lg shadow-xl w-full ${sizeClasses[size]} overflow-hidden transform transition-all`}
        role="dialog"
        aria-modal="true"
      >
        {/* Modal header */}
        {(title || !hideCloseButton) && (
          <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center">
            {title && (
              typeof title === 'string' ? (
                <h3 className="text-lg font-semibold text-white">{title}</h3>
              ) : (
                title
              )
            )}
            {!hideCloseButton && (
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-gray-600 rounded-full p-1"
                aria-label="Close"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Modal body */}
        <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
          {children}
        </div>

        {/* Modal footer */}
        {footer && (
          <div className="px-6 py-4 border-t border-gray-800 bg-gray-900">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
};

// Helper component for standard modal footer with action buttons
export const ModalFooter: React.FC<{
  cancelText?: string;
  confirmText?: string;
  onCancel?: () => void;
  onConfirm?: () => void;
  isConfirmLoading?: boolean;
  isConfirmDisabled?: boolean;
  confirmVariant?: 'primary' | 'danger';
  extraButtons?: React.ReactNode;
}> = ({
  cancelText = 'Cancel',
  confirmText = 'Confirm',
  onCancel,
  onConfirm,
  isConfirmLoading = false,
  isConfirmDisabled = false,
  confirmVariant = 'primary',
  extraButtons,
}) => {
  return (
    <div className="flex justify-end space-x-3">
      {extraButtons}
      {onCancel && (
        <Button
          variant="secondary"
          onClick={onCancel}
          disabled={isConfirmLoading}
        >
          {cancelText}
        </Button>
      )}
      {onConfirm && (
        <Button
          variant={confirmVariant}
          onClick={onConfirm}
          loading={isConfirmLoading}
          disabled={isConfirmDisabled || isConfirmLoading}
        >
          {confirmText}
        </Button>
      )}
    </div>
  );
};

export default Modal;