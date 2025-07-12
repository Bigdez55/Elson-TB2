/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    // Enable dark mode with class strategy for manual control
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          primary: {
            50: '#f0f9ff',
            100: '#e0f2fe',
            200: '#bae6fd',
            300: '#7dd3fc',
            400: '#38bdf8',
            500: '#0ea5e9',
            600: '#0284c7',
            700: '#0369a1',
            800: '#075985',
            900: '#0c4a6e',
          },
          // Add trading-specific colors
          profit: '#22c55e',  // green-500
          loss: '#ef4444',    // red-500
          neutral: '#6b7280', // gray-500
          
          // Accessibility-specific colors
          accessible: {
            error: '#ef4444',      // High contrast error (red-500)
            success: '#22c55e',    // High contrast success (green-500)
            focus: '#0ea5e9',      // Focus ring color (primary-500)
            warning: '#F59E0B',    // High visibility warning color
            notice: '#6366F1',     // Informational color
            link: {
              light: '#2563EB',    // Link color for light mode (blue-600)
              dark: '#93C5FD',     // Link color for dark mode (blue-300)
              visited: {
                light: '#7C3AED',  // Visited link for light mode (violet-600)
                dark: '#C4B5FD'    // Visited link for dark mode (violet-300)
              }
            }
          }
        },
        // Support for reduced-motion preferences
        transitionDuration: {
          '0': '0ms', // Used when reduced motion is preferred
        },
        // Enhanced outline styles for keyboard focus
        outline: {
          'accessible': '3px solid #0ea5e9',
        },
        // Spacing specifically for touch targets
        spacing: {
          'touch': '44px', // Minimum size for touch targets (44px)
        },
        // Screen reader utilities
        screens: {
          'xs': '375px',
          // Base breakpoints still apply
        },
      },
    },
    // Add custom variants for accessibility features
    variants: {
      extend: {
        // Enable hover only for devices that support hover
        backgroundColor: ['responsive', 'hover', 'focus', 'dark'],
        textColor: ['responsive', 'hover', 'focus', 'dark'],
        outline: ['focus', 'focus-visible'],
      },
    },
    plugins: [],
  }