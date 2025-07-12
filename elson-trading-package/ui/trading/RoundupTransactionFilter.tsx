import React, { useState } from 'react';
import { Button } from '../common/Button';

interface RoundupTransactionFilterProps {
  filters: {
    status: string;
    startDate: string;
    endDate: string;
  };
  onFilterChange: (filters: any) => void;
  darkMode?: boolean;
}

export const RoundupTransactionFilter: React.FC<RoundupTransactionFilterProps> = ({
  filters,
  onFilterChange,
  darkMode = true
}) => {
  const [localFilters, setLocalFilters] = useState({
    status: filters.status || '',
    startDate: filters.startDate || '',
    endDate: filters.endDate || ''
  });
  
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target;
    setLocalFilters({
      ...localFilters,
      [name]: value
    });
  };
  
  const handleApplyFilters = () => {
    onFilterChange(localFilters);
  };
  
  const handleResetFilters = () => {
    const resetFilters = {
      status: '',
      startDate: '',
      endDate: ''
    };
    setLocalFilters(resetFilters);
    onFilterChange(resetFilters);
  };
  
  // Styling based on dark/light mode
  const inputClassName = darkMode
    ? "bg-gray-800 border border-gray-700 text-white rounded-md px-3 py-2 w-full"
    : "bg-white border border-gray-300 text-gray-800 rounded-md px-3 py-2 w-full";
    
  const buttonClass = darkMode
    ? "bg-blue-600 hover:bg-blue-500 text-white px-3 py-2"
    : "bg-blue-500 hover:bg-blue-400 text-white px-3 py-2";
    
  const secondaryButtonClass = darkMode
    ? "bg-gray-700 hover:bg-gray-600 text-white px-3 py-2"
    : "bg-gray-200 hover:bg-gray-300 text-gray-800 px-3 py-2";
  
  return (
    <div className={`p-4 ${darkMode ? 'bg-gray-800' : 'bg-gray-100'} rounded-lg`}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className={`block mb-1 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            Status
          </label>
          <select
            name="status"
            value={localFilters.status}
            onChange={handleChange}
            className={inputClassName}
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="invested">Invested</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        
        <div>
          <label className={`block mb-1 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            Start Date
          </label>
          <input
            type="date"
            name="startDate"
            value={localFilters.startDate}
            onChange={handleChange}
            className={inputClassName}
          />
        </div>
        
        <div>
          <label className={`block mb-1 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            End Date
          </label>
          <input
            type="date"
            name="endDate"
            value={localFilters.endDate}
            onChange={handleChange}
            className={inputClassName}
          />
        </div>
        
        <div className="flex items-end gap-2">
          <Button
            className={buttonClass}
            onClick={handleApplyFilters}
          >
            Apply Filters
          </Button>
          <Button
            className={secondaryButtonClass}
            onClick={handleResetFilters}
          >
            Reset
          </Button>
        </div>
      </div>
    </div>
  );
};

export default RoundupTransactionFilter;
