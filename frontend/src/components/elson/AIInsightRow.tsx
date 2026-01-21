import React from 'react';
import { AIInsight, INSIGHT_TYPE_CONFIG } from '../../types/elson';
import { ArrowUpIcon, ArrowDownIcon, ExclamationCircleIcon } from '../icons/ElsonIcons';

interface AIInsightRowProps {
  insight: AIInsight;
}

const ICON_MAP = {
  buy: ArrowUpIcon,
  sell: ArrowDownIcon,
  alert: ExclamationCircleIcon,
};

export const AIInsightRow: React.FC<AIInsightRowProps> = ({ insight }) => {
  const config = INSIGHT_TYPE_CONFIG[insight.type];
  const Icon = ICON_MAP[insight.type];

  return (
    <div
      className="flex items-start gap-3 p-3 rounded-lg transition-all"
      style={{ backgroundColor: '#1a2535' }}
    >
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: config.bg }}
      >
        <Icon className="w-4 h-4" style={{ color: config.color }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold" style={{ color: config.color }}>{config.label}</span>
          {insight.symbol && (
            <span className="text-sm font-semibold text-white">{insight.symbol}</span>
          )}
          {insight.confidence && (
            <span className="text-xs text-gray-500">{insight.confidence}% confidence</span>
          )}
        </div>
        <p className="text-sm text-gray-400">{insight.text}</p>
      </div>
    </div>
  );
};

export default AIInsightRow;
