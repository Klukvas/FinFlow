import React from "react";
import { useTranslation } from "react-i18next";
import { SyncStatus } from "@/types/bankSync";

interface SyncHistoryProps {
 history: SyncStatus[];
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
 const { t } = useTranslation();

 const colorMap: Record<string, string> = {
 completed: "bg-[var(--success-dim)] text-success-base",
 completed_with_errors: "bg-[var(--warning-dim)] text-warning-base",
 in_progress: "bg-[var(--accent-dim)] text-accent-base",
 pending: "bg-[var(--warning-dim)] text-warning-base",
 failed: "bg-[var(--danger-dim)] text-danger-base",
 };

 const labelMap: Record<string, string> = {
 completed: t("bankSync.statusCompleted"),
 completed_with_errors: t("bankSync.statusCompletedWithErrors"),
 in_progress: t("bankSync.statusInProgress"),
 pending: t("bankSync.statusPending"),
 failed: t("bankSync.statusFailed"),
 };

 return (
 <span
 className={`px-2 py-0.5 rounded-full text-xs font-medium ${colorMap[status] || "bg-surface-alt text-content-secondary"}`}
 >
 {labelMap[status] || status}
 </span>
 );
};

export const SyncHistory: React.FC<SyncHistoryProps> = ({ history }) => {
 const { t } = useTranslation();

 if (history.length === 0) {
 return (
 <p className="text-sm text-content-secondary text-center py-4">
 {t("bankSync.noSyncHistory")}
 </p>
 );
 }

 return (
 <div className="overflow-x-auto">
 <table className="w-full text-sm">
 <thead>
 <tr className="border-[var(--border)] border-b">
 <th className="text-left py-2 px-3 text-content-secondary font-medium">
 {t("bankSync.syncDate")}
 </th>
 <th className="text-left py-2 px-3 text-content-secondary font-medium">
 {t("bankSync.status")}
 </th>
 <th className="text-right py-2 px-3 text-content-secondary font-medium">
 {t("bankSync.found")}
 </th>
 <th className="text-right py-2 px-3 text-content-secondary font-medium">
 {t("bankSync.imported")}
 </th>
 <th className="text-right py-2 px-3 text-content-secondary font-medium">
 {t("bankSync.skipped")}
 </th>
 </tr>
 </thead>
 <tbody>
 {history.map((item) => (
 <tr key={item.id} className="border-[var(--border)] border-b last:border-0">
 <td className="py-2 px-3 text-content">
 {item.started_at
 ? new Date(item.started_at).toLocaleString()
 : "—"}
 </td>
 <td className="py-2 px-3">
 <StatusBadge status={item.status} />
 </td>
 <td className="py-2 px-3 text-right text-content">
 {item.transactions_found}
 </td>
 <td className="py-2 px-3 text-right text-success-base">
 {item.transactions_imported}
 </td>
 <td className="py-2 px-3 text-right text-content-secondary">
 {item.transactions_skipped}
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 );
};
