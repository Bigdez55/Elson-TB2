import React from 'react';

interface MarketStatusStripProps {
  isOpen?: boolean;
  timeToClose?: string;
  timeToOpen?: string;
}

export const MarketStatusStrip: React.FC<MarketStatusStripProps> = ({
  isOpen = true,
  timeToClose = '2h 34m',
  timeToOpen = '14h 23m'
}) => (
  <div
    className="flex items-center justify-center gap-2 py-1.5"
    style={{ backgroundColor: '#050A0F', borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}
  >
    <span className={`w-1.5 h-1.5 rounded-full ${isOpen ? 'bg-green-500' : 'bg-red-500'}`} />
    <span className="text-xs text-gray-400">
      Market {isOpen ? 'Open' : 'Closed'} · {isOpen ? `Closes in ${timeToClose}` : `Opens in ${timeToOpen}`}
    </span>
  </div>
);

export default MarketStatusStrip;
