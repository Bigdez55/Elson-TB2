import React from 'react';
import { TIME_PERIODS, TimePeriod } from '../../types/elson';

interface TimePeriodSelectorProps {
  value: TimePeriod;
  onChange: (val: TimePeriod) => void;
}

export const TimePeriodSelector: React.FC<TimePeriodSelectorProps> = ({
  value,
  onChange
}) => (
  <div className="flex items-center gap-1 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0">
    {TIME_PERIODS.map((period) => (
      <button
        key={period}
        onClick={() => onChange(period)}
        className={`px-3 py-2 rounded-lg text-xs font-semibold min-h-[36px] min-w-[44px] transition-all flex-shrink-0 ${
          value === period
            ? 'text-[#C9A227]'
            : 'text-gray-500 hover:text-gray-300'
        }`}
        style={value === period ? { backgroundColor: 'rgba(201, 162, 39, 0.2)' } : {}}
      >
        {period}
      </button>
    ))}
  </div>
);

export default TimePeriodSelector;
