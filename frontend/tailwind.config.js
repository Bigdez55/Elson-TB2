/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      width: {
        '280': '280px',
      },
      fontFamily: {
        display: ['var(--font-display)', 'serif'],
        body: ['var(--font-body)', 'sans-serif'],
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        // Theme-aware colors using CSS variables
        primary: {
          DEFAULT: 'var(--color-primary)',
          light: 'var(--color-primary-light)',
          dark: 'var(--color-primary-dark)',
        },
        background: {
          base: 'var(--color-bg-base)',
          elevated: 'var(--color-bg-elevated)',
          surface: 'var(--color-bg-surface)',
        },
        card: {
          DEFAULT: 'var(--color-card-bg)',
          border: 'var(--color-card-border)',
          'border-hover': 'var(--color-card-border-hover)',
        },
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          accent: 'var(--color-text-accent)',
        },
        border: {
          subtle: 'var(--color-border-subtle)',
          medium: 'var(--color-border-medium)',
        },
        // Status colors
        profit: 'var(--color-profit)',
        loss: 'var(--color-loss)',
        warning: 'var(--color-warning)',
        info: 'var(--color-info)',
        // Keep existing purple palette for backwards compatibility
        purple: {
          400: '#a855f7',
          500: '#9333ea',
          600: '#7e22ce',
          700: '#6b21a8',
          800: '#581c87',
          900: '#4c1d95',
        }
      },
      backgroundImage: {
        'gradient-bg': 'linear-gradient(135deg, var(--gradient-start), var(--gradient-mid), var(--gradient-end))',
        'text-gradient': 'linear-gradient(90deg, var(--color-primary-light), var(--color-primary))',
      },
      transitionDuration: {
        fast: 'var(--transition-fast)',
        base: 'var(--transition-base)',
        slow: 'var(--transition-slow)',
      },
    },
  },
  plugins: [],
};
