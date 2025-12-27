import React, { useState, useEffect } from 'react';
import { usePerformanceMonitoring } from '../../hooks/usePerformanceMonitoring';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface PerformanceDashboardProps {
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  className = '',
  autoRefresh = true,
  refreshInterval = 5000
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [metrics, setMetrics] = useState<any>(null);
  const { generateReport, getComponentStats, getAPIStats } = usePerformanceMonitoring();

  useEffect(() => {
    if (autoRefresh && isVisible) {
      const updateMetrics = () => {
        setMetrics(generateReport());
      };

      updateMetrics();
      const interval = setInterval(updateMetrics, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, isVisible, refreshInterval, generateReport]);

  const refreshMetrics = () => {
    setMetrics(generateReport());
  };

  const getPerformanceStatus = (value: number, thresholds: { good: number; poor: number }) => {
    if (value <= thresholds.good) return { status: 'good', color: 'success' };
    if (value <= thresholds.poor) return { status: 'warning', color: 'warning' };
    return { status: 'poor', color: 'error' };
  };

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  if (!isVisible) {
    return (
      <div className={`fixed bottom-4 right-4 ${className}`}>
        <Button
          onClick={() => setIsVisible(true)}
          variant="outline"
          size="sm"
          className="bg-gray-800 border-gray-600 text-gray-300 hover:bg-gray-700"
        >
          📊 Performance
        </Button>
      </div>
    );
  }

  return (
    <div className={`fixed bottom-4 right-4 w-96 max-h-96 overflow-y-auto z-50 ${className}`}>
      <Card className="bg-gray-900 border-gray-700">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center">
              📊 Performance Monitor
              {autoRefresh && (
                <div className="ml-2 w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              )}
            </h3>
            <div className="flex space-x-2">
              <button
                onClick={refreshMetrics}
                className="text-gray-400 hover:text-white p-1 rounded"
                title="Refresh metrics"
              >
                🔄
              </button>
              <button
                onClick={() => setIsVisible(false)}
                className="text-gray-400 hover:text-white p-1 rounded"
                title="Close dashboard"
              >
                ✕
              </button>
            </div>
          </div>

          {metrics && (
            <div className="space-y-3">
              {/* Core Web Vitals */}
              <div>
                <h4 className="text-sm font-medium text-gray-300 mb-2">Core Web Vitals</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gray-800 rounded p-2">
                    <div className="text-gray-400">Component Render</div>
                    <div className="flex items-center space-x-2">
                      <span className="text-white font-medium">
                        {formatTime(metrics.componentRenderTime)}
                      </span>
                      <Badge
                        variant={getPerformanceStatus(metrics.componentRenderTime, { good: 16, poor: 50 }).color as any}
                        size="sm"
                      >
                        {getPerformanceStatus(metrics.componentRenderTime, { good: 16, poor: 50 }).status}
                      </Badge>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded p-2">
                    <div className="text-gray-400">API Response</div>
                    <div className="flex items-center space-x-2">
                      <span className="text-white font-medium">
                        {formatTime(metrics.apiResponseTime)}
                      </span>
                      <Badge
                        variant={getPerformanceStatus(metrics.apiResponseTime, { good: 500, poor: 1000 }).color as any}
                        size="sm"
                      >
                        {getPerformanceStatus(metrics.apiResponseTime, { good: 500, poor: 1000 }).status}
                      </Badge>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded p-2">
                    <div className="text-gray-400">WebSocket Latency</div>
                    <div className="flex items-center space-x-2">
                      <span className="text-white font-medium">
                        {formatTime(metrics.websocketLatency)}
                      </span>
                      <Badge
                        variant={getPerformanceStatus(metrics.websocketLatency, { good: 50, poor: 100 }).color as any}
                        size="sm"
                      >
                        {getPerformanceStatus(metrics.websocketLatency, { good: 50, poor: 100 }).status}
                      </Badge>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded p-2">
                    <div className="text-gray-400">Memory Usage</div>
                    <div className="flex items-center space-x-2">
                      <span className="text-white font-medium">
                        {metrics.memoryUsage.toFixed(1)}MB
                      </span>
                      <Badge
                        variant={getPerformanceStatus(metrics.memoryUsage, { good: 25, poor: 50 }).color as any}
                        size="sm"
                      >
                        {getPerformanceStatus(metrics.memoryUsage, { good: 25, poor: 50 }).status}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>

              {/* Additional Metrics */}
              <div>
                <h4 className="text-sm font-medium text-gray-300 mb-2">Resource Metrics</h4>
                <div className="bg-gray-800 rounded p-2 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Bundle Size:</span>
                    <span className="text-white">{formatSize(metrics.bundleSize * 1024 * 1024)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Time to Interactive:</span>
                    <span className="text-white">{formatTime(metrics.timeToInteractive)}</span>
                  </div>
                </div>
              </div>

              {/* Performance Issues Warning */}
              {(metrics.componentRenderTime > 50 || 
                metrics.apiResponseTime > 1000 || 
                metrics.memoryUsage > 50) && (
                <div className="bg-yellow-900/20 border border-yellow-600 rounded p-2">
                  <div className="text-yellow-400 text-xs font-medium mb-1">
                    ⚠️ Performance Issues Detected
                  </div>
                  <div className="text-yellow-300 text-xs space-y-1">
                    {metrics.componentRenderTime > 50 && (
                      <div>• Slow component rendering detected</div>
                    )}
                    {metrics.apiResponseTime > 1000 && (
                      <div>• API response times are high</div>
                    )}
                    {metrics.memoryUsage > 50 && (
                      <div>• Memory usage is elevated</div>
                    )}
                  </div>
                </div>
              )}

              {/* Controls */}
              <div className="flex justify-between items-center pt-2 border-t border-gray-700">
                <div className="text-xs text-gray-500">
                  Last updated: {new Date().toLocaleTimeString()}
                </div>
                <div className="flex space-x-2">
                  <Button
                    onClick={() => {
                      const report = generateReport();
                      console.log('📊 Full Performance Report:', report);
                      
                      // Copy to clipboard for sharing
                      navigator.clipboard.writeText(JSON.stringify(report, null, 2));
                    }}
                    variant="outline"
                    size="sm"
                    className="text-xs text-gray-400 hover:text-white"
                  >
                    Copy Report
                  </Button>
                </div>
              </div>
            </div>
          )}

          {!metrics && (
            <div className="text-center text-gray-400 py-8">
              <div className="text-2xl mb-2">📊</div>
              <div className="text-sm">Click refresh to load metrics</div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default PerformanceDashboard;