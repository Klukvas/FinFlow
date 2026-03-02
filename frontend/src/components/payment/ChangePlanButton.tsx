import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/shared/Button";
import { usePayment } from "@/contexts/PaymentContext";
import { useAuth } from "@/contexts/AuthContext";
import { FaSpinner, FaExchangeAlt } from "react-icons/fa";
import { toast } from "sonner";
import { logger } from "@/utils/logger";

interface ConsentData {
  consent_given: boolean;
  consent_version: string;
  consent_timestamp: string;
  consent_language: string;
}

interface ChangePlanButtonProps {
  newPlanCode: string;
  newPlanName: string;
  paddleSubscriptionId: string;
  disabled?: boolean;
  variant?: "primary" | "outline" | "secondary";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  className?: string;
  consentData?: ConsentData;
  onSuccess?: () => void;
}

export const ChangePlanButton: React.FC<ChangePlanButtonProps> = ({
  newPlanCode,
  newPlanName,
  paddleSubscriptionId,
  disabled = false,
  variant = "primary",
  size = "md",
  fullWidth = false,
  className = "",
  consentData,
  onSuccess,
}) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { changePlan, isProcessing } = usePayment();
  const [isChanging, setIsChanging] = useState(false);

  const handleChangePlan = async () => {
    if (!user?.id) {
      toast.error(t("payment.errors.notAuthenticated"));
      return;
    }

    setIsChanging(true);

    try {
      const result = await changePlan({
        user_id: String(user.id),
        new_plan_code: newPlanCode,
        paddle_subscription_id: paddleSubscriptionId,
        ...(consentData ? { metadata: { ...consentData } } : {}),
      });

      if (result?.success) {
        toast.success(
          t("subscription.planChanged", {
            defaultValue: `Plan changed to ${newPlanName}`,
            planName: newPlanName,
          }),
        );
        onSuccess?.();
      } else {
        toast.error(
          t("subscription.planChangeFailed", {
            defaultValue: "Failed to change plan. Please try again.",
          }),
        );
      }
    } catch (error) {
      logger.error("Plan change failed:", error);
      toast.error(
        t("payment.errors.unexpected", {
          defaultValue: "An unexpected error occurred",
        }),
      );
    } finally {
      setIsChanging(false);
    }
  };

  const isButtonDisabled = disabled || isChanging || isProcessing;

  return (
    <Button
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      disabled={isButtonDisabled}
      onClick={handleChangePlan}
      className={className}
    >
      {isChanging || isProcessing ? (
        <>
          <FaSpinner className="animate-spin mr-2" />
          {t("subscription.changingPlan", {
            defaultValue: "Changing plan...",
          })}
        </>
      ) : (
        <>
          <FaExchangeAlt className="mr-2" />
          {t("subscription.changePlan", { defaultValue: "Change Plan" })}
        </>
      )}
    </Button>
  );
};
