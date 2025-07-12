import React from 'react';

interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  headerClassName?: string;
  bodyClassName?: string;
}

const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = '',
  headerClassName = '',
  bodyClassName = ''
}) => {
  return (
    <div className={`bg-gray-900 rounded-xl shadow-lg border border-gray-800 overflow-hidden ${className}`}>
      {(title || subtitle || action) && (
        <div className={`flex flex-wrap justify-between items-center px-6 py-4 border-b border-gray-800 ${headerClassName}`}>
          <div>
            {title && (
              typeof title === 'string' ? (
                <h3 className="text-lg font-semibold text-white">{title}</h3>
              ) : title
            )}
            {subtitle && (
              typeof subtitle === 'string' ? (
                <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
              ) : subtitle
            )}
          </div>
          {action && (
            <div className="ml-auto">{action}</div>
          )}
        </div>
      )}
      <div className={`px-6 py-5 ${bodyClassName}`}>
        {children}
      </div>
    </div>
  );
};

export default Card;