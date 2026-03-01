import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  AccountResponse,
  AccountTransactionSummary,
} from "../../../types/account";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import {
  getTypeBadgeVariant,
  getStatusBadgeVariant,
  formatBalance,
  formatDate,
  ACCOUNT_TYPE_I18N_MAP,
} from "./accountHelpers";

interface AccountSidePanelProps {
  account: AccountResponse | null;
  transactionSummary: AccountTransactionSummary | null;
  transactionsLoading: boolean;
  isOpen: boolean;
  onClose: () => void;
  onEdit: () => void;
  onArchive: () => void;
}

export const AccountSidePanel: React.FC<AccountSidePanelProps> = ({
  account,
  transactionSummary,
  transactionsLoading,
  isOpen,
  onClose,
  onEdit,
  onArchive,
}) => {
  const { t } = useTranslation();

  // Close on ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  // Prevent body scroll when panel is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!account) return null;

  const balanceClass =
    account.balance >= 0
      ? "text-green-600/80 font-semibold"
      : "text-red-500/80 font-semibold";

  const overviewRows = [
    {
      label: t("accountPage.sidePanel.balance"),
      value: formatBalance(account.balance, account.currency),
      valueClass: balanceClass,
    },
    {
      label: t("accountPage.sidePanel.type"),
      value: t(ACCOUNT_TYPE_I18N_MAP[account.type] || account.type),
      valueClass: "theme-text-primary",
    },
    {
      label: t("accountPage.sidePanel.currency"),
      value: account.currency,
      valueClass: "theme-text-primary",
    },
    {
      label: t("accountPage.sidePanel.created"),
      value: formatDate(account.created_at),
      valueClass: "theme-text-primary",
    },
    {
      label: t("accountPage.sidePanel.transactions"),
      value: transactionSummary
        ? String(transactionSummary.transaction_count)
        : "\u2014",
      valueClass: "theme-text-primary",
    },
  ];

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/30 z-30 transition-opacity duration-300 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={`fixed inset-y-0 right-0 z-40 w-full sm:w-[480px] lg:w-[40%] max-w-[560px] theme-surface border-l theme-border shadow-2xl transform transition-transform duration-300 flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header - sticky */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b theme-border flex-shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="min-w-0">
              <h2 className="text-lg font-semibold theme-text-primary truncate">
                {account.name}
              </h2>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge
                  variant={getTypeBadgeVariant(account.type) as any}
                  size="sm"
                >
                  {t(ACCOUNT_TYPE_I18N_MAP[account.type] || account.type)}
                </Badge>
                <Badge
                  variant={getStatusBadgeVariant(account.is_archived) as any}
                  size="sm"
                >
                  {account.is_archived
                    ? t("accountPage.table.archived")
                    : t("accountPage.table.active")}
                </Badge>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:theme-bg-secondary transition-colors theme-text-secondary flex-shrink-0"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          {/* Overview */}
          <div className="p-4 sm:p-6 space-y-4">
            <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
              {t("accountPage.sidePanel.overview")}
            </h3>
            <div className="space-y-3">
              {overviewRows.map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm theme-text-secondary">
                    {row.label}
                  </span>
                  <span className={`text-sm tabular-nums ${row.valueClass}`}>
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Divider */}
          <div className="border-t theme-border" />

          {/* Financial Summary */}
          {transactionSummary && transactionSummary.transaction_count > 0 && (
            <>
              <div className="p-4 sm:p-6 space-y-3">
                <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
                  {t("accountPage.sidePanel.financialSummary")}
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm theme-text-secondary">
                      {t("accountPage.sidePanel.income")}
                    </span>
                    <span className="text-sm font-semibold tabular-nums text-green-600/80">
                      +
                      {formatBalance(
                        transactionSummary.total_income,
                        account.currency,
                      )}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm theme-text-secondary">
                      {t("accountPage.sidePanel.expenses")}
                    </span>
                    <span className="text-sm font-semibold tabular-nums text-red-500/80">
                      -
                      {formatBalance(
                        transactionSummary.total_expenses,
                        account.currency,
                      )}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t theme-border">
                    <span className="text-sm font-medium theme-text-primary">
                      {t("accountPage.sidePanel.netBalance")}
                    </span>
                    <span
                      className={`text-sm font-semibold tabular-nums ${
                        transactionSummary.net_balance >= 0
                          ? "text-green-600/80"
                          : "text-red-500/80"
                      }`}
                    >
                      {formatBalance(
                        transactionSummary.net_balance,
                        account.currency,
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border-t theme-border" />
            </>
          )}

          {/* Recent Transactions */}
          <div className="p-4 sm:p-6 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
                {t("accountPage.sidePanel.recentTransactions")}
              </h3>
              {transactionSummary &&
                transactionSummary.recent_transactions.length > 0 && (
                  <span className="text-xs theme-text-tertiary">
                    {t("accountPage.sidePanel.transactionsCount", {
                      count: transactionSummary.transaction_count,
                    })}
                  </span>
                )}
            </div>

            {transactionsLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-[var(--color-accent)] border-t-transparent" />
              </div>
            ) : !transactionSummary ||
              transactionSummary.recent_transactions.length === 0 ? (
              <p className="text-sm theme-text-tertiary italic py-2">
                {t("accountPage.sidePanel.noTransactions")}
              </p>
            ) : (
              <div className="rounded-lg border theme-border overflow-x-auto">
                <table className="w-full">
                  <thead className="theme-bg-secondary">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("accountPage.sidePanel.transactionDate")}
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("accountPage.sidePanel.transactionType")}
                      </th>
                      <th className="px-3 py-2 text-right text-xs font-medium theme-text-secondary">
                        {t("accountPage.sidePanel.transactionAmount")}
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("accountPage.sidePanel.transactionDescription")}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y theme-border">
                    {transactionSummary.recent_transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td className="px-3 py-2 text-sm theme-text-secondary tabular-nums">
                          {formatDate(tx.date)}
                        </td>
                        <td className="px-3 py-2">
                          <Badge
                            variant={
                              tx.type === "income" ? "success" : "destructive"
                            }
                            size="sm"
                          >
                            {tx.type === "income" ? "+" : "-"}
                          </Badge>
                        </td>
                        <td
                          className={`px-3 py-2 text-sm font-medium tabular-nums text-right ${
                            tx.type === "income"
                              ? "text-green-600/80"
                              : "text-red-500/80"
                          }`}
                        >
                          {formatBalance(tx.amount, account.currency)}
                        </td>
                        <td className="px-3 py-2 text-sm theme-text-secondary truncate max-w-[120px]">
                          {tx.description || "\u2014"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Action Footer - sticky */}
        <div className="border-t theme-border p-4 sm:p-6 flex-shrink-0">
          <div className="flex flex-wrap gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={onEdit}
              className="flex-1 sm:flex-none"
            >
              {t("accountPage.sidePanel.edit")}
            </Button>
            {!account.is_archived && (
              <Button variant="outline" size="sm" onClick={onArchive}>
                {t("accountPage.sidePanel.archive")}
              </Button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};
