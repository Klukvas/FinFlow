import React, { useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import { useApiClients } from "@/hooks/useApiClients";
import { useAuth } from "@/contexts/AuthContext";
import { Payment, PaymentStatus } from "@/types/payment";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  User,
  CreditCard,
  Receipt,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { logger } from "@/utils/logger";

const STATUS_CONFIG = {
  [PaymentStatus.PAID]: {
    icon: CheckCircle2,
    iconBg: "bg-success-base",
    iconColor: "text-[var(--text-primary)]",
    titleKey: "payment.success.title",
    messageKey: "payment.success.message",
    barColor: "var(--success)",
  },
  [PaymentStatus.FAILED]: {
    icon: XCircle,
    iconBg: "bg-danger-base",
    iconColor: "text-[var(--text-primary)]",
    titleKey: "payment.failed.title",
    messageKey: "payment.failed.message",
    barColor: "var(--danger)",
  },
  [PaymentStatus.EXPIRED]: {
    icon: XCircle,
    iconBg: "bg-warning-base",
    iconColor: "text-[var(--text-primary)]",
    titleKey: "payment.expired.title",
    messageKey: "payment.expired.message",
    barColor: "var(--warning)",
  },
  [PaymentStatus.PENDING]: {
    icon: Clock,
    iconBg: "bg-accent-base",
    iconColor: "text-[var(--text-primary)]",
    titleKey: "payment.pending.title",
    messageKey: "payment.pending.detail",
    barColor: "var(--accent)",
  },
  [PaymentStatus.CREATED]: {
    icon: Clock,
    iconBg: "bg-surface-alt",
    iconColor: "text-[var(--text-primary)]",
    titleKey: "payment.processingStatus.title",
    messageKey: "payment.processingStatus.message",
    barColor: "var(--bg-raised)",
  },
};

const LOCALE_MAP: Record<string, string> = {
  en: "en-US",
  uk: "uk-UA",
  ru: "ru-RU",
};

/** Statuses where no further change is expected */
const TERMINAL_STATUSES: ReadonlySet<string> = new Set([
  PaymentStatus.PAID,
  PaymentStatus.EXPIRED,
  PaymentStatus.CANCELED,
  PaymentStatus.REFUNDED,
]);

const POLL_INTERVAL_MS = 3000;
const MAX_POLL_DURATION_MS = 5 * 60 * 1000; // 5 minutes

export const PaymentReturn: React.FC = () => {
  const { t, i18n } = useTranslation();
  const displayLocale = LOCALE_MAP[i18n.language] || i18n.language;
  const [searchParams] = useSearchParams();
  const { payment: paymentApi } = useApiClients();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const toastShownRef = useRef(false);

  /** Hard-navigate to /profile so all contexts (subscription, features, limits) reload fresh. */
  const goToProfile = () => {
    window.location.href = "/profile";
  };

  // Resolve payment identifiers once
  const paymentId =
    searchParams.get("paymentId") || localStorage.getItem("pending_payment_id");
  const orderRef = searchParams.get("orderReference");

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      setError(t("payment.errors.notAuthenticated"));
      setLoading(false);
      return;
    }

    if (!paymentId && !orderRef) {
      setError(t("payment.errors.noPaymentId"));
      setLoading(false);
      return;
    }

    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | null = null;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;
    const startTime = Date.now();

    const fetchStatus = async (): Promise<Payment | null> => {
      if (paymentId) {
        const res = await paymentApi.getPayment(paymentId);
        return "error" in res ? null : res;
      }
      if (orderRef) {
        const res = await paymentApi.getPaymentByOrderRef(orderRef);
        return "error" in res ? null : res;
      }
      return null;
    };

    const showToast = (status: string) => {
      if (toastShownRef.current) return;
      toastShownRef.current = true;

      if (status === PaymentStatus.PAID) {
        toast.success(t("payment.success.title"), {
          description: t("payment.success.message"),
        });
      } else if (status === PaymentStatus.FAILED) {
        toast.error(t("payment.failed.title"));
      } else if (status === PaymentStatus.PENDING) {
        toast.info(t("payment.pending.message"));
      }
    };

    const cleanup = () => {
      if (intervalId) clearInterval(intervalId);
      if (timeoutId) clearTimeout(timeoutId);
      intervalId = null;
      timeoutId = null;
    };

    const poll = async () => {
      if (cancelled) {
        cleanup();
        return;
      }

      try {
        const result = await fetchStatus();

        if (cancelled) return;

        if (!result) {
          logger.warn("PaymentReturn: poll got null, will retry");
          return;
        }

        // Always update the displayed payment data
        setPayment(result);
        setLoading(false);

        if (TERMINAL_STATUSES.has(result.status)) {
          cleanup();
          showToast(result.status);
          if (
            result.status === PaymentStatus.PAID ||
            result.status === PaymentStatus.FAILED
          ) {
            localStorage.removeItem("pending_payment_id");
            localStorage.removeItem("pending_plan_code");
          }
          return;
        }

        // Stop polling after max duration
        if (Date.now() - startTime > MAX_POLL_DURATION_MS) {
          logger.info("PaymentReturn: max poll duration reached, stopping");
          cleanup();
        }
      } catch (err) {
        logger.warn("PaymentReturn: poll error, will retry", err);
      }
    };

    // Initial fetch, then poll every POLL_INTERVAL_MS
    poll();
    intervalId = setInterval(poll, POLL_INTERVAL_MS);

    // Safety net: stop polling after max duration
    timeoutId = setTimeout(cleanup, MAX_POLL_DURATION_MS);

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [authLoading, isAuthenticated, paymentId, orderRef, paymentApi, t]);

  const isPolling = payment ? !TERMINAL_STATUSES.has(payment.status) : false;

  // Loading state
  if (loading) {
    return (
      <div
        className="fixed inset-0 flex items-center justify-center backdrop-blur-sm"
        style={{ background: "rgba(0, 0, 0, 0.6)" }}
      >
        <div
          className="relative max-w-md w-full mx-4 rounded-2xl p-8 text-center"
          style={{
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border)",
            boxShadow: "var(--shadow-modal)",
          }}
        >
          <button
            onClick={() => goToProfile()}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-content-tertiary hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="w-20 h-20 rounded-full bg-[var(--accent-dim)] flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-10 h-10 text-accent-base animate-spin" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
            {t("payment.checkingStatus")}
          </h1>
          <p className="text-content-tertiary mb-4">
            {t("payment.pleaseWait")}
          </p>
          <div className="flex justify-center gap-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-accent-base animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        className="fixed inset-0 flex items-center justify-center backdrop-blur-sm"
        style={{ background: "rgba(0, 0, 0, 0.6)" }}
      >
        <div
          className="relative max-w-md w-full mx-4 rounded-2xl p-8 text-center"
          style={{
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border)",
            boxShadow: "var(--shadow-modal)",
          }}
        >
          <button
            onClick={() => goToProfile()}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-content-tertiary hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="w-20 h-20 rounded-full bg-[var(--danger-dim)] flex items-center justify-center mx-auto mb-6">
            <XCircle className="w-10 h-10 text-danger-base" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
            {t("payment.errors.title")}
          </h1>
          <p className="text-content-tertiary mb-6">{error}</p>
          <button
            onClick={() => goToProfile()}
            className="w-full py-3 px-4 rounded-lg font-semibold text-[var(--text-primary)] flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: "var(--accent)",
              boxShadow: "0 4px 15px var(--accent-dim)",
            }}
          >
            <User className="w-4 h-4" />
            {t("payment.goToProfile")}
          </button>
        </div>
      </div>
    );
  }

  if (!payment) return null;

  const config =
    STATUS_CONFIG[payment.status as keyof typeof STATUS_CONFIG] ||
    STATUS_CONFIG[PaymentStatus.CREATED];
  const StatusIcon = config.icon;
  const isPaid = payment.status === PaymentStatus.PAID;

  return (
    <div
      className="fixed inset-0 flex items-center justify-center overflow-y-auto py-8 backdrop-blur-sm"
      style={{ background: "rgba(0, 0, 0, 0.6)" }}
    >
      <div
        className="relative max-w-lg w-full mx-4 rounded-2xl overflow-hidden"
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border)",
          boxShadow: "var(--shadow-modal)",
        }}
      >
        {/* Close button — only when polling is done */}
        {!isPolling && (
          <button
            onClick={() => goToProfile()}
            className="absolute top-4 right-4 z-10 p-1.5 rounded-lg text-content-tertiary hover:text-[var(--text-primary)] hover:bg-[var(--bg-raised)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* Status color bar */}
        <div className="h-2" style={{ backgroundColor: config.barColor }} />

        <div className="p-8">
          {/* Status icon with animation */}
          <div className="text-center mb-6">
            <div
              className={`w-20 h-20 rounded-full ${config.iconBg} flex items-center justify-center mx-auto mb-4 ${isPaid ? "animate-bounce" : ""}`}
              style={{
                animationDuration: "1s",
                animationIterationCount: isPaid ? 3 : 0,
              }}
            >
              {isPolling ? (
                <Loader2 className="w-10 h-10 text-accent-base animate-spin" />
              ) : (
                <StatusIcon className={`w-10 h-10 ${config.iconColor}`} />
              )}
            </div>

            <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
              {t(config.titleKey)}
            </h1>

            {/* Status badge */}
            <span
              className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium text-[var(--text-primary)]"
              style={{ backgroundColor: config.barColor, opacity: 0.9 }}
            >
              {payment.status}
            </span>
          </div>

          {/* Payment details card */}
          <div
            className="rounded-xl p-5 mb-6 space-y-4"
            style={{
              backgroundColor: "var(--bg-raised)",
              border: "1px solid var(--border)",
            }}
          >
            {/* Amount - highlighted */}
            <div
              className="text-center pb-4"
              style={{ borderBottom: "1px solid var(--border)" }}
            >
              <p className="text-content-tertiary text-sm mb-1">
                {t("payment.amount")}
              </p>
              <p className="text-3xl font-bold text-[var(--text-primary)]">
                {new Intl.NumberFormat(displayLocale, {
                  style: "currency",
                  currency: payment.currency,
                }).format(Number(payment.amount))}
              </p>
            </div>

            {/* Details grid */}
            <div className="space-y-3">
              {payment.plan_code && (
                <div className="flex items-center justify-between">
                  <span className="text-content-tertiary flex items-center gap-2">
                    <CreditCard className="w-4 h-4" />
                    {t("payment.plan")}
                  </span>
                  <span className="text-[var(--text-primary)] font-medium capitalize">
                    {payment.plan_code.replace(/-/g, " ")}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-content-tertiary flex items-center gap-2">
                  <Receipt className="w-4 h-4" />
                  {t("payment.orderRef")}
                </span>
                <span className="text-content-tertiary font-mono text-xs">
                  {payment.order_reference.slice(-12)}
                </span>
              </div>

              {payment.paid_at && (
                <div className="flex items-center justify-between">
                  <span className="text-content-tertiary">
                    {t("payment.paidAt")}
                  </span>
                  <span className="text-[var(--text-primary)]">
                    {new Date(payment.paid_at).toLocaleString(displayLocale)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Failure reason */}
          {payment.failure_reason && (
            <div
              className="rounded-lg p-4 mb-6"
              style={{
                backgroundColor: "var(--danger-dim)",
                border: "1px solid var(--danger-border)",
              }}
            >
              <p className="text-danger-base text-sm text-center">
                {payment.failure_reason}
              </p>
            </div>
          )}

          {/* Success message */}
          {isPaid && (
            <div
              className="rounded-lg p-4 mb-6"
              style={{
                backgroundColor: "var(--success-dim)",
                border: "1px solid var(--success-border)",
              }}
            >
              <p className="text-success-base text-sm text-center">
                {t(config.messageKey)}
              </p>
            </div>
          )}

          {/* Pending message */}
          {payment.status === PaymentStatus.PENDING && (
            <div
              className="rounded-lg p-4 mb-6"
              style={{
                backgroundColor: "var(--accent-dim)",
                border: "1px solid var(--accent-border)",
              }}
            >
              <p className="text-accent-base text-sm text-center">
                {t(config.messageKey)}
              </p>
            </div>
          )}

          {/* CREATED status warning */}
          {payment.status === PaymentStatus.CREATED && (
            <div
              className="rounded-lg p-4 mb-6"
              style={{
                backgroundColor: "rgba(245, 158, 11, 0.1)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
              }}
            >
              <div className="flex items-start gap-3">
                <Clock className="w-5 h-5 text-warning-base flex-shrink-0 mt-0.5" />
                <div className="text-left">
                  <p className="text-warning-base text-sm font-semibold mb-2">
                    {t("payment.processingStatus.title", "Processing Payment")}
                  </p>
                  <p className="text-warning-base text-xs">
                    {t(
                      "payment.processingStatus.detail",
                      "Your payment is being processed by the payment provider. This usually takes a few moments. Check your profile shortly for the updated subscription status.",
                    )}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Action button — only when polling is done */}
          {!isPolling && (
            <button
              onClick={() => goToProfile()}
              className="w-full py-3 px-4 rounded-lg font-semibold text-[var(--text-primary)] flex items-center justify-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98]"
              style={{
                background: "var(--accent)",
                boxShadow: "0 4px 15px var(--accent-dim)",
              }}
            >
              <User className="w-4 h-4" />
              {t("payment.goToProfile")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaymentReturn;
