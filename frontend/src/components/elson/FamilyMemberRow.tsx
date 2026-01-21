import React from 'react';
import { FamilyMember, ROLE_STYLES, ROLE_LABELS } from '../../types/elson';

interface FamilyMemberRowProps {
  member: FamilyMember;
  onTrade?: () => void;
  onView?: () => void;
  canTrade?: boolean;
}

export const FamilyMemberRow: React.FC<FamilyMemberRowProps> = ({
  member,
  onTrade,
  onView,
  canTrade = true
}) => (
  <div
    className="flex items-center p-3 last:border-b-0 hover:bg-[#1B2838]/30 transition-all"
    style={{ borderBottom: '1px solid rgba(55, 65, 81, 0.3)' }}
  >
    <div
      className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
      style={{ background: 'linear-gradient(to bottom right, rgba(201, 162, 39, 0.3), rgba(201, 162, 39, 0.1))' }}
    >
      <span className="text-[#C9A227] text-sm font-bold">{member.name[0]}</span>
    </div>
    <div className="flex-1 ml-3 min-w-0">
      <div className="flex items-center gap-2">
        <p className="text-sm font-medium text-white truncate">{member.name}</p>
        <span
          className="px-1.5 py-0.5 rounded text-[10px] font-medium"
          style={ROLE_STYLES[member.role]}
        >
          {ROLE_LABELS[member.role]}
        </span>
      </div>
      <p className="text-xs text-gray-500">
        ${member.value.toLocaleString()}
        <span className={member.change >= 0 ? 'text-green-400' : 'text-red-400'}>
          {' '}({member.change >= 0 ? '+' : ''}{member.change}%)
        </span>
      </p>
    </div>
    <div className="flex items-center gap-2">
      {member.pendingApprovals && member.pendingApprovals > 0 && (
        <span
          className="px-2 py-1 rounded-full text-orange-400 text-xs font-medium"
          style={{ backgroundColor: 'rgba(249, 115, 22, 0.2)' }}
        >
          {member.pendingApprovals} pending
        </span>
      )}
      {canTrade && member.role !== 'child' ? (
        <button
          onClick={onTrade}
          className="px-3 py-1.5 rounded-lg text-[#C9A227] text-xs font-medium hover:bg-[#C9A227]/20 transition-colors"
          style={{ backgroundColor: 'rgba(201, 162, 39, 0.1)' }}
        >
          Trade
        </button>
      ) : (
        <button
          onClick={onView}
          className="px-3 py-1.5 rounded-lg text-gray-400 text-xs font-medium hover:bg-gray-500/20 transition-colors"
          style={{ backgroundColor: 'rgba(107, 114, 128, 0.1)' }}
        >
          View
        </button>
      )}
    </div>
  </div>
);

export default FamilyMemberRow;
