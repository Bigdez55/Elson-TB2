import React from 'react';

interface SkeletonProps {
  /**
   * The type of skeleton to render
   */
  type?: 'text' | 'circle' | 'rect' | 'card' | 'list' | 'table' | 'avatar';
  
  /**
   * Width in pixels or CSS value
   */
  width?: string | number;
  
  /**
   * Height in pixels or CSS value
   */
  height?: string | number;
  
  /**
   * Number of items to render for list and table types
   */
  count?: number;
  
  /**
   * Additional CSS classes
   */
  className?: string;
  
  /**
   * Border radius
   */
  borderRadius?: string;
}

/**
 * A skeleton loading component for various UI elements
 */
const Skeleton: React.FC<SkeletonProps> = ({
  type = 'text',
  width,
  height,
  count = 1,
  className = '',
  borderRadius,
}) => {
  const baseClass = "animate-pulse bg-gray-700";
  
  // Convert to CSS values if numbers
  const widthValue = typeof width === 'number' ? `${width}px` : width;
  const heightValue = typeof height === 'number' ? `${height}px` : height;
  
  // Style object
  const style: React.CSSProperties = {
    width: widthValue,
    height: heightValue,
    borderRadius,
  };
  
  // Render basic skeleton shape
  const renderSkeleton = () => {
    switch (type) {
      case 'circle':
        return (
          <div 
            className={`${baseClass} rounded-full ${className}`} 
            style={{ 
              ...style, 
              width: widthValue || '48px', 
              height: heightValue || '48px',
              borderRadius: '50%'
            }}
          />
        );
        
      case 'avatar':
        return (
          <div className="flex items-center space-x-3">
            <div 
              className={`${baseClass} rounded-full`} 
              style={{ width: '48px', height: '48px' }}
            />
            <div className="space-y-2">
              <div className={`${baseClass} h-4 w-32 rounded`} />
              <div className={`${baseClass} h-3 w-24 rounded`} />
            </div>
          </div>
        );
        
      case 'card':
        return (
          <div className={`${baseClass} rounded-lg overflow-hidden ${className}`} style={style}>
            <div className={`${baseClass} h-48 w-full`} />
            <div className="p-4 space-y-3">
              <div className={`${baseClass} h-6 w-3/4 rounded`} />
              <div className={`${baseClass} h-4 w-full rounded`} />
              <div className={`${baseClass} h-4 w-full rounded`} />
              <div className={`${baseClass} h-4 w-2/3 rounded`} />
            </div>
          </div>
        );
        
      case 'list':
        return (
          <div className={`space-y-3 ${className}`} style={style}>
            {Array.from({ length: count }).map((_, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`${baseClass} h-10 w-10 rounded-md`} />
                <div className="space-y-2 flex-1">
                  <div className={`${baseClass} h-4 w-full rounded`} />
                  <div className={`${baseClass} h-3 w-4/5 rounded`} />
                </div>
              </div>
            ))}
          </div>
        );
        
      case 'table':
        return (
          <div className={`space-y-2 ${className}`} style={style}>
            {/* Table header */}
            <div className="flex space-x-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={`header-${index}`} className={`${baseClass} h-8 flex-1 rounded`} />
              ))}
            </div>
            
            {/* Table rows */}
            {Array.from({ length: count }).map((_, rowIndex) => (
              <div key={`row-${rowIndex}`} className="flex space-x-2">
                {Array.from({ length: 4 }).map((_, colIndex) => (
                  <div key={`cell-${rowIndex}-${colIndex}`} className={`${baseClass} h-6 flex-1 rounded`} />
                ))}
              </div>
            ))}
          </div>
        );
        
      case 'rect':
        return (
          <div 
            className={`${baseClass} ${className}`} 
            style={{ 
              ...style, 
              width: widthValue || '100%', 
              height: heightValue || '16px',
              borderRadius: borderRadius || '0.25rem'
            }}
          />
        );
        
      case 'text':
      default:
        return (
          <div className="space-y-2" style={{ width: widthValue || '100%' }}>
            {Array.from({ length: count }).map((_, index) => (
              <div 
                key={index}
                className={`${baseClass} rounded ${className}`} 
                style={{ 
                  height: heightValue || '16px',
                  width: index === count - 1 && count > 1 ? '80%' : '100%'
                }}
              />
            ))}
          </div>
        );
    }
  };
  
  return renderSkeleton();
};

export default Skeleton;