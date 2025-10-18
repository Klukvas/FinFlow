/**
 * Frontend Logging Utility
 * 
 * This utility provides structured logging for the frontend application,
 * collecting browser console logs and sending them to the backend logging API.
 */

interface LogEntry {
  level: string;
  message: string;
  timestamp?: string;
  source?: string;
  stack?: string;
  user_id?: number;
  session_id?: string;
  url?: string;
  user_agent?: string;
  extra?: Record<string, any>;
}

interface LogBatch {
  logs: LogEntry[];
  session_id?: string;
  user_id?: number;
}

class FrontendLogger {
  private logs: LogEntry[] = [];
  private batchSize = 10;
  private flushInterval = 5000; // 5 seconds
  private apiUrl: string;
  private sessionId: string;
  private userId?: number;
  private flushTimer?: NodeJS.Timeout;
  private originalConsole: {
    log: typeof console.log;
    warn: typeof console.warn;
    error: typeof console.error;
    info: typeof console.info;
    debug: typeof console.debug;
  };

  constructor(apiUrl: string = '/api/logging') {
    this.apiUrl = apiUrl;
    this.sessionId = this.generateSessionId();
    this.originalConsole = {
      log: console.log.bind(console),
      warn: console.warn.bind(console),
      error: console.error.bind(console),
      info: console.info.bind(console),
      debug: console.debug.bind(console),
    };

    this.setupConsoleInterception();
    this.setupErrorHandling();
    this.startFlushTimer();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupConsoleInterception(): void {
    // Intercept console methods
    console.log = (...args: any[]) => {
      this.log('log', args.join(' '));
      this.originalConsole.log(...args);
    };

    console.warn = (...args: any[]) => {
      this.log('warn', args.join(' '));
      this.originalConsole.warn(...args);
    };

    console.error = (...args: any[]) => {
      this.log('error', args.join(' '));
      this.originalConsole.error(...args);
    };

    console.info = (...args: any[]) => {
      this.log('info', args.join(' '));
      this.originalConsole.info(...args);
    };

    console.debug = (...args: any[]) => {
      this.log('debug', args.join(' '));
      this.originalConsole.debug(...args);
    };
  }

  private setupErrorHandling(): void {
    // Global error handler
    window.addEventListener('error', (event) => {
      this.log('error', event.message, {
        source: `${event.filename}:${event.lineno}:${event.colno}`,
        stack: event.error?.stack,
        extra: {
          type: 'javascript_error',
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        }
      });
    });

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.log('error', `Unhandled Promise Rejection: ${event.reason}`, {
        source: 'unhandledrejection',
        stack: event.reason?.stack,
        extra: {
          type: 'promise_rejection',
          reason: event.reason,
        }
      });
    });
  }

  private log(level: string, message: string, options: Partial<LogEntry> = {}): void {
    const logEntry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      user_agent: navigator.userAgent,
      session_id: this.sessionId,
      user_id: this.userId,
      ...options
    };

    this.logs.push(logEntry);

    // Flush if batch size reached
    if (this.logs.length >= this.batchSize) {
      this.flush();
    }
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      if (this.logs.length > 0) {
        this.flush();
      }
    }, this.flushInterval);
  }

  private async flush(): Promise<void> {
    if (this.logs.length === 0) return;

    const logsToSend = [...this.logs];
    this.logs = [];

    try {
      const response = await fetch(`${this.apiUrl}/frontend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logs: logsToSend,
          session_id: this.sessionId,
          user_id: this.userId,
        } as LogBatch),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.debug(`Frontend logs flushed: ${result.processed} entries`);
    } catch (error) {
      console.error('Failed to send frontend logs:', error);
      // Re-add logs to queue for retry
      this.logs.unshift(...logsToSend);
    }
  }

  public setUserId(userId: number): void {
    this.userId = userId;
  }

  public clearUserId(): void {
    this.userId = undefined;
  }

  public logError(message: string, error?: Error, extra?: Record<string, any>): void {
    this.log('error', message, {
      source: error ? `${error.name}:${error.message}` : undefined,
      stack: error?.stack,
      extra: {
        type: 'manual_error',
        ...extra
      }
    });
  }

  public logInfo(message: string, extra?: Record<string, any>): void {
    this.log('info', message, {
      extra: {
        type: 'manual_info',
        ...extra
      }
    });
  }

  public logWarning(message: string, extra?: Record<string, any>): void {
    this.log('warn', message, {
      extra: {
        type: 'manual_warning',
        ...extra
      }
    });
  }

  public logBusinessEvent(event: string, data?: Record<string, any>): void {
    this.log('info', `Business Event: ${event}`, {
      extra: {
        type: 'business_event',
        event,
        data
      }
    });
  }

  public logUserAction(action: string, data?: Record<string, any>): void {
    this.log('info', `User Action: ${action}`, {
      extra: {
        type: 'user_action',
        action,
        data
      }
    });
  }

  public logApiCall(method: string, url: string, status: number, duration?: number): void {
    this.log('info', `API Call: ${method} ${url}`, {
      extra: {
        type: 'api_call',
        method,
        url,
        status,
        duration
      }
    });
  }

  public async flushImmediately(): Promise<void> {
    await this.flush();
  }

  public destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flushImmediately();
  }
}

// Create singleton instance
export const frontendLogger = new FrontendLogger();

// Export types for use in other modules
export type { LogEntry, LogBatch };

// Export the class for custom instances
export { FrontendLogger };

// Auto-cleanup on page unload
window.addEventListener('beforeunload', () => {
  frontendLogger.destroy();
});
