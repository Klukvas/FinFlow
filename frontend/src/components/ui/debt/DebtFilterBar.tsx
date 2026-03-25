import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../shared/Button";
import { DebtFilters } from "./debtHelpers";
import { DebtResponse, DebtType } from "../../../types/debt";
import { ContactResponse } from "../../../types/contact";
import { DEBT_TYPE_I18N_MAP } from "./debtHelpers";

interface DebtFilterBarProps {
 filters: DebtFilters;
 onFiltersChange: (filters: DebtFilters) => void;
 isVisible: boolean;
 contacts: ContactResponse[];
 debts: DebtResponse[];
}

export const DebtFilterBar: React.FC<DebtFilterBarProps> = ({
 filters,
 onFiltersChange,
 isVisible,
 contacts,
 debts,
}) => {
 const { t } = useTranslation();

 const currencies = useMemo(() => {
 const set = new Set(debts.map((d) => d.currency));
 return [...set].sort();
 }, [debts]);

 const debtTypes: DebtType[] = [
 "CREDIT_CARD",
 "LOAN",
 "MORTGAGE",
 "PERSONAL_LOAN",
 "AUTO_LOAN",
 "STUDENT_LOAN",
 "OTHER",
 ];

 if (!isVisible) return null;

 const update = (partial: {
 [K in keyof DebtFilters]?: DebtFilters[K] | undefined;
 }) => {
 const merged = { ...filters, ...partial, page: 1 };
 (Object.keys(merged) as (keyof typeof merged)[]).forEach((k) => {
 if (merged[k] === undefined) delete merged[k];
 });
 onFiltersChange(merged as DebtFilters);
 };

 const clearAll = () => {
 const base: DebtFilters = { page: 1, size: filters.size };
 onFiltersChange(base);
 };

 const hasActiveFilters =
 (filters.status && filters.status !== "all") ||
 filters.debt_type ||
 filters.contact_id ||
 filters.currency ||
 filters.date_from ||
 filters.date_to;

 const inputClasses =
 "py-2 px-3 text-sm rounded-lg border border-[var(--border)] bg-elevated text-content focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-colors";

 return (
 <div className="bg-elevated border border-[var(--border)] rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
 <div className="flex flex-wrap items-end gap-3">
 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("debtPage.filters.status")}
 </label>
 <select
 className={inputClasses}
 value={filters.status || "all"}
 onChange={(e) => {
 const val = e.target.value as "active" | "paid_off" | "all";
 update({ status: val === "all" ? undefined : val });
 }}
 >
 <option value="all">{t("debtPage.filters.allStatuses")}</option>
 <option value="active">{t("debtPage.status.active")}</option>
 <option value="paid_off">{t("debtPage.status.paidOff")}</option>
 </select>
 </div>

 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("debtPage.filters.debtType")}
 </label>
 <select
 className={inputClasses}
 value={filters.debt_type || ""}
 onChange={(e) => {
 const val = e.target.value;
 update({ debt_type: val ? (val as DebtType) : undefined });
 }}
 >
 <option value="">{t("debtPage.filters.allTypes")}</option>
 {debtTypes.map((dt) => (
 <option key={dt} value={dt}>
 {t(DEBT_TYPE_I18N_MAP[dt])}
 </option>
 ))}
 </select>
 </div>

 {contacts.length > 0 && (
 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("debtPage.filters.contact")}
 </label>
 <select
 className={inputClasses}
 value={filters.contact_id ?? ""}
 onChange={(e) => {
 const val = e.target.value;
 update({ contact_id: val ? Number(val) : undefined });
 }}
 >
 <option value="">{t("debtPage.filters.allContacts")}</option>
 {contacts.map((c) => (
 <option key={c.id} value={c.id}>
 {c.name}
 </option>
 ))}
 </select>
 </div>
 )}

 {currencies.length > 1 && (
 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("debtPage.filters.currency")}
 </label>
 <select
 className={inputClasses}
 value={filters.currency ?? ""}
 onChange={(e) =>
 update({ currency: e.target.value || undefined })
 }
 >
 <option value="">{t("debtPage.filters.allCurrencies")}</option>
 {currencies.map((c) => (
 <option key={c} value={c}>
 {c}
 </option>
 ))}
 </select>
 </div>
 )}

 <div className="flex flex-col gap-1">
 <label className="text-xs font-medium text-content-secondary">
 {t("debtPage.filters.dateFrom")}
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
 {t("debtPage.filters.dateTo")}
 </label>
 <input
 type="date"
 className={inputClasses}
 value={filters.date_to || ""}
 onChange={(e) => update({ date_to: e.target.value || undefined })}
 />
 </div>

 {hasActiveFilters && (
 <Button variant="ghost" size="sm" onClick={clearAll}>
 {t("debtPage.filters.clearAll")}
 </Button>
 )}
 </div>
 </div>
 );
};
