# Elson Wealth Trading Platform - Frontend

## Overview

The Elson Wealth Trading Platform frontend is a modern React application designed to provide an accessible, responsive, and user-friendly interface for users to manage their investments, learn about trading, and execute trades. The application is designed to be accessible to users of all abilities and to work seamlessly across all devices.

## Key Features

### Accessibility

The platform is built with accessibility in mind, following WCAG 2.1 AA standards:

- Comprehensive accessibility context system for managing user preferences
- Screen reader support with aria-live announcements
- Keyboard navigation with focus management
- Skip navigation links for keyboard users
- Accessible modals with proper focus trapping
- High contrast mode support
- Text resizing options
- Reduced motion settings
- Extensive accessibility testing with jest-axe

### Mobile Optimization

The application is fully optimized for mobile devices:

- Responsive design that adapts to all screen sizes
- Touch-friendly interface with appropriately sized targets (44px+)
- Mobile-specific layout components
- Off-canvas menu for mobile navigation
- Bottom navigation bar for easy mobile access
- Mobile-optimized versions of all key pages

### Progressive Web App (PWA)

The application functions as a Progressive Web App for a native-like experience:

- Offline capability through service worker caching
- Installable on home screen via web app manifest
- Offline fallback page
- Update notification system
- Fast loading through asset caching

## Technology Stack

- React 18
- TypeScript
- Redux Toolkit for state management
- React Router for navigation
- Tailwind CSS for styling
- Vitest for testing
- Vite for fast development and building

## Development

### Installation

```bash
npm install
```

### Development Server

```bash
npm run dev
```

### Building

```bash
npm run build
```

### Testing

```bash
npm run test
```

## Accessibility Implementation

The platform follows a comprehensive accessibility strategy:

1. **Phase 1**: Basic Compliance
   - Semantic HTML
   - ARIA attributes
   - Keyboard accessibility
   - Focus management

2. **Phase 2**: User Preferences
   - Dark mode
   - Text resizing
   - Reduced motion
   - High contrast mode

3. **Phase 3**: Enhanced Interactions
   - Screen reader announcements
   - Accessible modals
   - Skip navigation
   - Form validation messages

4. **Phase 4**: Testing & Refinement
   - Automated accessibility testing
   - User testing
   - Continuous improvement

## Mobile-First Design

The application follows mobile-first design principles:

1. **Responsive Layout**: Uses CSS Grid and Flexbox for fluid layouts
2. **Touch Optimization**: All interactive elements are sized appropriately for touch
3. **Performance**: Optimized bundle size and code splitting for fast mobile performance
4. **Offline Support**: Key features work without an internet connection

## Project Structure

```
src/
├── app/
│   ├── components/
│   │   ├── common/       # Shared components like SkipNav, AccessibleModal
│   │   ├── dashboard/    # Dashboard components
│   │   ├── education/    # Educational content components
│   │   ├── family/       # Family account management components
│   │   ├── layout/       # Layout components including mobile layouts
│   │   ├── portfolio/    # Portfolio management components
│   │   └── trading/      # Trading interface components
│   ├── hooks/            # Custom hooks including useAccessibility
│   ├── services/         # API services
│   ├── store/            # Redux store configuration
│   ├── utils/            # Utility functions
│   └── types/            # TypeScript type definitions
├── pages/                # Top-level page components
├── styles/               # Global styles
├── public/               # Static assets and PWA files
└── main.tsx              # Application entry point
```

## Contribution Guidelines

- Follow the established code style and patterns
- Ensure all new code passes accessibility tests
- Test on multiple devices and screen sizes
- Document any new components or utilities