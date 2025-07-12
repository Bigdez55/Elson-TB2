import React, { ReactNode } from 'react';

interface ResponsiveContainerProps {
  /**
   * The content to display
   */
  children: ReactNode;
  
  /**
   * Breakpoint at which the container changes from mobile to desktop layout
   */
  breakpoint?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  
  /**
   * Container classes to apply for mobile view
   */
  mobileClasses?: string;
  
  /**
   * Container classes to apply for desktop view
   */
  desktopClasses?: string;
  
  /**
   * Additional classes to apply to the container at all breakpoints
   */
  className?: string;
  
  /**
   * HTML element type to render (default: 'div')
   */
  as?: 'div' | 'section' | 'article' | 'main' | 'aside' | 'nav';
  
  /**
   * Support for RTL (right-to-left) text direction
   */
  rtl?: boolean;
}

/**
 * A utility component for creating responsive layouts that adapt to different screen sizes
 */
const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  breakpoint = 'md',
  mobileClasses = 'flex flex-col',
  desktopClasses = 'flex flex-row',
  className = '',
  as: Component = 'div',
  rtl = false,
}) => {
  // Tailwind classes for responsive container
  const breakpointMap: Record<string, string> = {
    'sm': 'sm:',
    'md': 'md:',
    'lg': 'lg:',
    'xl': 'xl:',
    '2xl': '2xl:',
  };
  
  const prefix = breakpointMap[breakpoint];
  
  // Add prefix to each desktop class individually
  const responsiveDesktopClasses = desktopClasses
    .split(' ')
    .map(cls => cls ? `${prefix}${cls}` : '') // Skip empty strings
    .join(' ');
  
  // Build the responsive container class
  const containerClass = `${mobileClasses} ${responsiveDesktopClasses} ${className} ${rtl ? 'direction-rtl' : ''}`.trim();
  
  return (
    <Component 
      className={containerClass}
      dir={rtl ? 'rtl' : undefined}
      data-testid="responsive-container"
    >
      {children}
    </Component>
  );
};

export default ResponsiveContainer;