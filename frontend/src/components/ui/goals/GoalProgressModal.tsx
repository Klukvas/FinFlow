import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Goal, GoalProgressUpdate } from "@/types";
import { Modal } from "../shared/Modal";
import { Button } from "../shared/Button";
import { DollarSign } from "lucide-react";

interface GoalProgressModalProps {
  goal: Goal;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (goalId: number, progress: GoalProgressUpdate) => void;
  isLoading?: boolean;
}

export const GoalProgressModal: React.FC<GoalProgressModalProps> = ({
  goal,
  isOpen,
  onClose,
  onUpdate,
  isLoading = false,
}) => {
  const { t } = useTranslation();
  const [currentAmount, setCurrentAmount] = useState(
    goal.current_amount.toString(),
  );
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const amount = parseFloat(currentAmount);

    if (isNaN(amount) || amount < 0) {
      setError(t("goalsPage.progressModal.enterValidAmount"));
      return;
    }

    if (amount > goal.target_amount) {
      setError(t("goalsPage.progressModal.exceedsTarget"));
      return;
    }

    onUpdate(goal.id, { current_amount: amount });
  };

  const handleClose = () => {
    setCurrentAmount(goal.current_amount.toString());
    setError("");
    onClose();
  };

  const getProgressPercentage = () => {
    const amount = parseFloat(currentAmount);
    if (isNaN(amount) || goal.target_amount === 0) return 0;
    return Math.min((amount / goal.target_amount) * 100, 100);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t("goalsPage.progressModalTitle")}
      size="md"
    >
      <div className="space-y-6">
        {/* Goal Info */}
        <div className="bg-surface-alt rounded-lg p-4">
          <h3 className="font-semibold text-content mb-2">{goal.title}</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-content-secondary">
                {t("goalsPage.progressModal.currentAmount")}:
              </span>
              <p className="font-mono font-medium text-content">
                {goal.current_amount.toLocaleString()} {goal.currency}
              </p>
            </div>
            <div>
              <span className="text-content-secondary">
                {t("goalsPage.progressModal.targetAmount")}:
              </span>
              <p className="font-mono font-medium text-content">
                {goal.target_amount.toLocaleString()} {goal.currency}
              </p>
            </div>
          </div>
        </div>

        {/* Progress Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="current_amount"
              className="block text-sm font-medium text-content mb-2"
            >
              {t("goalsPage.progressModal.newCurrentAmount")}
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <DollarSign className="h-5 w-5 text-content-tertiary" />
              </div>
              <input
                type="number"
                id="current_amount"
                data-testid="goal-progress-amount-input"
                value={currentAmount}
                onChange={(e) => {
                  setCurrentAmount(e.target.value);
                  setError("");
                }}
                step="0.01"
                min="0"
                max={goal.target_amount}
                className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-accent bg-surface text-content ${
                  error
                    ? "bg-[var(--danger-dim)] border-[var(--border)]"
                    : "border-[var(--border)]"
                }`}
                placeholder="0.00"
              />
            </div>
            {error && <p className="mt-1 text-sm text-danger-base">{error}</p>}
          </div>

          {/* Progress Preview */}
          <div className="bg-[var(--accent-dim)] rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-content">
                {t("goalsPage.progressModal.newProgress")}
              </span>
              <span className="text-sm font-bold text-accent-base">
                {getProgressPercentage().toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-surface-alt rounded-full h-2">
              <div
                className="bg-accent-base h-2 rounded-full transition-all duration-300"
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
            <p className="text-xs text-content-secondary mt-2">
              {t("goalsPage.progressModal.remaining")}:{" "}
              {(
                goal.target_amount - parseFloat(currentAmount || "0")
              ).toLocaleString()}{" "}
              {goal.currency}
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={isLoading}
            >
              {t("common.cancel")}
            </Button>
            <Button
              type="submit"
              data-testid="goal-progress-submit"
              disabled={isLoading || !!error}
            >
              {isLoading
                ? t("goalsPage.progressModal.updating")
                : t("goalsPage.progressModal.updateProgress")}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
