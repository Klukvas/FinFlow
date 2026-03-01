import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { IncomeOut } from "@/types";
import { Pagination } from "@/components/ui";
import { Badge } from "@/components/ui/shared/Badge";
import { Button } from "@/components/ui/shared/Button";

interface IncomeListProps {
  incomes: IncomeOut[];
  loading: boolean;
  categories: Record<number, string>;
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onDeleteRequest?: (income: IncomeOut) => void;
  emptyMessage?: string;
}

type SortField = "date" | "amount" | "category";
type SortOrder = "asc" | "desc";

export const IncomeList: React.FC<IncomeListProps> = ({
  incomes,
  loading,
  categories,
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  onDeleteRequest,
  emptyMessage,
}) => {
  const { t } = useTranslation();
  const [sortField, setSortField] = useState<SortField>("date");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const sortedIncomes = useMemo(() => {
    const sorted = [...incomes].sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "date":
          cmp = new Date(a.date).getTime() - new Date(b.date).getTime();
          break;
        case "amount":
          cmp = a.amount - b.amount;
          break;
        case "category":
          cmp = (categories[a.category_id ?? 0] || "").localeCompare(
            categories[b.category_id ?? 0] || "",
          );
          break;
      }
      return sortOrder === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [incomes, sortField, sortOrder, categories]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
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

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return t("incomePage.list.noDate");
    return new Date(dateString).toLocaleDateString("uk-UA");
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-6 w-6 border-2 border-[var(--color-accent)] border-t-transparent" />
        <span className="ml-3 theme-text-secondary text-sm">
          {t("incomePage.list.loading")}
        </span>
      </div>
    );
  }

  if (incomes.length === 0) {
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
              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"
            />
          </svg>
        </div>
        <h3 className="text-base font-semibold theme-text-primary mb-1">
          {emptyMessage ||
            (totalItems === 0
              ? t("incomePage.list.noIncomesAtAll")
              : t("incomePage.list.noIncomesOnPage"))}
        </h3>
        <p className="theme-text-secondary text-sm max-w-md mx-auto">
          {totalItems === 0
            ? t("incomePage.list.noIncomesSubtitle")
            : t("incomePage.list.noIncomesOnPageSubtitle")}
        </p>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Mobile Cards View */}
      <div className="block lg:hidden space-y-2 p-4">
        {sortedIncomes.map((inc) => (
          <div
            key={inc.id}
            className="theme-bg-secondary rounded-lg border theme-border p-3 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-green-600/80">
                    +{inc.amount.toLocaleString("uk-UA")}
                  </span>
                  <span className="text-xs theme-text-secondary">
                    {inc.currency}
                  </span>
                  <span className="text-xs theme-text-tertiary">
                    {formatDate(inc.date)}
                  </span>
                </div>
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="secondary" size="sm">
                    {categories[inc.category_id ?? 0] ||
                      t("incomePage.list.unknownCategory")}
                  </Badge>
                </div>
                {inc.description && (
                  <p className="text-xs theme-text-secondary truncate">
                    {inc.description}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                {onDeleteRequest && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDeleteRequest(inc)}
                    className="text-red-500 hover:text-red-600 !p-1.5 !min-h-0"
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
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop Table View */}
      <div className="hidden lg:block">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="theme-bg-secondary sticky top-0 z-10">
              <tr>
                <th
                  className="px-4 py-3 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider cursor-pointer select-none hover:theme-text-primary transition-colors"
                  onClick={() => toggleSort("date")}
                >
                  {t("incomePage.list.date")}
                  <SortIcon field="date" />
                </th>
                <th
                  className="px-4 py-3 text-right text-xs font-semibold theme-text-secondary uppercase tracking-wider cursor-pointer select-none hover:theme-text-primary transition-colors"
                  onClick={() => toggleSort("amount")}
                >
                  {t("incomePage.list.amount")}
                  <SortIcon field="amount" />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                  {t("incomePage.list.currency")}
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider cursor-pointer select-none hover:theme-text-primary transition-colors"
                  onClick={() => toggleSort("category")}
                >
                  {t("incomePage.list.category")}
                  <SortIcon field="category" />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                  {t("incomePage.list.description")}
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                  {t("incomePage.list.actions")}
                </th>
              </tr>
            </thead>
            <tbody className="theme-surface divide-y theme-border">
              {sortedIncomes.map((inc) => (
                <tr
                  key={inc.id}
                  className="hover:theme-surface-hover transition-colors group"
                >
                  <td className="px-4 py-3">
                    <span className="text-sm theme-text-secondary">
                      {formatDate(inc.date)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-sm font-semibold text-green-600/80 tabular-nums">
                      +
                      {inc.amount.toLocaleString("uk-UA", {
                        minimumFractionDigits: 2,
                      })}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm theme-text-secondary">
                      {inc.currency}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="secondary" size="sm">
                      {categories[inc.category_id ?? 0] ||
                        t("incomePage.list.unknownCategory")}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm theme-text-secondary max-w-xs truncate block">
                      {inc.description || (
                        <span className="theme-text-tertiary italic">
                          {t("incomePage.list.noDescription")}
                        </span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {onDeleteRequest && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onDeleteRequest(inc)}
                          className="text-red-500 hover:text-red-600 !p-1.5 !min-h-0"
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
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
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
            showPageSizeSelector={true}
            pageSizeOptions={[10, 25, 50]}
          />
        </div>
      )}
    </div>
  );
};
