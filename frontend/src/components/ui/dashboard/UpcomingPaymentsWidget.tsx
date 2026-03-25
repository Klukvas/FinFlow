import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { CalendarClock, ArrowRight } from "lucide-react";
import { RecurringPayment } from "@/services/api/recurringApi";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface UpcomingPaymentsWidgetProps {
  payments: RecurringPayment[];
}

const getDaysUntil = (dateStr: string): number => {
  const target = new Date(dateStr);
  const now = new Date();
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
};

export const UpcomingPaymentsWidget: React.FC<UpcomingPaymentsWidgetProps> = ({
  payments,
}) => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrencyConversion();

  const formatRelativeDate = (dateStr: string): string => {
    const diffDays = getDaysUntil(dateStr);

    if (diffDays <= 0) return t("dashboard.upcoming.today");
    if (diffDays === 1) return t("dashboard.upcoming.tomorrow");
    if (diffDays <= 7)
      return t("dashboard.upcoming.inDays", { days: diffDays });

    const target = new Date(dateStr);
    return target.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  };

  const upcoming = useMemo(
    () =>
      [...payments]
        .sort(
          (a, b) =>
            new Date(a.next_execution).getTime() -
            new Date(b.next_execution).getTime(),
        )
        .slice(0, 5),
    [payments],
  );

  return (
    <div className="bg-elevated p-6 rounded-lg theme-shadow border-[var(--border)] border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <CalendarClock className="h-5 w-5 text-accent-base mr-2" />
          <h2 className="text-lg font-semibold text-content">
            {t("dashboard.upcoming.title")}
          </h2>
        </div>
        <Link
          to="/recurring"
          className="text-accent-base text-sm font-medium flex items-center gap-1 transition-colors"
        >
          {t("dashboard.upcoming.viewAll")}
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {upcoming.length === 0 ? (
        <div className="text-center py-6">
          <CalendarClock className="w-8 h-8 text-content-secondary mx-auto mb-2" />
          <p className="text-sm text-content-secondary">
            {t("dashboard.upcoming.empty")}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {upcoming.map((payment) => {
            const daysUntil = getDaysUntil(payment.next_execution);
            const isUrgent = daysUntil <= 3;
            const isExpense = payment.payment_type.toUpperCase() === "EXPENSE";

            return (
              <div
                key={payment.id}
                className={`flex items-center justify-between p-2 rounded-lg ${
                  isUrgent
                    ? "bg-[var(--danger-dim)] border border-[var(--danger-dim)]"
                    : "bg-surface-alt"
                }`}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-content truncate">
                    {payment.name}
                  </p>
                  <p className="text-xs text-content-secondary">
                    {formatRelativeDate(payment.next_execution)}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-2">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                      isExpense
                        ? "bg-[var(--danger-dim)] text-danger-base"
                        : "bg-[var(--success-dim)] text-success-base"
                    }`}
                  >
                    {isExpense
                      ? t("dashboard.upcoming.expense")
                      : t("dashboard.upcoming.income")}
                  </span>
                  <span
                    className={`text-sm font-mono font-medium ${
                      isExpense ? "text-danger-base" : "text-success-base"
                    }`}
                  >
                    {isExpense ? "-" : "+"}
                    {formatCurrency(payment.amount, payment.currency)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
