import React from 'react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  className?: string;
}

export const Logo: React.FC<LogoProps> = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8',      // 32px
    md: 'h-10 w-10',    // 40px
    lg: 'h-12 w-12',    // 48px - Navigation bar
    xl: 'h-14 w-14',    // 56px - Footer
    '2xl': 'h-16 w-16'  // 64px - Hero/Login
  };

  return (
    <img
      src="/logo.png"
      alt="Elson Wealth"
      className={`${sizeClasses[size]} rounded-lg ${className}`}
    />
  );
};
