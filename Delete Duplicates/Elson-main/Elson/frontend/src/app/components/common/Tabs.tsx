import React, { useState, useCallback } from 'react';

interface TabItem {
  id: string;
  label: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  defaultActiveTab?: string;
  onChange?: (tabId: string) => void;
  variant?: 'default' | 'pill' | 'underline';
  className?: string;
  tabsClassName?: string;
  contentClassName?: string;
  orientation?: 'horizontal' | 'vertical';
}

const Tabs: React.FC<TabsProps> = ({ 
  tabs, 
  defaultActiveTab,
  onChange,
  variant = 'default',
  className = '',
  tabsClassName = '',
  contentClassName = '',
  orientation = 'horizontal'
}) => {
  // Set active tab to the first non-disabled tab if no default is provided
  const firstActiveTab = defaultActiveTab || 
    tabs.find(tab => !tab.disabled)?.id || 
    (tabs.length > 0 ? tabs[0].id : '');

  const [activeTab, setActiveTab] = useState(firstActiveTab);

  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId);
    if (onChange) {
      onChange(tabId);
    }
  }, [onChange]);

  // Get styles based on variant
  const getTabStyles = (tab: TabItem) => {
    const isActive = activeTab === tab.id;
    const isDisabled = tab.disabled;
    
    // Common styles
    const baseStyle = 'transition-colors duration-200 focus:outline-none';
    
    // Disabled styles
    const disabledStyle = isDisabled 
      ? 'cursor-not-allowed opacity-50' 
      : 'cursor-pointer';
    
    // Variant specific styles
    const variantStyles = {
      default: `px-4 py-2 text-sm font-medium rounded-lg ${
        isActive 
          ? 'bg-gray-800 text-white' 
          : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800'
      }`,
      pill: `px-4 py-2 text-sm font-medium rounded-full ${
        isActive 
          ? 'bg-purple-700 text-white' 
          : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800'
      }`,
      underline: `px-4 py-2 text-sm font-medium border-b-2 ${
        isActive 
          ? 'border-purple-500 text-purple-400' 
          : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-700'
      }`
    };
    
    return `${baseStyle} ${disabledStyle} ${variantStyles[variant]}`;
  };

  // Container styles based on orientation
  const containerStyles = orientation === 'vertical' 
    ? 'flex flex-col sm:flex-row'
    : '';

  // Tabs list styles based on orientation
  const tabsListStyles = orientation === 'vertical'
    ? 'flex flex-col space-y-1 sm:w-48 sm:flex-shrink-0 border-r border-gray-800 pr-4'
    : 'flex flex-wrap space-x-2 border-b border-gray-800';

  // Tab content styles based on orientation
  const tabContentStyles = orientation === 'vertical'
    ? 'mt-4 sm:mt-0 sm:ml-6 flex-grow'
    : 'mt-4';

  return (
    <div className={`${containerStyles} ${className}`}>
      {/* Tabs list */}
      <div className={`${tabsListStyles} ${tabsClassName}`}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && handleTabChange(tab.id)}
            className={getTabStyles(tab)}
            disabled={tab.disabled}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className={`${tabContentStyles} ${contentClassName}`}>
        {tabs.map((tab) => (
          <div
            key={tab.id}
            id={`tabpanel-${tab.id}`}
            role="tabpanel"
            aria-labelledby={`tab-${tab.id}`}
            className={activeTab === tab.id ? 'block' : 'hidden'}
          >
            {tab.content}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Tabs;