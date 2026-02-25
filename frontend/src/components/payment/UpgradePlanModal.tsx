import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { FaCheck, FaTimes, FaSpinner, FaArrowLeft } from "react-icons/fa";
import { Modal } from "@/components/ui/shared/Modal";
import { Button } from "@/components/ui/shared/Button";
import { PaymentButton } from "@/components/payment/PaymentButton";
import { ChangePlanButton } from "@/components/payment/ChangePlanButton";
import { ConsentCheckbox } from "@/components/subscription/ConsentCheckbox";
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
  const [selectedPlan, setSelectedPlan] = useState<PlanWithFeatures | null>(
    null,
  );
  const [showConsentStep, setShowConsentStep] = useState(false);
  const [consentGiven, setConsentGiven] = useState(false);

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
      // Sort plans: basic, professional, enterprise
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

  const calculateNextBillingDate = () => {
    const today = new Date();
    const next = new Date(today);
    next.setMonth(next.getMonth() + 1);
    return next.toISOString().split("T")[0];
  };

  const handlePlanSelect = (plan: PlanWithFeatures) => {
    if (PLAN_PRICING[plan.code].price === 0) {
      return; // Free plan, no selection needed
    }
    setSelectedPlan(plan);
    setShowConsentStep(true);
    setConsentGiven(false);
  };

  const handleBackToPlans = () => {
    setShowConsentStep(false);
    setSelectedPlan(null);
    setConsentGiven(false);
  };

  const handleClose = () => {
    setShowConsentStep(false);
    setSelectedPlan(null);
    setConsentGiven(false);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={
        showConsentStep
          ? t("subscription.reviewTerms", "Review Subscription Terms")
          : t("subscription.upgradePlan")
      }
      size="4xl"
    >
      <div className="space-y-6">
        {!showConsentStep && (
          <p className="theme-text-secondary text-center">
            {t("subscription.upgradeDescription")}
          </p>
        )}

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <FaSpinner className="animate-spin text-4xl theme-text-secondary" />
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={fetchPlans} variant="outline">
              {t("common.retry", "Retry")}
            </Button>
          </div>
        ) : !showConsentStep ? (
          // Step 1: Plan Selection
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const pricing = PLAN_PRICING[plan.code] || { price: 0 };
              const features = Object.values(plan.features);
              const isCurrentPlan = currentPlanCode === plan.code;
              const canSelect = !isCurrentPlan && pricing.price > 0;

              return (
                <div
                  key={plan.code}
                  className={`relative theme-surface theme-border border rounded-xl p-6 transition-all ${
                    isCurrentPlan
                      ? "ring-2 ring-emerald-500"
                      : pricing.popular
                        ? "ring-2 ring-blue-500 scale-[1.02]"
                        : ""
                  } ${canSelect ? "hover:theme-shadow hover:scale-[1.01] cursor-pointer" : ""} ${
                    isCurrentPlan ? "opacity-80" : ""
                  }`}
                  onClick={() => canSelect && handlePlanSelect(plan)}
                >
                  {isCurrentPlan ? (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-4 py-1 rounded-full text-xs font-medium shadow-lg">
                        {t("subscription.currentPlan", "Current Plan")}
                      </span>
                    </div>
                  ) : pricing.popular ? (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-1 rounded-full text-xs font-medium shadow-lg">
                        {t("pricingPage.popular", "Most Popular")}
                      </span>
                    </div>
                  ) : null}

                  <div className="text-center mb-6 pt-2">
                    <h3 className="text-xl font-bold theme-text-primary mb-2">
                      {plan.name}
                    </h3>
                    <div className="mb-4">
                      <span className="text-4xl font-bold theme-text-primary">
                        {pricing.price === 0
                          ? t("pricingPage.free", "Free")
                          : `$${pricing.price}`}
                      </span>
                      <span className="theme-text-secondary text-sm ml-1">
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
                        <FaCheck className="w-4 h-4 theme-success mr-3 mt-0.5 flex-shrink-0" />
                        <span className="theme-text-primary">
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
                      onClick={(e) => {
                        e.stopPropagation();
                        handleClose();
                      }}
                    >
                      {t("pricingPage.free", "Free")}
                    </Button>
                  ) : (
                    <Button
                      variant={pricing.popular ? "primary" : "outline"}
                      fullWidth
                      size="md"
                      onClick={() => handlePlanSelect(plan)}
                    >
                      {t("subscription.selectPlan", "Select Plan")}
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          selectedPlan && (
            // Step 2: Consent and Payment
            <div className="space-y-6">
              {/* Plan Comparison (shown when changing plans) */}
              {currentPlanCode && currentPlanCode !== selectedPlan.code && (
                <div className="flex items-center justify-center gap-4 p-4 rounded-lg theme-bg-secondary border theme-border">
                  <div className="text-center">
                    <p className="text-xs theme-text-secondary mb-1">
                      {t("subscription.currentPlan", "Current Plan")}
                    </p>
                    <p className="font-semibold theme-text-primary">
                      {plans.find((p) => p.code === currentPlanCode)?.name ||
                        currentPlanCode}
                    </p>
                    <p className="text-sm theme-text-secondary">
                      ${PLAN_PRICING[currentPlanCode]?.price ?? 0}/
                      {t("pricingPage.perMonth", "mo")}
                    </p>
                  </div>
                  <div className="text-2xl theme-text-secondary">&rarr;</div>
                  <div className="text-center">
                    <p className="text-xs theme-text-secondary mb-1">
                      {t("subscription.selectPlan", "New Plan")}
                    </p>
                    <p className="font-semibold theme-accent">
                      {selectedPlan.name}
                    </p>
                    <p className="text-sm theme-accent">
                      ${PLAN_PRICING[selectedPlan.code]?.price ?? 0}/
                      {t("pricingPage.perMonth", "mo")}
                    </p>
                  </div>
                </div>
              )}

              <div className="theme-bg-secondary p-4 rounded-lg border theme-border">
                <h3 className="text-lg font-semibold theme-text-primary mb-3">
                  {t(
                    "subscription.subscriptionDetails",
                    "Subscription Details",
                  )}
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="theme-text-secondary">
                      {t("subscription.plan", "Plan")}:
                    </p>
                    <p className="font-semibold theme-text-primary">
                      {selectedPlan.name}
                    </p>
                  </div>
                  <div>
                    <p className="theme-text-secondary">
                      {t("subscription.price", "Price")}:
                    </p>
                    <p className="font-semibold theme-text-primary">
                      {PLAN_PRICING[selectedPlan.code]?.price ?? 0} USD/month
                    </p>
                  </div>
                  <div>
                    <p className="theme-text-secondary">
                      {t("subscription.firstBilling", "First Billing")}:
                    </p>
                    <p className="font-semibold theme-text-primary">
                      {new Date().toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="theme-text-secondary">
                      {t("subscription.nextBilling", "Next Billing")}:
                    </p>
                    <p className="font-semibold theme-text-primary">
                      {new Date(
                        calculateNextBillingDate(),
                      ).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>

              <ConsentCheckbox
                checked={consentGiven}
                onChange={setConsentGiven}
                planName={selectedPlan.name}
                amount={PLAN_PRICING[selectedPlan.code].price}
                currency="USD"
                nextBillingDate={calculateNextBillingDate()}
              />

              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={handleBackToPlans}
                  className="flex items-center gap-2"
                >
                  <FaArrowLeft className="w-4 h-4" />
                  {t("common.back", "Back")}
                </Button>
                {paddleSubscriptionId ? (
                  <ChangePlanButton
                    newPlanCode={selectedPlan.code}
                    newPlanName={selectedPlan.name}
                    paddleSubscriptionId={paddleSubscriptionId}
                    disabled={!consentGiven}
                    variant="primary"
                    size="md"
                    fullWidth
                    onSuccess={handleClose}
                    consentData={{
                      consent_given: consentGiven,
                      consent_version: "v1.0.0",
                      consent_timestamp: new Date().toISOString(),
                      consent_language: i18n.language === "uk" ? "uk" : "en",
                    }}
                  />
                ) : (
                  <PaymentButton
                    planCode={selectedPlan.code}
                    planName={selectedPlan.name}
                    amount={PLAN_PRICING[selectedPlan.code].price}
                    currency="USD"
                    disabled={!consentGiven}
                    variant="primary"
                    size="md"
                    fullWidth
                    onPaymentSuccess={handleClose}
                    consentData={{
                      consent_given: consentGiven,
                      consent_version: "v1.0.0",
                      consent_timestamp: new Date().toISOString(),
                      consent_language: i18n.language === "uk" ? "uk" : "en",
                    }}
                  />
                )}
              </div>
            </div>
          )
        )}
      </div>
    </Modal>
  );
};
