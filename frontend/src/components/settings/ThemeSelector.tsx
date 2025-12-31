import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { themeConfigs, ThemeName } from '../../lib/theme';
import { cn } from '../../lib/cn';

// Check icon component
const CheckIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24">
    <path fillRule="evenodd" d="M19.916 4.626a.75.75 0 01.208 1.04l-9 13.5a.75.75 0 01-1.154.114l-6-6a.75.75 0 011.06-1.06l5.353 5.353 8.493-12.739a.75.75 0 011.04-.208z" clipRule="evenodd" />
  </svg>
);

export function ThemeSelector() {
  const { theme, setTheme, availableThemes } = useTheme();

  return (
    <div className="theme-card p-6">
      <h3 className="text-lg font-semibold text-text-primary mb-2">Appearance</h3>
      <p className="text-text-muted text-sm mb-6">Choose your preferred color scheme</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {availableThemes.map((themeName: ThemeName) => {
          const config = themeConfigs[themeName];
          const isActive = theme === themeName;

          return (
            <button
              key={themeName}
              onClick={() => setTheme(themeName)}
              className={cn(
                'p-4 rounded-xl border-2 transition-all text-left',
                'hover:border-primary/50 hover:bg-primary/5',
                isActive
                  ? 'border-primary bg-primary/10'
                  : 'border-border-subtle bg-background-surface/30'
              )}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div
                    className="w-8 h-8 rounded-full"
                    style={{
                      background: `linear-gradient(135deg, ${config.previewColors[1]}, ${config.previewColors[2]})`
                    }}
                  />
                  <span className="text-text-primary font-medium">
                    {config.displayName}
                  </span>
                </div>
                {isActive && (
                  <CheckIcon className="w-5 h-5 text-primary" />
                )}
              </div>

              <p className="text-text-muted text-xs mb-3">
                {config.description}
              </p>

              <div className="flex space-x-2">
                {config.previewColors.map((color, index) => (
                  <div
                    key={index}
                    className="w-6 h-6 rounded"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default ThemeSelector;
