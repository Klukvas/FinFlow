import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  AccountResponse,
  AccountSummary,
  AccountStatisticsResponse,
  AccountTransactionSummary,
} from "@/types";
import { useApiClients } from "@/hooks/useApiClients";
import { AccountPageHeader } from "@/components/ui/account/AccountPageHeader";
import { AccountSummaryStrip } from "@/components/ui/account/AccountSummaryStrip";
import { AccountFilterBar } from "@/components/ui/account/AccountFilterBar";
import { AccountTable } from "@/components/ui/account/AccountTable";
import { AccountSidePanel } from "@/components/ui/account/AccountSidePanel";
import { CreateAccountModal } from "@/components/ui/account/CreateAccountModal";
import { EditAccountModal } from "@/components/ui/account/EditAccountModal";
import {
  AccountsPageFilters,
  getUniqueCurrencies,
} from "@/components/ui/account/accountHelpers";
import { Modal } from "@/components/ui/shared/Modal";
import { Card } from "@/components/ui/shared/Card";
import { Button } from "@/components/ui/shared/Button";
import { exportAccountsCsv } from "@/utils/exportAccountsCsv";
import { toast } from "sonner";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { logger } from "@/utils/logger";

export const Account: React.FC = () => {
  const { t } = useTranslation();
  const { account: accountApi } = useApiClients();
  const { handleAccountError } = useErrorHandler();

  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);

  // Selected items
  const [editingAccount, setEditingAccount] = useState<AccountResponse | null>(
    null,
  );
  const [archiveTarget, setArchiveTarget] = useState<AccountResponse | null>(
    null,
  );

  // Side panel state
  const [sidePanelAccount, setSidePanelAccount] =
    useState<AccountResponse | null>(null);
  const [sidePanelTransactions, setSidePanelTransactions] =
    useState<AccountTransactionSummary | null>(null);
  const [sidePanelTransactionsLoading, setSidePanelTransactionsLoading] =
    useState(false);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  // Filter state
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [filters, setFilters] = useState<AccountsPageFilters>({
    page: 1,
    size: 10,
  });

  // Data state
  const [allAccounts, setAllAccounts] = useState<AccountResponse[]>([]);
  const [summaries, setSummaries] = useState<AccountSummary[]>([]);
  const [stats, setStats] = useState<AccountStatisticsResponse | null>(null);
  const [allLoading, setAllLoading] = useState(true);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setAllLoading(true);
    try {
      const [accountsResult, summariesResult, statsResult] = await Promise.all([
        accountApi.getAccounts(),
        accountApi.getAccountSummaries(),
        accountApi.getAccountStatistics(),
      ]);

      if (!("error" in accountsResult)) setAllAccounts(accountsResult);
      if (!("error" in summariesResult)) setSummaries(summariesResult);
      if (!("error" in statsResult)) setStats(statsResult);
    } catch (err) {
      logger.error("Error loading accounts data:", err);
    } finally {
      setAllLoading(false);
    }
  }, [accountApi]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Only show active accounts (filter out archived)
  const activeAccounts = useMemo(
    () => allAccounts.filter((a) => !a.is_archived),
    [allAccounts],
  );

  // Available currencies for filter dropdown
  const availableCurrencies = useMemo(
    () => getUniqueCurrencies(activeAccounts),
    [activeAccounts],
  );

  // Client-side filtering
  const filteredAccounts = useMemo(() => {
    let result = [...activeAccounts];

    if (filters.type && filters.type !== "all") {
      result = result.filter((a) => a.type === filters.type);
    }
    if (filters.currency && filters.currency !== "all") {
      result = result.filter((a) => a.currency === filters.currency);
    }
    if (filters.search && filters.search.trim()) {
      const q = filters.search.toLowerCase();
      result = result.filter((a) => a.name.toLowerCase().includes(q));
    }

    return result;
  }, [activeAccounts, filters]);

  // Client-side pagination
  const paginatedAccounts = useMemo(() => {
    const start = ((filters.page || 1) - 1) * (filters.size || 10);
    return filteredAccounts.slice(start, start + (filters.size || 10));
  }, [filteredAccounts, filters.page, filters.size]);

  const totalItems = filteredAccounts.length;
  const totalPages = Math.ceil(totalItems / (filters.size || 10));

  // Keyboard shortcut: N to add
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "n" || e.key === "N") {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
        e.preventDefault();
        setIsCreateModalOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Side panel
  const openSidePanel = async (account: AccountResponse) => {
    setSidePanelAccount(account);
    setSidePanelOpen(true);
    setSidePanelTransactionsLoading(true);
    try {
      const result = await accountApi.getAccountTransactions(account.id);
      if (!("error" in result)) {
        setSidePanelTransactions(result);
      } else {
        setSidePanelTransactions(null);
      }
    } catch {
      setSidePanelTransactions(null);
    } finally {
      setSidePanelTransactionsLoading(false);
    }
  };

  const closeSidePanel = () => {
    setSidePanelOpen(false);
    setTimeout(() => {
      setSidePanelAccount(null);
      setSidePanelTransactions(null);
    }, 300);
  };

  // Create handler
  const handleCreateAccount = async (accountData: any) => {
    const result = await accountApi.createAccount(accountData);
    if (result && "error" in result) {
      handleAccountError(result);
      return;
    }
    setIsCreateModalOpen(false);
    toast.success(t("accountPage.messages.accountCreated"));
    fetchAllData();
  };

  // Edit handler
  const handleUpdateAccount = async (id: number, accountData: any) => {
    const result = await accountApi.updateAccount(id, accountData);
    if (result && "error" in result) return;
    setIsEditModalOpen(false);
    setEditingAccount(null);
    toast.success(t("accountPage.messages.accountUpdated"));
    fetchAllData();
    // Refresh side panel if open for the same account
    if (sidePanelAccount && sidePanelAccount.id === id) {
      const updated = await accountApi.getAccount(id);
      if (!("error" in updated)) setSidePanelAccount(updated);
    }
  };

  // Archive handler
  const handleArchiveConfirm = async () => {
    if (!archiveTarget) return;
    setIsArchiving(true);
    try {
      const result = await accountApi.archiveAccount(archiveTarget.id);
      if (result && "error" in result) {
        toast.error(t("accountPage.messages.archiveFailed"));
        return;
      }
      setAllAccounts((prev) =>
        prev.map((a) =>
          a.id === archiveTarget.id ? { ...a, is_archived: true } : a,
        ),
      );
      if (sidePanelAccount?.id === archiveTarget.id) closeSidePanel();
      const statsResult = await accountApi.getAccountStatistics();
      if (!("error" in statsResult)) setStats(statsResult);
      toast.success(t("accountPage.messages.accountArchived"));
    } catch (err) {
      logger.error("Error archiving account:", err);
      toast.error(t("accountPage.messages.archiveFailed"));
    } finally {
      setIsArchiving(false);
      setIsArchiveModalOpen(false);
      setArchiveTarget(null);
    }
  };

  // Export CSV
  const handleExportCsv = () => {
    exportAccountsCsv(filteredAccounts, summaries);
  };

  // Filter change
  const handleFiltersChange = (newFilters: AccountsPageFilters) => {
    setFilters(newFilters);
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handlePageSizeChange = (size: number) => {
    setFilters((prev) => ({ ...prev, size, page: 1 }));
  };

  const hasActiveFilters =
    (filters.type && filters.type !== "all") ||
    (filters.currency && filters.currency !== "all") ||
    (filters.search && filters.search.trim() !== "");

  return (
    <div
      className="min-h-screen bg-surface p-2 sm:p-4 md:p-6 lg:p-8"
      data-testid="account-page"
    >
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <AccountPageHeader
          onAdd={() => setIsCreateModalOpen(true)}
          onToggleFilters={() => setFiltersVisible((v) => !v)}
          onExportCsv={handleExportCsv}
          filtersActive={Boolean(hasActiveFilters)}
        />

        {/* KPI Strip */}
        <AccountSummaryStrip
          stats={stats}
          uniqueCurrencies={availableCurrencies.length}
          loading={allLoading}
        />

        {/* Filter Bar */}
        <AccountFilterBar
          filters={filters}
          onFiltersChange={handleFiltersChange}
          isVisible={filtersVisible}
          availableCurrencies={availableCurrencies}
        />

        {/* Table */}
        <Card>
          <AccountTable
            accounts={paginatedAccounts}
            summaries={summaries}
            loading={allLoading}
            currentPage={filters.page || 1}
            totalPages={totalPages}
            pageSize={filters.size || 10}
            totalItems={totalItems}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            onRowClick={openSidePanel}
            onEdit={(account) => {
              setEditingAccount(account);
              setIsEditModalOpen(true);
            }}
            onArchive={(account) => {
              setArchiveTarget(account);
              setIsArchiveModalOpen(true);
            }}
            groupBy={filters.groupBy || "none"}
            emptyMessage={
              hasActiveFilters
                ? t("accountPage.filters.noMatchFilters")
                : undefined
            }
          />
        </Card>

        {/* Side Panel */}
        <AccountSidePanel
          account={sidePanelAccount}
          transactionSummary={sidePanelTransactions}
          transactionsLoading={sidePanelTransactionsLoading}
          isOpen={sidePanelOpen}
          onClose={closeSidePanel}
          onEdit={() => {
            if (sidePanelAccount) {
              setEditingAccount(sidePanelAccount);
              setIsEditModalOpen(true);
            }
          }}
          onArchive={() => {
            if (sidePanelAccount) {
              setArchiveTarget(sidePanelAccount);
              setIsArchiveModalOpen(true);
            }
          }}
        />

        {/* Create Modal */}
        {isCreateModalOpen && (
          <CreateAccountModal
            onClose={() => setIsCreateModalOpen(false)}
            onSubmit={handleCreateAccount}
          />
        )}

        {/* Edit Modal */}
        {editingAccount && isEditModalOpen && (
          <EditAccountModal
            account={editingAccount}
            onClose={() => {
              setIsEditModalOpen(false);
              setEditingAccount(null);
            }}
            onSubmit={handleUpdateAccount}
          />
        )}

        {/* Archive Confirmation Modal */}
        <Modal
          isOpen={isArchiveModalOpen}
          onClose={() => {
            setIsArchiveModalOpen(false);
            setArchiveTarget(null);
          }}
          title={t("accountPage.archiveConfirmModal.title")}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm text-content-secondary">
              {t("accountPage.archiveConfirmModal.message")}
            </p>
            {archiveTarget && (
              <div className="bg-surface-alt rounded-lg p-3 text-sm">
                <span className="font-medium text-content">
                  {archiveTarget.name}
                </span>
                <span
                  className={`ml-2 font-semibold tabular-nums ${
                    archiveTarget.balance >= 0
                      ? "text-success-base"
                      : "text-danger-base"
                  }`}
                >
                  {archiveTarget.balance.toLocaleString("uk-UA", {
                    minimumFractionDigits: 2,
                  })}{" "}
                  {archiveTarget.currency}
                </span>
              </div>
            )}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsArchiveModalOpen(false);
                  setArchiveTarget(null);
                }}
              >
                {t("accountPage.archiveConfirmModal.cancel")}
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={isArchiving}
                onClick={handleArchiveConfirm}
                data-testid="confirm-archive-button"
              >
                {t("accountPage.archiveConfirmModal.confirm")}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};

export default Account;
