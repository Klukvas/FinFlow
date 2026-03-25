import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Wallet, ArrowRight } from "lucide-react";
import { Badge } from "../shared/Badge";
import { AccountSummary } from "@/types";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface AccountBalancesCardProps {
  accounts: AccountSummary[];
}

export const AccountBalancesCard: React.FC<AccountBalancesCardProps> = ({
  accounts,
}) => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrencyConversion();

  return (
    <div
      className="bg-elevated rounded-lg theme-shadow border-[var(--border)] border p-6"
      data-testid="dashboard-account-balances"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Wallet className="h-5 w-5 text-accent-base mr-2" strokeWidth={1.5} />
          <h3 className="text-lg font-semibold text-content">
            {t("dashboard.accounts.title")}
          </h3>
        </div>
        <Link
          to="/account"
          className="text-accent-base hover:text-accent-base text-sm font-medium flex items-center transition-colors"
        >
          {t("dashboard.accounts.viewAll")}
          <ArrowRight className="ml-1 w-3 h-3" strokeWidth={1.5} />
        </Link>
      </div>

      {accounts.length === 0 ? (
        <p className="text-content-tertiary text-sm">
          {t("dashboard.accounts.noAccounts")}
        </p>
      ) : (
        <div className="space-y-3">
          {accounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between p-3 bg-surface-alt rounded-lg"
            >
              <div className="flex items-center gap-2">
                <span className="font-medium text-content text-sm">
                  {account.name}
                </span>
                <Badge size="sm" variant="outline">
                  {account.currency}
                </Badge>
              </div>
              <span className="font-mono font-semibold text-content">
                {formatCurrency(account.balance, account.currency)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
