import React from 'react';

interface ActivityRowProps {
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  iconBg: string;
  title: string;
  subtitle: string;
  time: string;
  isAutoTrade?: boolean;
}

export const ActivityRow: React.FC<ActivityRowProps> = ({
  icon: Icon,
  iconColor,
  iconBg,
  title,
  subtitle,
  time,
  isAutoTrade = false
}) => (
  <div
    className="flex items-center gap-3 py-3 last:border-b-0"
    style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}
  >
    <div
      className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ backgroundColor: iconBg }}
    >
      <Icon className={`w-4 h-4 ${iconColor}`} />
    </div>
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-2">
        <p className="text-sm font-medium text-white">{title}</p>
        {isAutoTrade && (
          <span
            className="px-1.5 py-0.5 rounded text-[10px] font-medium text-blue-400"
            style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)' }}
          >
            AUTO
          </span>
        )}
      </div>
      <p className="text-xs text-gray-500">{subtitle}</p>
    </div>
    <p className="text-xs text-gray-500">{time}</p>
  </div>
);

export default ActivityRow;
