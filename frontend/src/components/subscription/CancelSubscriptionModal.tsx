import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Modal } from "@/components/ui/shared/Modal";
import { Button } from "@/components/ui/shared/Button";
import { FaExclamationTriangle, FaSpinner } from "react-icons/fa";
import { toast } from "sonner";
import { useApiClients } from "@/hooks/useApiClients";

interface Subscription {
  id: number;
  plan_code: string;
  plan_name?: string;
  expires_at: string | null;
  amount?: number;
  currency?: string;
}

interface CancelSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  subscription: Subscription | null;
  onCancelSuccess: () => void;
}

const CANCELLATION_REASONS = [
  { value: "too_expensive", label: "cancellation.reasons.tooExpensive" },
  { value: "not_using", label: "cancellation.reasons.notUsing" },
  { value: "missing_features", label: "cancellation.reasons.missingFeatures" },
  {
    value: "switching_service",
    label: "cancellation.reasons.switchingService",
  },
  { value: "other", label: "cancellation.reasons.other" },
];

export const CancelSubscriptionModal: React.FC<
  CancelSubscriptionModalProps
> = ({ isOpen, onClose, subscription, onCancelSuccess }) => {
  const { t } = useTranslation();
  const { subscription: subscriptionApi } = useApiClients();
  const [cancelImmediately, setCancelImmediately] = useState(false);
  const [reason, setReason] = useState("");
  const [comment, setComment] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!subscription) {
    return null;
  }

  const expiresAt = subscription.expires_at
    ? new Date(subscription.expires_at)
    : null;
  const formattedExpiryDate = expiresAt
    ? expiresAt.toLocaleDateString()
    : "N/A";

  const handleCancel = async () => {
    setIsSubmitting(true);

    try {
      const result = await subscriptionApi.cancelSubscription(subscription.id, {
        cancellation_reason: reason || undefined,
        cancellation_comment: comment || undefined,
        cancel_immediately: cancelImmediately,
      });

      if ("error" in result) {
        throw new Error(result.error);
      }

      toast.success(
        cancelImmediately
          ? t(
              "cancellation.successImmediate",
              "Subscription canceled immediately",
            )
          : t("cancellation.successPeriodEnd", {
              date: formattedExpiryDate,
              defaultValue: `Subscription canceled. Access until ${formattedExpiryDate}`,
            }),
      );

      onCancelSuccess();
      onClose();
    } catch (error) {
      console.error("Cancellation error:", error);
      toast.error(t("cancellation.error", "Failed to cancel subscription"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("cancellation.title", "Cancel Subscription?")}
      size="lg"
    >
      <div className="space-y-6">
        {/* Warning */}
        <div className="flex items-start gap-3 p-4 rounded-lg theme-bg-warning border theme-border-warning">
          <FaExclamationTriangle className="w-5 h-5 theme-warning flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-semibold theme-text-primary mb-1">
              {t("cancellation.warning", "Are you sure you want to cancel?")}
            </h4>
            <p className="text-sm theme-text-secondary">
              {t(
                "cancellation.warningText",
                "This action will stop future charges to your payment method.",
              )}
            </p>
          </div>
        </div>

        {/* Subscription Info */}
        <div className="theme-bg-secondary p-4 rounded-lg border theme-border">
          <h4 className="font-semibold theme-text-primary mb-3">
            {t("cancellation.currentSubscription", "Current Subscription")}
          </h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="theme-text-secondary">
                {t("subscription.plan", "Plan")}:
              </p>
              <p className="font-medium theme-text-primary">
                {subscription.plan_name || subscription.plan_code}
              </p>
            </div>
            <div>
              <p className="theme-text-secondary">
                {t("subscription.periodEnds", "Period Ends")}:
              </p>
              <p className="font-medium theme-text-primary">
                {formattedExpiryDate}
              </p>
            </div>
            {subscription.amount && (
              <div>
                <p className="theme-text-secondary">
                  {t("subscription.amount", "Amount")}:
                </p>
                <p className="font-medium theme-text-primary">
                  {subscription.amount} {subscription.currency || "UAH"}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Cancellation Options */}
        <div className="space-y-4">
          <h4 className="font-semibold theme-text-primary">
            {t("cancellation.whenToCancel", "When to cancel?")}
          </h4>

          <label className="flex items-start gap-3 p-4 rounded-lg border theme-border cursor-pointer hover:theme-bg-secondary transition-colors">
            <input
              type="radio"
              name="cancelType"
              checked={!cancelImmediately}
              onChange={() => setCancelImmediately(false)}
              className="mt-1 w-4 h-4 theme-accent-border"
            />
            <div className="flex-1">
              <p className="font-medium theme-text-primary mb-1">
                {t("cancellation.endOfPeriod", "Cancel at end of period")} (
                {t("cancellation.recommended", "Recommended")})
              </p>
              <p className="text-sm theme-text-secondary">
                {t(
                  "cancellation.endOfPeriodDesc",
                  `Keep full access until ${formattedExpiryDate}. No refund needed.`,
                )}
              </p>
            </div>
          </label>

          <label className="flex items-start gap-3 p-4 rounded-lg border theme-border cursor-pointer hover:theme-bg-secondary transition-colors">
            <input
              type="radio"
              name="cancelType"
              checked={cancelImmediately}
              onChange={() => setCancelImmediately(true)}
              className="mt-1 w-4 h-4 theme-accent-border"
            />
            <div className="flex-1">
              <p className="font-medium theme-text-primary mb-1">
                {t("cancellation.immediately", "Cancel immediately")}
              </p>
              <p className="text-sm theme-text-secondary">
                {t(
                  "cancellation.immediatelyDesc",
                  "Lose access now. May issue pro-rata refund.",
                )}
              </p>
            </div>
          </label>
        </div>

        {/* Reason (Optional) */}
        <div className="space-y-2">
          <label
            htmlFor="cancelReason"
            className="text-sm font-medium theme-text-primary"
          >
            {t("cancellation.reason", "Reason for canceling")} (
            {t("common.optional", "optional")})
          </label>
          <select
            id="cancelReason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border theme-border theme-bg-primary theme-text-primary focus:ring-2 focus:ring-blue-500"
          >
            <option value="">
              {t("cancellation.selectReason", "Select a reason...")}
            </option>
            {CANCELLATION_REASONS.map((r) => (
              <option key={r.value} value={r.value}>
                {t(r.label, r.value.replace("_", " "))}
              </option>
            ))}
          </select>
        </div>

        {/* Comment (Optional) */}
        <div className="space-y-2">
          <label
            htmlFor="cancelComment"
            className="text-sm font-medium theme-text-primary"
          >
            {t("cancellation.additionalComments", "Additional comments")} (
            {t("common.optional", "optional")})
          </label>
          <textarea
            id="cancelComment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            maxLength={500}
            placeholder={t(
              "cancellation.commentPlaceholder",
              "Tell us why you're canceling...",
            )}
            className="w-full px-3 py-2 rounded-lg border theme-border theme-bg-primary theme-text-primary focus:ring-2 focus:ring-blue-500 resize-none"
          />
          <p className="text-xs theme-text-secondary text-right">
            {comment.length}/500
          </p>
        </div>

        {/* What Happens */}
        <div className="theme-bg-secondary p-4 rounded-lg border theme-border">
          <h4 className="font-semibold theme-text-primary mb-2">
            {t("cancellation.whatHappens", "What happens after cancellation?")}
          </h4>
          <ul className="space-y-1 text-sm theme-text-secondary">
            <li className="flex items-start gap-2">
              <span className="theme-success mt-1">✓</span>
              <span>
                {t(
                  "cancellation.noFutureCharges",
                  "No future charges will be made",
                )}
              </span>
            </li>
            {!cancelImmediately && (
              <li className="flex items-start gap-2">
                <span className="theme-success mt-1">✓</span>
                <span>
                  {t("cancellation.keepAccess", {
                    date: formattedExpiryDate,
                    defaultValue: `Keep full access until ${formattedExpiryDate}`,
                  })}
                </span>
              </li>
            )}
            <li className="flex items-start gap-2">
              <span className="theme-success mt-1">✓</span>
              <span>
                {t("cancellation.dataPreserved", "Your data will be preserved")}
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="theme-success mt-1">✓</span>
              <span>
                {t("cancellation.canReactivate", "You can reactivate anytime")}
              </span>
            </li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            variant="outline"
            onClick={onClose}
            fullWidth
            disabled={isSubmitting}
          >
            {t("common.keepSubscription", "Keep Subscription")}
          </Button>
          <Button
            variant="danger"
            onClick={handleCancel}
            fullWidth
            disabled={isSubmitting}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {isSubmitting ? (
              <>
                <FaSpinner className="animate-spin mr-2" />
                {t("common.processing", "Processing...")}
              </>
            ) : (
              t("common.cancelSubscription", "Cancel Subscription")
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
