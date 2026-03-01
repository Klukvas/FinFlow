import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Category } from "../../../types/category";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import {
  getTypeBadgeVariant,
  formatDate,
  CATEGORY_TYPE_I18N_MAP,
  CategoryUsageData,
} from "./categoryHelpers";

interface CategorySidePanelProps {
  category: Category | null;
  usageData: CategoryUsageData | null;
  usageLoading: boolean;
  childCategories: Category[];
  isOpen: boolean;
  onClose: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onChildClick: (child: Category) => void;
}

export const CategorySidePanel: React.FC<CategorySidePanelProps> = ({
  category,
  usageData,
  usageLoading,
  childCategories,
  isOpen,
  onClose,
  onEdit,
  onDelete,
  onChildClick,
}) => {
  const { t } = useTranslation();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

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

  if (!category) return null;

  const totalUsage = usageData
    ? usageData.expenseCount + usageData.incomeCount
    : 0;
  const hasChildCategories = childCategories.length > 0;
  const deleteDisabled = hasChildCategories || totalUsage > 0;

  const deleteTooltip = hasChildCategories
    ? t("categoryPage.sidePanel.deleteDisabledChildren")
    : totalUsage > 0
      ? t("categoryPage.sidePanel.deleteDisabledUsage", { count: totalUsage })
      : undefined;

  const overviewRows = [
    {
      label: t("categoryPage.sidePanel.type"),
      value: t(CATEGORY_TYPE_I18N_MAP[category.type] || category.type),
      valueClass: "theme-text-primary",
    },
    {
      label: t("categoryPage.sidePanel.parent"),
      value: category.parent_id
        ? String(category.parent_id)
        : t("categoryPage.table.rootCategory"),
      valueClass: "theme-text-primary",
    },
    {
      label: t("categoryPage.sidePanel.source"),
      value:
        category.created_by === "SYSTEM"
          ? t("categoryPage.sidePanel.system")
          : t("categoryPage.sidePanel.user"),
      valueClass: "theme-text-primary",
    },
    {
      label: t("categoryPage.sidePanel.created"),
      value: formatDate(category.created_at),
      valueClass: "theme-text-primary",
    },
    {
      label: t("categoryPage.sidePanel.updated"),
      value: formatDate(category.updated_at),
      valueClass: "theme-text-primary",
    },
  ];

  if (category.mcc_code) {
    overviewRows.push({
      label: t("categoryPage.sidePanel.mccCode"),
      value: String(category.mcc_code),
      valueClass: "theme-text-primary font-mono",
    });
  }

  // Combine recent expenses + incomes, sorted by date
  const recentTransactions = usageData
    ? [
        ...usageData.recentExpenses.slice(0, 5).map((e) => ({
          id: `exp-${e.id}`,
          date: e.date,
          type: "expense" as const,
          amount: e.amount,
          description: e.description,
          currency: e.currency,
        })),
        ...usageData.recentIncomes.slice(0, 5).map((i) => ({
          id: `inc-${i.id}`,
          date: i.date,
          type: "income" as const,
          amount: i.amount,
          description: i.description,
          currency: i.currency,
        })),
      ]
        .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
        .slice(0, 5)
    : [];

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
                {category.name}
              </h2>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge
                  variant={getTypeBadgeVariant(category.type) as any}
                  size="sm"
                >
                  {t(CATEGORY_TYPE_I18N_MAP[category.type] || category.type)}
                </Badge>
                <Badge
                  variant={
                    category.created_by === "SYSTEM" ? "secondary" : "default"
                  }
                  size="sm"
                >
                  {category.created_by === "SYSTEM"
                    ? t("categoryPage.sidePanel.system")
                    : t("categoryPage.sidePanel.user")}
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
              {t("categoryPage.sidePanel.overview")}
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
                  <span className={`text-sm ${row.valueClass}`}>
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t theme-border" />

          {/* Usage Statistics */}
          <div className="p-4 sm:p-6 space-y-3">
            <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
              {t("categoryPage.sidePanel.usageStatistics")}
            </h3>
            {usageLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-[var(--color-accent)] border-t-transparent" />
              </div>
            ) : !usageData || totalUsage === 0 ? (
              <p className="text-sm theme-text-tertiary italic py-2">
                {t("categoryPage.sidePanel.noTransactions")}
              </p>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm theme-text-secondary">
                    {t("categoryPage.sidePanel.totalTransactions")}
                  </span>
                  <span className="text-sm font-semibold theme-text-primary tabular-nums">
                    {totalUsage}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm theme-text-secondary">
                    {t("categoryPage.sidePanel.expenseCount")}
                  </span>
                  <span className="text-sm tabular-nums text-red-500/80">
                    {usageData.expenseCount}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm theme-text-secondary">
                    {t("categoryPage.sidePanel.incomeCount")}
                  </span>
                  <span className="text-sm tabular-nums text-green-600/80">
                    {usageData.incomeCount}
                  </span>
                </div>
                {usageData.totalAmount > 0 && (
                  <>
                    <div className="flex items-center justify-between pt-2 border-t theme-border">
                      <span className="text-sm theme-text-secondary">
                        {t("categoryPage.sidePanel.totalAmount")}
                      </span>
                      <span className="text-sm font-semibold theme-text-primary tabular-nums">
                        {usageData.totalAmount.toLocaleString("uk-UA", {
                          minimumFractionDigits: 2,
                        })}{" "}
                        {usageData.currency}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm theme-text-secondary">
                        {t("categoryPage.sidePanel.averageAmount")}
                      </span>
                      <span className="text-sm theme-text-primary tabular-nums">
                        {usageData.averageAmount.toLocaleString("uk-UA", {
                          minimumFractionDigits: 2,
                        })}{" "}
                        {usageData.currency}
                      </span>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="border-t theme-border" />

          {/* Subcategories */}
          {hasChildCategories && (
            <>
              <div className="p-4 sm:p-6 space-y-3">
                <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
                  {t("categoryPage.sidePanel.children")}
                </h3>
                <div className="space-y-2">
                  {childCategories.map((child) => (
                    <button
                      key={child.id}
                      className="w-full flex items-center justify-between p-2 rounded-lg hover:theme-bg-secondary transition-colors text-left"
                      onClick={() => onChildClick(child)}
                    >
                      <span className="text-sm theme-text-primary">
                        {child.name}
                      </span>
                      <Badge
                        variant={getTypeBadgeVariant(child.type) as any}
                        size="sm"
                      >
                        {t(CATEGORY_TYPE_I18N_MAP[child.type] || child.type)}
                      </Badge>
                    </button>
                  ))}
                </div>
              </div>
              <div className="border-t theme-border" />
            </>
          )}

          {/* Recent Transactions */}
          <div className="p-4 sm:p-6 space-y-3">
            <h3 className="text-sm font-semibold theme-text-primary uppercase tracking-wide">
              {t("categoryPage.sidePanel.recentTransactions")}
            </h3>
            {usageLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-[var(--color-accent)] border-t-transparent" />
              </div>
            ) : recentTransactions.length === 0 ? (
              <p className="text-sm theme-text-tertiary italic py-2">
                {t("categoryPage.sidePanel.noTransactions")}
              </p>
            ) : (
              <div className="rounded-lg border theme-border overflow-x-auto">
                <table className="w-full">
                  <thead className="theme-bg-secondary">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("categoryPage.sidePanel.transactionDate")}
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("categoryPage.sidePanel.transactionType")}
                      </th>
                      <th className="px-3 py-2 text-right text-xs font-medium theme-text-secondary">
                        {t("categoryPage.sidePanel.transactionAmount")}
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium theme-text-secondary">
                        {t("categoryPage.sidePanel.transactionDescription")}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y theme-border">
                    {recentTransactions.map((tx) => (
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
                          {tx.amount.toLocaleString("uk-UA", {
                            minimumFractionDigits: 2,
                          })}{" "}
                          {tx.currency}
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
              {t("categoryPage.sidePanel.edit")}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onDelete}
              disabled={deleteDisabled && usageData !== null}
              title={deleteTooltip}
            >
              {t("categoryPage.sidePanel.delete")}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};
