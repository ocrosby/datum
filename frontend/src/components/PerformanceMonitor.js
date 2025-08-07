import React, { useEffect, useState } from 'react';
import { ClockIcon, ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const PerformanceMonitor = () => {
  const [metrics, setMetrics] = useState({
    avgResponseTime: 0,
    cacheHitRate: 0,
    totalRequests: 0,
    slowRequests: 0
  });

  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Monitor API performance
    const originalFetch = window.fetch;
    let totalRequests = 0;
    let totalTime = 0;
    let slowRequests = 0;

    window.fetch = async (...args) => {
      const startTime = performance.now();
      totalRequests++;

      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        totalTime += duration;
        
        if (duration > 1000) { // Requests taking more than 1 second
          slowRequests++;
        }

        // Update metrics
        setMetrics(prev => ({
          avgResponseTime: totalTime / totalRequests,
          cacheHitRate: 0, // This would come from server metrics
          totalRequests,
          slowRequests
        }));

        return response;
      } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        totalTime += duration;
        
        if (duration > 1000) {
          slowRequests++;
        }

        setMetrics(prev => ({
          ...prev,
          avgResponseTime: totalTime / totalRequests,
          totalRequests,
          slowRequests
        }));

        throw error;
      }
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  const getPerformanceColor = (avgTime) => {
    if (avgTime < 200) return 'text-success-600';
    if (avgTime < 500) return 'text-warning-600';
    return 'text-danger-600';
  };

  const getPerformanceStatus = (avgTime) => {
    if (avgTime < 200) return 'Excellent';
    if (avgTime < 500) return 'Good';
    if (avgTime < 1000) return 'Fair';
    return 'Poor';
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 bg-primary-600 text-white p-2 rounded-full shadow-lg hover:bg-primary-700 transition-colors"
        title="Performance Monitor"
      >
        <ChartBarIcon className="w-5 h-5" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 w-80 z-50">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">Performance Monitor</h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ClockIcon className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Avg Response Time</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`text-sm font-medium ${getPerformanceColor(metrics.avgResponseTime)}`}>
              {metrics.avgResponseTime.toFixed(0)}ms
            </span>
            <span className="text-xs text-gray-500">
              ({getPerformanceStatus(metrics.avgResponseTime)})
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Total Requests</span>
          <span className="text-sm font-medium text-gray-900">
            {metrics.totalRequests}
          </span>
        </div>

        {metrics.slowRequests > 0 && (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="w-4 h-4 text-warning-500" />
              <span className="text-sm text-gray-600">Slow Requests</span>
            </div>
            <span className="text-sm font-medium text-warning-600">
              {metrics.slowRequests}
            </span>
          </div>
        )}

        <div className="pt-2 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            <div>• Green: &lt;200ms (Excellent)</div>
            <div>• Yellow: 200-500ms (Good)</div>
            <div>• Orange: 500-1000ms (Fair)</div>
            <div>• Red: &gt;1000ms (Poor)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMonitor; 