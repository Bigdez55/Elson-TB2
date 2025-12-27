import { useEffect, useRef, useCallback } from 'react';
import { performanceManager } from '../utils/performance';

/**
 * Hook for monitoring React component performance
 */
export const useComponentPerformance = (componentName: string) => {
  const renderStartRef = useRef<number>(0);
  const endRenderRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    // Start profiling on component mount
    renderStartRef.current = performance.now();
    endRenderRef.current = performanceManager.componentProfiler.startRender(componentName);

    return () => {
      // End profiling on component unmount
      if (endRenderRef.current) {
        endRenderRef.current();
      }
    };
  }, [componentName]);

  const startRender = useCallback(() => {
    endRenderRef.current = performanceManager.componentProfiler.startRender(componentName);
  }, [componentName]);

  const endRender = useCallback(() => {
    if (endRenderRef.current) {
      endRenderRef.current();
      endRenderRef.current = null;
    }
  }, []);

  return { startRender, endRender };
};

/**
 * Hook for monitoring API call performance
 */
export const useAPIPerformance = () => {
  const trackAPICall = useCallback(async <T>(
    endpoint: string,
    apiCall: () => Promise<T>
  ): Promise<T> => {
    return performanceManager.apiTracker.trackAPICall(endpoint, apiCall);
  }, []);

  return { trackAPICall };
};

/**
 * Hook for monitoring memory usage
 */
export const useMemoryMonitoring = (enabled = true) => {
  useEffect(() => {
    if (!enabled) return;

    performanceManager.memoryMonitor.startMonitoring();

    return () => {
      performanceManager.memoryMonitor.stopMonitoring();
    };
  }, [enabled]);

  const getMemoryStats = useCallback(() => {
    return performanceManager.memoryMonitor.getMemoryStats();
  }, []);

  return { getMemoryStats };
};

/**
 * Hook for monitoring WebSocket performance
 */
export const useWebSocketPerformance = () => {
  const onConnect = useCallback(() => {
    performanceManager.websocketTracker.onConnect();
  }, []);

  const onDisconnect = useCallback(() => {
    performanceManager.websocketTracker.onDisconnect();
  }, []);

  const measureLatency = useCallback(() => {
    performanceManager.websocketTracker.measureLatency();
  }, []);

  const getLatencyStats = useCallback(() => {
    return performanceManager.websocketTracker.getLatencyStats();
  }, []);

  return { onConnect, onDisconnect, measureLatency, getLatencyStats };
};

/**
 * Hook for overall performance monitoring
 */
export const usePerformanceMonitoring = (options: {
  trackComponents?: boolean;
  trackMemory?: boolean;
  trackWebSockets?: boolean;
  reportInterval?: number;
} = {}) => {
  const {
    trackComponents = true,
    trackMemory = true,
    trackWebSockets = true,
    reportInterval = 60000 // 1 minute
  } = options;

  const reportIntervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Initialize performance monitoring
    performanceManager.initialize();

    // Set up periodic reporting
    if (reportInterval > 0) {
      reportIntervalRef.current = setInterval(() => {
        const report = performanceManager.generateReport();
        console.log('📊 Performance Report:', report);
        
        // Send to analytics if in production
        if (process.env.NODE_ENV === 'production' && (window as any).gtag) {
          (window as any).gtag('event', 'performance_report', {
            component_render_time: report.componentRenderTime,
            api_response_time: report.apiResponseTime,
            websocket_latency: report.websocketLatency,
            memory_usage_mb: report.memoryUsage,
            bundle_size_mb: report.bundleSize,
            time_to_interactive: report.timeToInteractive,
            custom_map: {
              performance_monitoring: true
            }
          });
        }
      }, reportInterval);
    }

    return () => {
      if (reportIntervalRef.current) {
        clearInterval(reportIntervalRef.current);
      }
      performanceManager.cleanup();
    };
  }, [reportInterval]);

  const generateReport = useCallback(() => {
    return performanceManager.generateReport();
  }, []);

  const getComponentStats = useCallback((componentName: string) => {
    return performanceManager.componentProfiler.getComponentStats(componentName);
  }, []);

  const getAPIStats = useCallback((endpoint: string) => {
    return performanceManager.apiTracker.getAPIStats(endpoint);
  }, []);

  return {
    generateReport,
    getComponentStats,
    getAPIStats,
    performanceManager
  };
};

/**
 * Hook for performance-aware lazy loading
 */
export const usePerformantLazyLoading = <T>(
  loader: () => Promise<T>,
  options: {
    threshold?: number;
    rootMargin?: string;
    onVisible?: () => void;
  } = {}
) => {
  const { threshold = 0.1, rootMargin = '50px', onVisible } = options;
  const elementRef = useRef<HTMLElement>(null);
  const isLoadedRef = useRef(false);
  const componentRef = useRef<T | null>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element || isLoadedRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && !isLoadedRef.current) {
          isLoadedRef.current = true;
          
          const loadStart = performance.now();
          loader().then((component) => {
            const loadTime = performance.now() - loadStart;
            componentRef.current = component;
            
            console.log(`📦 Lazy loaded component in ${loadTime.toFixed(2)}ms`);
            
            if (onVisible) {
              onVisible();
            }
          });
          
          observer.unobserve(element);
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [loader, threshold, rootMargin, onVisible]);

  return { elementRef, component: componentRef.current };
};

/**
 * Hook for debouncing expensive operations with performance tracking
 */
export const usePerformantDebounce = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number,
  trackingName?: string
): T => {
  const timeoutRef = useRef<NodeJS.Timeout>();
  const performanceStartRef = useRef<number>(0);

  const debouncedCallback = useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    performanceStartRef.current = performance.now();

    timeoutRef.current = setTimeout(() => {
      const executeStart = performance.now();
      const result = callback(...args);
      const executeTime = performance.now() - executeStart;
      const totalTime = performance.now() - performanceStartRef.current;

      if (trackingName) {
        console.log(
          `⏱️ ${trackingName}: debounced=${totalTime.toFixed(2)}ms, execution=${executeTime.toFixed(2)}ms`
        );
      }

      return result;
    }, delay);
  }, [callback, delay, trackingName]) as T;

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
};

/**
 * Hook for throttling high-frequency operations with performance tracking
 */
export const usePerformantThrottle = <T extends (...args: any[]) => any>(
  callback: T,
  limit: number,
  trackingName?: string
): T => {
  const inThrottleRef = useRef(false);
  const lastCallRef = useRef<number>(0);

  const throttledCallback = useCallback((...args: Parameters<T>) => {
    if (!inThrottleRef.current) {
      const executeStart = performance.now();
      const result = callback(...args);
      const executeTime = performance.now() - executeStart;
      const timeSinceLastCall = executeStart - lastCallRef.current;

      if (trackingName) {
        console.log(
          `🚦 ${trackingName}: execution=${executeTime.toFixed(2)}ms, interval=${timeSinceLastCall.toFixed(2)}ms`
        );
      }

      lastCallRef.current = executeStart;
      inThrottleRef.current = true;

      setTimeout(() => {
        inThrottleRef.current = false;
      }, limit);

      return result;
    }
  }, [callback, limit, trackingName]) as T;

  return throttledCallback;
};