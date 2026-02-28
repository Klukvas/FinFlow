import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { FaDollarSign, FaArrowRight } from "react-icons/fa";
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
    <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <FaDollarSign className="h-5 w-5 theme-accent mr-2" />
          <h3 className="text-lg font-semibold theme-text-primary">
            {t("dashboard.debt.title")}
          </h3>
        </div>
        <Link
          to="/debts"
          aria-label={t("dashboard.debt.title")}
          className="theme-accent hover:theme-accent text-sm font-medium flex items-center theme-transition"
        >
          <FaArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {!debtSummary || debtSummary.active_debts === 0 ? (
        <p className="theme-text-tertiary text-sm">
          {t("dashboard.debt.noDebts")}
        </p>
      ) : (
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm theme-text-secondary">
              {t("dashboard.debt.totalDebt")}
            </span>
            <span className="font-semibold theme-text-primary">
              {formatCurrency(debtSummary.total_debt, debtSummary.currency)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm theme-text-secondary">
              {t("dashboard.debt.active")}
            </span>
            <span className="font-medium theme-text-primary">
              {debtSummary.active_debts}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm theme-text-secondary">
              {t("dashboard.debt.paidOff")}
            </span>
            <span className="font-medium theme-text-primary">
              {debtSummary.paid_off_debts}
            </span>
          </div>
          {debtSummary.average_interest_rate != null && (
            <div className="flex justify-between">
              <span className="text-sm theme-text-secondary">
                {t("dashboard.debt.avgRate")}
              </span>
              <span className="font-medium theme-text-primary">
                {debtSummary.average_interest_rate.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
