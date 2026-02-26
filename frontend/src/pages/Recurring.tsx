import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/contexts/AuthContext";
import { useApiClients } from "@/hooks/useApiClients";
import {
  RecurringPayment,
  PaymentSchedule,
  PaymentStatistics,
} from "@/services/api/recurringApi";
import { CreateRecurringPayment } from "@/components/ui/recurring/CreateRecurringPayment";
import { RecurringPageHeader } from "@/components/ui/recurring/RecurringPageHeader";
import { RecurringSummaryStrip } from "@/components/ui/recurring/RecurringSummaryStrip";
import { RecurringFilterBar } from "@/components/ui/recurring/RecurringFilterBar";
import { UpcomingExecutions } from "@/components/ui/recurring/UpcomingExecutions";
import { RecurringTable } from "@/components/ui/recurring/RecurringTable";
import { RecurringSidePanel } from "@/components/ui/recurring/RecurringSidePanel";
import { RecurringFilters } from "@/components/ui/recurring/recurringHelpers";
import { Modal } from "@/components/ui/shared/Modal";
import { Card } from "@/components/ui/shared/Card";
import { Button } from "@/components/ui/shared/Button";
import { exportRecurringCsv } from "@/utils/exportRecurringCsv";
import { toast } from "sonner";
import { logger } from "@/utils/logger";

export const Recurring = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { recurring } = useApiClients();

  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Selected items
  const [selectedPayment, setSelectedPayment] =
    useState<RecurringPayment | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<RecurringPayment | null>(
    null,
  );

  // Side panel state
  const [sidePanelPayment, setSidePanelPayment] =
    useState<RecurringPayment | null>(null);
  const [sidePanelSchedules, setSidePanelSchedules] = useState<
    PaymentSchedule[]
  >([]);
  const [sidePanelSchedulesLoading, setSidePanelSchedulesLoading] =
    useState(false);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  // Filter state
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [filters, setFilters] = useState<RecurringFilters>({
    page: 1,
    size: 10,
  });

  // Data state
  const [allPayments, setAllPayments] = useState<RecurringPayment[]>([]);
  const [stats, setStats] = useState<PaymentStatistics | null>(null);
  const [allLoading, setAllLoading] = useState(true);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    if (!user?.id) return;
    setAllLoading(true);
    try {
      const [firstPage, statsResult] = await Promise.all([
        recurring.getRecurringPayments({ size: 100, page: 1 }),
        recurring.getPaymentStatistics(),
      ]);

      if (!("error" in firstPage)) {
        let allItems = [...firstPage.items];
        // Fetch remaining pages if total exceeds first page
        if (firstPage.pages > 1) {
          const remaining = await Promise.all(
            Array.from({ length: firstPage.pages - 1 }, (_, i) =>
              recurring.getRecurringPayments({ size: 100, page: i + 2 }),
            ),
          );
          for (const page of remaining) {
            if (!("error" in page)) allItems = [...allItems, ...page.items];
          }
        }
        setAllPayments(allItems);
      }
      if (!("error" in statsResult)) setStats(statsResult);
    } catch (err) {
      logger.error("Error loading recurring data:", err);
    } finally {
      setAllLoading(false);
    }
  }, [user?.id, recurring]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Client-side filtering
  const filteredPayments = useMemo(() => {
    let result = [...allPayments];

    if (filters.status && filters.status !== "all") {
      result = result.filter((p) => p.status === filters.status);
    }
    if (filters.payment_type && filters.payment_type !== "all") {
      result = result.filter(
        (p) =>
          p.payment_type === filters.payment_type ||
          p.payment_type === filters.payment_type?.toUpperCase(),
      );
    }
    if (filters.schedule_type && filters.schedule_type !== "all") {
      result = result.filter((p) => p.schedule_type === filters.schedule_type);
    }

    return result;
  }, [allPayments, filters]);

  // Client-side pagination
  const paginatedPayments = useMemo(() => {
    const start = ((filters.page || 1) - 1) * (filters.size || 10);
    return filteredPayments.slice(start, start + (filters.size || 10));
  }, [filteredPayments, filters.page, filters.size]);

  const totalItems = filteredPayments.length;
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
  const openSidePanel = async (payment: RecurringPayment) => {
    setSidePanelPayment(payment);
    setSidePanelOpen(true);
    setSidePanelSchedulesLoading(true);
    try {
      const result = await recurring.getPaymentSchedules(payment.id, {
        size: 100,
      });
      if (!("error" in result)) {
        setSidePanelSchedules(result.items);
      } else {
        setSidePanelSchedules([]);
      }
    } catch {
      setSidePanelSchedules([]);
    } finally {
      setSidePanelSchedulesLoading(false);
    }
  };

  const closeSidePanel = () => {
    setSidePanelOpen(false);
    setTimeout(() => {
      setSidePanelPayment(null);
      setSidePanelSchedules([]);
    }, 300);
  };

  // Create handler
  const handleCreateSuccess = () => {
    setIsCreateModalOpen(false);
    fetchAllData();
  };

  // Edit handler
  const handleEditSuccess = () => {
    setIsEditModalOpen(false);
    setSelectedPayment(null);
    fetchAllData();
    // Refresh side panel if open for the same payment
    if (
      sidePanelPayment &&
      selectedPayment &&
      sidePanelPayment.id === selectedPayment.id
    ) {
      recurring.getRecurringPayment(selectedPayment.id).then((result) => {
        if (!("error" in result)) {
          setSidePanelPayment(result);
        }
      });
    }
  };

  // Delete handler
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const result = await recurring.deleteRecurringPayment(deleteTarget.id);
      if (result && "error" in result) {
        toast.error(t("recurringPage.messages.deleteFailed"));
        return;
      }
      setAllPayments((prev) => prev.filter((p) => p.id !== deleteTarget.id));
      if (sidePanelPayment?.id === deleteTarget.id) closeSidePanel();
      const statsResult = await recurring.getPaymentStatistics();
      if (!("error" in statsResult)) setStats(statsResult);
      toast.success(t("recurringPage.messages.deleted"));
    } catch (err) {
      logger.error("Error deleting recurring payment:", err);
      toast.error(t("recurringPage.messages.deleteFailed"));
    } finally {
      setIsDeleting(false);
      setIsDeleteModalOpen(false);
      setDeleteTarget(null);
    }
  };

  // Pause/Resume handler
  const handlePauseResume = async (payment: RecurringPayment) => {
    try {
      const isPaused = payment.status === "paused";
      const result = isPaused
        ? await recurring.resumeRecurringPayment(payment.id)
        : await recurring.pauseRecurringPayment(payment.id);

      if (result && "error" in result) {
        toast.error(t("recurringPage.messages.pauseResumeFailed"));
        return;
      }

      // Refetch the updated payment
      const updatedPayment = await recurring.getRecurringPayment(payment.id);
      if (!("error" in updatedPayment)) {
        setAllPayments((prev) =>
          prev.map((p) => (p.id === payment.id ? updatedPayment : p)),
        );
        if (sidePanelPayment?.id === payment.id) {
          setSidePanelPayment(updatedPayment);
        }
      }

      const statsResult = await recurring.getPaymentStatistics();
      if (!("error" in statsResult)) setStats(statsResult);

      toast.success(
        t(
          isPaused
            ? "recurringPage.messages.resumed"
            : "recurringPage.messages.paused",
        ),
      );
    } catch (err) {
      logger.error("Error toggling payment status:", err);
      toast.error(t("recurringPage.messages.pauseResumeFailed"));
    }
  };

  // Export CSV
  const handleExportCsv = () => {
    exportRecurringCsv(filteredPayments);
  };

  // Filter change
  const handleFiltersChange = (newFilters: RecurringFilters) => {
    setFilters(newFilters);
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handlePageSizeChange = (size: number) => {
    setFilters((prev) => ({ ...prev, size, page: 1 }));
  };

  const hasActiveFilters =
    (filters.status && filters.status !== "all") ||
    (filters.payment_type && filters.payment_type !== "all") ||
    (filters.schedule_type && filters.schedule_type !== "all");

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <RecurringPageHeader
          onAdd={() => setIsCreateModalOpen(true)}
          onToggleFilters={() => setFiltersVisible((v) => !v)}
          onExportCsv={handleExportCsv}
          filtersActive={Boolean(hasActiveFilters)}
        />

        {/* KPI Strip */}
        <RecurringSummaryStrip stats={stats} loading={allLoading} />

        {/* Filter Bar */}
        <RecurringFilterBar
          filters={filters}
          onFiltersChange={handleFiltersChange}
          isVisible={filtersVisible}
        />

        {/* Upcoming Executions */}
        <UpcomingExecutions
          payments={allPayments}
          loading={allLoading}
          onPaymentClick={openSidePanel}
        />

        {/* Table */}
        <Card>
          <RecurringTable
            payments={paginatedPayments}
            loading={allLoading}
            currentPage={filters.page || 1}
            totalPages={totalPages}
            pageSize={filters.size || 10}
            totalItems={totalItems}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            onRowClick={openSidePanel}
            onPauseResume={handlePauseResume}
            onEdit={(payment) => {
              setSelectedPayment(payment);
              setIsEditModalOpen(true);
            }}
            onDelete={(payment) => {
              setDeleteTarget(payment);
              setIsDeleteModalOpen(true);
            }}
            emptyMessage={
              hasActiveFilters
                ? t("recurringPage.filters.noMatchFilters")
                : undefined
            }
          />
        </Card>

        {/* Side Panel */}
        <RecurringSidePanel
          payment={sidePanelPayment}
          schedules={sidePanelSchedules}
          schedulesLoading={sidePanelSchedulesLoading}
          isOpen={sidePanelOpen}
          onClose={closeSidePanel}
          onPauseResume={() => {
            if (sidePanelPayment) handlePauseResume(sidePanelPayment);
          }}
          onEdit={() => {
            if (sidePanelPayment) {
              setSelectedPayment(sidePanelPayment);
              setIsEditModalOpen(true);
            }
          }}
          onDelete={() => {
            if (sidePanelPayment) {
              setDeleteTarget(sidePanelPayment);
              setIsDeleteModalOpen(true);
            }
          }}
        />

        {/* Create Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={t("recurringPage.createModal.title")}
          size="xl"
        >
          <CreateRecurringPayment
            onSuccess={handleCreateSuccess}
            onCancel={() => setIsCreateModalOpen(false)}
            mode="create"
            showCard={false}
          />
        </Modal>

        {/* Edit Modal */}
        <Modal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false);
            setSelectedPayment(null);
          }}
          title={t("recurringPage.editModal.title")}
          size="xl"
        >
          {selectedPayment && (
            <CreateRecurringPayment
              onSuccess={handleEditSuccess}
              onCancel={() => {
                setIsEditModalOpen(false);
                setSelectedPayment(null);
              }}
              mode="edit"
              initialData={selectedPayment}
              showCard={false}
            />
          )}
        </Modal>

        {/* Delete Confirmation Modal */}
        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => {
            setIsDeleteModalOpen(false);
            setDeleteTarget(null);
          }}
          title={t("recurringPage.deleteConfirmModal.title")}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm theme-text-secondary">
              {t("recurringPage.deleteConfirmModal.message")}
            </p>
            {deleteTarget && (
              <div className="theme-bg-secondary rounded-lg p-3 text-sm">
                <span className="font-medium theme-text-primary">
                  {deleteTarget.name}
                </span>
                <span
                  className={`ml-2 font-semibold tabular-nums ${
                    deleteTarget.payment_type === "expense" ||
                    deleteTarget.payment_type === ("EXPENSE" as string)
                      ? "text-red-500/80 dark:text-red-400/70"
                      : "text-green-600/80 dark:text-green-400/70"
                  }`}
                >
                  {deleteTarget.amount.toLocaleString("uk-UA", {
                    minimumFractionDigits: 2,
                  })}{" "}
                  {deleteTarget.currency}
                </span>
              </div>
            )}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsDeleteModalOpen(false);
                  setDeleteTarget(null);
                }}
              >
                {t("recurringPage.deleteConfirmModal.cancel")}
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={isDeleting}
                onClick={handleDeleteConfirm}
              >
                {t("recurringPage.deleteConfirmModal.confirm")}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};

export default Recurring;
