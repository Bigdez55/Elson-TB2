import React from 'react';

interface TabGroupProps {
  tabs: string[];
  value: string;
  onChange: (val: string) => void;
}

export const TabGroup: React.FC<TabGroupProps> = ({
  tabs,
  value,
  onChange
}) => (
  <div className="flex gap-1 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0">
    {tabs.map((tab) => (
      <button
        key={tab}
        onClick={() => onChange(tab)}
        className={`px-4 py-2 rounded-lg text-sm font-medium min-h-[40px] whitespace-nowrap transition-all ${
          value === tab
            ? 'text-[#C9A227]'
            : 'text-gray-400 hover:text-gray-200'
        }`}
        style={value === tab ? { backgroundColor: 'rgba(201, 162, 39, 0.2)', border: '1px solid rgba(201, 162, 39, 0.3)' } : {}}
      >
        {tab}
      </button>
    ))}
  </div>
);

export default TabGroup;
