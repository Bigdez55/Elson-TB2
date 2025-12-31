import React from 'react';

interface EducationalTooltipProps {
  term?: string;
  title?: string;
  definition?: string;
  content?: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  position?: 'top' | 'bottom' | 'left' | 'right';
  children?: React.ReactNode;
}

/**
 * A tooltip component for displaying educational content
 */
const EducationalTooltip: React.FC<EducationalTooltipProps> = ({
  term,
  title,
  definition,
  content,
  placement,
  position,
  children
}) => {
  const actualPlacement = placement || position || 'top';
  const displayTitle = term || title || '';
  const displayContent = definition || content || '';

  // Simple icon when no children provided
  const triggerElement = children || (
    <span className="inline-flex items-center justify-center w-4 h-4 text-xs text-blue-600 bg-blue-100 rounded-full cursor-help ml-1">
      ?
    </span>
  );

  return (
    <div className="group relative inline-block">
      {triggerElement}
      <div className={`invisible group-hover:visible absolute z-50 w-64 p-3 text-sm bg-white border border-gray-200 rounded-lg shadow-lg
        ${actualPlacement === 'right' ? 'left-full ml-2 top-1/2 -translate-y-1/2' :
          actualPlacement === 'left' ? 'right-full mr-2 top-1/2 -translate-y-1/2' :
          actualPlacement === 'bottom' ? 'top-full mt-2 left-1/2 -translate-x-1/2' :
          'bottom-full mb-2 left-1/2 -translate-x-1/2'}`}
      >
        {displayTitle && <div className="font-semibold text-gray-900 mb-1">{displayTitle}</div>}
        {displayContent && <div className="text-gray-600">{displayContent}</div>}
      </div>
    </div>
  );
};

export { EducationalTooltip };
export default EducationalTooltip;
