import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Check, Loader2 } from "lucide-react";
import { Modal } from "@/components/ui/shared/Modal";
import { Button } from "@/components/ui/shared/Button";
import { PaymentButton } from "@/components/payment/PaymentButton";
import { ChangePlanButton } from "@/components/payment/ChangePlanButton";
import { useApiClients } from "@/hooks/useApiClients";
import { PlanWithFeatures } from "@/types/subscription";
import { PLAN_PRICING } from "@/config/plans";

interface UpgradePlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlanCode?: string;
  paddleSubscriptionId?: string;
}

export const UpgradePlanModal: React.FC<UpgradePlanModalProps> = ({
  isOpen,
  onClose,
  currentPlanCode,
  paddleSubscriptionId,
}) => {
  const { t, i18n } = useTranslation();
  const { subscription } = useApiClients();
  const [plans, setPlans] = useState<PlanWithFeatures[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchPlans();
    }
  }, [isOpen]);

  const fetchPlans = async () => {
    setLoading(true);
    setError(null);

    const result = await subscription.getPlansWithFeatures();

    if ("error" in result) {
      setError(result.error);
    } else {
      const sortedPlans = result.sort((a, b) => {
        const order = ["basic", "professional", "enterprise"];
        return order.indexOf(a.code) - order.indexOf(b.code);
      });
      setPlans(sortedPlans);
    }

    setLoading(false);
  };

  const formatFeatureLimit = (feature: {
    name: string;
    limit_value: number | null;
  }): string => {
    if (feature.limit_value === null) {
      return `Unlimited ${feature.name}`;
    }
    return `${feature.limit_value} ${feature.name}`;
  };

  const makeConsentData = () => ({
    consent_given: true,
    consent_version: "v1.0.0",
    consent_timestamp: new Date().toISOString(),
    consent_language: i18n.language === "uk" ? "uk" : "en",
  });

  const handleClose = () => {
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t("subscription.upgradePlan")}
      size="4xl"
    >
      <div className="space-y-6">
        <p className="text-content-secondary text-center">
          {t("subscription.upgradeDescription")}
        </p>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="animate-spin text-4xl text-content-secondary" />
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-danger-base mb-4">{error}</p>
            <Button onClick={fetchPlans} variant="outline">
              {t("common.retry", "Retry")}
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const pricing = PLAN_PRICING[plan.code] || { price: 0 };
              const features = Object.values(plan.features);
              const isCurrentPlan = currentPlanCode === plan.code;

              return (
                <div
                  key={plan.code}
                  className={`relative bg-elevated border-[var(--border)] border rounded-xl p-6 transition-all ${
                    isCurrentPlan
                      ? "ring-2 ring-[var(--success)]"
                      : pricing.popular
                        ? "ring-2 ring-[var(--accent)] scale-[1.02]"
                        : ""
                  } ${isCurrentPlan ? "opacity-80" : ""}`}
                >
                  {isCurrentPlan ? (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-[var(--success-dim)] text-[var(--success)] px-4 py-1 rounded-full text-xs font-medium">
                        {t("subscription.currentPlan", "Current Plan")}
                      </span>
                    </div>
                  ) : pricing.popular ? (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-[var(--accent-dim)] text-[var(--accent)] px-4 py-1 rounded-full text-xs font-medium">
                        {t("pricingPage.popular", "Most Popular")}
                      </span>
                    </div>
                  ) : null}

                  <div className="text-center mb-6 pt-2">
                    <h3 className="text-xl font-bold text-content mb-2">
                      {plan.name}
                    </h3>
                    <div className="mb-4">
                      <span className="text-4xl font-bold text-content">
                        {pricing.price === 0
                          ? t("pricingPage.free", "Free")
                          : `$${pricing.price}`}
                      </span>
                      <span className="text-content-secondary text-sm ml-1">
                        {pricing.price === 0
                          ? ""
                          : t("pricingPage.perMonth", "/month")}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-3 mb-6 min-h-[280px]">
                    {features.map((feature) => (
                      <div
                        key={feature.code}
                        className="flex items-start text-sm"
                      >
                        <Check className="w-4 h-4 text-success-base mr-3 mt-0.5 flex-shrink-0" />
                        <span className="text-content">
                          {formatFeatureLimit(feature)}
                        </span>
                      </div>
                    ))}
                  </div>

                  {isCurrentPlan ? (
                    <Button variant="outline" fullWidth size="md" disabled>
                      {t("subscription.currentPlan", "Current Plan")}
                    </Button>
                  ) : pricing.price === 0 ? (
                    <Button
                      variant="outline"
                      fullWidth
                      size="md"
                      onClick={handleClose}
                    >
                      {t("pricingPage.free", "Free")}
                    </Button>
                  ) : paddleSubscriptionId ? (
                    <ChangePlanButton
                      newPlanCode={plan.code}
                      newPlanName={plan.name}
                      paddleSubscriptionId={paddleSubscriptionId}
                      variant={pricing.popular ? "primary" : "outline"}
                      size="md"
                      fullWidth
                      onSuccess={handleClose}
                      consentData={makeConsentData()}
                    />
                  ) : (
                    <PaymentButton
                      planCode={plan.code}
                      planName={plan.name}
                      amount={pricing.price}
                      currency="USD"
                      variant={pricing.popular ? "primary" : "outline"}
                      size="md"
                      fullWidth
                      onPaymentSuccess={handleClose}
                      consentData={makeConsentData()}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Modal>
  );
};
