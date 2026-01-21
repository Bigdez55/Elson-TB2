import React from 'react';
import { UserTier } from '../../types/elson';
import { LockIcon } from '../icons/ElsonIcons';

interface PremiumLockProps {
  feature: string;
  requiredTier?: UserTier;
  children?: React.ReactNode;
  onUpgrade?: () => void;
}

export const PremiumLock: React.FC<PremiumLockProps> = ({
  feature,
  requiredTier = 'Growth',
  children,
  onUpgrade
}) => (
  <div className="relative">
    <div
      className="absolute inset-0 rounded-xl flex flex-col items-center justify-center z-10"
      style={{ backgroundColor: 'rgba(13, 27, 42, 0.9)' }}
    >
      <LockIcon className="w-8 h-8 text-gray-500 mb-2" />
      <p className="text-sm text-gray-400 mb-1">{feature}</p>
      <p className="text-xs text-gray-500 mb-3">Requires {requiredTier} tier</p>
      <button
        onClick={onUpgrade}
        className="px-4 py-2 rounded-lg text-[#0D1B2A] text-sm font-semibold"
        style={{ background: 'linear-gradient(to right, #C9A227, #E8D48B)' }}
      >
        Upgrade
      </button>
    </div>
    <div className="opacity-30 pointer-events-none">
      {children}
    </div>
  </div>
);

export default PremiumLock;
