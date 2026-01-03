import React from 'react';

interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'card';
  width?: string | number;
  height?: string | number;
  className?: string;
  animation?: 'pulse' | 'wave' | 'none';
  lines?: number;
  darkMode?: boolean;
}

/**
 * Skeleton loading component for displaying placeholder content while data loads.
 * Supports various shapes and animations for different use cases.
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'rectangular',
  width,
  height,
  className = '',
  animation = 'pulse',
  lines = 1,
  darkMode = true,
}) => {
  const baseClasses = darkMode
    ? 'bg-gray-700'
    : 'bg-gray-200';

  const animationClasses: Record<string, string> = {
    pulse: 'animate-pulse',
    wave: 'skeleton-wave',
    none: '',
  };

  const variantClasses: Record<string, string> = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded',
    card: 'rounded-lg',
  };

  const getStyle = (): React.CSSProperties => {
    const style: React.CSSProperties = {};

    if (width) {
      style.width = typeof width === 'number' ? `${width}px` : width;
    }

    if (height) {
      style.height = typeof height === 'number' ? `${height}px` : height;
    }

    // Default heights for variants if not specified
    if (!height) {
      switch (variant) {
        case 'text':
          style.height = '1rem';
          break;
        case 'circular':
          style.height = style.width || '40px';
          style.width = style.width || '40px';
          break;
        case 'rectangular':
          style.height = '100px';
          break;
        case 'card':
          style.height = '200px';
          break;
      }
    }

    return style;
  };

  // Render multiple lines for text variant
  if (variant === 'text' && lines > 1) {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={`${baseClasses} ${animationClasses[animation]} ${variantClasses[variant]}`}
            style={{
              ...getStyle(),
              // Make last line shorter for natural appearance
              width: index === lines - 1 ? '75%' : (width || '100%'),
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${baseClasses} ${animationClasses[animation]} ${variantClasses[variant]} ${className}`}
      style={getStyle()}
    />
  );
};

// Pre-built skeleton compositions for common UI patterns

interface SkeletonCardProps {
  className?: string;
  darkMode?: boolean;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({ className = '', darkMode = true }) => {
  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';

  return (
    <div className={`${bgClass} rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-4">
        <Skeleton variant="circular" width={48} height={48} darkMode={darkMode} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" darkMode={darkMode} />
          <Skeleton variant="text" width="80%" darkMode={darkMode} />
        </div>
      </div>
      <div className="mt-4">
        <Skeleton variant="text" lines={3} darkMode={darkMode} />
      </div>
    </div>
  );
};

interface SkeletonTableRowProps {
  columns?: number;
  className?: string;
  darkMode?: boolean;
}

export const SkeletonTableRow: React.FC<SkeletonTableRowProps> = ({
  columns = 5,
  className = '',
  darkMode = true,
}) => {
  return (
    <tr className={className}>
      {Array.from({ length: columns }).map((_, index) => (
        <td key={index} className="px-4 py-3">
          <Skeleton
            variant="text"
            width={index === 0 ? '80%' : index === columns - 1 ? '50%' : '70%'}
            darkMode={darkMode}
          />
        </td>
      ))}
    </tr>
  );
};

interface SkeletonListItemProps {
  hasAvatar?: boolean;
  hasAction?: boolean;
  className?: string;
  darkMode?: boolean;
}

export const SkeletonListItem: React.FC<SkeletonListItemProps> = ({
  hasAvatar = true,
  hasAction = false,
  className = '',
  darkMode = true,
}) => {
  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';

  return (
    <div className={`${bgClass} flex items-center justify-between p-4 ${className}`}>
      <div className="flex items-center space-x-3">
        {hasAvatar && <Skeleton variant="circular" width={40} height={40} darkMode={darkMode} />}
        <div className="space-y-2">
          <Skeleton variant="text" width={120} darkMode={darkMode} />
          <Skeleton variant="text" width={80} darkMode={darkMode} />
        </div>
      </div>
      {hasAction && (
        <Skeleton variant="rectangular" width={60} height={32} darkMode={darkMode} />
      )}
    </div>
  );
};

interface SkeletonStatsCardProps {
  className?: string;
  darkMode?: boolean;
}

export const SkeletonStatsCard: React.FC<SkeletonStatsCardProps> = ({
  className = '',
  darkMode = true,
}) => {
  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';

  return (
    <div className={`${bgClass} rounded-lg p-4 ${className}`}>
      <Skeleton variant="text" width="40%" height={12} darkMode={darkMode} />
      <div className="mt-2">
        <Skeleton variant="text" width="60%" height={28} darkMode={darkMode} />
      </div>
      <div className="mt-3 flex items-center space-x-2">
        <Skeleton variant="rectangular" width={60} height={20} darkMode={darkMode} />
        <Skeleton variant="text" width="30%" darkMode={darkMode} />
      </div>
    </div>
  );
};

interface SkeletonChartProps {
  className?: string;
  darkMode?: boolean;
}

export const SkeletonChart: React.FC<SkeletonChartProps> = ({
  className = '',
  darkMode = true,
}) => {
  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';
  const barClass = darkMode ? 'bg-gray-700' : 'bg-gray-200';

  return (
    <div className={`${bgClass} rounded-lg p-4 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <Skeleton variant="text" width="30%" darkMode={darkMode} />
        <Skeleton variant="rectangular" width={100} height={32} darkMode={darkMode} />
      </div>
      <div className="flex items-end justify-between h-40 space-x-2">
        {[40, 65, 45, 80, 55, 70, 90, 60, 75, 50, 85, 95].map((height, index) => (
          <div
            key={index}
            className={`${barClass} animate-pulse rounded-t flex-1`}
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  );
};

interface SkeletonPortfolioProps {
  positions?: number;
  className?: string;
  darkMode?: boolean;
}

export const SkeletonPortfolio: React.FC<SkeletonPortfolioProps> = ({
  positions = 5,
  className = '',
  darkMode = true,
}) => {
  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';

  return (
    <div className={`${bgClass} rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex justify-between items-center">
          <div className="space-y-2">
            <Skeleton variant="text" width={100} darkMode={darkMode} />
            <Skeleton variant="text" width={180} height={28} darkMode={darkMode} />
          </div>
          <Skeleton variant="rectangular" width={80} height={36} darkMode={darkMode} />
        </div>
      </div>

      {/* Table Header */}
      <div className="px-4 py-2 border-b border-gray-700">
        <div className="grid grid-cols-5 gap-4">
          {['Symbol', 'Shares', 'Price', 'Value', 'P/L'].map((_, index) => (
            <Skeleton key={index} variant="text" width="70%" height={12} darkMode={darkMode} />
          ))}
        </div>
      </div>

      {/* Rows */}
      {Array.from({ length: positions }).map((_, index) => (
        <div key={index} className="px-4 py-3 border-b border-gray-700 last:border-b-0">
          <div className="grid grid-cols-5 gap-4">
            <div className="flex items-center space-x-2">
              <Skeleton variant="circular" width={32} height={32} darkMode={darkMode} />
              <Skeleton variant="text" width="60%" darkMode={darkMode} />
            </div>
            <Skeleton variant="text" width="50%" darkMode={darkMode} />
            <Skeleton variant="text" width="60%" darkMode={darkMode} />
            <Skeleton variant="text" width="70%" darkMode={darkMode} />
            <Skeleton variant="text" width="50%" darkMode={darkMode} />
          </div>
        </div>
      ))}
    </div>
  );
};

export default Skeleton;
