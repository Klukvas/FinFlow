import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { FaRedo, FaArrowRight } from "react-icons/fa";
import { PaymentStatistics } from "@/services/api/recurringApi";

interface RecurringOverviewCardProps {
  recurringStats: PaymentStatistics | null;
}

export const RecurringOverviewCard: React.FC<RecurringOverviewCardProps> = ({
  recurringStats,
}) => {
  const { t } = useTranslation();

  return (
    <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <FaRedo className="h-5 w-5 theme-accent mr-2" />
          <h3 className="text-lg font-semibold theme-text-primary">
            {t("dashboard.recurring.title")}
          </h3>
        </div>
        <Link
          to="/recurring"
          aria-label={t("dashboard.recurring.title")}
          className="theme-accent hover:theme-accent text-sm font-medium flex items-center theme-transition"
        >
          <FaArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {!recurringStats || recurringStats.active_payments === 0 ? (
        <p className="theme-text-tertiary text-sm">
          {t("dashboard.recurring.noRecurring")}
        </p>
      ) : (
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm theme-text-secondary">
              {t("dashboard.recurring.active")}
            </span>
            <span className="font-semibold theme-text-primary">
              {recurringStats.active_payments}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm theme-text-secondary">
              {t("dashboard.recurring.executed")} (
              {t("dashboard.recurring.thisMonth")})
            </span>
            <span className="font-medium theme-text-primary">
              {recurringStats.executed_this_month}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm theme-text-secondary">
              {t("dashboard.recurring.failed")} (
              {t("dashboard.recurring.thisMonth")})
            </span>
            <span
              className={`font-medium ${recurringStats.failed_this_month > 0 ? "text-red-500" : "theme-text-primary"}`}
            >
              {recurringStats.failed_this_month}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
