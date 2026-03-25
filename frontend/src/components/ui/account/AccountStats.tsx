import React from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
import { LineChart, DollarSign, Wallet } from "lucide-react";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface AccountStatistics {
  total_accounts: number;
  active_accounts: number;
  total_balance: number;
  currency: string;
  unconvertible_accounts_count: number;
}

interface AccountStatsProps {
  statistics: AccountStatistics;
  isLoading?: boolean;
}

export const AccountStats: React.FC<AccountStatsProps> = ({
  statistics,
  isLoading = false,
}) => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrencyConversion();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6 animate-pulse">
            <div className="h-6 bg-surface-alt rounded mb-2"></div>
            <div className="h-8 bg-surface-alt rounded w-24"></div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-6">
        <div className="flex items-center">
          <div className="p-3 bg-[var(--accent-dim)] rounded-lg">
            <Wallet className="w-6 h-6 text-accent-base" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-content-secondary">
              {t("accountPage.stats.totalAccounts")}
            </p>
            <p className="text-2xl font-bold text-content">
              {statistics.total_accounts}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center">
          <div className="p-3 bg-[var(--success-dim)] rounded-lg">
            <DollarSign className="w-6 h-6 text-success-base" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-content-secondary">
              {t("accountPage.stats.totalBalance")}
            </p>
            <p className="text-2xl font-mono font-bold text-content">
              {formatCurrency(statistics.total_balance, statistics.currency)}
            </p>
            {statistics.unconvertible_accounts_count > 0 && (
              <p className="text-xs text-warning-base mt-1">
                ⚠️ {statistics.unconvertible_accounts_count}{" "}
                {statistics.unconvertible_accounts_count === 1
                  ? t("accountPage.stats.notIncludedSingle")
                  : t("accountPage.stats.notIncludedPlural")}
              </p>
            )}
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center">
          <div className="p-3 bg-[var(--purple-dim)] rounded-lg">
            <LineChart className="w-6 h-6 text-[var(--purple)]" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-content-secondary">
              {t("accountPage.stats.active")}
            </p>
            <p className="text-2xl font-bold text-content">
              {statistics.active_accounts}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
