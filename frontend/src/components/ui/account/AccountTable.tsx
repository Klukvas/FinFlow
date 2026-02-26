import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Lock } from "lucide-react";
import { AccountResponse, AccountSummary } from "../../../types/account";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import { Pagination } from "../shared/Pagination";
import {
  getTypeBadgeVariant,
  getStatusBadgeVariant,
  formatBalance,
  formatDate,
  groupAccounts,
  ACCOUNT_TYPE_I18N_MAP,
} from "./accountHelpers";
import { Skeleton } from "../shared/Skeleton";

interface AccountTableProps {
  accounts: AccountResponse[];
  summaries: AccountSummary[];
  loading: boolean;
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onRowClick: (account: AccountResponse) => void;
  onEdit: (account: AccountResponse) => void;
  onArchive: (account: AccountResponse) => void;
  groupBy?: "none" | "currency" | "type";
  emptyMessage?: string;
}

type SortField =
  | "name"
  | "type"
  | "currency"
  | "balance"
  | "transactions"
  | "created";
type SortOrder = "asc" | "desc";

export const AccountTable: React.FC<AccountTableProps> = ({
  accounts,
  summaries,
  loading,
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  onRowClick,
  onEdit,
  onArchive,
  groupBy = "none",
  emptyMessage,
}) => {
  const { t } = useTranslation();
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(
    new Set(),
  );

  const summaryMap = useMemo(
    () => new Map(summaries.map((s) => [s.id, s])),
    [summaries],
  );

  const sortedAccounts = useMemo(() => {
    const sorted = [...accounts].sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "type":
          cmp = a.type.localeCompare(b.type);
          break;
        case "currency":
          cmp = a.currency.localeCompare(b.currency);
          break;
        case "balance":
          cmp = a.balance - b.balance;
          break;
        case "transactions": {
          const aCount = summaryMap.get(a.id)?.transaction_count ?? 0;
          const bCount = summaryMap.get(b.id)?.transaction_count ?? 0;
          cmp = aCount - bCount;
          break;
        }
        case "created":
          cmp = (a.created_at || "").localeCompare(b.created_at || "");
          break;
      }
      return sortOrder === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [accounts, sortField, sortOrder, summaryMap]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const toggleGroup = (key: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const SortIcon: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field)
      return <span className="text-[10px] theme-text-tertiary ml-1">↕</span>;
    return (
      <span className="text-[10px] theme-accent ml-1">
        {sortOrder === "asc" ? "↑" : "↓"}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="space-y-3 p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 flex-[2]" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-12" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-12" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (accounts.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 theme-bg-tertiary rounded-xl flex items-center justify-center">
          <svg
            className="w-8 h-8 theme-text-tertiary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
            />
          </svg>
        </div>
        <h3 className="text-base font-semibold theme-text-primary mb-1">
          {emptyMessage || t("accountPage.table.noAccounts")}
        </h3>
        <p className="theme-text-secondary text-sm max-w-md mx-auto">
          {!emptyMessage && t("accountPage.table.noAccountsDescription")}
        </p>
      </div>
    );
  }

  const thClasses =
    "px-4 py-3 text-xs font-semibold theme-text-secondary uppercase tracking-wider";
  const sortableTh = `${thClasses} cursor-pointer select-none hover:theme-text-primary transition-colors`;

  const groups = groupAccounts(sortedAccounts, groupBy);
  const isGrouped = groupBy !== "none";

  const getGroupLabel = (key: string): string => {
    if (groupBy === "type") {
      return t(ACCOUNT_TYPE_I18N_MAP[key] || key);
    }
    return key; // currency codes are already readable
  };

  const renderRow = (account: AccountResponse) => {
    const summary = summaryMap.get(account.id);
    const balanceClass =
      account.balance >= 0
        ? "text-green-600/80 dark:text-green-400/70"
        : "text-red-500/80 dark:text-red-400/70";

    return (
      <tr
        key={account.id}
        className="hover:theme-surface-hover transition-colors group cursor-pointer"
        onClick={() => onRowClick(account)}
      >
        <td className="px-4 py-3">
          <span className="text-sm font-medium theme-text-primary inline-flex items-center gap-1.5">
            {account.name}
            {account.is_read_only && (
              <Lock className="w-4 h-4 text-amber-500 flex-shrink-0" />
            )}
          </span>
        </td>
        <td className="px-4 py-3">
          <Badge variant={getTypeBadgeVariant(account.type) as any} size="sm">
            {t(ACCOUNT_TYPE_I18N_MAP[account.type] || account.type)}
          </Badge>
        </td>
        <td className="px-4 py-3">
          <span className="text-sm theme-text-secondary">
            {account.currency}
          </span>
        </td>
        <td className="px-4 py-3 text-right">
          <span
            className={`text-sm font-semibold tabular-nums ${balanceClass}`}
          >
            {formatBalance(account.balance, account.currency)}
          </span>
        </td>
        <td className="px-4 py-3 text-right">
          <span className="text-sm theme-text-secondary tabular-nums">
            {summary?.transaction_count ?? "\u2014"}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className="text-sm theme-text-secondary">
            {formatDate(account.created_at)}
          </span>
        </td>
        <td className="px-4 py-3">
          <Badge
            variant={getStatusBadgeVariant(account.is_archived) as any}
            size="sm"
          >
            {account.is_archived
              ? t("accountPage.table.archived")
              : t("accountPage.table.active")}
          </Badge>
        </td>
        <td className="px-4 py-3 text-right">
          <div className="flex items-center justify-end gap-1">
            <Button
              variant="ghost"
              size="sm"
              disabled={account.is_read_only}
              onClick={(e) => {
                e.stopPropagation();
                onEdit(account);
              }}
              className="theme-text-secondary hover:theme-text-primary !p-1.5 !min-h-0"
              title={
                account.is_read_only
                  ? "Read-only: upgrade or delete excess records"
                  : t("accountPage.sidePanel.edit")
              }
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </Button>
            {!account.is_archived && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onArchive(account);
                }}
                className="text-red-500/60 hover:text-red-500 !p-1.5 !min-h-0"
                title={t("accountPage.sidePanel.archive")}
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"
                  />
                </svg>
              </Button>
            )}
          </div>
        </td>
      </tr>
    );
  };

  const renderMobileCard = (account: AccountResponse) => {
    const summary = summaryMap.get(account.id);
    const balanceClass =
      account.balance >= 0
        ? "text-green-600/80 dark:text-green-400/70"
        : "text-red-500/80 dark:text-red-400/70";

    return (
      <div
        key={account.id}
        className="theme-bg-secondary rounded-lg border theme-border p-3 transition-colors cursor-pointer hover:theme-surface-hover"
        onClick={() => onRowClick(account)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium theme-text-primary truncate inline-flex items-center gap-1.5">
                {account.name}
                {account.is_read_only && (
                  <Lock className="w-4 h-4 text-amber-500 flex-shrink-0" />
                )}
              </span>
              <Badge
                variant={getTypeBadgeVariant(account.type) as any}
                size="sm"
              >
                {t(ACCOUNT_TYPE_I18N_MAP[account.type] || account.type)}
              </Badge>
              {account.is_archived && (
                <Badge variant="secondary" size="sm">
                  {t("accountPage.table.archived")}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`text-sm font-semibold tabular-nums ${balanceClass}`}
              >
                {formatBalance(account.balance, account.currency)}
              </span>
              {summary && (
                <span className="text-xs theme-text-tertiary">
                  {summary.transaction_count}{" "}
                  {t("accountPage.table.transactions").toLowerCase()}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 ml-2 flex-shrink-0">
            <Button
              variant="ghost"
              size="sm"
              disabled={account.is_read_only}
              onClick={(e) => {
                e.stopPropagation();
                onEdit(account);
              }}
              className="theme-text-secondary !p-1.5 !min-h-0"
              title={
                account.is_read_only
                  ? "Read-only: upgrade or delete excess records"
                  : undefined
              }
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
            </Button>
            {!account.is_archived && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onArchive(account);
                }}
                className="text-red-500/60 hover:text-red-500 !p-1.5 !min-h-0"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"
                  />
                </svg>
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full">
      {/* Mobile Cards View */}
      <div className="block lg:hidden space-y-2 p-4">
        {isGrouped
          ? Object.entries(groups).map(([key, groupAccts]) => (
              <div key={key}>
                <button
                  className="w-full flex items-center justify-between px-3 py-2 theme-bg-secondary rounded-lg mb-2 text-sm font-medium theme-text-primary"
                  onClick={() => toggleGroup(key)}
                >
                  <span>
                    {getGroupLabel(key)} ({groupAccts.length})
                  </span>
                  <svg
                    className={`w-4 h-4 transition-transform ${collapsedGroups.has(key) ? "" : "rotate-180"}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {!collapsedGroups.has(key) && (
                  <div className="space-y-2 mb-3">
                    {groupAccts.map(renderMobileCard)}
                  </div>
                )}
              </div>
            ))
          : sortedAccounts.map(renderMobileCard)}
      </div>

      {/* Desktop Table View */}
      <div className="hidden lg:block">
        <div className="overflow-hidden">
          <table className="w-full">
            <thead className="theme-bg-secondary sticky top-0 z-10">
              <tr>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("name")}
                >
                  {t("accountPage.table.name")}
                  <SortIcon field="name" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("type")}
                >
                  {t("accountPage.table.type")}
                  <SortIcon field="type" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("currency")}
                >
                  {t("accountPage.table.currency")}
                  <SortIcon field="currency" />
                </th>
                <th
                  className={`${sortableTh} text-right`}
                  onClick={() => toggleSort("balance")}
                >
                  {t("accountPage.table.balance")}
                  <SortIcon field="balance" />
                </th>
                <th
                  className={`${sortableTh} text-right`}
                  onClick={() => toggleSort("transactions")}
                >
                  {t("accountPage.table.transactions")}
                  <SortIcon field="transactions" />
                </th>
                <th
                  className={`${sortableTh} text-left`}
                  onClick={() => toggleSort("created")}
                >
                  {t("accountPage.table.created")}
                  <SortIcon field="created" />
                </th>
                <th className={`${thClasses} text-left`}>
                  {t("accountPage.table.status")}
                </th>
                <th className={`${thClasses} text-right`}>
                  {t("accountPage.table.actions")}
                </th>
              </tr>
            </thead>
            {isGrouped ? (
              Object.entries(groups).map(([key, groupAccts]) => (
                <tbody key={key} className="theme-surface">
                  <tr
                    className="theme-bg-secondary cursor-pointer hover:theme-surface-hover transition-colors"
                    onClick={() => toggleGroup(key)}
                  >
                    <td colSpan={8} className="px-4 py-2">
                      <div className="flex items-center gap-2">
                        <svg
                          className={`w-4 h-4 theme-text-secondary transition-transform ${collapsedGroups.has(key) ? "" : "rotate-180"}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                        <span className="text-sm font-semibold theme-text-primary">
                          {getGroupLabel(key)}
                        </span>
                        <span className="text-xs theme-text-tertiary">
                          ({groupAccts.length})
                        </span>
                      </div>
                    </td>
                  </tr>
                  {!collapsedGroups.has(key) && groupAccts.map(renderRow)}
                </tbody>
              ))
            ) : (
              <tbody className="theme-surface divide-y theme-border">
                {sortedAccounts.map(renderRow)}
              </tbody>
            )}
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="p-4 border-t theme-border">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            itemsPerPage={pageSize}
            totalItems={totalItems}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            showPageSizeSelector
            pageSizeOptions={[10, 25, 50]}
          />
        </div>
      )}
    </div>
  );
};
