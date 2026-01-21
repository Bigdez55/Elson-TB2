import React from 'react';

interface SidebarItemProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  active?: boolean;
  onClick?: () => void;
  badge?: number;
}

export const SidebarItem: React.FC<SidebarItemProps> = ({
  icon: Icon,
  label,
  active = false,
  onClick,
  badge
}) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all min-h-[44px] ${
      active
        ? 'text-[#C9A227]'
        : 'text-gray-400 hover:bg-[#C9A227]/10 hover:text-gray-200'
    }`}
    style={active ? { backgroundColor: 'rgba(201, 162, 39, 0.15)', borderLeft: '3px solid #C9A227', marginLeft: '-3px' } : {}}
  >
    <Icon className="w-5 h-5" />
    <span className="flex-1 text-left">{label}</span>
    {badge && badge > 0 && (
      <span
        className="px-2 py-0.5 rounded-full text-[#C9A227] text-xs font-medium"
        style={{ backgroundColor: 'rgba(201, 162, 39, 0.2)' }}
      >
        {badge}
      </span>
    )}
  </button>
);

export default SidebarItem;
