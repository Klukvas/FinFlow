import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { ExpenseResponse } from "@/types";
import { EditButton, Pagination } from "@/components/ui";
import { Badge } from "@/components/ui/shared/Badge";
import { Button } from "@/components/ui/shared/Button";

interface ExpenseListProps {
 expenses: ExpenseResponse[];
 loading: boolean;
 categories: Record<number, string>;
 currentPage: number;
 totalPages: number;
 pageSize: number;
 totalItems: number;
 onPageChange: (page: number) => void;
 onPageSizeChange: (size: number) => void;
 onEditExpense?: (expense: ExpenseResponse) => void;
 onDeleteRequest?: (expense: ExpenseResponse) => void;
 emptyMessage?: string | undefined;
}

type SortField = "date" | "amount" | "category";
type SortOrder = "asc" | "desc";

export const ExpenseList: React.FC<ExpenseListProps> = ({
 expenses,
 loading,
 categories,
 currentPage,
 totalPages,
 pageSize,
 totalItems,
 onPageChange,
 onPageSizeChange,
 onEditExpense,
 onDeleteRequest,
 emptyMessage,
}) => {
 const { t } = useTranslation();
 const [sortField, setSortField] = useState<SortField>("date");
 const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

 const sortedExpenses = useMemo(() => {
 const sorted = [...expenses].sort((a, b) => {
 let cmp = 0;
 switch (sortField) {
 case "date":
 cmp =
 new Date(a.date ?? 0).getTime() - new Date(b.date ?? 0).getTime();
 break;
 case "amount":
 cmp = a.amount - b.amount;
 break;
 case "category":
 cmp = (
 a.category_id != null ? categories[a.category_id] || "" : ""
 ).localeCompare(
 b.category_id != null ? categories[b.category_id] || "" : "",
 );
 break;
 }
 return sortOrder === "asc" ? cmp : -cmp;
 });
 return sorted;
 }, [expenses, sortField, sortOrder, categories]);

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
 return <span className="text-[10px] text-content-tertiary ml-1">↕</span>;
 return (
 <span className="text-[10px] text-accent-base ml-1">
 {sortOrder === "asc" ? "↑" : "↓"}
 </span>
 );
 };

 const formatDate = (dateString: string | null | undefined) => {
 if (!dateString) return t("expense.list.noDate");
 return new Date(dateString).toLocaleDateString("uk-UA");
 };

 if (loading) {
 return (
 <div className="flex justify-center items-center py-12">
 <div className="animate-spin rounded-full h-6 w-6 border-2 border-[var(--color-accent)] border-t-transparent" />
 <span className="ml-3 text-content-secondary text-sm">
 {t("expense.list.loading")}
 </span>
 </div>
 );
 }

 if (expenses.length === 0) {
 return (
 <div className="text-center py-12">
 <div className="w-16 h-16 mx-auto mb-4 bg-surface-alt rounded-xl flex items-center justify-center">
 <svg
 className="w-8 h-8 text-content-tertiary"
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
 <h3 className="text-base font-semibold text-content mb-1">
 {emptyMessage ||
 (totalItems === 0
 ? t("expense.list.noExpensesAtAll")
 : t("expense.list.noExpensesOnPage"))}
 </h3>
 <p className="text-content-secondary text-sm max-w-md mx-auto">
 {totalItems === 0
 ? t("expense.list.noExpensesSubtitle")
 : t("expense.list.noExpensesOnPageSubtitle")}
 </p>
 </div>
 );
 }

 return (
 <div className="w-full">
 {/* Mobile Cards View */}
 <div className="block lg:hidden space-y-2 p-4">
 {sortedExpenses.map((expense) => (
 <div
 key={expense.id}
 className="bg-surface-alt rounded-lg border border-[var(--color-border)] p-3 transition-colors"
 >
 <div className="flex items-start justify-between">
 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2 mb-1">
 <span className="text-sm font-semibold text-danger-base/80">
 {expense.amount.toLocaleString("uk-UA")}
 </span>
 <span className="text-xs text-content-secondary">
 {expense.currency}
 </span>
 <span className="text-xs text-content-tertiary">
 {formatDate(expense.date)}
 </span>
 </div>
 <div className="flex items-center gap-2 mb-1">
 <Badge variant="secondary" size="sm">
 {(expense.category_id != null
 ? categories[expense.category_id]
 : undefined) || t("expense.list.unknownCategory")}
 </Badge>
 </div>
 {expense.description && (
 <p className="text-xs text-content-secondary truncate">
 {expense.description}
 </p>
 )}
 </div>
 <div className="flex items-center gap-1 ml-2 flex-shrink-0">
 {onEditExpense && (
 <EditButton
 onEdit={() => onEditExpense(expense)}
 variant="icon"
 size="sm"
 />
 )}
 {onDeleteRequest && (
 <Button
 variant="ghost"
 size="sm"
 onClick={() => onDeleteRequest(expense)}
 className="text-danger-base hover:text-danger-base-hover !p-1.5 !min-h-0"
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
 <thead className="bg-surface-alt sticky top-0 z-10">
 <tr>
 <th
 className="px-4 py-3 text-left text-xs font-semibold text-content-secondary uppercase tracking-wider cursor-pointer select-none hover:text-content transition-colors"
 onClick={() => toggleSort("date")}
 >
 {t("expense.list.date")}
 <SortIcon field="date" />
 </th>
 <th
 className="px-4 py-3 text-right text-xs font-semibold text-content-secondary uppercase tracking-wider cursor-pointer select-none hover:text-content transition-colors"
 onClick={() => toggleSort("amount")}
 >
 {t("expense.list.amount")}
 <SortIcon field="amount" />
 </th>
 <th className="px-4 py-3 text-left text-xs font-semibold text-content-secondary uppercase tracking-wider">
 {t("expense.list.currency")}
 </th>
 <th
 className="px-4 py-3 text-left text-xs font-semibold text-content-secondary uppercase tracking-wider cursor-pointer select-none hover:text-content transition-colors"
 onClick={() => toggleSort("category")}
 >
 {t("expense.list.category")}
 <SortIcon field="category" />
 </th>
 <th className="px-4 py-3 text-left text-xs font-semibold text-content-secondary uppercase tracking-wider">
 {t("expense.list.description")}
 </th>
 <th className="px-4 py-3 text-right text-xs font-semibold text-content-secondary uppercase tracking-wider">
 {t("expense.list.actions")}
 </th>
 </tr>
 </thead>
 <tbody className="bg-elevated divide-y border-[var(--color-border)]">
 {sortedExpenses.map((expense) => (
 <tr
 key={expense.id}
 className="hover:bg-surface-alt transition-colors group"
 >
 <td className="px-4 py-3">
 <span className="text-sm text-content-secondary">
 {formatDate(expense.date)}
 </span>
 </td>
 <td className="px-4 py-3 text-right">
 <span className="text-sm font-semibold text-danger-base/80 tabular-nums">
 {expense.amount.toLocaleString("uk-UA", {
 minimumFractionDigits: 2,
 })}
 </span>
 </td>
 <td className="px-4 py-3">
 <span className="text-sm text-content-secondary">
 {expense.currency}
 </span>
 </td>
 <td className="px-4 py-3">
 <Badge variant="secondary" size="sm">
 {(expense.category_id != null
 ? categories[expense.category_id]
 : undefined) || t("expense.list.unknownCategory")}
 </Badge>
 </td>
 <td className="px-4 py-3">
 <span className="text-sm text-content-secondary max-w-xs truncate block">
 {expense.description || (
 <span className="text-content-tertiary italic">
 {t("expense.list.noDescription")}
 </span>
 )}
 </span>
 </td>
 <td className="px-4 py-3 text-right">
 <div className="flex items-center justify-end gap-1">
 {onEditExpense && (
 <EditButton
 onEdit={() => onEditExpense(expense)}
 variant="icon"
 size="sm"
 />
 )}
 {onDeleteRequest && (
 <Button
 variant="ghost"
 size="sm"
 onClick={() => onDeleteRequest(expense)}
 className="text-danger-base hover:text-danger-base-hover !p-1.5 !min-h-0"
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
 <div className="p-4 border-t border-[var(--color-border)]">
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
