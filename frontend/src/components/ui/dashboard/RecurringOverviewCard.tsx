import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { RefreshCw, ArrowRight } from "lucide-react";
import { PaymentStatistics } from "@/services/api/recurringApi";

interface RecurringOverviewCardProps {
  recurringStats: PaymentStatistics | null;
}

export const RecurringOverviewCard: React.FC<RecurringOverviewCardProps> = ({
  recurringStats,
}) => {
  const { t } = useTranslation();

  return (
    <div className="bg-elevated rounded-lg theme-shadow border-[var(--border)] border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <RefreshCw className="h-5 w-5 text-accent-base mr-2" />
          <h3 className="text-lg font-semibold text-content">
            {t("dashboard.recurring.title")}
          </h3>
        </div>
        <Link
          to="/recurring"
          aria-label={t("dashboard.recurring.title")}
          className="text-accent-base hover:text-accent-base text-sm font-medium flex items-center transition-colors"
        >
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {!recurringStats || recurringStats.active_payments === 0 ? (
        <p className="text-content-tertiary text-sm">
          {t("dashboard.recurring.noRecurring")}
        </p>
      ) : (
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-content-secondary">
              {t("dashboard.recurring.active")}
            </span>
            <span className="font-semibold text-content">
              {recurringStats.active_payments}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-content-secondary">
              {t("dashboard.recurring.executed")} (
              {t("dashboard.recurring.thisMonth")})
            </span>
            <span className="font-medium text-content">
              {recurringStats.executed_this_month}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-content-secondary">
              {t("dashboard.recurring.failed")} (
              {t("dashboard.recurring.thisMonth")})
            </span>
            <span
              className={`font-medium ${recurringStats.failed_this_month > 0 ? "text-danger-base" : "text-content"}`}
            >
              {recurringStats.failed_this_month}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
