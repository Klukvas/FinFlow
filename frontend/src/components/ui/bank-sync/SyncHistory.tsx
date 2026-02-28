import React from "react";
import { useTranslation } from "react-i18next";
import { SyncStatus } from "@/types/bankSync";

interface SyncHistoryProps {
  history: SyncStatus[];
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const { t } = useTranslation();

  const colorMap: Record<string, string> = {
    completed: "bg-green-100 text-green-700",
    completed_with_errors: "bg-yellow-100 text-yellow-700",
    in_progress: "bg-blue-100 text-blue-700",
    pending: "bg-yellow-100 text-yellow-700",
    failed: "bg-red-100 text-red-700",
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
      className={`px-2 py-0.5 rounded-full text-xs font-medium ${colorMap[status] || "bg-gray-100 text-gray-700"}`}
    >
      {labelMap[status] || status}
    </span>
  );
};

export const SyncHistory: React.FC<SyncHistoryProps> = ({ history }) => {
  const { t } = useTranslation();

  if (history.length === 0) {
    return (
      <p className="text-sm theme-text-secondary text-center py-4">
        {t("bankSync.noSyncHistory")}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="theme-border border-b">
            <th className="text-left py-2 px-3 theme-text-secondary font-medium">
              {t("bankSync.syncDate")}
            </th>
            <th className="text-left py-2 px-3 theme-text-secondary font-medium">
              {t("bankSync.status")}
            </th>
            <th className="text-right py-2 px-3 theme-text-secondary font-medium">
              {t("bankSync.found")}
            </th>
            <th className="text-right py-2 px-3 theme-text-secondary font-medium">
              {t("bankSync.imported")}
            </th>
            <th className="text-right py-2 px-3 theme-text-secondary font-medium">
              {t("bankSync.skipped")}
            </th>
          </tr>
        </thead>
        <tbody>
          {history.map((item) => (
            <tr key={item.id} className="theme-border border-b last:border-0">
              <td className="py-2 px-3 theme-text-primary">
                {item.started_at
                  ? new Date(item.started_at).toLocaleString()
                  : "—"}
              </td>
              <td className="py-2 px-3">
                <StatusBadge status={item.status} />
              </td>
              <td className="py-2 px-3 text-right theme-text-primary">
                {item.transactions_found}
              </td>
              <td className="py-2 px-3 text-right text-green-600">
                {item.transactions_imported}
              </td>
              <td className="py-2 px-3 text-right theme-text-secondary">
                {item.transactions_skipped}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
