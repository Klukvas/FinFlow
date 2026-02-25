import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useApiClients } from "@/hooks/useApiClients";
import { useAuth } from "@/contexts/AuthContext";
import { UserFeature } from "@/types/subscription";
import { Card } from "@/components/ui/shared/Card";
import { Button } from "@/components/ui/shared/Button";
import { LoadingSpinner } from "@/components/ui/shared/LoadingSpinner";
import { UpgradePlanModal } from "@/components/payment/UpgradePlanModal";
import { CancelSubscriptionModal } from "@/components/subscription/CancelSubscriptionModal";
import {
  FaFolder,
  FaWallet,
  FaReceipt,
  FaArrowUp,
  FaCreditCard,
  FaRedo,
  FaBullseye,
  FaCrown,
  FaCheckCircle,
  FaTimesCircle,
  FaRocket,
  FaBan,
  FaExclamationTriangle,
} from "react-icons/fa";

interface SubscriptionLimitsProps {
  className?: string;
}

const featureIcons: Record<string, React.ReactNode> = {
  categories: <FaFolder className="w-4 h-4" />,
  accounts: <FaWallet className="w-4 h-4" />,
  expenses: <FaReceipt className="w-4 h-4" />,
  incomes: <FaArrowUp className="w-4 h-4" />,
  debts: <FaCreditCard className="w-4 h-4" />,
  recurring: <FaRedo className="w-4 h-4" />,
  goals: <FaBullseye className="w-4 h-4" />,
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
  id: number;
  user_id: string;
  plan_code: string;
  status: string;
  auto_renew: boolean;
  expires_at: string | null;
  canceled_at: string | null;
  paddle_subscription_id?: string;
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
        console.warn("Failed to load current counts:", countsResponse.error);
        // Don't fail the whole component if counts fail
      } else {
        setCurrentCounts(countsResponse);
      }

      setFeatures(featuresResponse);

      // Set subscription if exists and not an error
      if (subscriptionResponse && !("error" in subscriptionResponse)) {
        setSubscription(subscriptionResponse);
      }
    } catch (err) {
      setError(t("subscription.errors.loadFailed"));
      console.error("Failed to load subscription limits:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSubscriptionLimits();
  }, [user?.id, subscriptionApi]);

  const handleCancelSuccess = async () => {
    // Reload subscription data after cancellation
    if (user?.id) {
      const subscriptionResponse = await subscriptionApi
        .getUserSubscription(user.id)
        .catch(() => null);
      if (subscriptionResponse && !("error" in subscriptionResponse)) {
        setSubscription(subscriptionResponse);
      }
    }
  };

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center py-8">
          <FaTimesCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-600">{error}</p>
        </div>
      </Card>
    );
  }

  const isPaidPlan = subscription && subscription.plan_code !== "basic";
  const isCanceled = subscription && !subscription.auto_renew;
  const isPastDue = subscription?.status === "past_due";
  const isPaused = subscription?.status === "paused";
  const isActive = subscription?.status === "active" && !isCanceled;
  const expiresAt = subscription?.expires_at
    ? new Date(subscription.expires_at)
    : null;

  return (
    <>
      <Card className={`p-6 ${className}`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <FaCrown className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold theme-text-primary">
                {t("subscription.title")}
              </h3>
              <p className="text-sm theme-text-secondary">
                {t("subscription.subtitle")}
              </p>
              {subscription && (
                <>
                  <p className="text-xs theme-text-secondary mt-1">
                    {t("subscription.currentPlan")}:{" "}
                    <span className="font-semibold theme-text-primary">
                      {subscription.plan_code}
                    </span>
                    {isCanceled && (
                      <span className="ml-2 text-orange-600">
                        ({t("subscription.canceled")} -{" "}
                        {t("subscription.accessUntil")}{" "}
                        {expiresAt?.toLocaleDateString()})
                      </span>
                    )}
                  </p>
                  {isActive && expiresAt && (
                    <p className="text-xs theme-text-secondary">
                      {t("subscription.renewsOn", {
                        date: expiresAt.toLocaleDateString(),
                      })}
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {isPaidPlan && !isCanceled && (
              <button
                onClick={() => setIsCancelModalOpen(true)}
                className="px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-all hover:scale-105 active:scale-95 border-2 border-red-500 text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
              >
                <FaBan className="w-4 h-4" />
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
              <FaRocket className="w-4 h-4 relative z-10" />
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

        {/* Cancellation Warning Banner */}
        {isCanceled && expiresAt && (
          <div className="mb-4 p-4 rounded-lg bg-orange-50 dark:bg-orange-950 border-2 border-orange-500 flex items-start gap-3">
            <FaExclamationTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-orange-900 dark:text-orange-200 mb-1">
                {t("subscription.subscriptionCanceled")}
              </p>
              <p className="text-sm text-orange-800 dark:text-orange-300">
                {t("subscription.accessUntilDate", {
                  date: expiresAt.toLocaleDateString(),
                })}
              </p>
            </div>
          </div>
        )}

        {/* Past Due Warning Banner */}
        {isPastDue && (
          <div className="mb-4 p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950 border-2 border-yellow-500 flex items-start gap-3">
            <FaExclamationTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-yellow-900 dark:text-yellow-200 mb-1">
                {t("subscription.pastDue.title")}
              </p>
              <p className="text-sm text-yellow-800 dark:text-yellow-300 mb-2">
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
          <div className="mb-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-800 border-2 border-gray-400 flex items-start gap-3">
            <FaBan className="w-5 h-5 text-gray-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-gray-900 dark:text-gray-200 mb-1">
                {t("subscription.paused.title")}
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
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
              <FaCheckCircle className="w-4 h-4" />
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
                    ? "theme-surface theme-border"
                    : "theme-bg-tertiary theme-border opacity-60"
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      feature.enabled
                        ? "theme-accent-light"
                        : "theme-bg-tertiary"
                    }`}
                  >
                    <div
                      className={
                        feature.enabled ? "theme-accent" : "theme-text-tertiary"
                      }
                    >
                      {icon}
                    </div>
                  </div>
                  <div className="flex-1">
                    <h4
                      className={`font-medium ${
                        feature.enabled
                          ? "theme-text-primary"
                          : "theme-text-tertiary"
                      }`}
                    >
                      {name}
                    </h4>
                  </div>
                  <div
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      feature.enabled
                        ? "theme-success-light theme-success"
                        : "theme-bg-tertiary theme-text-tertiary"
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
                      <span className="theme-text-secondary">
                        {t("subscription.used")}:
                      </span>
                      <span
                        className={`font-medium ${
                          isAtLimit
                            ? "theme-error"
                            : isNearLimit
                              ? "theme-warning"
                              : "theme-text-primary"
                        }`}
                      >
                        {currentCount}
                      </span>
                    </div>

                    {limit !== null && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="theme-text-secondary">
                          {t("subscription.limit")}:
                        </span>
                        <span className="theme-text-primary font-medium">
                          {limit}
                        </span>
                      </div>
                    )}

                    {limit !== null && (
                      <div className="w-full theme-bg-tertiary rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            isAtLimit
                              ? "theme-error-bg"
                              : isNearLimit
                                ? "theme-warning-bg"
                                : "theme-success-bg"
                          }`}
                          style={{
                            width: `${Math.min((currentCount / limit) * 100, 100)}%`,
                          }}
                        />
                      </div>
                    )}

                    {limit === null && (
                      <div className="text-sm theme-success">
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
            <FaCrown className="w-8 h-8 theme-text-tertiary mx-auto mb-2" />
            <p className="theme-text-secondary">{t("subscription.noData")}</p>
          </div>
        )}
      </Card>

      <UpgradePlanModal
        isOpen={isUpgradeModalOpen}
        onClose={() => {
          setIsUpgradeModalOpen(false);
          loadSubscriptionLimits();
        }}
        currentPlanCode={subscription?.plan_code}
        paddleSubscriptionId={subscription?.paddle_subscription_id}
      />

      <CancelSubscriptionModal
        isOpen={isCancelModalOpen}
        onClose={() => setIsCancelModalOpen(false)}
        subscription={
          subscription
            ? {
                id: subscription.id,
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
