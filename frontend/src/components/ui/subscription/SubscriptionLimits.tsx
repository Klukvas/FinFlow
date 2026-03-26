import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { useApiClients } from "@/hooks/useApiClients";
import { useAuth } from "@/contexts/AuthContext";
import { UserFeature } from "@/types/subscription";
import { Card } from "@/components/ui/shared/Card";
import { Button } from "@/components/ui/shared/Button";
import { Skeleton } from "@/components/ui/shared/Skeleton";
import { UpgradePlanModal } from "@/components/payment/UpgradePlanModal";
import { CancelSubscriptionModal } from "@/components/subscription/CancelSubscriptionModal";
import {
  Folder,
  Wallet,
  Receipt,
  ArrowUp,
  CreditCard,
  RefreshCw,
  Target,
  Crown,
  CheckCircle2,
  XCircle,
  Rocket,
  Ban,
  AlertTriangle,
} from "lucide-react";

interface SubscriptionLimitsProps {
  className?: string;
}

const featureIcons: Record<string, React.ReactNode> = {
  categories: <Folder className="w-4 h-4" />,
  accounts: <Wallet className="w-4 h-4" />,
  expenses: <Receipt className="w-4 h-4" />,
  incomes: <ArrowUp className="w-4 h-4" />,
  debts: <CreditCard className="w-4 h-4" />,
  recurring: <RefreshCw className="w-4 h-4" />,
  goals: <Target className="w-4 h-4" />,
};

const featureNames: Record<string, string> = {
  categories: "subscription.features.categories",
  accounts: "subscription.features.accounts",
  expenses: "subscription.features.expenses",
  incomes: "subscription.features.incomes",
  debts: "subscription.features.debts",
  recurring: "subscription.features.recurring",
  goals: "subscription.features.goals",
};

interface Subscription {
  user_id: string;
  plan_code: string;
  status: string;
  auto_renew?: boolean;
  expires_at: string | null;
  canceled_at: string | null;
  paddle_subscription_id?: string | null;
}

export const SubscriptionLimits: React.FC<SubscriptionLimitsProps> = ({
  className = "",
}) => {
  const { t } = useTranslation();
  const { subscription: subscriptionApi } = useApiClients();
  const { user } = useAuth();
  const [features, setFeatures] = useState<UserFeature[]>([]);
  const [currentCounts, setCurrentCounts] = useState<Record<string, number>>(
    {},
  );
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);

  const loadSubscriptionLimits = async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      setError(null);

      // Load features, current counts, and subscription in parallel
      const [featuresResponse, countsResponse, subscriptionResponse] =
        await Promise.all([
          subscriptionApi.getUserFeatures(user.id),
          subscriptionApi.getCurrentCounts(user.id),
          subscriptionApi.getUserSubscription(user.id).catch(() => null),
        ]);

      if ("error" in featuresResponse) {
        setError(t("subscription.errors.loadFailed"));
        return;
      }

      if ("error" in countsResponse) {
        logger.warn("Failed to load current counts:", countsResponse.error);
        // Don't fail the whole component if counts fail
      } else {
        setCurrentCounts(countsResponse);
      }

      setFeatures(featuresResponse);

      // Set subscription (null when no active subscription)
      if (subscriptionResponse && !("error" in subscriptionResponse)) {
        setSubscription(subscriptionResponse);
      } else {
        setSubscription(null);
      }
    } catch (err) {
      setError(t("subscription.errors.loadFailed"));
      logger.error("Failed to load subscription limits:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubscriptionLimits();
  }, [user?.id, subscriptionApi]);

  const handleCancelSuccess = async () => {
    // Reload all data after cancellation (subscription + features + counts)
    await loadSubscriptionLimits();
  };

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-6">
          <Skeleton className="w-10 h-10 rounded-lg" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-3 w-56" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="p-4 rounded-lg border border-[var(--border)] space-y-3"
            >
              <div className="flex items-center gap-3">
                <Skeleton className="w-8 h-8 rounded-lg" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-5 w-14 rounded-full" />
              </div>
              <Skeleton className="h-2 w-full rounded-full" />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center py-8">
          <XCircle className="w-8 h-8 text-danger-base mx-auto mb-2" />
          <p className="text-danger-base">{error}</p>
        </div>
      </Card>
    );
  }

  const isPaidPlan = subscription && subscription.plan_code !== "basic";
  const isCanceled = subscription?.canceled_at != null;
  const isPastDue = subscription?.status === "past_due";
  const isPaused = subscription?.status === "paused";
  const isActive = subscription?.status === "active" && !isCanceled;
  const expiresAt = subscription?.expires_at
    ? new Date(subscription.expires_at)
    : null;
  const isExpired = expiresAt ? expiresAt < new Date() : false;
  const planCode = subscription?.plan_code ?? "basic";

  return (
    <>
      <Card className={`p-6 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[var(--purple-dim)] border border-[var(--purple-border)] rounded-lg flex items-center justify-center">
              <Crown className="w-5 h-5 text-[var(--purple)]" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-content">
                {t("subscription.title")}
              </h3>
              <p className="text-sm text-content-secondary">
                {t("subscription.subtitle")}
              </p>
              <p className="text-xs text-content-secondary mt-1">
                {t("subscription.currentPlan")}:{" "}
                <span className="font-semibold text-content">{planCode}</span>
                {isCanceled && !isExpired && expiresAt && (
                  <span className="ml-2 text-warning-base">
                    ({t("subscription.canceled")} -{" "}
                    {t("subscription.accessUntil")}{" "}
                    {expiresAt.toLocaleDateString()})
                  </span>
                )}
              </p>
              {isActive && !isCanceled && expiresAt && (
                <p className="text-xs text-content-secondary">
                  {t("subscription.renewsOn", {
                    date: expiresAt.toLocaleDateString(),
                  })}
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {isPaidPlan && !isCanceled && (
              <button
                onClick={() => setIsCancelModalOpen(true)}
                className="px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-all hover:scale-105 active:scale-95 border-2 border-danger-base text-danger-base hover:bg-surface-alt"
              >
                <Ban className="w-4 h-4" />
                <span>{t("subscription.cancelButton")}</span>
              </button>
            )}
            <button
              onClick={() => setIsUpgradeModalOpen(true)}
              className="relative px-4 py-2 rounded-lg font-medium text-white text-sm flex items-center gap-2 overflow-hidden group transition-transform hover:scale-105 active:scale-95"
              style={{
                background:
                  "linear-gradient(90deg, #8b5cf6, #ec4899, #f97316, #8b5cf6)",
                backgroundSize: "300% 100%",
                animation: "gradient-shift 3s ease infinite",
              }}
            >
              <span className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
              <Rocket className="w-4 h-4 relative z-10" />
              <span className="relative z-10">
                {isPaidPlan
                  ? t("subscription.changePlan")
                  : t("subscription.upgradePlan")}
              </span>
            </button>
          </div>
          <style>{`
 @keyframes gradient-shift {
 0% { background-position: 0% 50%; }
 50% { background-position: 100% 50%; }
 100% { background-position: 0% 50%; }
 }
 `}</style>
        </div>

        {/* Cancellation Warning Banner — only while access is still active */}
        {isCanceled && expiresAt && !isExpired && (
          <div className="mb-4 p-4 rounded-lg bg-[var(--warning-dim)] border-2 border-warning-base flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-warning-base flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-content mb-1">
                {t("subscription.subscriptionCanceled")}
              </p>
              <p className="text-sm text-content-secondary">
                {t("subscription.accessUntilDate", {
                  date: expiresAt.toLocaleDateString(),
                })}
              </p>
            </div>
          </div>
        )}

        {/* Past Due Warning Banner */}
        {isPastDue && (
          <div className="mb-4 p-4 rounded-lg bg-[var(--warning-dim)] border-2 border-warning-base flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-warning-base flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-content mb-1">
                {t("subscription.pastDue.title")}
              </p>
              <p className="text-sm text-content-secondary mb-2">
                {t("subscription.pastDue.message")}
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsUpgradeModalOpen(true)}
              >
                {t("subscription.pastDue.action")}
              </Button>
            </div>
          </div>
        )}

        {/* Paused Info Banner */}
        {isPaused && (
          <div className="mb-4 p-4 rounded-lg bg-surface-alt border-2 border-[var(--border)] flex items-start gap-3">
            <Ban className="w-5 h-5 text-content-tertiary flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-content mb-1">
                {t("subscription.paused.title")}
              </p>
              <p className="text-sm text-content-secondary mb-2">
                {t("subscription.paused.message")}
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsUpgradeModalOpen(true)}
              >
                {t("subscription.paused.action")}
              </Button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {features.map((feature) => {
            const icon = featureIcons[feature.feature_code] || (
              <CheckCircle2 className="w-4 h-4" />
            );
            const name = t(
              featureNames[feature.feature_code] || feature.feature_code,
            );
            const currentCount = currentCounts[feature.feature_code] || 0;
            const limit = feature.limit_value;
            const isNearLimit = limit !== null && currentCount >= limit * 0.8; // 80% of limit
            const isAtLimit = limit !== null && currentCount >= limit;

            return (
              <div
                key={feature.feature_code}
                className={`p-4 rounded-lg border transition-colors ${
                  feature.enabled
                    ? "bg-elevated border-[var(--border)]"
                    : "bg-surface-alt border-[var(--border)] opacity-60"
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      feature.enabled
                        ? "bg-[var(--accent-dim)]"
                        : "bg-surface-alt"
                    }`}
                  >
                    <div
                      className={
                        feature.enabled
                          ? "text-accent-base"
                          : "text-content-tertiary"
                      }
                    >
                      {icon}
                    </div>
                  </div>
                  <div className="flex-1">
                    <h4
                      className={`font-medium ${
                        feature.enabled
                          ? "text-content"
                          : "text-content-tertiary"
                      }`}
                    >
                      {name}
                    </h4>
                  </div>
                  <div
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      feature.enabled
                        ? "bg-[var(--success-dim)] text-success-base"
                        : "bg-surface-alt text-content-tertiary"
                    }`}
                  >
                    {feature.enabled
                      ? t("subscription.status.active")
                      : t("subscription.status.inactive")}
                  </div>
                </div>

                {feature.enabled && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-content-secondary">
                        {t("subscription.used")}:
                      </span>
                      <span
                        className={`font-medium ${
                          isAtLimit
                            ? "text-danger-base"
                            : isNearLimit
                              ? "text-warning-base"
                              : "text-content"
                        }`}
                      >
                        {currentCount}
                      </span>
                    </div>

                    {limit !== null && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-content-secondary">
                          {t("subscription.limit")}:
                        </span>
                        <span className="text-content font-medium">
                          {limit}
                        </span>
                      </div>
                    )}

                    {limit !== null && (
                      <div className="w-full bg-surface-alt rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            isAtLimit
                              ? "bg-danger-base"
                              : isNearLimit
                                ? "bg-warning-base"
                                : "bg-success-base"
                          }`}
                          style={{
                            width: `${Math.min((currentCount / limit) * 100, 100)}%`,
                          }}
                        />
                      </div>
                    )}

                    {limit === null && (
                      <div className="text-sm text-success-base">
                        {t("subscription.unlimited")}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {features.length === 0 && (
          <div className="text-center py-8">
            <Crown className="w-8 h-8 text-content-tertiary mx-auto mb-2" />
            <p className="text-content-secondary">{t("subscription.noData")}</p>
          </div>
        )}
      </Card>

      <UpgradePlanModal
        isOpen={isUpgradeModalOpen}
        onClose={() => {
          setIsUpgradeModalOpen(false);
          loadSubscriptionLimits();
        }}
        {...(subscription?.plan_code !== undefined
          ? { currentPlanCode: subscription.plan_code }
          : {})}
        {...(subscription?.paddle_subscription_id
          ? { paddleSubscriptionId: subscription.paddle_subscription_id }
          : {})}
      />

      <CancelSubscriptionModal
        isOpen={isCancelModalOpen}
        onClose={() => setIsCancelModalOpen(false)}
        subscription={
          subscription
            ? {
                id: Number(subscription.user_id),
                plan_code: subscription.plan_code,
                expires_at: subscription.expires_at,
              }
            : null
        }
        onCancelSuccess={handleCancelSuccess}
      />
    </>
  );
};
