import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { FaWallet, FaArrowRight } from "react-icons/fa";
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
    <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <FaWallet className="h-5 w-5 theme-accent mr-2" />
          <h3 className="text-lg font-semibold theme-text-primary">
            {t("dashboard.accounts.title")}
          </h3>
        </div>
        <Link
          to="/account"
          className="theme-accent hover:theme-accent text-sm font-medium flex items-center theme-transition"
        >
          {t("dashboard.accounts.viewAll")}
          <FaArrowRight className="ml-1 w-3 h-3" />
        </Link>
      </div>

      {accounts.length === 0 ? (
        <p className="theme-text-tertiary text-sm">
          {t("dashboard.accounts.noAccounts")}
        </p>
      ) : (
        <div className="space-y-3">
          {accounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between p-3 theme-bg-secondary rounded-lg"
            >
              <div className="flex items-center gap-2">
                <span className="font-medium theme-text-primary text-sm">
                  {account.name}
                </span>
                <Badge size="sm" variant="outline">
                  {account.currency}
                </Badge>
              </div>
              <span className="font-semibold theme-text-primary">
                {formatCurrency(account.balance, account.currency)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
