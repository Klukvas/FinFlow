import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { DebtResponse } from "../../../types/debt";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";
import { Pagination } from "../../ui/shared/Pagination";
import {
 getProgressPercentage,
 getDebtStatus,
 getStatusBadgeVariant,
 DEBT_TYPE_I18N_MAP,
} from "./debtHelpers";
import { Skeleton } from "../shared/Skeleton";

interface DebtTableProps {
 debts: DebtResponse[];
 loading: boolean;
 currentPage: number;
 totalPages: number;
 pageSize: number;
 totalItems: number;
 onPageChange: (page: number) => void;
 onPageSizeChange: (size: number) => void;
 onRowClick: (debt: DebtResponse) => void;
 onMakePayment: (debt: DebtResponse) => void;
 onEdit: (debt: DebtResponse) => void;
 onDelete: (debt: DebtResponse) => void;
 emptyMessage?: string | undefined;
}

type SortField = "name" | "balance" | "initial" | "interest" | "dueDate";
type SortOrder = "asc" | "desc";

export const DebtTable: React.FC<DebtTableProps> = ({
 debts,
 loading,
 currentPage,
 totalPages,
 pageSize,
 totalItems,
 onPageChange,
 onPageSizeChange,
 onRowClick,
 onMakePayment,
 onEdit,
 onDelete,
 emptyMessage,
}) => {
 const { t } = useTranslation();
 const [sortField, setSortField] = useState<SortField>("name");
 const [sortOrder, setSortOrder] = useState<SortOrder>("asc");

 const sortedDebts = useMemo(() => {
 const sorted = [...debts].sort((a, b) => {
 let cmp = 0;
 switch (sortField) {
 case "name":
 cmp = a.name.localeCompare(b.name);
 break;
 case "balance":
 cmp = Math.abs(a.current_balance) - Math.abs(b.current_balance);
 break;
 case "initial":
 cmp = Math.abs(a.initial_amount) - Math.abs(b.initial_amount);
 break;
 case "interest":
 cmp = (a.interest_rate ?? 0) - (b.interest_rate ?? 0);
 break;
 case "dueDate":
 cmp = (a.due_date || "").localeCompare(b.due_date || "");
 break;
 }
 return sortOrder === "asc" ? cmp : -cmp;
 });
 return sorted;
 }, [debts, sortField, sortOrder]);

 const toggleSort = (field: SortField) => {
 if (sortField === field) {
 setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
 } else {
 setSortField(field);
 setSortOrder("asc");
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
 if (!dateString) return "—";
 return new Date(dateString).toLocaleDateString("uk-UA");
 };

 if (loading) {
 return (
 <div className="space-y-3 p-4">
 {Array.from({ length: 5 }).map((_, i) => (
 <div key={i} className="flex items-center gap-4">
 <Skeleton className="h-4 flex-[2]" />
 <Skeleton className="h-4 flex-1" />
 <Skeleton className="h-4 flex-1" />
 <Skeleton className="h-4 w-12" />
 <Skeleton className="h-4 flex-1" />
 <Skeleton className="h-4 w-20" />
 <Skeleton className="h-4 w-16" />
 <Skeleton className="h-4 w-16" />
 </div>
 ))}
 </div>
 );
 }

 if (debts.length === 0) {
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
 ? t("debtPage.table.noDebtsAtAll")
 : t("debtPage.table.noDebtsOnPage"))}
 </h3>
 <p className="text-content-secondary text-sm max-w-md mx-auto">
 {totalItems === 0
 ? t("debtPage.table.noDebtsSubtitle")
 : t("debtPage.table.noDebtsOnPageSubtitle")}
 </p>
 </div>
 );
 }

 const thClasses =
 "px-4 py-3 text-xs font-semibold text-content-secondary uppercase tracking-wider";
 const sortableTh = `${thClasses} cursor-pointer select-none hover:text-content transition-colors`;

 return (
 <div className="w-full">
 {/* Mobile Cards View */}
 <div className="block lg:hidden space-y-2 p-4">
 {sortedDebts.map((debt) => {
 const status = getDebtStatus(debt);
 const progress = getProgressPercentage(debt);
 return (
 <div
 key={debt.id}
 className="bg-surface-alt rounded-lg border border-[var(--color-border)] p-3 transition-colors cursor-pointer hover:bg-surface-alt"
 onClick={() => onRowClick(debt)}
 >
 <div className="flex items-start justify-between">
 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2 mb-1">
 <span className="text-sm font-medium text-content truncate">
 {debt.name}
 </span>
 <Badge
 variant={
 getStatusBadgeVariant(status) as
 | "success"
 | "info"
 | "secondary"
 }
 size="sm"
 >
 {t(
 `debtPage.status.${status === "paid_off" ? "paidOff" : status}`,
 )}
 </Badge>
 </div>
 <div className="text-xs text-content-tertiary mb-1">
 {t(DEBT_TYPE_I18N_MAP[debt.debt_type])}
 </div>
 <div className="flex items-center gap-3 mb-2">
 <span className="text-sm font-semibold text-danger-base/80 tabular-nums">
 {Math.abs(debt.current_balance).toLocaleString("uk-UA", {
 minimumFractionDigits: 2,
 })}{" "}
 {debt.currency}
 </span>
 {debt.due_date && (
 <span className="text-xs text-content-tertiary">
 {formatDate(debt.due_date)}
 </span>
 )}
 </div>
 {/* Progress bar */}
 <div className="w-full h-1.5 rounded-full bg-surface-alt overflow-hidden">
 <div
 className="h-full rounded-full bg-success-base/70 transition-all duration-300"
 style={{ width: `${progress}%` }}
 />
 </div>
 </div>
 <div className="flex items-center gap-1 ml-2 flex-shrink-0">
 {!debt.is_paid_off && (
 <Button
 variant="ghost"
 size="sm"
 onClick={(e) => {
 e.stopPropagation();
 onMakePayment(debt);
 }}
 className="text-accent-base !p-1.5 !min-h-0"
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
 d="M12 6v6m0 0v6m0-6h6m-6 0H6"
 />
 </svg>
 </Button>
 )}
 <Button
 variant="ghost"
 size="sm"
 onClick={(e) => {
 e.stopPropagation();
 onDelete(debt);
 }}
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
 </div>
 </div>
 </div>
 );
 })}
 </div>

 {/* Desktop Table View */}
 <div className="hidden lg:block">
 <div className="overflow-x-auto">
 <table className="w-full">
 <thead className="bg-surface-alt sticky top-0 z-10">
 <tr>
 <th
 className={`${sortableTh} text-left`}
 onClick={() => toggleSort("name")}
 >
 {t("debtPage.table.name")}
 <SortIcon field="name" />
 </th>
 <th
 className={`${sortableTh} text-right`}
 onClick={() => toggleSort("balance")}
 >
 {t("debtPage.table.balance")}
 <SortIcon field="balance" />
 </th>
 <th
 className={`${sortableTh} text-right`}
 onClick={() => toggleSort("initial")}
 >
 {t("debtPage.table.initialAmount")}
 <SortIcon field="initial" />
 </th>
 <th
 className={`${sortableTh} text-right`}
 onClick={() => toggleSort("interest")}
 >
 {t("debtPage.table.interest")}
 <SortIcon field="interest" />
 </th>
 <th
 className={`${sortableTh} text-left`}
 onClick={() => toggleSort("dueDate")}
 >
 {t("debtPage.table.dueDate")}
 <SortIcon field="dueDate" />
 </th>
 <th className={`${thClasses} text-center`}>
 {t("debtPage.table.progress")}
 </th>
 <th className={`${thClasses} text-left`}>
 {t("debtPage.table.status")}
 </th>
 <th className={`${thClasses} text-right`}>
 {t("debtPage.table.actions")}
 </th>
 </tr>
 </thead>
 <tbody className="bg-elevated divide-y border-[var(--color-border)]">
 {sortedDebts.map((debt) => {
 const status = getDebtStatus(debt);
 const progress = getProgressPercentage(debt);
 return (
 <tr
 key={debt.id}
 className="hover:bg-surface-alt transition-colors group cursor-pointer"
 onClick={() => onRowClick(debt)}
 >
 <td className="px-4 py-3">
 <div>
 <span className="text-sm font-medium text-content">
 {debt.name}
 </span>
 <span className="block text-xs text-content-tertiary">
 {t(DEBT_TYPE_I18N_MAP[debt.debt_type])}
 </span>
 </div>
 </td>
 <td className="px-4 py-3 text-right">
 <span className="text-sm font-semibold text-danger-base/80 tabular-nums">
 {Math.abs(debt.current_balance).toLocaleString(
 "uk-UA",
 { minimumFractionDigits: 2 },
 )}
 </span>
 <span className="text-xs text-content-tertiary ml-1">
 {debt.currency}
 </span>
 </td>
 <td className="px-4 py-3 text-right">
 <span className="text-sm text-content-secondary tabular-nums">
 {Math.abs(debt.initial_amount).toLocaleString("uk-UA", {
 minimumFractionDigits: 2,
 })}
 </span>
 </td>
 <td className="px-4 py-3 text-right">
 <span className="text-sm text-content-secondary">
 {debt.interest_rate != null
 ? `${debt.interest_rate}%`
 : "—"}
 </span>
 </td>
 <td className="px-4 py-3">
 <span className="text-sm text-content-secondary">
 {formatDate(debt.due_date)}
 </span>
 </td>
 <td className="px-4 py-3">
 <div className="flex items-center gap-2">
 <div className="w-20 h-1.5 rounded-full bg-surface-alt overflow-hidden">
 <div
 className="h-full rounded-full bg-success-base/70 transition-all duration-300"
 style={{ width: `${progress}%` }}
 />
 </div>
 <span className="text-xs text-content-tertiary tabular-nums w-8">
 {Math.round(progress)}%
 </span>
 </div>
 </td>
 <td className="px-4 py-3">
 <Badge
 variant={
 getStatusBadgeVariant(status) as
 | "success"
 | "info"
 | "secondary"
 }
 size="sm"
 >
 {t(
 `debtPage.status.${status === "paid_off" ? "paidOff" : status}`,
 )}
 </Badge>
 </td>
 <td className="px-4 py-3 text-right">
 <div className="flex items-center justify-end gap-1">
 {!debt.is_paid_off && (
 <Button
 variant="ghost"
 size="sm"
 onClick={(e) => {
 e.stopPropagation();
 onMakePayment(debt);
 }}
 className="text-accent-base !p-1.5 !min-h-0"
 title={t("debtPage.sidePanel.makePayment")}
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
 d="M12 6v6m0 0v6m0-6h6m-6 0H6"
 />
 </svg>
 </Button>
 )}
 <Button
 variant="ghost"
 size="sm"
 onClick={(e) => {
 e.stopPropagation();
 onEdit(debt);
 }}
 className="text-content-secondary hover:text-content !p-1.5 !min-h-0"
 title={t("debtPage.sidePanel.edit")}
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
 <Button
 variant="ghost"
 size="sm"
 onClick={(e) => {
 e.stopPropagation();
 onDelete(debt);
 }}
 className="text-danger-base hover:text-danger-base-hover !p-1.5 !min-h-0"
 title={t("debtPage.sidePanel.delete")}
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
 </div>
 </td>
 </tr>
 );
 })}
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
