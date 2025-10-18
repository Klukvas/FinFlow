/**
 * API Call Logging Interceptor
 * 
 * This utility automatically logs all API calls made by the frontend application.
 */

import { frontendLogger } from './logging';

interface ApiCallConfig {
  method: string;
  url: string;
  startTime: number;
  requestId?: string;
}

class ApiLogger {
  private activeCalls = new Map<string, ApiCallConfig>();

  public logRequest(method: string, url: string, requestId?: string): string {
    const callId = requestId || this.generateCallId();
    const startTime = performance.now();

    this.activeCalls.set(callId, {
      method,
      url,
      startTime,
      requestId: callId
    });

    frontendLogger.logInfo(`API Request: ${method} ${url}`, {
      type: 'api_request',
      method,
      url,
      requestId: callId,
      timestamp: new Date().toISOString()
    });

    return callId;
  }

  public logResponse(
    callId: string, 
    status: number, 
    statusText?: string, 
    error?: Error
  ): void {
    const callConfig = this.activeCalls.get(callId);
    if (!callConfig) {
      console.warn(`No active call found for ID: ${callId}`);
      return;
    }

    const duration = performance.now() - callConfig.startTime;
    this.activeCalls.delete(callId);

    const isError = status >= 400 || !!error;
    const logLevel = isError ? 'error' : 'info';

    const logData = {
      type: 'api_response',
      method: callConfig.method,
      url: callConfig.url,
      status,
      statusText,
      duration: Math.round(duration),
      requestId: callId,
      timestamp: new Date().toISOString()
    };

    if (error) {
      logData.error = {
        name: error.name,
        message: error.message,
        stack: error.stack
      };
    }

    if (isError) {
      frontendLogger.logError(
        `API Error: ${callConfig.method} ${callConfig.url} - ${status} ${statusText}`,
        error,
        logData
      );
    } else {
      frontendLogger.logApiCall(
        callConfig.method,
        callConfig.url,
        status,
        duration
      );
    }
  }

  public logTimeout(callId: string, timeout: number): void {
    const callConfig = this.activeCalls.get(callId);
    if (!callConfig) {
      console.warn(`No active call found for ID: ${callId}`);
      return;
    }

    const duration = performance.now() - callConfig.startTime;
    this.activeCalls.delete(callId);

    frontendLogger.logError(
      `API Timeout: ${callConfig.method} ${callConfig.url}`,
      new Error(`Request timed out after ${timeout}ms`),
      {
        type: 'api_timeout',
        method: callConfig.method,
        url: callConfig.url,
        timeout,
        duration: Math.round(duration),
        requestId: callId,
        timestamp: new Date().toISOString()
      }
    );
  }

  private generateCallId(): string {
    return `api_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  public getActiveCalls(): ApiCallConfig[] {
    return Array.from(this.activeCalls.values());
  }

  public clearActiveCalls(): void {
    this.activeCalls.clear();
  }
}

// Create singleton instance
export const apiLogger = new ApiLogger();

// Fetch interceptor
const originalFetch = window.fetch;

window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
  const method = init?.method || 'GET';
  
  const callId = apiLogger.logRequest(method, url);

  try {
    const response = await originalFetch(input, init);
    apiLogger.logResponse(callId, response.status, response.statusText);
    return response;
  } catch (error) {
    apiLogger.logResponse(callId, 0, 'Network Error', error as Error);
    throw error;
  }
};

// XMLHttpRequest interceptor
const originalXHROpen = XMLHttpRequest.prototype.open;
const originalXHRSend = XMLHttpRequest.prototype.send;

XMLHttpRequest.prototype.open = function(method: string, url: string | URL, ...args: any[]) {
  this._apiCallId = apiLogger.logRequest(method, url.toString());
  this._apiMethod = method;
  this._apiUrl = url.toString();
  return originalXHROpen.call(this, method, url, ...args);
};

XMLHttpRequest.prototype.send = function(body?: Document | XMLHttpRequestBodyInit | null) {
  const xhr = this;
  
  const handleLoad = () => {
    apiLogger.logResponse(xhr._apiCallId, xhr.status, xhr.statusText);
  };

  const handleError = () => {
    apiLogger.logResponse(xhr._apiCallId, xhr.status, xhr.statusText, new Error('XHR Error'));
  };

  const handleTimeout = () => {
    apiLogger.logTimeout(xhr._apiCallId, xhr.timeout);
  };

  xhr.addEventListener('load', handleLoad);
  xhr.addEventListener('error', handleError);
  xhr.addEventListener('timeout', handleTimeout);

  return originalXHRSend.call(this, body);
};

// Export the class for custom usage
export { ApiLogger };
