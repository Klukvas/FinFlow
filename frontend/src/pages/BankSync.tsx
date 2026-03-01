import React, { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useApiClients } from "@/hooks/useApiClients";
import { ConnectForm } from "@/components/ui/bank-sync/ConnectForm";
import { AccountsList } from "@/components/ui/bank-sync/AccountsList";
import { SyncHistory } from "@/components/ui/bank-sync/SyncHistory";
import { SyncTransactionReview } from "@/components/ui/bank-sync/SyncTransactionReview";
import {
  BankConnection,
  SyncStatus,
  SyncPreviewResponse,
  SyncConfirmTransaction,
} from "@/types/bankSync";
import { AccountResponse } from "@/types";
import {
  FaSync,
  FaUnlink,
  FaCheckCircle,
  FaExclamationTriangle,
} from "react-icons/fa";

const BankSync: React.FC = () => {
  const { t } = useTranslation();
  const { bankSync, account: accountApi } = useApiClients();

  const [connections, setConnections] = useState<BankConnection[]>([]);
  const [finflowAccounts, setFinflowAccounts] = useState<AccountResponse[]>([]);
  const [syncHistory, setSyncHistory] = useState<SyncStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [daysBack, setDaysBack] = useState(30);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<SyncPreviewResponse | null>(
    null,
  );
  const [isConfirming, setIsConfirming] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [connResult, accResult] = await Promise.all([
        bankSync.getConnections(),
        accountApi.getAccounts(),
      ]);

      if (!("error" in connResult)) {
        setConnections(connResult);

        // Load sync history for first active connection
        const active = connResult.find((c) => c.is_active);
        if (active) {
          const historyResult = await bankSync.getSyncHistory(active.id);
          if (!("error" in historyResult)) {
            setSyncHistory(historyResult);
          }
        }
      }

      if (!("error" in accResult)) {
        setFinflowAccounts(accResult);
      }
    } catch {
      setError(t("bankSync.loadError"));
    } finally {
      setIsLoading(false);
    }
  }, [bankSync, accountApi, t]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleConnect = async (token: string) => {
    setIsConnecting(true);
    setError(null);
    try {
      const result = await bankSync.connect({ token });
      if ("error" in result) {
        setError(result.error);
      } else {
        setSuccessMsg(t("bankSync.connectSuccess"));
        setTimeout(() => setSuccessMsg(null), 3000);
        await loadData();
      }
    } catch {
      setError(t("bankSync.connectError"));
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async (connectionId: number) => {
    if (!window.confirm(t("bankSync.disconnectConfirm"))) return;

    try {
      const result = await bankSync.disconnect(connectionId);
      if (result && "error" in result) {
        setError(result.error);
      } else {
        await loadData();
      }
    } catch {
      setError(t("bankSync.disconnectError"));
    }
  };

  const handleSync = async (connectionId: number) => {
    setIsSyncing(true);
    setError(null);
    try {
      const result = await bankSync.previewSync(connectionId, {
        days_back: daysBack,
      });
      if ("error" in result) {
        setError(result.error);
      } else if (result.total_new === 0) {
        setSuccessMsg(t("bankSync.review.noNewTransactions"));
        setTimeout(() => setSuccessMsg(null), 5000);
      } else {
        setPreviewData(result);
      }
    } catch {
      setError(t("bankSync.syncError"));
    } finally {
      setIsSyncing(false);
    }
  };

  const handleConfirmSync = async (transactions: SyncConfirmTransaction[]) => {
    const active = connections.find((c) => c.is_active);
    if (!active) return;

    setIsConfirming(true);
    setError(null);
    try {
      const result = await bankSync.confirmSync(active.id, {
        days_back: daysBack,
        transactions,
      });
      if ("error" in result) {
        setError(result.error);
      } else {
        setPreviewData(null);
        setSuccessMsg(
          t("bankSync.syncComplete", {
            imported: result.transactions_imported,
            found: result.transactions_found,
          }),
        );
        setTimeout(() => setSuccessMsg(null), 5000);
        await loadData();
      }
    } catch {
      setError(t("bankSync.syncError"));
    } finally {
      setIsConfirming(false);
    }
  };

  const handleLinkAccount = async (
    linkedAccountId: number,
    finflowAccountId: number,
  ) => {
    const active = connections.find((c) => c.is_active);
    if (!active) return;

    try {
      const result = await bankSync.linkAccount(active.id, linkedAccountId, {
        finflow_account_id: finflowAccountId,
      });
      if ("error" in result) {
        setError(result.error);
      } else {
        await loadData();
      }
    } catch {
      setError(t("bankSync.linkError"));
    }
  };

  const handleToggleSync = async (linkedAccountId: number) => {
    const active = connections.find((c) => c.is_active);
    if (!active) return;

    try {
      const result = await bankSync.toggleAccountSync(
        active.id,
        linkedAccountId,
      );
      if ("error" in result) {
        setError(result.error);
      } else {
        await loadData();
      }
    } catch {
      setError(t("bankSync.toggleError"));
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="theme-text-secondary">{t("common.loading")}</div>
      </div>
    );
  }

  const activeConnection = connections.find((c) => c.is_active);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold theme-text-primary mb-6">
        {t("bankSync.title")}
      </h1>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2">
          <FaExclamationTriangle className="text-red-500 w-4 h-4 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {successMsg && (
        <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 flex items-center gap-2">
          <FaCheckCircle className="text-green-500 w-4 h-4 flex-shrink-0" />
          <p className="text-sm text-green-700">{successMsg}</p>
        </div>
      )}

      {!activeConnection ? (
        <ConnectForm onConnect={handleConnect} isLoading={isConnecting} />
      ) : (
        <div className="space-y-6">
          {/* Connection Status Card */}
          <div className="theme-surface rounded-lg p-5 theme-border border">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-semibold theme-text-primary">
                  {activeConnection.client_name || "Monobank"}
                </h2>
                <p className="text-sm theme-text-secondary">
                  {t("bankSync.connectedSince")}{" "}
                  {activeConnection.created_at
                    ? new Date(activeConnection.created_at).toLocaleDateString()
                    : "—"}
                </p>
                {activeConnection.last_sync_at && (
                  <p className="text-xs theme-text-secondary mt-1">
                    {t("bankSync.lastSync")}:{" "}
                    {new Date(activeConnection.last_sync_at).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={daysBack}
                  onChange={(e) => setDaysBack(Number(e.target.value))}
                  disabled={isSyncing}
                  className="px-3 py-2 md:py-2 min-h-[44px] rounded-lg text-sm theme-surface theme-border border theme-text-primary disabled:opacity-50"
                >
                  {[7, 14, 30].map((d) => (
                    <option key={d} value={d}>
                      {t("bankSync.daysBack", { count: d })}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => handleSync(activeConnection.id)}
                  disabled={isSyncing}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 theme-transition"
                >
                  <FaSync
                    className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`}
                  />
                  {isSyncing ? t("bankSync.syncing") : t("bankSync.syncNow")}
                </button>
                <button
                  onClick={() => handleDisconnect(activeConnection.id)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium theme-error hover:theme-error-light theme-border border theme-transition"
                >
                  <FaUnlink className="w-3.5 h-3.5" />
                  {t("bankSync.disconnect")}
                </button>
              </div>
            </div>
          </div>

          {/* Accounts */}
          <AccountsList
            accounts={activeConnection.accounts}
            finflowAccounts={finflowAccounts}
            onLinkAccount={handleLinkAccount}
            onToggleSync={handleToggleSync}
          />

          {/* Sync History */}
          <div className="theme-surface rounded-lg p-5 theme-border border">
            <h3 className="font-medium theme-text-primary mb-3">
              {t("bankSync.syncHistory")}
            </h3>
            <SyncHistory history={syncHistory} />
          </div>
        </div>
      )}

      {previewData && (
        <SyncTransactionReview
          transactions={previewData.transactions}
          totalFound={previewData.total_found}
          totalSkipped={previewData.total_skipped}
          onConfirm={handleConfirmSync}
          onClose={() => setPreviewData(null)}
          isConfirming={isConfirming}
        />
      )}
    </div>
  );
};

export default BankSync;
