import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/shared/Button";
import { usePayment } from "@/contexts/PaymentContext";
import { useAuth } from "@/contexts/AuthContext";
import { usePaddle } from "@/hooks/usePaddle";
import { PaymentPurpose } from "@/types/payment";
import { FaSpinner, FaCrown, FaLock } from "react-icons/fa";
import { toast } from "sonner";
import { config } from "@/config/env";
import { logger } from "@/utils/logger";

interface ConsentData {
  consent_given: boolean;
  consent_version: string;
  consent_timestamp: string;
  consent_language: string;
}

interface PaymentButtonProps {
  planCode: string;
  planName: string;
  amount: number;
  currency?: string;
  variant?: "primary" | "outline" | "secondary";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  disabled?: boolean;
  className?: string;
  consentData?: ConsentData;
  onPaymentSuccess?: () => void;
}

export const PaymentButton: React.FC<PaymentButtonProps> = ({
  planCode,
  planName,
  amount,
  currency = "USD",
  variant = "primary",
  size = "lg",
  fullWidth = false,
  disabled = false,
  className = "",
  consentData,
  onPaymentSuccess,
}) => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { createPayment, isProcessing } = usePayment();
  const [isCreating, setIsCreating] = useState(false);

  const { openCheckout } = usePaddle({
    onCheckoutComplete: () => {
      toast.success(
        t("payment.success", { defaultValue: "Payment successful!" }),
      );
      onPaymentSuccess?.();
      navigate("/payment/return");
    },
    onCheckoutClosed: () => {
      setIsCreating(false);
    },
  });

  const handlePayment = async () => {
    if (!config.features.paymentsEnabled) {
      toast.error(
        t("payment.errors.paymentsDisabled", {
          defaultValue:
            "Payments are temporarily disabled. Please contact support.",
        }),
      );
      return;
    }

    if (!user?.id) {
      toast.error(t("payment.errors.notAuthenticated"));
      navigate("/login");
      return;
    }

    setIsCreating(true);

    try {
      const returnUrl = `${window.location.origin}/payment/return`;

      const payment = await createPayment({
        user_id: String(user.id),
        ...(user.default_workspace_id
          ? { workspace_id: String(user.default_workspace_id) }
          : {}),
        purpose: PaymentPurpose.SUBSCRIPTION,
        plan_code: planCode,
        amount: amount,
        currency: currency,
        return_url: returnUrl,
        metadata: {
          plan_name: planName,
          user_email: user.email,
          ...(consentData || {}),
        },
      });

      if (!payment) {
        toast.error(t("payment.errors.createFailed"));
        setIsCreating(false);
        return;
      }

      // Store payment ID for return page
      localStorage.setItem("pending_payment_id", payment.id);
      localStorage.setItem("pending_plan_code", planCode);

      logger.info("Payment created:", {
        transaction_id: payment.transaction_id,
        checkout_url: payment.checkout_url,
        provider_payment_url: payment.provider_payment_url,
      });

      // Use Paddle.js overlay checkout with transaction ID
      if (payment.transaction_id) {
        // Map i18n language to ISO 3166-1 alpha-2 country code
        const langToCountry: Record<string, string> = {
          uk: "UA",
          en: "US",
          ru: "RU",
        };
        const opened = openCheckout(payment.transaction_id, {
          email: user.email,
          ...(langToCountry[i18n.language]
            ? { countryCode: langToCountry[i18n.language] }
            : {}),
          locale: i18n.language,
        });
        if (!opened) {
          toast.error(
            "Failed to open Paddle checkout. Check console for details.",
          );
          setIsCreating(false);
        }
        // No redirect fallback — overlay should open on this page
        return;
      }

      toast.error("No transaction ID returned. Cannot open checkout.");
      setIsCreating(false);
    } catch (error) {
      logger.error("Payment creation failed:", error);
      toast.error(t("payment.errors.unexpected"));
      setIsCreating(false);
    }
  };

  const isButtonDisabled =
    disabled || isCreating || isProcessing || !config.features.paymentsEnabled;

  return (
    <Button
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      disabled={isButtonDisabled}
      onClick={handlePayment}
      className={className}
      title={
        !config.features.paymentsEnabled
          ? t("payment.errors.paymentsDisabled", {
              defaultValue: "Payments are temporarily disabled",
            })
          : undefined
      }
    >
      {!config.features.paymentsEnabled ? (
        <>
          <FaLock className="mr-2" />
          {t("payment.disabled", { defaultValue: "Payments Disabled" })}
        </>
      ) : isCreating || isProcessing ? (
        <>
          <FaSpinner className="animate-spin mr-2" />
          {t("payment.processing")}
        </>
      ) : (
        <>
          <FaCrown className="mr-2" />
          {t("payment.choosePlan")}
        </>
      )}
    </Button>
  );
};
