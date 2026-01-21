import React from 'react';

interface CardHeaderProps {
  title: string;
  action?: () => void;
  actionLabel?: string;
  badge?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  action,
  actionLabel = 'View All',
  badge
}) => (
  <div className="flex items-center justify-between p-4 border-b border-gray-800/50">
    <div className="flex items-center gap-2">
      <h2 className="text-base font-semibold text-white">{title}</h2>
      {badge && (
        <span
          className="px-2 py-0.5 rounded-full text-[#C9A227] text-xs font-medium"
          style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
        >
          {badge}
        </span>
      )}
    </div>
    {action && (
      <button onClick={action} className="text-[#C9A227] text-sm font-medium hover:underline">
        {actionLabel}
      </button>
    )}
  </div>
);

export default CardHeader;
