/**
 * React Hook for Frontend Logging
 * 
 * This hook provides easy access to logging functionality in React components.
 */

import { useEffect, useCallback } from 'react';
import { frontendLogger, LogEntry } from '../utils/logging';

interface UseLoggingReturn {
  logError: (message: string, error?: Error, extra?: Record<string, any>) => void;
  logInfo: (message: string, extra?: Record<string, any>) => void;
  logWarning: (message: string, extra?: Record<string, any>) => void;
  logBusinessEvent: (event: string, data?: Record<string, any>) => void;
  logUserAction: (action: string, data?: Record<string, any>) => void;
  logApiCall: (method: string, url: string, status: number, duration?: number) => void;
  setUserId: (userId: number) => void;
  clearUserId: () => void;
  flushLogs: () => Promise<void>;
}

export const useLogging = (): UseLoggingReturn => {
  // Set up component lifecycle logging
  useEffect(() => {
    frontendLogger.logInfo('Component mounted', {
      component: 'unknown', // This will be overridden by individual components
      timestamp: new Date().toISOString()
    });

    return () => {
      frontendLogger.logInfo('Component unmounted', {
        component: 'unknown',
        timestamp: new Date().toISOString()
      });
    };
  }, []);

  const logError = useCallback((message: string, error?: Error, extra?: Record<string, any>) => {
    frontendLogger.logError(message, error, extra);
  }, []);

  const logInfo = useCallback((message: string, extra?: Record<string, any>) => {
    frontendLogger.logInfo(message, extra);
  }, []);

  const logWarning = useCallback((message: string, extra?: Record<string, any>) => {
    frontendLogger.logWarning(message, extra);
  }, []);

  const logBusinessEvent = useCallback((event: string, data?: Record<string, any>) => {
    frontendLogger.logBusinessEvent(event, data);
  }, []);

  const logUserAction = useCallback((action: string, data?: Record<string, any>) => {
    frontendLogger.logUserAction(action, data);
  }, []);

  const logApiCall = useCallback((method: string, url: string, status: number, duration?: number) => {
    frontendLogger.logApiCall(method, url, status, duration);
  }, []);

  const setUserId = useCallback((userId: number) => {
    frontendLogger.setUserId(userId);
  }, []);

  const clearUserId = useCallback(() => {
    frontendLogger.clearUserId();
  }, []);

  const flushLogs = useCallback(async () => {
    await frontendLogger.flushImmediately();
  }, []);

  return {
    logError,
    logInfo,
    logWarning,
    logBusinessEvent,
    logUserAction,
    logApiCall,
    setUserId,
    clearUserId,
    flushLogs,
  };
};

// Higher-order component for automatic logging
export const withLogging = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentName: string
) => {
  const WithLoggingComponent = (props: P) => {
    const logging = useLogging();

    useEffect(() => {
      logging.logInfo(`${componentName} component mounted`, {
        component: componentName,
        props: Object.keys(props)
      });

      return () => {
        logging.logInfo(`${componentName} component unmounted`, {
          component: componentName
        });
      };
    }, [logging]);

    return <WrappedComponent {...props} />;
  };

  WithLoggingComponent.displayName = `withLogging(${componentName})`;
  return WithLoggingComponent;
};

// Hook for component-specific logging
export const useComponentLogging = (componentName: string) => {
  const logging = useLogging();

  const logComponentError = useCallback((message: string, error?: Error, extra?: Record<string, any>) => {
    logging.logError(`${componentName}: ${message}`, error, {
      component: componentName,
      ...extra
    });
  }, [logging, componentName]);

  const logComponentInfo = useCallback((message: string, extra?: Record<string, any>) => {
    logging.logInfo(`${componentName}: ${message}`, {
      component: componentName,
      ...extra
    });
  }, [logging, componentName]);

  const logComponentWarning = useCallback((message: string, extra?: Record<string, any>) => {
    logging.logWarning(`${componentName}: ${message}`, {
      component: componentName,
      ...extra
    });
  }, [logging, componentName]);

  const logComponentAction = useCallback((action: string, data?: Record<string, any>) => {
    logging.logUserAction(`${componentName}: ${action}`, {
      component: componentName,
      ...data
    });
  }, [logging, componentName]);

  return {
    logError: logComponentError,
    logInfo: logComponentInfo,
    logWarning: logComponentWarning,
    logAction: logComponentAction,
    ...logging
  };
};
