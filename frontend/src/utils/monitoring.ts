/**
 * Production monitoring and analytics configuration
 */

// Error tracking configuration
export interface ErrorTrackingConfig {
  dsn: string;
  environment: string;
  sampleRate: number;
  beforeSend?: (event: any) => any | null;
}

// Analytics configuration
export interface AnalyticsConfig {
  trackingId: string;
  anonymizeIp: boolean;
  cookieFlags: string;
  customDimensions: Record<string, string>;
}

// Monitoring service implementation
export class MonitoringService {
  private isInitialized = false;
  private errorTrackingEnabled = false;
  private analyticsEnabled = false;

  constructor(
    private errorConfig?: ErrorTrackingConfig,
    private analyticsConfig?: AnalyticsConfig
  ) {}

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    console.log('🔍 Initializing monitoring services...');

    try {
      // Initialize error tracking (Sentry)
      if (this.errorConfig) {
        await this.initializeErrorTracking();
      }

      // Initialize analytics (Google Analytics)
      if (this.analyticsConfig) {
        await this.initializeAnalytics();
      }

      // Initialize performance monitoring
      this.initializePerformanceMonitoring();

      // Initialize user feedback collection
      this.initializeUserFeedback();

      this.isInitialized = true;
      console.log('✅ Monitoring services initialized');

    } catch (error) {
      console.error('❌ Failed to initialize monitoring:', error);
    }
  }

  private async initializeErrorTracking(): Promise<void> {
    if (!this.errorConfig || process.env.NODE_ENV !== 'production') {
      return;
    }

    try {
      // Dynamically import Sentry to avoid bundling in development
      // Note: Install @sentry/react package for production use
      // const { init, configureScope } = await import('@sentry/react');
      
      // init({
      //   dsn: this.errorConfig.dsn,
      //   environment: this.errorConfig.environment,
      //   sampleRate: this.errorConfig.sampleRate,
      //   beforeSend: this.errorConfig.beforeSend || this.filterSensitiveData,
      //   integrations: [
      //     // Add performance monitoring
      //   ]
      // });

      // // Configure user context
      // configureScope((scope) => {
      //   scope.setTag('component', 'trading-frontend');
      // });

      this.errorTrackingEnabled = true;
      console.log('📊 Error tracking initialized (stub)');

    } catch (error) {
      console.warn('Failed to initialize error tracking:', error);
    }
  }

  private async initializeAnalytics(): Promise<void> {
    if (!this.analyticsConfig || process.env.NODE_ENV !== 'production') {
      return;
    }

    try {
      // Load Google Analytics
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${this.analyticsConfig.trackingId}`;
      document.head.appendChild(script);

      // Initialize gtag
      (window as any).dataLayer = (window as any).dataLayer || [];
      const gtag = (...args: any[]) => {
        (window as any).dataLayer.push(args);
      };

      gtag('js', new Date());
      gtag('config', this.analyticsConfig.trackingId, {
        anonymize_ip: this.analyticsConfig.anonymizeIp,
        cookie_flags: this.analyticsConfig.cookieFlags,
        custom_map: this.analyticsConfig.customDimensions
      });

      // Store gtag globally
      (window as any).gtag = gtag;

      this.analyticsEnabled = true;
      console.log('📈 Analytics initialized');

    } catch (error) {
      console.warn('Failed to initialize analytics:', error);
    }
  }

  private initializePerformanceMonitoring(): void {
    // Monitor Core Web Vitals
    if (typeof PerformanceObserver !== 'undefined') {
      try {
        // Cumulative Layout Shift (CLS)
        new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              this.trackMetric('CLS', (entry as any).value);
            }
          }
        }).observe({ entryTypes: ['layout-shift'] });

        // First Contentful Paint (FCP)
        new PerformanceObserver((entryList) => {
          for (const entry of entryList.getEntries()) {
            this.trackMetric('FCP', entry.startTime);
          }
        }).observe({ entryTypes: ['paint'] });

        console.log('📊 Performance monitoring active');

      } catch (error) {
        console.warn('Performance monitoring not supported:', error);
      }
    }
  }

  private initializeUserFeedback(): void {
    // Add global error handler
    window.addEventListener('error', (event) => {
      this.trackError(event.error, {
        type: 'javascript_error',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
    });

    // Add unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.trackError(event.reason, {
        type: 'unhandled_promise_rejection'
      });
    });

    console.log('🛡️ Error handlers initialized');
  }

  // Public methods for tracking
  trackEvent(eventName: string, parameters?: Record<string, any>): void {
    if (this.analyticsEnabled && (window as any).gtag) {
      (window as any).gtag('event', eventName, parameters);
    }

    console.log(`📊 Event: ${eventName}`, parameters);
  }

  trackError(error: Error, context?: Record<string, any>): void {
    if (this.errorTrackingEnabled) {
      // Sentry will handle this automatically, but we can add context
      console.error('🚨 Error tracked:', error, context);
    } else {
      console.error('🚨 Error:', error, context);
    }
  }

  trackMetric(metricName: string, value: number, unit?: string): void {
    if (this.analyticsEnabled && (window as any).gtag) {
      (window as any).gtag('event', 'performance_metric', {
        metric_name: metricName,
        metric_value: value,
        metric_unit: unit || 'ms'
      });
    }

    console.log(`📏 Metric: ${metricName} = ${value}${unit || 'ms'}`);
  }

  trackUserAction(action: string, category: string, details?: any): void {
    this.trackEvent('user_action', {
      action_name: action,
      action_category: category,
      action_details: JSON.stringify(details)
    });
  }

  trackPageView(pageName: string, additionalData?: Record<string, any>): void {
    if (this.analyticsEnabled && (window as any).gtag) {
      (window as any).gtag('event', 'page_view', {
        page_title: pageName,
        page_location: window.location.href,
        ...additionalData
      });
    }
  }

  trackConversion(conversionId: string, value?: number): void {
    if (this.analyticsEnabled && (window as any).gtag) {
      (window as any).gtag('event', 'conversion', {
        send_to: conversionId,
        value: value
      });
    }
  }

  // Helper methods
  private filterSensitiveData = (event: any): any | null => {
    // Remove sensitive data from error reports
    if (event.request?.data) {
      const data = event.request.data;
      
      // Remove auth tokens
      delete data.token;
      delete data.password;
      delete data.api_key;
      
      // Remove PII
      if (data.user) {
        delete data.user.ssn;
        delete data.user.account_number;
      }
    }

    // Filter out known non-critical errors
    if (event.exception?.values) {
      const errorMessages = event.exception.values.map((v: any) => v.value);
      
      const ignoredErrors = [
        'ResizeObserver loop limit exceeded',
        'Script error',
        'Network request failed',
        'Non-Error promise rejection captured'
      ];

      if (errorMessages.some((msg: string) => 
        ignoredErrors.some(ignored => msg?.includes(ignored))
      )) {
        return null; // Don't send these errors
      }
    }

    return event;
  };

  setUserContext(userId: string, userType: string, additionalData?: Record<string, any>): void {
    if (this.errorTrackingEnabled) {
      // Set user context for error tracking
      if ((window as any).Sentry) {
        (window as any).Sentry.configureScope((scope: any) => {
          scope.setUser({
            id: userId,
            type: userType,
            ...additionalData
          });
        });
      }
    }

    if (this.analyticsEnabled && (window as any).gtag) {
      (window as any).gtag('set', {
        user_id: userId,
        custom_map: {
          user_type: userType,
          ...additionalData
        }
      });
    }
  }

  clearUserContext(): void {
    if (this.errorTrackingEnabled && (window as any).Sentry) {
      (window as any).Sentry.configureScope((scope: any) => {
        scope.clear();
      });
    }

    if (this.analyticsEnabled && (window as any).gtag) {
      (window as any).gtag('set', {
        user_id: null
      });
    }
  }
}

// Create singleton instance
const monitoringService = new MonitoringService(
  // Error tracking config (Sentry)
  process.env.NODE_ENV === 'production' ? {
    dsn: process.env.REACT_APP_SENTRY_DSN || '',
    environment: process.env.REACT_APP_ENVIRONMENT || 'production',
    sampleRate: 0.1, // 10% sampling
  } : undefined,
  
  // Analytics config (Google Analytics)
  process.env.NODE_ENV === 'production' ? {
    trackingId: process.env.REACT_APP_GA_TRACKING_ID || '',
    anonymizeIp: true,
    cookieFlags: 'secure;samesite=strict',
    customDimensions: {
      app_version: process.env.REACT_APP_VERSION || '1.0.0',
      user_type: 'trader'
    }
  } : undefined
);

export { monitoringService };

// Hook for React components
export const useMonitoring = () => {
  return {
    trackEvent: monitoringService.trackEvent.bind(monitoringService),
    trackError: monitoringService.trackError.bind(monitoringService),
    trackMetric: monitoringService.trackMetric.bind(monitoringService),
    trackUserAction: monitoringService.trackUserAction.bind(monitoringService),
    trackPageView: monitoringService.trackPageView.bind(monitoringService),
    setUserContext: monitoringService.setUserContext.bind(monitoringService),
    clearUserContext: monitoringService.clearUserContext.bind(monitoringService)
  };
};

// Trading-specific tracking helpers
export const tradingMetrics = {
  trackOrderPlacement: (orderData: any) => {
    monitoringService.trackEvent('order_placed', {
      symbol: orderData.symbol,
      order_type: orderData.order_type,
      side: orderData.side,
      mode: orderData.mode,
      estimated_value: orderData.estimated_cost
    });
  },

  trackOrderExecution: (orderResult: any, executionTime: number) => {
    monitoringService.trackEvent('order_executed', {
      order_id: orderResult.order_id,
      status: orderResult.status,
      execution_time: executionTime
    });
    
    monitoringService.trackMetric('order_execution_time', executionTime);
  },

  trackMarketDataLatency: (symbol: string, latency: number) => {
    monitoringService.trackMetric('market_data_latency', latency);
  },

  trackWebSocketReconnection: (reason: string, downtime: number) => {
    monitoringService.trackEvent('websocket_reconnection', {
      reason,
      downtime
    });
  },

  trackRiskViolation: (violationType: string, orderData: any) => {
    monitoringService.trackEvent('risk_violation', {
      violation_type: violationType,
      symbol: orderData.symbol,
      order_value: orderData.estimated_cost
    });
  }
};

// Initialize monitoring when module is loaded
if (process.env.NODE_ENV === 'production') {
  monitoringService.initialize();
}