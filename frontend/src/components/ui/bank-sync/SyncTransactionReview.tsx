import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useApiClients } from "@/hooks/useApiClients";
import {
 SyncPreviewTransaction,
 SyncConfirmTransaction,
} from "@/types/bankSync";
import { Category } from "@/types";
import { Skeleton } from "@/components/ui/shared/Skeleton";
import { logger } from "@/utils/logger";

interface SyncTransactionReviewProps {
 transactions: SyncPreviewTransaction[];
 totalFound: number;
 totalSkipped: number;
 onConfirm: (transactions: SyncConfirmTransaction[]) => void;
 onClose: () => void;
 isConfirming: boolean;
}

interface EditableTransaction extends SyncPreviewTransaction {
 included: boolean;
}

const TransactionRowSkeleton: React.FC = () => (
 <div className="border-[var(--border)] border rounded-lg p-4">
 <div className="flex items-start gap-3">
 <Skeleton
 variant="rectangular"
 width={16}
 height={16}
 className="mt-1 rounded"
 />
 <div className="flex-1 space-y-3">
 <div className="flex flex-wrap items-center gap-2">
 <Skeleton variant="text" className="h-5 w-16" />
 <Skeleton variant="text" className="h-5 w-24" />
 <Skeleton variant="text" className="h-4 w-20" />
 </div>
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 <Skeleton variant="rectangular" className="h-8 w-full rounded-md" />
 <Skeleton variant="rectangular" className="h-8 w-full rounded-md" />
 </div>
 </div>
 </div>
 </div>
);

export const SyncTransactionReview: React.FC<SyncTransactionReviewProps> = ({
 transactions,
 totalFound,
 totalSkipped,
 onConfirm,
 onClose,
 isConfirming,
}) => {
 const { t } = useTranslation();
 const { category: categoryApi, expense, income } = useApiClients();

 const [editableTransactions, setEditableTransactions] = useState<
 EditableTransaction[]
 >([]);
 const [categories, setCategories] = useState<Category[]>([]);
 const [isLoading, setIsLoading] = useState(true);

 // Limit state
 const [expenseCount, setExpenseCount] = useState(0);
 const [incomeCount, setIncomeCount] = useState(0);
 const [expenseLimit, setExpenseLimit] = useState<number | null>(null);
 const [incomeLimit, setIncomeLimit] = useState<number | null>(null);

 useEffect(() => {
 const init = async () => {
 try {
 const [catResult, expenseData, incomeData] = await Promise.all([
 categoryApi.getCategories(),
 expense.getCurrentMonthCount(),
 income.getCurrentMonthCount(),
 ]);

 if (!("error" in catResult)) {
 setCategories(catResult);
 }
 if (!("error" in expenseData)) {
 setExpenseCount(expenseData.count);
 setExpenseLimit(expenseData.limit);
 }
 if (!("error" in incomeData)) {
 setIncomeCount(incomeData.count);
 setIncomeLimit(incomeData.limit);
 }
 } catch (err) {
 logger.error("SyncTransactionReview: Failed to load data", err);
 } finally {
 setIsLoading(false);
 }
 };

 setEditableTransactions(
 transactions.map((txn) => ({ ...txn, included: true })),
 );
 init();
 // eslint-disable-next-line react-hooks/exhaustive-deps
 }, [transactions]);

 // Warn user before leaving the page (browser tab close / navigation)
 const hasUnsavedChanges = editableTransactions.length > 0 && !isConfirming;

 const handleBeforeUnload = useCallback(
 (e: BeforeUnloadEvent) => {
 if (hasUnsavedChanges) {
 e.preventDefault();
 }
 },
 [hasUnsavedChanges],
 );

 useEffect(() => {
 window.addEventListener("beforeunload", handleBeforeUnload);
 return () => window.removeEventListener("beforeunload", handleBeforeUnload);
 }, [handleBeforeUnload]);

 const updateTransaction = (
 index: number,
 updates: Partial<EditableTransaction>,
 ) => {
 setEditableTransactions((prev) =>
 prev.map((txn, i) => (i === index ? { ...txn, ...updates } : txn)),
 );
 };

 const toggleAll = (included: boolean) => {
 setEditableTransactions((prev) =>
 prev.map((txn) => ({ ...txn, included })),
 );
 };

 // Stats
 const stats = useMemo(() => {
 const selected = editableTransactions.filter((t) => t.included);
 return {
 total: editableTransactions.length,
 selected: selected.length,
 expenses: selected.filter((t) => t.type === "expense").length,
 incomes: selected.filter((t) => t.type === "income").length,
 };
 }, [editableTransactions]);

 // Limit validation
 const limitWarnings = useMemo(() => {
 const warnings: string[] = [];
 if (expenseLimit !== null) {
 const remaining = expenseLimit - expenseCount;
 if (stats.expenses > remaining) {
 warnings.push(
 t("bankSync.review.expenseQuota", {
 count: expenseCount + stats.expenses,
 limit: expenseLimit,
 }) +
 " — " +
 t("bankSync.review.limitWarning"),
 );
 }
 }
 if (incomeLimit !== null) {
 const remaining = incomeLimit - incomeCount;
 if (stats.incomes > remaining) {
 warnings.push(
 t("bankSync.review.incomeQuota", {
 count: incomeCount + stats.incomes,
 limit: incomeLimit,
 }) +
 " — " +
 t("bankSync.review.limitWarning"),
 );
 }
 }
 return warnings;
 }, [stats, expenseCount, incomeCount, expenseLimit, incomeLimit, t]);

 const canConfirm = stats.selected > 0 && limitWarnings.length === 0;

 const handleConfirm = () => {
 const selected: SyncConfirmTransaction[] = editableTransactions
 .filter((t) => t.included)
 .map((t) => ({
 external_id: t.external_id,
 type: t.type,
 amount: t.amount,
 currency: t.currency,
 date: t.date,
 description: t.description,
 category_id: t.category_id,
 account_id: t.account_id,
 }));
 onConfirm(selected);
 };

 return (
 <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 overflow-y-auto p-2 sm:p-4">
 <div className="bg-elevated rounded-xl theme-shadow-hover w-full max-w-6xl max-h-[95vh] overflow-hidden flex flex-col mx-auto">
 {/* Header */}
 <div className="flex justify-between items-center p-4 sm:p-6 border-[var(--border)] border-b bg-surface-alt">
 <div className="flex-1 min-w-0">
 <h2 className="text-xl sm:text-2xl font-bold text-content">
 {t("bankSync.review.title")}
 </h2>
 <p className="text-sm text-content-secondary mt-1">
 {t("bankSync.review.subtitle")}
 </p>
 </div>
 <button
 onClick={onClose}
 disabled={isConfirming}
 className="text-content-tertiary hover:text-content rounded-full p-2 transition-colors flex-shrink-0"
 >
 <svg
 className="w-5 h-5 sm:w-6 sm:h-6"
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

 {isLoading ? (
 /* Skeleton loading state */
 <>
 {/* Stats skeleton */}
 <div className="p-4 sm:p-6 bg-surface-alt border-[var(--border)] border-b">
 <div className="flex flex-wrap items-center gap-4 sm:gap-6">
 <Skeleton variant="text" className="h-5 w-20" />
 <Skeleton variant="text" className="h-5 w-24" />
 <Skeleton variant="text" className="h-5 w-24" />
 <Skeleton variant="text" className="h-5 w-20" />
 </div>
 </div>

 {/* Transaction rows skeleton */}
 <div className="flex-1 overflow-y-auto">
 <div className="p-4 sm:p-6 space-y-3">
 {Array.from({ length: Math.min(transactions.length, 6) }).map(
 (_, i) => (
 <TransactionRowSkeleton key={i} />
 ),
 )}
 </div>
 </div>

 {/* Footer skeleton */}
 <div className="flex justify-between items-center p-4 sm:p-6 border-[var(--border)] border-t bg-surface-alt">
 <Skeleton variant="text" className="h-5 w-32" />
 <div className="flex gap-3">
 <Skeleton
 variant="rectangular"
 className="h-9 w-20 rounded-lg"
 />
 <Skeleton
 variant="rectangular"
 className="h-9 w-40 rounded-lg"
 />
 </div>
 </div>
 </>
 ) : (
 /* Loaded content */
 <>
 {/* Limit warnings */}
 {limitWarnings.length > 0 && (
 <div className="mx-4 sm:mx-6 mt-4 space-y-2">
 {limitWarnings.map((warning, idx) => (
 <div
 key={idx}
 className="p-3 bg-[var(--warning-dim)] border-l-4 border-warning-base rounded-r-lg"
 >
 <p className="text-sm text-warning-base">{warning}</p>
 </div>
 ))}
 </div>
 )}

 {/* Stats bar */}
 <div className="p-4 sm:p-6 bg-surface-alt border-[var(--border)] border-b">
 <div className="flex flex-wrap items-center gap-4 sm:gap-6">
 <div className="flex items-center space-x-2">
 <div className="w-3 h-3 bg-accent-base rounded-full" />
 <span className="text-xs sm:text-sm font-medium text-content">
 {t("bankSync.review.total")}: {stats.total}
 </span>
 </div>
 <div className="flex items-center space-x-2">
 <div className="w-3 h-3 bg-success-base rounded-full" />
 <span className="text-xs sm:text-sm font-medium text-content">
 {t("bankSync.review.selected")}: {stats.selected}
 </span>
 </div>
 <div className="flex items-center space-x-2">
 <div className="w-3 h-3 bg-danger-base rounded-full" />
 <span className="text-xs sm:text-sm font-medium text-content">
 {t("bankSync.review.expenses")}: {stats.expenses}
 </span>
 </div>
 <div className="flex items-center space-x-2">
 <div className="w-3 h-3 bg-success-base rounded-full" />
 <span className="text-xs sm:text-sm font-medium text-content">
 {t("bankSync.review.incomes")}: {stats.incomes}
 </span>
 </div>
 {totalSkipped > 0 && (
 <span className="text-xs text-content-secondary">
 {t("bankSync.review.skippedDuplicates", {
 count: totalSkipped,
 })}
 </span>
 )}
 </div>

 {/* Quota info */}
 {(expenseLimit !== null || incomeLimit !== null) && (
 <div className="flex flex-wrap gap-4 mt-3 pt-3 border-t border-[var(--border)]">
 {expenseLimit !== null && (
 <span className="text-xs text-content-secondary">
 {t("bankSync.review.expenseQuota", {
 count: expenseCount,
 limit: expenseLimit,
 })}{" "}
 (
 {t("bankSync.review.quotaRemaining", {
 remaining: Math.max(0, expenseLimit - expenseCount),
 })}
 )
 </span>
 )}
 {incomeLimit !== null && (
 <span className="text-xs text-content-secondary">
 {t("bankSync.review.incomeQuota", {
 count: incomeCount,
 limit: incomeLimit,
 })}{" "}
 (
 {t("bankSync.review.quotaRemaining", {
 remaining: Math.max(0, incomeLimit - incomeCount),
 })}
 )
 </span>
 )}
 </div>
 )}

 {/* Select/deselect all */}
 <div className="flex gap-3 mt-3">
 <button
 onClick={() => toggleAll(true)}
 className="text-xs text-accent-base hover:text-accent-base font-medium"
 >
 {t("bankSync.review.selectAll")}
 </button>
 <button
 onClick={() => toggleAll(false)}
 className="text-xs text-accent-base hover:text-accent-base font-medium"
 >
 {t("bankSync.review.deselectAll")}
 </button>
 </div>
 </div>

 {/* Transactions list */}
 <div className="flex-1 overflow-y-auto">
 <div className="p-4 sm:p-6 space-y-3">
 {editableTransactions.map((txn, index) => (
 <div
 key={txn.external_id}
 className={`border-[var(--border)] border rounded-lg p-4 transition-colors ${
 txn.included
 ? "bg-elevated"
 : "opacity-50 bg-surface-alt"
 }`}
 >
 <div className="flex items-start gap-3">
 {/* Checkbox */}
 <label className="flex items-center mt-1 cursor-pointer flex-shrink-0">
 <input
 type="checkbox"
 checked={txn.included}
 onChange={() =>
 updateTransaction(index, {
 included: !txn.included,
 })
 }
 className="w-4 h-4 text-accent-base rounded focus:ring-[var(--accent)]"
 />
 </label>

 {/* Content */}
 <div className="flex-1 min-w-0">
 <div className="flex flex-wrap items-center gap-2 mb-2">
 {/* Type badge */}
 <span
 className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
 txn.type === "income"
 ? "bg-[var(--success-dim)] text-success-base"
 : "bg-[var(--danger-dim)] text-danger-base"
 }`}
 >
 {txn.type === "income" ? "+" : "-"}{" "}
 {txn.type.toUpperCase()}
 </span>

 {/* Amount */}
 <span className="text-sm font-semibold text-content">
 {Number(txn.amount).toFixed(2)} {txn.currency}
 </span>

 {/* Date */}
 <span className="text-xs text-content-secondary">
 {txn.date}
 </span>

 {/* MCC */}
 {txn.mcc && (
 <span className="text-xs text-content-tertiary">
 MCC: {txn.mcc}
 </span>
 )}
 </div>

 {/* Editable fields */}
 <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
 {/* Description */}
 <div>
 <label className="block text-xs font-medium text-content-secondary mb-1">
 {t("bankSync.review.description")}
 </label>
 <input
 type="text"
 value={txn.description}
 onChange={(e) =>
 updateTransaction(index, {
 description: e.target.value,
 })
 }
 disabled={!txn.included}
 className="w-full px-2 py-1.5 text-sm border-[var(--border)] border rounded-md bg-elevated text-content disabled:opacity-50"
 />
 </div>

 {/* Category */}
 <div>
 <label className="block text-xs font-medium text-content-secondary mb-1">
 {t("bankSync.review.category")}
 {txn.category_name && !txn.category_id && (
 <span className="ml-1 text-xs text-content-tertiary">
 (MCC: {txn.category_name})
 </span>
 )}
 </label>
 <select
 value={txn.category_id ?? ""}
 onChange={(e) =>
 updateTransaction(index, {
 category_id: e.target.value
 ? parseInt(e.target.value)
 : null,
 })
 }
 disabled={!txn.included}
 className="w-full px-2 py-1.5 text-sm border-[var(--border)] border rounded-md bg-elevated text-content disabled:opacity-50"
 >
 <option value="">
 {txn.category_name
 ? `${txn.category_name} (MCC)`
 : t("bankSync.review.selectCategory")}
 </option>
 {categories.map((cat) => (
 <option key={cat.id} value={cat.id}>
 {cat.name}
 </option>
 ))}
 </select>
 </div>
 </div>
 </div>
 </div>
 </div>
 ))}
 </div>
 </div>

 {/* Footer */}
 <div className="flex justify-between items-center p-4 sm:p-6 border-[var(--border)] border-t bg-surface-alt">
 <div className="text-sm text-content-secondary">
 {t("bankSync.found")}: {totalFound} |{" "}
 {t("bankSync.review.selected")}: {stats.selected}
 </div>
 <div className="flex gap-3">
 <button
 onClick={onClose}
 disabled={isConfirming}
 className="px-4 py-2 border-[var(--border)] border text-content rounded-lg hover:bg-surface-alt transition-colors font-medium text-sm"
 >
 {t("bankSync.review.cancel")}
 </button>
 <button
 onClick={handleConfirm}
 disabled={!canConfirm || isConfirming}
 className="px-6 py-2 rounded-lg font-medium text-sm text-white bg-accent-base hover:bg-accent-base-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
 >
 {isConfirming && (
 <svg
 className="animate-spin h-4 w-4 text-white"
 viewBox="0 0 24 24"
 >
 <circle
 className="opacity-25"
 cx="12"
 cy="12"
 r="10"
 stroke="currentColor"
 strokeWidth="4"
 fill="none"
 />
 <path
 className="opacity-75"
 fill="currentColor"
 d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
 />
 </svg>
 )}
 {isConfirming
 ? t("bankSync.review.confirming")
 : t("bankSync.review.confirm", {
 count: stats.selected,
 })}
 </button>
 </div>
 </div>
 </>
 )}
 </div>
 </div>
 );
};
