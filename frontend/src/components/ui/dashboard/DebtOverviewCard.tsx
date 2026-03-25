import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { DollarSign, ArrowRight } from "lucide-react";
import { DebtSummary } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface DebtOverviewCardProps {
  debtSummary: DebtSummary | null;
}

export const DebtOverviewCard: React.FC<DebtOverviewCardProps> = ({
  debtSummary,
}) => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrencyConversion();

  return (
    <div className="bg-elevated rounded-lg theme-shadow border-[var(--border)] border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <DollarSign className="h-5 w-5 text-accent-base mr-2" />
          <h3 className="text-lg font-semibold text-content">
            {t("dashboard.debt.title")}
          </h3>
        </div>
        <Link
          to="/debts"
          aria-label={t("dashboard.debt.title")}
          className="text-accent-base hover:text-accent-base text-sm font-medium flex items-center transition-colors"
        >
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {!debtSummary || debtSummary.active_debts === 0 ? (
        <p className="text-content-tertiary text-sm">
          {t("dashboard.debt.noDebts")}
        </p>
      ) : (
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-content-secondary">
              {t("dashboard.debt.totalDebt")}
            </span>
            <span className="font-mono font-semibold text-content">
              {formatCurrency(debtSummary.total_debt, debtSummary.currency)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-content-secondary">
              {t("dashboard.debt.active")}
            </span>
            <span className="font-medium text-content">
              {debtSummary.active_debts}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-content-secondary">
              {t("dashboard.debt.paidOff")}
            </span>
            <span className="font-medium text-content">
              {debtSummary.paid_off_debts}
            </span>
          </div>
          {debtSummary.average_interest_rate != null && (
            <div className="flex justify-between">
              <span className="text-sm text-content-secondary">
                {t("dashboard.debt.avgRate")}
              </span>
              <span className="font-medium text-content">
                {debtSummary.average_interest_rate.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
