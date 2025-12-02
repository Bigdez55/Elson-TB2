import React, { useRef, useState, useEffect } from 'react';

/**
 * Skip navigation link - allows keyboard users to skip navigation
 * and directly access the main content of the page
 */
interface SkipNavLinkProps {
  /**
   * The text to show when the skip link is focused
   */
  label?: string;
  
  /**
   * The ID of the element to skip to (without the #)
   */
  skipTo?: string;
  
  /**
   * Additional CSS classes
   */
  className?: string;
  
  /**
   * Optional children to override the label
   */
  children?: React.ReactNode;
}

export const SkipNavLink: React.FC<SkipNavLinkProps> = ({
  label = 'Skip to content',
  skipTo = 'main-content',
  className = '',
  children,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  
  const handleFocus = () => setIsFocused(true);
  const handleBlur = () => setIsFocused(false);
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const target = document.getElementById(skipTo);
    if (target) {
      target.tabIndex = -1;
      target.focus();
      // Reset tabIndex after transition
      setTimeout(() => {
        target.removeAttribute('tabindex');
      }, 500);
    }
  };
  
  return (
    <a
      href={`#${skipTo}`}
      className={`
        skip-nav fixed top-4 left-4 z-50 transform transition-transform duration-200
        bg-purple-600 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2
        focus:ring-purple-400 focus:ring-offset-2 focus:ring-offset-gray-900
        ${isFocused ? 'translate-y-0 opacity-100' : '-translate-y-16 opacity-0'}
        ${className}
      `}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onClick={handleClick}
    >
      {children || label}
    </a>
  );
};

/**
 * Skip navigation target - creates an invisible target that the
 * skip navigation link jumps to
 */
interface SkipNavContentProps {
  /**
   * The ID to jump to (should match the skipTo prop on SkipNavLink)
   */
  id?: string;
}

export const SkipNavContent: React.FC<SkipNavContentProps> = ({
  id = 'main-content',
}) => {
  return (
    <div 
      id={id} 
      tabIndex={-1} 
      style={{ outline: 'none' }}
      className="focus:outline-none"
      data-testid={id}
    />
  );
};

/**
 * Combined component for easy import
 */
interface SkipNavProps extends SkipNavLinkProps {
  contentId?: string;
}

export const SkipNav: React.FC<SkipNavProps> = ({
  label = 'Skip to content',
  skipTo = 'main-content',
  className = '',
  contentId,
  children,
}) => {
  return (
    <>
      <SkipNavLink 
        label={label} 
        skipTo={skipTo || contentId || 'main-content'} 
        className={className}
      >
        {children}
      </SkipNavLink>
      <SkipNavContent id={contentId || skipTo || 'main-content'} />
    </>
  );
};