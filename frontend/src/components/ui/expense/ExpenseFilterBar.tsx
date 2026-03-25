import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../shared/Button";
import { useCategories } from "../../../contexts/CategoriesContext";
import { useAccounts } from "../../../contexts/AccountsContext";
import { ExpenseFilters } from "../../../types/expense";

interface ExpenseFilterBarProps {
 filters: ExpenseFilters;
 onFiltersChange: (filters: ExpenseFilters) => void;
 isVisible: boolean;
}

export const ExpenseFilterBar: React.FC<ExpenseFilterBarProps> = ({
 filters,
 onFiltersChange,
 isVisible,
}) => {
 const { t } = useTranslation();
 const { categories } = useCategories();
 const { activeAccounts } = useAccounts();

 if (!isVisible) return null;

 const expenseCategories = categories.filter((c) => c.type === "EXPENSE");
 const currencies = [...new Set(activeAccounts.map((a) => a.currency))].sort();

 const update = (partial: {
 [K in keyof ExpenseFilters]?: ExpenseFilters[K] | undefined;
 }) => {
 const merged = { ...filters, ...partial, page: 1 };
 (Object.keys(merged) as (keyof typeof merged)[]).forEach((k) => {
 if (merged[k] === undefined) delete merged[k];
 });
 onFiltersChange(merged as ExpenseFilters);
 };

 const clearAll = () => {
 const base: ExpenseFilters = { page: 1 };
 if (filters.size !== undefined) base.size = filters.size;
 onFiltersChange(base);
 };

 const hasActiveFilters =
 filters.date_from ||
 filters.date_to ||
 (filters.category_ids && filters.category_ids.length > 0) ||
 filters.account_id ||
 filters.currency;

 const inputClasses =
 "py-2 px-3 text-sm rounded-lg border border-[var(--border)] bg-elevated text-content focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-colors";

 return (
 <div className="bg-elevated border border-[var(--border)] rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
 <div className="flex flex-wrap items-end gap-3">
 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("expensePage.filters.dateFrom")}
 </label>
 <input
 type="date"
 className={inputClasses}
 value={filters.date_from || ""}
 onChange={(e) => update({ date_from: e.target.value || undefined })}
 />
 </div>

 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("expensePage.filters.dateTo")}
 </label>
 <input
 type="date"
 className={inputClasses}
 value={filters.date_to || ""}
 onChange={(e) => update({ date_to: e.target.value || undefined })}
 />
 </div>

 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("expensePage.filters.category")}
 </label>
 <select
 className={inputClasses}
 value={filters.category_ids?.[0] ?? ""}
 onChange={(e) => {
 const val = e.target.value;
 update({ category_ids: val ? [Number(val)] : undefined });
 }}
 >
 <option value="">{t("expensePage.filters.allCategories")}</option>
 {expenseCategories.map((c) => (
 <option key={c.id} value={c.id}>
 {c.name}
 </option>
 ))}
 </select>
 </div>

 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("expensePage.filters.account")}
 </label>
 <select
 className={inputClasses}
 value={filters.account_id ?? ""}
 onChange={(e) => {
 const val = e.target.value;
 update({ account_id: val ? Number(val) : undefined });
 }}
 >
 <option value="">{t("expensePage.filters.allAccounts")}</option>
 {activeAccounts.map((a) => (
 <option key={a.id} value={a.id}>
 {a.name}
 </option>
 ))}
 </select>
 </div>

 {currencies.length > 1 && (
 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("expensePage.filters.currency")}
 </label>
 <select
 className={inputClasses}
 value={filters.currency ?? ""}
 onChange={(e) =>
 update({ currency: e.target.value || undefined })
 }
 >
 <option value="">{t("expensePage.filters.allCurrencies")}</option>
 {currencies.map((c) => (
 <option key={c} value={c}>
 {c}
 </option>
 ))}
 </select>
 </div>
 )}

 {hasActiveFilters && (
 <Button variant="ghost" size="sm" onClick={clearAll}>
 {t("expensePage.filters.clearAll")}
 </Button>
 )}
 </div>
 </div>
 );
};
