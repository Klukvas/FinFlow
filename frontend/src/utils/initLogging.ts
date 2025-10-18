/**
 * Frontend Logging Initialization
 * 
 * This file initializes the frontend logging system and should be imported
 * early in the application lifecycle.
 */

import { frontendLogger } from './logging';
import './apiLogger'; // Import to set up API interceptors

// Initialize logging system
export const initFrontendLogging = (config?: {
  apiUrl?: string;
  userId?: number;
  sessionId?: string;
}) => {
  // Log application startup
  frontendLogger.logInfo('Frontend application starting', {
    type: 'app_startup',
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href,
    referrer: document.referrer,
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight
    }
  });

  // Set user ID if provided
  if (config?.userId) {
    frontendLogger.setUserId(config.userId);
  }

  // Log performance metrics
  if ('performance' in window) {
    window.addEventListener('load', () => {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      frontendLogger.logInfo('Page load performance metrics', {
        type: 'performance',
        metrics: {
          domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
          loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
          totalLoadTime: perfData.loadEventEnd - perfData.fetchStart,
          dnsLookup: perfData.domainLookupEnd - perfData.domainLookupStart,
          tcpConnect: perfData.connectEnd - perfData.connectStart,
          request: perfData.responseEnd - perfData.requestStart,
          response: perfData.responseEnd - perfData.responseStart
        }
      });
    });
  }

  // Log route changes (for SPA)
  let currentPath = window.location.pathname;
  const logRouteChange = () => {
    const newPath = window.location.pathname;
    if (newPath !== currentPath) {
      frontendLogger.logInfo(`Route changed: ${currentPath} -> ${newPath}`, {
        type: 'route_change',
        from: currentPath,
        to: newPath,
        timestamp: new Date().toISOString()
      });
      currentPath = newPath;
    }
  };

  // Listen for route changes
  window.addEventListener('popstate', logRouteChange);
  
  // For React Router or other SPA routing, you might need to call logRouteChange()
  // manually when routes change, or use a custom hook

  // Log uncaught errors
  window.addEventListener('error', (event) => {
    frontendLogger.logError('Uncaught error', event.error, {
      type: 'uncaught_error',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      timestamp: new Date().toISOString()
    });
  });

  // Log unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    frontendLogger.logError('Unhandled promise rejection', event.reason, {
      type: 'unhandled_rejection',
      reason: event.reason?.toString(),
      timestamp: new Date().toISOString()
    });
  });

  // Log visibility changes
  document.addEventListener('visibilitychange', () => {
    frontendLogger.logInfo(`Page visibility changed: ${document.visibilityState}`, {
      type: 'visibility_change',
      state: document.visibilityState,
      timestamp: new Date().toISOString()
    });
  });

  // Log before unload
  window.addEventListener('beforeunload', () => {
    frontendLogger.logInfo('Page unloading', {
      type: 'page_unload',
      timestamp: new Date().toISOString()
    });
    
    // Flush logs immediately
    frontendLogger.flushImmediately();
  });

  console.log('Frontend logging initialized');
};

// Auto-initialize if not in test environment
if (process.env.NODE_ENV !== 'test') {
  initFrontendLogging();
}

export default initFrontendLogging;
