import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AccessibilityProvider, useAccessibility } from './useAccessibility';
import { vi, expect } from 'vitest';

// Mock localStorage
const mockLocalStorage: Record<string, string> = {};

beforeEach(() => {
  // Setup localStorage mock
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(
    (key: string) => mockLocalStorage[key] || null
  );
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(
    (key: string, value: string) => {
      mockLocalStorage[key] = value;
    }
  );
  
  // Reset localStorage between tests
  Object.keys(mockLocalStorage).forEach(key => delete mockLocalStorage[key]);
  
  // Mock document methods/properties used in component
  Object.defineProperty(document, 'documentElement', {
    value: {
      classList: {
        add: vi.fn(),
        remove: vi.fn(),
        toggle: vi.fn(),
      },
    },
    writable: true,
  });
  
  // Mock createElement and appendChild for testing purposes
  document.createElement = vi.fn().mockImplementation(() => ({
    id: '',
    className: '',
    setAttribute: vi.fn(),
    appendChild: vi.fn(),
  }));
  
  document.body.appendChild = vi.fn();
  document.body.removeChild = vi.fn();
  document.getElementById = vi.fn().mockImplementation(() => null);
  
  // Mock matchMedia
  window.matchMedia = vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
});

afterEach(() => {
  vi.clearAllMocks();
});

// Test component that uses the accessibility hook
const TestComponent = () => {
  const { 
    isDarkMode, 
    toggleDarkMode, 
    textSize, 
    setTextSize,
    prefersReducedMotion,
    setPrefersReducedMotion,
    isHighContrast,
    toggleHighContrast,
    focusOutlineVisible,
    announce
  } = useAccessibility();
  
  return (
    <div>
      <div data-testid="dark-mode">{isDarkMode ? 'dark' : 'light'}</div>
      <div data-testid="text-size">{textSize}</div>
      <div data-testid="reduced-motion">{prefersReducedMotion ? 'reduced' : 'normal'}</div>
      <div data-testid="high-contrast">{isHighContrast ? 'high' : 'normal'}</div>
      <div data-testid="focus-outline">{focusOutlineVisible ? 'visible' : 'hidden'}</div>
      
      <button onClick={() => toggleDarkMode()}>Toggle Dark Mode</button>
      <button onClick={() => setTextSize('large')}>Set Large Text</button>
      <button onClick={() => setPrefersReducedMotion(true)}>Set Reduced Motion</button>
      <button onClick={() => toggleHighContrast()}>Toggle High Contrast</button>
      <button onClick={() => announce('Test announcement', true)}>Announce</button>
    </div>
  );
};

describe('useAccessibility', () => {
  it('should provide default values when no localStorage values exist', () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Check default values
    expect(screen.getByTestId('dark-mode')).toHaveTextContent('light');
    expect(screen.getByTestId('text-size')).toHaveTextContent('default');
    expect(screen.getByTestId('reduced-motion')).toHaveTextContent('normal');
    expect(screen.getByTestId('high-contrast')).toHaveTextContent('normal');
    expect(screen.getByTestId('focus-outline')).toHaveTextContent('visible');
  });
  
  it('should load values from localStorage if they exist', () => {
    // Setup localStorage with values
    mockLocalStorage['elson-dark-mode'] = 'true';
    mockLocalStorage['elson-text-size'] = 'large';
    mockLocalStorage['elson-reduced-motion'] = 'true';
    mockLocalStorage['elson-high-contrast'] = 'true';
    
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Check loaded values
    expect(screen.getByTestId('dark-mode')).toHaveTextContent('dark');
    expect(screen.getByTestId('text-size')).toHaveTextContent('large');
    expect(screen.getByTestId('reduced-motion')).toHaveTextContent('reduced');
    expect(screen.getByTestId('high-contrast')).toHaveTextContent('high');
  });
  
  it('should toggle dark mode when the toggle function is called', () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Initially light mode
    expect(screen.getByTestId('dark-mode')).toHaveTextContent('light');
    
    // Toggle to dark mode
    fireEvent.click(screen.getByText('Toggle Dark Mode'));
    expect(screen.getByTestId('dark-mode')).toHaveTextContent('dark');
    
    // Check localStorage was updated
    expect(mockLocalStorage['elson-dark-mode']).toBe('true');
    
    // Toggle back to light mode
    fireEvent.click(screen.getByText('Toggle Dark Mode'));
    expect(screen.getByTestId('dark-mode')).toHaveTextContent('light');
    
    // Check localStorage was updated
    expect(mockLocalStorage['elson-dark-mode']).toBe('false');
  });
  
  it('should update text size when setTextSize is called', () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Initially default text size
    expect(screen.getByTestId('text-size')).toHaveTextContent('default');
    
    // Change to large text
    fireEvent.click(screen.getByText('Set Large Text'));
    expect(screen.getByTestId('text-size')).toHaveTextContent('large');
    
    // Check localStorage was updated
    expect(mockLocalStorage['elson-text-size']).toBe('large');
  });
  
  it('should update motion preference when setPrefersReducedMotion is called', () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Initially normal motion
    expect(screen.getByTestId('reduced-motion')).toHaveTextContent('normal');
    
    // Change to reduced motion
    fireEvent.click(screen.getByText('Set Reduced Motion'));
    expect(screen.getByTestId('reduced-motion')).toHaveTextContent('reduced');
    
    // Check localStorage was updated
    expect(mockLocalStorage['elson-reduced-motion']).toBe('true');
  });
  
  it('should toggle high contrast when toggleHighContrast is called', () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Initially normal contrast
    expect(screen.getByTestId('high-contrast')).toHaveTextContent('normal');
    
    // Toggle to high contrast
    fireEvent.click(screen.getByText('Toggle High Contrast'));
    expect(screen.getByTestId('high-contrast')).toHaveTextContent('high');
    
    // Check localStorage was updated
    expect(mockLocalStorage['elson-high-contrast']).toBe('true');
  });
  
  it('should create screen reader announcement elements', () => {
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Verify that the announcement elements were created
    expect(document.createElement).toHaveBeenCalledTimes(2);
    expect(document.body.appendChild).toHaveBeenCalledTimes(2);
  });
  
  it('should make announcements when announce is called', () => {
    // Mock getElementById to return an element
    const announcerEl = { textContent: '', offsetWidth: 10 };
    document.getElementById = vi.fn().mockImplementation(() => announcerEl);
    
    render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    );
    
    // Call announce
    fireEvent.click(screen.getByText('Announce'));
    
    // Verify the announcement was made
    expect(announcerEl.textContent).toBe('Test announcement');
  });
});