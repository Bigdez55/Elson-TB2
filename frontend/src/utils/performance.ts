/**
 * Performance utilities for production monitoring and optimization
 */

// Performance metrics tracking
export interface PerformanceMetrics {
  componentRenderTime: number;
  apiResponseTime: number;
  websocketLatency: number;
  memoryUsage: number;
  bundleSize: number;
  timeToInteractive: number;
}

// Performance thresholds
export const PERFORMANCE_THRESHOLDS = {
  COMPONENT_RENDER_MAX: 16, // 60fps = 16ms per frame
  API_RESPONSE_WARNING: 1000, // 1 second
  API_RESPONSE_CRITICAL: 3000, // 3 seconds
  WEBSOCKET_LATENCY_MAX: 100, // 100ms
  MEMORY_WARNING_MB: 50,
  MEMORY_CRITICAL_MB: 100,
  BUNDLE_SIZE_WARNING_MB: 2,
  BUNDLE_SIZE_CRITICAL_MB: 5,
  TIME_TO_INTERACTIVE_TARGET: 3000, // 3 seconds
};

// Component performance profiler
export class ComponentProfiler {
  private renderTimes: Map<string, number[]> = new Map();
  private isProduction = process.env.NODE_ENV === 'production';

  startRender(componentName: string): () => void {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      this.recordRenderTime(componentName, renderTime);
      
      if (renderTime > PERFORMANCE_THRESHOLDS.COMPONENT_RENDER_MAX) {
        console.warn(
          `🐌 Slow render detected: ${componentName} took ${renderTime.toFixed(2)}ms`
        );
        
        if (this.isProduction) {
          this.reportSlowRender(componentName, renderTime);
        }
      }
    };
  }

  private recordRenderTime(componentName: string, renderTime: number): void {
    if (!this.renderTimes.has(componentName)) {
      this.renderTimes.set(componentName, []);
    }
    
    const times = this.renderTimes.get(componentName)!;
    times.push(renderTime);
    
    // Keep only last 100 measurements
    if (times.length > 100) {
      times.shift();
    }
  }

  private reportSlowRender(componentName: string, renderTime: number): void {
    // Send to monitoring service
    if ((window as any).gtag) {
      (window as any).gtag('event', 'slow_component_render', {
        component_name: componentName,
        render_time: renderTime,
        custom_map: {
          performance_issue: true
        }
      });
    }
  }

  getComponentStats(componentName: string) {
    const times = this.renderTimes.get(componentName) || [];
    if (times.length === 0) return null;

    const avg = times.reduce((sum, time) => sum + time, 0) / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);
    const p95 = times.sort((a, b) => a - b)[Math.floor(times.length * 0.95)];

    return {
      average: avg,
      minimum: min,
      maximum: max,
      p95,
      sampleCount: times.length
    };
  }

  getAllStats() {
    const stats: Record<string, any> = {};
    const componentNames = Array.from(this.renderTimes.keys());
    componentNames.forEach(componentName => {
      stats[componentName] = this.getComponentStats(componentName);
    });
    return stats;
  }
}

// API performance tracker
export class APIPerformanceTracker {
  private apiTimes: Map<string, number[]> = new Map();
  private isProduction = process.env.NODE_ENV === 'production';

  async trackAPICall<T>(
    endpoint: string,
    apiCall: () => Promise<T>
  ): Promise<T> {
    const startTime = performance.now();
    
    try {
      const result = await apiCall();
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      this.recordAPITime(endpoint, responseTime);
      this.checkAPIPerformance(endpoint, responseTime);
      
      return result;
    } catch (error) {
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      this.recordAPITime(endpoint, responseTime, true);
      throw error;
    }
  }

  private recordAPITime(endpoint: string, responseTime: number, error = false): void {
    const key = `${endpoint}${error ? '_error' : ''}`;
    
    if (!this.apiTimes.has(key)) {
      this.apiTimes.set(key, []);
    }
    
    const times = this.apiTimes.get(key)!;
    times.push(responseTime);
    
    // Keep only last 50 measurements per endpoint
    if (times.length > 50) {
      times.shift();
    }
  }

  private checkAPIPerformance(endpoint: string, responseTime: number): void {
    if (responseTime > PERFORMANCE_THRESHOLDS.API_RESPONSE_CRITICAL) {
      console.error(
        `🚨 Critical API slowness: ${endpoint} took ${responseTime.toFixed(2)}ms`
      );
      
      if (this.isProduction) {
        this.reportSlowAPI(endpoint, responseTime, 'critical');
      }
    } else if (responseTime > PERFORMANCE_THRESHOLDS.API_RESPONSE_WARNING) {
      console.warn(
        `⚠️ Slow API response: ${endpoint} took ${responseTime.toFixed(2)}ms`
      );
      
      if (this.isProduction) {
        this.reportSlowAPI(endpoint, responseTime, 'warning');
      }
    }
  }

  private reportSlowAPI(endpoint: string, responseTime: number, severity: string): void {
    if ((window as any).gtag) {
      (window as any).gtag('event', 'slow_api_response', {
        endpoint,
        response_time: responseTime,
        severity,
        custom_map: {
          performance_issue: true
        }
      });
    }
  }

  getAPIStats(endpoint: string) {
    const times = this.apiTimes.get(endpoint) || [];
    const errorTimes = this.apiTimes.get(`${endpoint}_error`) || [];
    
    if (times.length === 0) return null;

    const avg = times.reduce((sum, time) => sum + time, 0) / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);
    
    return {
      average: avg,
      minimum: min,
      maximum: max,
      successCount: times.length,
      errorCount: errorTimes.length,
      errorRate: errorTimes.length / (times.length + errorTimes.length)
    };
  }
}

// WebSocket latency tracker
export class WebSocketPerformanceTracker {
  private latencyMeasurements: number[] = [];
  private connectionUptime: number = 0;
  private connectionStart: number = 0;
  private disconnections: number = 0;

  onConnect(): void {
    this.connectionStart = performance.now();
  }

  onDisconnect(): void {
    if (this.connectionStart > 0) {
      this.connectionUptime += performance.now() - this.connectionStart;
      this.disconnections++;
    }
  }

  measureLatency(): void {
    const pingStart = performance.now();
    
    // Send ping message and measure response
    // This would be integrated with actual WebSocket ping/pong
    setTimeout(() => {
      const latency = performance.now() - pingStart;
      this.recordLatency(latency);
    }, 0);
  }

  private recordLatency(latency: number): void {
    this.latencyMeasurements.push(latency);
    
    // Keep only last 100 measurements
    if (this.latencyMeasurements.length > 100) {
      this.latencyMeasurements.shift();
    }

    if (latency > PERFORMANCE_THRESHOLDS.WEBSOCKET_LATENCY_MAX) {
      console.warn(`📡 High WebSocket latency: ${latency.toFixed(2)}ms`);
    }
  }

  getLatencyStats() {
    if (this.latencyMeasurements.length === 0) return null;

    const avg = this.latencyMeasurements.reduce((sum, lat) => sum + lat, 0) / this.latencyMeasurements.length;
    const min = Math.min(...this.latencyMeasurements);
    const max = Math.max(...this.latencyMeasurements);
    
    return {
      average: avg,
      minimum: min,
      maximum: max,
      sampleCount: this.latencyMeasurements.length,
      uptime: this.connectionUptime,
      disconnections: this.disconnections
    };
  }
}

// Memory usage monitor
export class MemoryMonitor {
  private measurements: Array<{ timestamp: number; usage: number }> = [];
  private isMonitoring = false;
  private monitoringInterval?: NodeJS.Timeout;

  startMonitoring(intervalMs = 5000): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.monitoringInterval = setInterval(() => {
      this.recordMemoryUsage();
    }, intervalMs);
  }

  stopMonitoring(): void {
    this.isMonitoring = false;
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }
  }

  private recordMemoryUsage(): void {
    const performanceMemory = (performance as any).memory;
    if (!performanceMemory) return;

    const usage = performanceMemory.usedJSHeapSize / (1024 * 1024); // Convert to MB
    const timestamp = Date.now();

    this.measurements.push({ timestamp, usage });

    // Keep only last 100 measurements
    if (this.measurements.length > 100) {
      this.measurements.shift();
    }

    if (usage > PERFORMANCE_THRESHOLDS.MEMORY_CRITICAL_MB) {
      console.error(`🧠 Critical memory usage: ${usage.toFixed(2)}MB`);
      this.reportMemoryIssue(usage, 'critical');
    } else if (usage > PERFORMANCE_THRESHOLDS.MEMORY_WARNING_MB) {
      console.warn(`🧠 High memory usage: ${usage.toFixed(2)}MB`);
      this.reportMemoryIssue(usage, 'warning');
    }
  }

  private reportMemoryIssue(usage: number, severity: string): void {
    if ((window as any).gtag && process.env.NODE_ENV === 'production') {
      (window as any).gtag('event', 'high_memory_usage', {
        memory_usage_mb: usage,
        severity,
        custom_map: {
          performance_issue: true
        }
      });
    }
  }

  getMemoryStats() {
    if (this.measurements.length === 0) return null;

    const usages = this.measurements.map(m => m.usage);
    const avg = usages.reduce((sum, usage) => sum + usage, 0) / usages.length;
    const max = Math.max(...usages);
    const current = usages[usages.length - 1];

    return {
      current,
      average: avg,
      maximum: max,
      trend: this.calculateTrend(),
      measurements: this.measurements.length
    };
  }

  private calculateTrend(): 'increasing' | 'decreasing' | 'stable' {
    if (this.measurements.length < 10) return 'stable';

    const recent = this.measurements.slice(-5).map(m => m.usage);
    const earlier = this.measurements.slice(-10, -5).map(m => m.usage);

    const recentAvg = recent.reduce((sum, usage) => sum + usage, 0) / recent.length;
    const earlierAvg = earlier.reduce((sum, usage) => sum + usage, 0) / earlier.length;

    const threshold = 0.5; // MB
    if (recentAvg - earlierAvg > threshold) return 'increasing';
    if (earlierAvg - recentAvg > threshold) return 'decreasing';
    return 'stable';
  }
}

// Global performance manager
export class PerformanceManager {
  public componentProfiler = new ComponentProfiler();
  public apiTracker = new APIPerformanceTracker();
  public websocketTracker = new WebSocketPerformanceTracker();
  public memoryMonitor = new MemoryMonitor();

  private vitalsObserver?: PerformanceObserver;

  initialize(): void {
    // Start memory monitoring
    this.memoryMonitor.startMonitoring();

    // Monitor Core Web Vitals
    this.setupWebVitalsMonitoring();

    // Monitor long tasks
    this.setupLongTaskMonitoring();

    // Report initial page load metrics
    this.reportPageLoadMetrics();
  }

  private setupWebVitalsMonitoring(): void {
    if (typeof PerformanceObserver !== 'undefined') {
      try {
        // Monitor Largest Contentful Paint (LCP)
        const lcpObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const lastEntry = entries[entries.length - 1];
          
          if (lastEntry && lastEntry.startTime > 2500) {
            console.warn(`📊 Poor LCP: ${lastEntry.startTime.toFixed(2)}ms`);
          }
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

        // Monitor First Input Delay (FID)
        const fidObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          entries.forEach(entry => {
            const performanceEntry = entry as any;
            if (performanceEntry.processingStart && performanceEntry.processingStart - entry.startTime > 100) {
              console.warn(`⌨️ Poor FID: ${(performanceEntry.processingStart - entry.startTime).toFixed(2)}ms`);
            }
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });

      } catch (error) {
        console.warn('Performance Observer not supported:', error);
      }
    }
  }

  private setupLongTaskMonitoring(): void {
    if (typeof PerformanceObserver !== 'undefined') {
      try {
        const longTaskObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          entries.forEach(entry => {
            if (entry.duration > 50) {
              console.warn(`🐌 Long task detected: ${entry.duration.toFixed(2)}ms`);
              
              if (process.env.NODE_ENV === 'production' && (window as any).gtag) {
                (window as any).gtag('event', 'long_task', {
                  task_duration: entry.duration,
                  custom_map: {
                    performance_issue: true
                  }
                });
              }
            }
          });
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });
      } catch (error) {
        console.warn('Long task monitoring not supported:', error);
      }
    }
  }

  private reportPageLoadMetrics(): void {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        if (navigation) {
          const metrics = {
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
            firstPaint: this.getFirstPaint(),
            timeToInteractive: this.calculateTimeToInteractive()
          };

          console.log('📊 Page Load Metrics:', metrics);

          if (process.env.NODE_ENV === 'production' && (window as any).gtag) {
            (window as any).gtag('event', 'page_load_metrics', {
              dom_content_loaded: metrics.domContentLoaded,
              load_complete: metrics.loadComplete,
              first_paint: metrics.firstPaint,
              time_to_interactive: metrics.timeToInteractive
            });
          }
        }
      }, 0);
    });
  }

  private getFirstPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
    return firstPaint ? firstPaint.startTime : 0;
  }

  private calculateTimeToInteractive(): number {
    // Simplified TTI calculation
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return navigation ? navigation.loadEventEnd - navigation.fetchStart : 0;
  }

  // Generate performance report
  generateReport(): PerformanceMetrics {
    const componentStats = this.componentProfiler.getAllStats();
    const memoryStats = this.memoryMonitor.getMemoryStats();
    const wsStats = this.websocketTracker.getLatencyStats();

    return {
      componentRenderTime: this.getAverageRenderTime(componentStats),
      apiResponseTime: this.getAverageAPIResponseTime(),
      websocketLatency: wsStats?.average || 0,
      memoryUsage: memoryStats?.current || 0,
      bundleSize: this.estimateBundleSize(),
      timeToInteractive: this.calculateTimeToInteractive()
    };
  }

  private getAverageRenderTime(stats: Record<string, any>): number {
    const renderTimes = Object.values(stats)
      .filter(stat => stat && typeof stat.average === 'number')
      .map(stat => stat.average);
    
    return renderTimes.length > 0 
      ? renderTimes.reduce((sum, time) => sum + time, 0) / renderTimes.length
      : 0;
  }

  private getAverageAPIResponseTime(): number {
    // This would aggregate API response times across all endpoints
    return 0; // Placeholder
  }

  private estimateBundleSize(): number {
    // Estimate bundle size from resource timing
    const resources = performance.getEntriesByType('resource');
    const jsResources = resources.filter(resource => 
      resource.name.includes('.js') && !resource.name.includes('chunk')
    );
    
    return jsResources.reduce((total, resource) => {
      return total + ((resource as any).transferSize || 0);
    }, 0) / (1024 * 1024); // Convert to MB
  }

  cleanup(): void {
    this.memoryMonitor.stopMonitoring();
    if (this.vitalsObserver) {
      this.vitalsObserver.disconnect();
    }
  }
}

// Global instance
export const performanceManager = new PerformanceManager();