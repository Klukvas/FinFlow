import React from "react";
import { useTranslation } from "react-i18next";
import { Card } from "../shared/Card";
import { Skeleton } from "../shared/Skeleton";
import { AccountStatisticsResponse } from "../../../types/account";
import { useCurrencyConversion } from "@/hooks/useCurrencyConversion";

interface AccountSummaryStripProps {
 stats: AccountStatisticsResponse | null;
 uniqueCurrencies: number;
 loading: boolean;
}

export const AccountSummaryStrip: React.FC<AccountSummaryStripProps> = ({
 stats,
 uniqueCurrencies,
 loading,
}) => {
 const { t } = useTranslation();
 const { formatCurrency } = useCurrencyConversion();

 if (loading) {
 return (
 <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
 {Array.from({ length: 4 }).map((_, i) => (
 <Card key={i}>
 <div className="p-4 space-y-2">
 <Skeleton variant="text" className="h-3 w-20" />
 <Skeleton variant="text" className="h-6 w-16" />
 </div>
 </Card>
 ))}
 </div>
 );
 }

 const kpiCards = [
 {
 label: t("accountPage.kpi.totalAccounts"),
 value: String(stats?.total_accounts ?? 0),
 valueClass: "text-content",
 extra: null,
 },
 {
 label: t("accountPage.kpi.totalBalance"),
 value: stats ? formatCurrency(stats.total_balance, stats.currency) : "0",
 valueClass: "text-success-base/80",
 extra:
 stats && stats.unconvertible_accounts_count > 0
 ? t("accountPage.kpi.notIncluded", {
 count: stats.unconvertible_accounts_count,
 })
 : null,
 },
 {
 label: t("accountPage.kpi.activeAccounts"),
 value: String(stats?.active_accounts ?? 0),
 valueClass: "text-accent-base/80",
 extra: null,
 },
 {
 label: t("accountPage.kpi.currencies"),
 value: String(uniqueCurrencies),
 valueClass: "text-content",
 extra: null,
 },
 ];

 return (
 <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
 {kpiCards.map((card) => (
 <Card key={card.label}>
 <div className="p-4">
 <p className="text-xs font-medium text-content-secondary uppercase tracking-wide">
 {card.label}
 </p>
 <p className={`text-xl font-semibold mt-1 ${card.valueClass}`}>
 {card.value}
 </p>
 {card.extra && (
 <p className="text-xs text-warning-base/80 mt-0.5">{card.extra}</p>
 )}
 </div>
 </Card>
 ))}
 </div>
 );
};
