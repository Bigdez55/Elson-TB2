import React, { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useAccessibility } from '../../hooks/useAccessibility';
import FocusLock from 'react-focus-lock';

interface AccessibleModalProps {
  /**
   * Whether the modal is currently open
   */
  isOpen: boolean;
  
  /**
   * Function to call when the modal should be closed
   */
  onClose: () => void;
  
  /**
   * The title of the modal, required for accessibility
   */
  title: string;
  
  /**
   * Optional description for additional context (for screen readers)
   */
  description?: string;
  
  /**
   * The modal content
   */
  children: React.ReactNode;
  
  /**
   * Additional classes for the modal content wrapper
   */
  className?: string;
  
  /**
   * If true, clicking the modal backdrop will not close the modal
   */
  preventBackdropClose?: boolean;
  
  /**
   * If true, pressing Escape will not close the modal
   */
  preventEscapeClose?: boolean;
  
  /**
   * Max width of the modal content (with responsive variants)
   */
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full';
  
  /**
   * Custom styles for the modal content wrapper
   */
  contentStyle?: React.CSSProperties;
}

export const AccessibleModal: React.FC<AccessibleModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  className = '',
  preventBackdropClose = false,
  preventEscapeClose = false,
  maxWidth = 'lg',
  contentStyle,
}) => {
  const [isMounted, setIsMounted] = useState(false);
  const { prefersReducedMotion } = useAccessibility();
  const previousFocusRef = useRef<HTMLElement | null>(null);
  
  // Store previously focused element when modal opens
  useEffect(() => {
    if (isOpen && !isMounted) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      setIsMounted(true);
    } else if (!isOpen && isMounted) {
      // Return focus when modal closes
      if (previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
      setIsMounted(false);
    }
  }, [isOpen, isMounted]);
  
  // Handle Escape key
  useEffect(() => {
    if (!isOpen || preventEscapeClose) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, preventEscapeClose]);
  
  // Handle scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      document.body.style.paddingRight = 'var(--scrollbar-width, 0px)';
    } else {
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    }
    
    return () => {
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    };
  }, [isOpen]);
  
  // Size classes
  const maxWidthClasses = {
    xs: 'max-w-xs',
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
    '5xl': 'max-w-5xl',
    full: 'max-w-full',
  };
  
  if (!isOpen && !isMounted) return null;
  
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Only close if clicking directly on the backdrop, not its children
    if (e.target === e.currentTarget && !preventBackdropClose) {
      onClose();
    }
  };
  
  // Create portal to render modal at the document root
  return createPortal(
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center overflow-y-auto overflow-x-hidden bg-black/50 backdrop-blur-sm transition-opacity ${
        isOpen ? 'opacity-100' : 'opacity-0'
      } ${prefersReducedMotion ? 'duration-[0.01ms]' : 'duration-200'}`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby={description ? 'modal-description' : undefined}
      onClick={handleBackdropClick}
    >
      <FocusLock returnFocus={true}>
        <div
          className={`relative m-4 w-full ${maxWidthClasses[maxWidth]} transform rounded-lg bg-white dark:bg-gray-800 shadow-xl transition-all ${
            isOpen ? 'translate-y-0 scale-100' : 'translate-y-4 scale-95'
          } ${prefersReducedMotion ? 'duration-[0.01ms]' : 'duration-200'} ${className}`}
          style={contentStyle}
        >
          {/* Header */}
          <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
            <h2 id="modal-title" className="text-lg font-semibold text-gray-900 dark:text-white">
              {title}
            </h2>
            {description && (
              <p id="modal-description" className="sr-only">
                {description}
              </p>
            )}
            <button
              type="button"
              className="absolute right-4 top-4 rounded-md p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
              onClick={onClose}
              aria-label="Close modal"
            >
              <svg
                className="h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Content */}
          <div className="p-6">{children}</div>
        </div>
      </FocusLock>
    </div>,
    document.body
  );
};

export default AccessibleModal;