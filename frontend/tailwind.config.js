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
      colors: {
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
        'gradient-bg': 'linear-gradient(135deg, #1e1b4b, #7e22ce)',
        'text-gradient': 'linear-gradient(90deg, #a855f7, #d8b4fe)',
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
};