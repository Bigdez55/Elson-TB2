import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hover = true
}) => (
  <div
    className={`rounded-2xl transition-all ${hover ? 'hover:border-[#C9A227]/25' : ''} ${className}`}
    style={{ backgroundColor: '#1B2838', border: '1px solid rgba(201, 162, 39, 0.1)' }}
  >
    {children}
  </div>
);

export default Card;
