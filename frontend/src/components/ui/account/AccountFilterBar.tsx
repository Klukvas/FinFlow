import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../shared/Button";
import {
  AccountsPageFilters,
  ACCOUNT_TYPES,
  ACCOUNT_TYPE_I18N_MAP,
} from "./accountHelpers";

interface AccountFilterBarProps {
  filters: AccountsPageFilters;
  onFiltersChange: (filters: AccountsPageFilters) => void;
  isVisible: boolean;
  availableCurrencies: string[];
}

export const AccountFilterBar: React.FC<AccountFilterBarProps> = ({
  filters,
  onFiltersChange,
  isVisible,
  availableCurrencies,
}) => {
  const { t } = useTranslation();

  if (!isVisible) return null;

  const update = (partial: {
    [K in keyof AccountsPageFilters]?: AccountsPageFilters[K] | undefined;
  }) => {
    const merged = { ...filters, ...partial, page: 1 };
    (Object.keys(merged) as (keyof typeof merged)[]).forEach((k) => {
      if (merged[k] === undefined) delete merged[k];
    });
    onFiltersChange(merged as AccountsPageFilters);
  };

  const clearAll = () => {
    const base: AccountsPageFilters = {
      page: 1,
      size: filters.size,
      ...(filters.groupBy !== undefined ? { groupBy: filters.groupBy } : {}),
    };
    onFiltersChange(base);
  };

  const hasActiveFilters =
    (filters.type && filters.type !== "all") ||
    (filters.currency && filters.currency !== "all") ||
    (filters.search && filters.search.trim() !== "");

  const inputClasses =
    "py-2 px-3 text-sm rounded-lg border theme-border theme-surface theme-text-primary focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] theme-transition";

  return (
    <div className="theme-surface border theme-border rounded-xl p-4 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t("accountPage.filters.type")}
          </label>
          <select
            className={inputClasses}
            value={filters.type || "all"}
            onChange={(e) => {
              const val = e.target.value;
              update({ type: val === "all" ? undefined : val });
            }}
          >
            <option value="all">{t("accountPage.filters.allTypes")}</option>
            {ACCOUNT_TYPES.map((type) => (
              <option key={type} value={type}>
                {t(ACCOUNT_TYPE_I18N_MAP[type] || "")}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t("accountPage.filters.currency")}
          </label>
          <select
            className={inputClasses}
            value={filters.currency || "all"}
            onChange={(e) => {
              const val = e.target.value;
              update({ currency: val === "all" ? undefined : val });
            }}
          >
            <option value="all">
              {t("accountPage.filters.allCurrencies")}
            </option>
            {availableCurrencies.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t("accountPage.filters.search")}
          </label>
          <input
            type="text"
            className={inputClasses}
            placeholder={t("accountPage.filters.searchPlaceholder")}
            value={filters.search || ""}
            onChange={(e) => update({ search: e.target.value })}
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium theme-text-secondary">
            {t("accountPage.filters.groupBy")}
          </label>
          <select
            className={inputClasses}
            value={filters.groupBy || "none"}
            onChange={(e) => {
              const val = e.target.value as "none" | "currency" | "type";
              update({ groupBy: val });
            }}
          >
            <option value="none">{t("accountPage.filters.groupByNone")}</option>
            <option value="currency">
              {t("accountPage.filters.groupByCurrency")}
            </option>
            <option value="type">{t("accountPage.filters.groupByType")}</option>
          </select>
        </div>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll}>
            {t("accountPage.filters.clearAll")}
          </Button>
        )}
      </div>
    </div>
  );
};
