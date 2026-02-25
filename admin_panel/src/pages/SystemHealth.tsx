import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { config } from "@/config/env";
import { ServiceHealth, ApiError } from "@/types";
import { UserService } from "@/services/userService";
import { SubscriptionService } from "@/services/subscriptionService";
import { PaymentService } from "@/services/paymentService";
import { FaSync, FaCircle } from "react-icons/fa";

interface PaymentConfig {
  status: string;
  checks: Record<string, { configured?: boolean; value?: string }>;
  production_ready: boolean;
}

export const SystemHealth: React.FC = () => {
  const { token, logout, refreshToken } = useAuth();

  const [services, setServices] = useState<ServiceHealth[]>([
    {
      name: "User Service",
      url: config.api.userServiceUrl,
      status: "loading",
    },
    {
      name: "Subscription Service",
      url: config.api.subscriptionServiceUrl,
      status: "loading",
    },
    {
      name: "Payment Service",
      url: config.api.paymentServiceUrl,
      status: "loading",
    },
    {
      name: "Scheduler Service",
      url: config.api.schedulerServiceUrl,
      status: "loading",
    },
  ]);

  const [paymentConfig, setPaymentConfig] = useState<PaymentConfig | null>(
    null,
  );
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const userService = React.useMemo(
    () => new UserService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const subscriptionService = React.useMemo(
    () => new SubscriptionService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const paymentService = React.useMemo(
    () => new PaymentService(() => token, logout, refreshToken),
    [token, logout, refreshToken],
  );

  const checkHealth = useCallback(async () => {
    setIsRefreshing(true);

    const checks = [
      { name: "User Service", check: () => userService.getHealth() },
      {
        name: "Subscription Service",
        check: () => subscriptionService.getHealth(),
      },
      { name: "Payment Service", check: () => paymentService.getHealth() },
      {
        name: "Scheduler Service",
        check: async (): Promise<{ status: string } | ApiError> => {
          try {
            const res = await fetch(
              `${config.api.schedulerServiceUrl}/health/live`,
            );
            if (!res.ok) return { error: `HTTP ${res.status}` };
            return await res.json();
          } catch {
            return { error: "Connection refused" };
          }
        },
      },
    ];

    const results = await Promise.allSettled(
      checks.map(async (c) => {
        const result = await c.check();
        return {
          name: c.name,
          isUp: !("error" in result),
          detail: "error" in result ? result.error : undefined,
        };
      }),
    );

    setServices((prev) =>
      prev.map((s, i) => {
        const result = results[i];
        if (result.status === "fulfilled") {
          return {
            ...s,
            status: result.value.isUp ? "up" : "down",
            detail: result.value.detail,
          };
        }
        return { ...s, status: "down", detail: "Check failed" };
      }),
    );

    // Check payment config
    try {
      const configResult = await paymentService.getPaymentConfig();
      if (!("error" in configResult)) {
        // Fetch the detailed config check
        try {
          const res = await fetch(
            `${config.api.paymentServiceUrl}/v1/config/check`,
          );
          if (res.ok) {
            setPaymentConfig(await res.json());
          }
        } catch {
          // ignore
        }
      }
    } catch {
      // ignore
    }

    setLastChecked(new Date());
    setIsRefreshing(false);
  }, [userService, subscriptionService, paymentService]);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const statusColor = (status: string) => {
    switch (status) {
      case "up":
        return "text-green-400";
      case "down":
        return "text-red-400";
      default:
        return "text-slate-500 animate-pulse";
    }
  };

  const statusLabel = (status: string) => {
    switch (status) {
      case "up":
        return "Healthy";
      case "down":
        return "Down";
      default:
        return "Checking...";
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">System Health</h1>
          <p className="text-slate-400">
            Service status and configuration
            {lastChecked && (
              <span className="ml-2 text-xs text-slate-500">
                Last checked: {lastChecked.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button
          onClick={checkHealth}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-slate-300 hover:text-white hover:border-slate-600 transition-colors disabled:opacity-50"
        >
          <FaSync
            className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`}
          />
          Refresh
        </button>
      </div>

      {/* Service Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {services.map((service) => (
          <div
            key={service.name}
            className="bg-slate-800 rounded-xl border border-slate-700 p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <FaCircle
                className={`w-3 h-3 ${statusColor(service.status)}`}
              />
              <h3 className="text-white font-semibold">{service.name}</h3>
            </div>
            <p
              className={`text-sm font-medium ${statusColor(service.status)}`}
            >
              {statusLabel(service.status)}
            </p>
            {service.detail && (
              <p className="text-xs text-slate-500 mt-1">{service.detail}</p>
            )}
            <p className="text-xs text-slate-600 mt-2 font-mono truncate">
              {service.url}
            </p>
          </div>
        ))}
      </div>

      {/* Payment Configuration */}
      {paymentConfig && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="p-6 border-b border-slate-700">
            <h2 className="text-lg font-semibold text-white">
              Paddle Configuration
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(paymentConfig.checks).map(([key, check]) => (
                <div
                  key={key}
                  className="py-3 px-4 bg-slate-900/50 rounded-lg"
                >
                  <p className="text-xs text-slate-400 mb-1">
                    {key.replace(/_/g, " ")}
                  </p>
                  {check.configured !== undefined ? (
                    <p
                      className={`text-sm font-medium ${check.configured ? "text-green-400" : "text-red-400"}`}
                    >
                      {check.configured ? "Configured" : "Not configured"}
                    </p>
                  ) : (
                    <p className="text-sm text-white">{check.value}</p>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2">
              <FaCircle
                className={`w-2 h-2 ${paymentConfig.production_ready ? "text-green-400" : "text-amber-400"}`}
              />
              <span
                className={`text-sm ${paymentConfig.production_ready ? "text-green-400" : "text-amber-400"}`}
              >
                {paymentConfig.production_ready
                  ? "Production ready"
                  : "Not production ready"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
