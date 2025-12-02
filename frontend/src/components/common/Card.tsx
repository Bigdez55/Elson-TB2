import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'feature' | 'premium';
  hover?: boolean;
  padding?: 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'default',
  hover = false,
  padding = 'md',
}) => {
  const baseClasses = 'rounded-xl shadow-md';
  
  const variantClasses = {
    default: 'bg-gray-900',
    feature: 'bg-gray-900 transition-all duration-300',
    premium: 'bg-gradient-to-r from-purple-900 to-blue-900',
  };

  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const hoverClasses = hover ? 'hover:transform hover:-translate-y-1 hover:shadow-lg' : '';

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${paddingClasses[padding]} ${hoverClasses} ${className}`}
    >
      {children}
    </div>
  );
};

interface StatsCardProps {
  title: string;
  value: string;
  change?: {
    value: string;
    positive: boolean;
  };
  badge?: {
    text: string;
    variant: 'success' | 'warning' | 'info' | 'premium';
  };
  icon?: React.ReactNode;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  badge,
  icon,
}) => {
  const badgeVariants = {
    success: 'bg-green-900 text-green-300',
    warning: 'bg-yellow-900 text-yellow-300',
    info: 'bg-blue-900 text-blue-300',
    premium: 'bg-purple-900 text-purple-300',
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        {badge && (
          <span className={`text-xs px-2 py-1 rounded-full ${badgeVariants[badge.variant]}`}>
            {badge.text}
          </span>
        )}
      </div>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-3xl font-bold text-white mb-2">{value}</p>
          {change && (
            <div className={`flex items-center ${change.positive ? 'text-green-400' : 'text-red-400'}`}>
              <svg className="h-5 w-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                  d={change.positive ? "M5 10l7-7m0 0l7 7m-7-7v18" : "M19 14l-7 7m0 0l-7-7m7 7V4"} />
              </svg>
              <span>{change.value}</span>
            </div>
          )}
        </div>
        {icon && <div className="text-purple-400">{icon}</div>}
      </div>
    </Card>
  );
};