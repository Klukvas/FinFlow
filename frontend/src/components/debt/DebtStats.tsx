import React from "react";
import { useTranslation } from "react-i18next";
import { DebtSummary } from "@/types/debt";
import { Card, CardContent } from "@/components/ui";
import {
  DollarSign,
  TrendingDown,
  CreditCard,
  CheckCircle,
} from "lucide-react";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface DebtStatsProps {
  summary: DebtSummary | null;
}

export const DebtStats: React.FC<DebtStatsProps> = ({ summary }) => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrencyConversion();

  if (!summary) {
    return null;
  }

  const formatAmount = (amount: number) => {
    return formatCurrency(amount, summary.currency);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <Card className="theme-surface theme-border border">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium theme-text-tertiary">
                {t("debtPage.stats.totalDebt")}
              </p>
              <p className="text-2xl font-bold theme-text-primary">
                {formatAmount(summary.total_debt)}
              </p>
            </div>
            <div className="p-3 rounded-full theme-error-light">
              <TrendingDown className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="theme-surface theme-border border">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium theme-text-tertiary">
                {t("debtPage.stats.totalPaid")}
              </p>
              <p className="text-2xl font-bold theme-text-primary">
                {formatAmount(summary.total_payments)}
              </p>
            </div>
            <div className="p-3 rounded-full theme-success-light">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="theme-surface theme-border border">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium theme-text-tertiary">
                {t("debtPage.stats.activeDebts")}
              </p>
              <p className="text-2xl font-bold theme-text-primary">
                {summary.active_debts}
              </p>
            </div>
            <div className="p-3 rounded-full theme-accent-light">
              <CreditCard className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="theme-surface theme-border border">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium theme-text-tertiary">
                {t("debtPage.stats.paidOff")}
              </p>
              <p className="text-2xl font-bold theme-text-primary">
                {summary.paid_off_debts}
              </p>
            </div>
            <div className="p-3 rounded-full theme-success-light">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
