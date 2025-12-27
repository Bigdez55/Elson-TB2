/**
 * Bundle optimization utilities and webpack configuration helpers
 */

// Dynamic import helper for code splitting
export const loadComponent = async <T>(
  factory: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) => {
  try {
    const module = await factory();
    return module.default;
  } catch (error) {
    console.error('Failed to load component:', error);
    return fallback || (() => null as any);
  }
};

// Chunk loading priority
export const CHUNK_PRIORITIES = {
  HIGH: ['trading', 'auth', 'dashboard'],
  MEDIUM: ['portfolio', 'settings', 'charts'],
  LOW: ['admin', 'reports', 'help']
};

// Preload critical chunks
export const preloadCriticalChunks = () => {
  const criticalChunks = [
    // Trading components
    () => import('../pages/TradingPage'),
    () => import('../components/trading/EnhancedOrderForm'),
    () => import('../components/trading/LiveMarketData'),
    
    // Authentication
    () => import('../pages/LoginPage'),
    
    // Dashboard essentials
    () => import('../pages/DashboardPage'),
  ];

  // Preload in background with low priority
  criticalChunks.forEach((chunk, index) => {
    setTimeout(() => {
      chunk().catch(() => {
        // Silently fail preloading
      });
    }, index * 100); // Stagger preloading
  });
};

// Resource hints for better loading
export const addResourceHints = () => {
  const head = document.head;
  
  // Preconnect to critical domains
  const preconnectDomains = [
    'https://api.trading.elson.com',
    'https://ws.trading.elson.com',
    'https://cdn.jsdelivr.net', // Chart.js CDN
  ];

  preconnectDomains.forEach(domain => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = domain;
    link.crossOrigin = 'anonymous';
    head.appendChild(link);
  });

  // DNS prefetch for additional domains
  const dnsPrefetchDomains = [
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com',
  ];

  dnsPrefetchDomains.forEach(domain => {
    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = domain;
    head.appendChild(link);
  });
};

// Service Worker registration for caching
export const registerServiceWorker = async () => {
  if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js');
      
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // Show update available notification
              console.log('App update available. Please refresh.');
              
              // Optionally show user notification
              if (window.confirm('A new version is available. Refresh to update?')) {
                window.location.reload();
              }
            }
          });
        }
      });

      console.log('Service Worker registered successfully');
    } catch (error) {
      console.error('Service Worker registration failed:', error);
    }
  }
};

// Image optimization utilities
export const optimizeImage = (
  src: string,
  options: {
    width?: number;
    height?: number;
    quality?: number;
    format?: 'webp' | 'avif' | 'jpg' | 'png';
    loading?: 'lazy' | 'eager';
  } = {}
) => {
  const { width, height, quality = 85, format = 'webp', loading = 'lazy' } = options;
  
  // In production, this would integrate with an image optimization service
  // For now, return optimized parameters
  return {
    src: src,
    width: width,
    height: height,
    quality: quality,
    format: format,
    loading: loading,
    // Add srcset for responsive images
    srcSet: width ? [
      `${src}?w=${Math.floor(width * 0.5)} ${Math.floor(width * 0.5)}w`,
      `${src}?w=${width} ${width}w`,
      `${src}?w=${Math.floor(width * 1.5)} ${Math.floor(width * 1.5)}w`,
      `${src}?w=${width * 2} ${width * 2}w`,
    ].join(', ') : undefined
  };
};

// Font loading optimization
export const optimizeFontLoading = () => {
  // Preload critical fonts
  const criticalFonts = [
    '/fonts/inter-var.woff2',
    '/fonts/inter-medium.woff2'
  ];

  criticalFonts.forEach(font => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = font;
    link.as = 'font';
    link.type = 'font/woff2';
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });

  // Add font-display: swap for better loading experience
  const style = document.createElement('style');
  style.textContent = `
    @font-face {
      font-family: 'Inter';
      font-style: normal;
      font-weight: 100 900;
      font-display: swap;
      src: url('/fonts/inter-var.woff2') format('woff2');
      unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
    }
  `;
  document.head.appendChild(style);
};

// Third-party script optimization
export const loadThirdPartyScript = async (
  src: string,
  options: {
    async?: boolean;
    defer?: boolean;
    onLoad?: () => void;
    onError?: (error: any) => void;
    timeout?: number;
  } = {}
) => {
  const { async = true, defer = true, onLoad, onError, timeout = 10000 } = options;

  return new Promise<void>((resolve, reject) => {
    // Check if script is already loaded
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = async;
    script.defer = defer;

    const timeoutId = setTimeout(() => {
      script.remove();
      const error = new Error(`Script loading timeout: ${src}`);
      if (onError) onError(error);
      reject(error);
    }, timeout);

    script.onload = () => {
      clearTimeout(timeoutId);
      if (onLoad) onLoad();
      resolve();
    };

    script.onerror = (error) => {
      clearTimeout(timeoutId);
      script.remove();
      if (onError) onError(error);
      reject(error);
    };

    document.head.appendChild(script);
  });
};

// Critical CSS inlining helper
export const inlineCriticalCSS = () => {
  const criticalCSS = `
    /* Critical CSS for above-the-fold content */
    body {
      margin: 0;
      padding: 0;
      font-family: Inter, system-ui, -apple-system, sans-serif;
      background-color: #111827;
      color: #f9fafb;
    }
    
    /* Loading state */
    .loading-container {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background-color: #111827;
    }
    
    .loading-spinner {
      width: 32px;
      height: 32px;
      border: 2px solid #374151;
      border-top: 2px solid #3b82f6;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    
    /* Header critical styles */
    .header {
      background-color: #1f2937;
      border-bottom: 1px solid #374151;
    }
    
    /* Navigation critical styles */
    .nav {
      background-color: #111827;
    }
  `;

  const style = document.createElement('style');
  style.textContent = criticalCSS;
  document.head.insertBefore(style, document.head.firstChild);
};

// Bundle analyzer helper (development only)
export const analyzeBundleSize = () => {
  if (process.env.NODE_ENV !== 'development') return;

  console.group('📦 Bundle Analysis');
  
  // Estimate component sizes
  const estimateComponentSize = (name: string, element: any) => {
    try {
      const stringified = JSON.stringify(element);
      return stringified.length;
    } catch {
      return 0;
    }
  };

  // Performance resource timing
  const resources = performance.getEntriesByType('resource');
  const jsResources = resources.filter(resource => resource.name.includes('.js'));
  
  console.table(jsResources.map(resource => ({
    name: resource.name.split('/').pop(),
    size: `${((resource as any).transferSize / 1024).toFixed(1)}KB`,
    loadTime: `${(resource.duration).toFixed(1)}ms`
  })));

  console.groupEnd();
};

// Webpack configuration helpers (for build-time optimization)
export const getWebpackOptimizationConfig = () => {
  return {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // Vendor chunk
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          chunks: 'all',
          priority: 10
        },
        // Trading-specific chunk
        trading: {
          test: /[\\/]src[\\/](pages|components)[\\/]trading[\\/]/,
          name: 'trading',
          chunks: 'all',
          priority: 20
        },
        // Charts chunk (heavy dependencies)
        charts: {
          test: /[\\/]node_modules[\\/](chart\.js|react-chartjs-2)[\\/]/,
          name: 'charts',
          chunks: 'all',
          priority: 30
        },
        // Common utilities
        utils: {
          test: /[\\/]src[\\/](utils|hooks|services)[\\/]/,
          name: 'utils',
          chunks: 'all',
          minChunks: 2,
          priority: 5
        }
      }
    },
    runtimeChunk: {
      name: 'runtime'
    }
  };
};

// Initialize all optimizations
export const initializeBundleOptimizations = () => {
  // Add resource hints
  addResourceHints();
  
  // Optimize font loading
  optimizeFontLoading();
  
  // Inline critical CSS
  inlineCriticalCSS();
  
  // Preload critical chunks
  preloadCriticalChunks();
  
  // Register service worker
  registerServiceWorker();
  
  // Bundle analysis in development
  if (process.env.NODE_ENV === 'development') {
    setTimeout(analyzeBundleSize, 2000);
  }

  console.log('🚀 Bundle optimizations initialized');
};