import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useApiClients } from "@/hooks/useApiClients";
import { useCategories } from "@/contexts/CategoriesContext";
import {
  DebtResponse,
  DebtCreate,
  DebtUpdate,
  DebtSummary,
  DebtPaymentResponse,
  DebtPaymentCreate,
} from "@/types/debt";
import {
  ContactResponse,
  ContactCreate,
  ContactUpdate,
  ContactSummary,
} from "@/types/contact";
import { DebtForm } from "@/components/debt/DebtForm";
import { PaymentForm } from "@/components/debt/PaymentForm";
import { ContactForm } from "@/components/contact/ContactForm";
import { DebtPageHeader } from "@/components/ui/debt/DebtPageHeader";
import { DebtSummaryStrip } from "@/components/ui/debt/DebtSummaryStrip";
import { DebtFilterBar } from "@/components/ui/debt/DebtFilterBar";
import { DebtTable } from "@/components/ui/debt/DebtTable";
import { DebtSidePanel } from "@/components/ui/debt/DebtSidePanel";
import { ContactTable } from "@/components/ui/debt/ContactTable";
import { DebtFilters } from "@/components/ui/debt/debtHelpers";
import { Modal } from "@/components/ui/shared/Modal";
import { Card } from "@/components/ui/shared/Card";
import { Button } from "@/components/ui/shared/Button";
import { Tabs } from "@/components/ui/shared/Tabs";
import { FaTable, FaAddressBook } from "react-icons/fa";
import { exportDebtsCsv } from "@/utils/exportDebtsCsv";
import { toast } from "sonner";
import { logger } from "@/utils/logger";

type TabType = "debts" | "contacts";

export const Debts = () => {
  const { t } = useTranslation();
  const { debt: debtApi, contact: contactApi } = useApiClients();
  const { categories } = useCategories();

  // Modal state
  const [isCreateDebtModalOpen, setIsCreateDebtModalOpen] = useState(false);
  const [isEditDebtModalOpen, setIsEditDebtModalOpen] = useState(false);
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [isDeleteDebtModalOpen, setIsDeleteDebtModalOpen] = useState(false);
  const [isCreateContactModalOpen, setIsCreateContactModalOpen] =
    useState(false);
  const [isEditContactModalOpen, setIsEditContactModalOpen] = useState(false);
  const [isDeleteContactModalOpen, setIsDeleteContactModalOpen] =
    useState(false);
  const [isDeletingDebt, setIsDeletingDebt] = useState(false);
  const [isDeletingContact, setIsDeletingContact] = useState(false);

  // Selected items
  const [selectedDebt, setSelectedDebt] = useState<DebtResponse | null>(null);
  const [selectedContact, setSelectedContact] =
    useState<ContactResponse | null>(null);
  const [deleteDebtTarget, setDeleteDebtTarget] = useState<DebtResponse | null>(
    null,
  );
  const [deleteContactTarget, setDeleteContactTarget] =
    useState<ContactResponse | null>(null);

  // Side panel state
  const [sidePanelDebt, setSidePanelDebt] = useState<DebtResponse | null>(null);
  const [sidePanelPayments, setSidePanelPayments] = useState<
    DebtPaymentResponse[]
  >([]);
  const [sidePanelPaymentsLoading, setSidePanelPaymentsLoading] =
    useState(false);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  // Tab & filter state
  const [activeTab, setActiveTab] = useState<TabType>("debts");
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [filters, setFilters] = useState<DebtFilters>({ page: 1, size: 10 });

  // Data state
  const [allDebts, setAllDebts] = useState<DebtResponse[]>([]);
  const [contacts, setContacts] = useState<ContactResponse[]>([]);
  const [contactSummaries, setContactSummaries] = useState<ContactSummary[]>(
    [],
  );
  const [summary, setSummary] = useState<DebtSummary | null>(null);
  const [allLoading, setAllLoading] = useState(true);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setAllLoading(true);
    try {
      const [debtsResult, contactsResult, summaryResult, summariesResult] =
        await Promise.all([
          debtApi.getDebts(),
          contactApi.getContacts(),
          debtApi.getDebtSummary(),
          contactApi.getContactSummaries(),
        ]);

      if (!("error" in debtsResult)) setAllDebts(debtsResult);
      if (!("error" in contactsResult)) setContacts(contactsResult);
      if (!("error" in summaryResult)) setSummary(summaryResult);
      if (!("error" in summariesResult)) setContactSummaries(summariesResult);
    } catch (err) {
      logger.error("Error loading debts data:", err);
    } finally {
      setAllLoading(false);
    }
  }, [debtApi, contactApi]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Client-side filtering
  const filteredDebts = useMemo(() => {
    let result = [...allDebts];

    if (filters.status && filters.status !== "all") {
      if (filters.status === "active") {
        result = result.filter((d) => d.is_active && !d.is_paid_off);
      } else if (filters.status === "paid_off") {
        result = result.filter((d) => d.is_paid_off);
      }
    }
    if (filters.debt_type) {
      result = result.filter((d) => d.debt_type === filters.debt_type);
    }
    if (filters.contact_id) {
      result = result.filter((d) => d.contact_id === filters.contact_id);
    }
    if (filters.currency) {
      result = result.filter((d) => d.currency === filters.currency);
    }
    if (filters.date_from) {
      result = result.filter(
        (d) => (d.due_date || d.start_date) >= filters.date_from!,
      );
    }
    if (filters.date_to) {
      result = result.filter(
        (d) => (d.due_date || d.start_date) <= filters.date_to!,
      );
    }

    return result;
  }, [allDebts, filters]);

  // Client-side pagination
  const paginatedDebts = useMemo(() => {
    const start = ((filters.page || 1) - 1) * (filters.size || 10);
    return filteredDebts.slice(start, start + (filters.size || 10));
  }, [filteredDebts, filters.page, filters.size]);

  const totalItems = filteredDebts.length;
  const totalPages = Math.ceil(totalItems / (filters.size || 10));

  // Keyboard shortcut: N to add
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "n" || e.key === "N") {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
        e.preventDefault();
        if (activeTab === "debts") {
          setIsCreateDebtModalOpen(true);
        } else {
          setIsCreateContactModalOpen(true);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [activeTab]);

  const tabs = [
    {
      id: "debts",
      label: t("debtPage.tabs.debts"),
      icon: <FaTable className="w-4 h-4" />,
    },
    {
      id: "contacts",
      label: t("debtPage.tabs.contacts"),
      icon: <FaAddressBook className="w-4 h-4" />,
    },
  ];

  // Side panel
  const openSidePanel = async (debt: DebtResponse) => {
    setSidePanelDebt(debt);
    setSidePanelOpen(true);
    setSidePanelPaymentsLoading(true);
    try {
      const result = await debtApi.getPayments(debt.id);
      if (!("error" in result)) {
        setSidePanelPayments(result);
      } else {
        setSidePanelPayments([]);
      }
    } catch {
      setSidePanelPayments([]);
    } finally {
      setSidePanelPaymentsLoading(false);
    }
  };

  const closeSidePanel = () => {
    setSidePanelOpen(false);
    setTimeout(() => {
      setSidePanelDebt(null);
      setSidePanelPayments([]);
    }, 300);
  };

  // Debt CRUD handlers
  const handleCreateDebt = async (debtData: DebtCreate | DebtUpdate) => {
    try {
      const result = await debtApi.createDebt(debtData as DebtCreate);
      if (!("error" in result)) {
        setAllDebts((prev) => [...prev, result]);
        setIsCreateDebtModalOpen(false);
        const summaryResult = await debtApi.getDebtSummary();
        if (!("error" in summaryResult)) setSummary(summaryResult);
        toast.success(t("debtPage.messages.debtCreated"));
      }
    } catch (err) {
      logger.error("Error creating debt:", err);
    }
  };

  const handleUpdateDebt = async (debtData: DebtCreate | DebtUpdate) => {
    if (!selectedDebt) return;
    try {
      const result = await debtApi.updateDebt(
        selectedDebt.id,
        debtData as DebtUpdate,
      );
      if (!("error" in result)) {
        setAllDebts((prev) =>
          prev.map((d) => (d.id === selectedDebt.id ? result : d)),
        );
        setIsEditDebtModalOpen(false);
        setSelectedDebt(null);
        if (sidePanelDebt?.id === selectedDebt.id) {
          setSidePanelDebt(result);
        }
        const summaryResult = await debtApi.getDebtSummary();
        if (!("error" in summaryResult)) setSummary(summaryResult);
        toast.success(t("debtPage.messages.debtUpdated"));
      }
    } catch (err) {
      logger.error("Error updating debt:", err);
    }
  };

  const handleDeleteDebtConfirm = async () => {
    if (!deleteDebtTarget) return;
    setIsDeletingDebt(true);
    try {
      const result = await debtApi.deleteDebt(deleteDebtTarget.id);
      if (typeof result === "boolean" && result === true) {
        setAllDebts((prev) => prev.filter((d) => d.id !== deleteDebtTarget.id));
        if (sidePanelDebt?.id === deleteDebtTarget.id) closeSidePanel();
        const summaryResult = await debtApi.getDebtSummary();
        if (!("error" in summaryResult)) setSummary(summaryResult);
        toast.success(t("debtPage.messages.debtDeleted"));
      }
    } catch (err) {
      logger.error("Error deleting debt:", err);
    } finally {
      setIsDeletingDebt(false);
      setIsDeleteDebtModalOpen(false);
      setDeleteDebtTarget(null);
    }
  };

  const handleMakePayment = async (paymentData: DebtPaymentCreate) => {
    if (!selectedDebt) return;
    try {
      const [paymentResult, updatedDebtResult, summaryResult] =
        await Promise.all([
          debtApi.createPayment(selectedDebt.id, paymentData),
          debtApi.getDebt(selectedDebt.id),
          debtApi.getDebtSummary(),
        ]);

      if (!("error" in paymentResult)) {
        if (!("error" in updatedDebtResult)) {
          setAllDebts((prev) =>
            prev.map((d) => (d.id === selectedDebt.id ? updatedDebtResult : d)),
          );
          if (sidePanelDebt?.id === selectedDebt.id) {
            setSidePanelDebt(updatedDebtResult);
            // Refresh payments in side panel
            const paymentsResult = await debtApi.getPayments(selectedDebt.id);
            if (!("error" in paymentsResult))
              setSidePanelPayments(paymentsResult);
          }
        }
        if (!("error" in summaryResult)) setSummary(summaryResult);
        setIsPaymentModalOpen(false);
        setSelectedDebt(null);
        toast.success(t("debtPage.messages.paymentMade"));
      }
    } catch (err) {
      logger.error("Error making payment:", err);
    }
  };

  const handleMarkAsPaid = async () => {
    if (!sidePanelDebt) return;
    try {
      const result = await debtApi.updateDebt(sidePanelDebt.id, {
        is_paid_off: true,
        is_active: false,
      });
      if (!("error" in result)) {
        setAllDebts((prev) =>
          prev.map((d) => (d.id === sidePanelDebt.id ? result : d)),
        );
        setSidePanelDebt(result);
        const summaryResult = await debtApi.getDebtSummary();
        if (!("error" in summaryResult)) setSummary(summaryResult);
        toast.success(t("debtPage.messages.markedAsPaid"));
      }
    } catch (err) {
      logger.error("Error marking as paid:", err);
    }
  };

  // Contact CRUD handlers
  const handleCreateContact = async (
    contactData: ContactCreate | ContactUpdate,
  ) => {
    try {
      const result = await contactApi.createContact(
        contactData as ContactCreate,
      );
      if (!("error" in result)) {
        setContacts((prev) => [...prev, result]);
        setIsCreateContactModalOpen(false);
        toast.success(t("debtPage.messages.contactCreated"));
      }
    } catch (err) {
      logger.error("Error creating contact:", err);
    }
  };

  const handleUpdateContact = async (
    contactData: ContactCreate | ContactUpdate,
  ) => {
    if (!selectedContact) return;
    try {
      const result = await contactApi.updateContact(
        selectedContact.id,
        contactData as ContactUpdate,
      );
      if (!("error" in result)) {
        setContacts((prev) =>
          prev.map((c) => (c.id === selectedContact.id ? result : c)),
        );
        setIsEditContactModalOpen(false);
        setSelectedContact(null);
        toast.success(t("debtPage.messages.contactUpdated"));
      }
    } catch (err) {
      logger.error("Error updating contact:", err);
    }
  };

  const handleDeleteContactConfirm = async () => {
    if (!deleteContactTarget) return;
    setIsDeletingContact(true);
    try {
      const result = await contactApi.deleteContact(deleteContactTarget.id);
      if (typeof result === "boolean" && result === true) {
        setContacts((prev) =>
          prev.filter((c) => c.id !== deleteContactTarget.id),
        );
        toast.success(t("debtPage.messages.contactDeleted"));
      }
    } catch (err) {
      logger.error("Error deleting contact:", err);
    } finally {
      setIsDeletingContact(false);
      setIsDeleteContactModalOpen(false);
      setDeleteContactTarget(null);
    }
  };

  const handleExportCsv = () => {
    exportDebtsCsv(filteredDebts);
  };

  const handleFiltersChange = (newFilters: DebtFilters) => {
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
    filters.debt_type ||
    filters.contact_id ||
    filters.currency ||
    filters.date_from ||
    filters.date_to;

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <DebtPageHeader
          onAddDebt={() => setIsCreateDebtModalOpen(true)}
          onToggleFilters={() => setFiltersVisible((v) => !v)}
          onExportCsv={handleExportCsv}
          filtersActive={Boolean(hasActiveFilters)}
        />

        {/* KPI Strip */}
        <DebtSummaryStrip summary={summary} loading={allLoading} />

        {/* Filter Bar */}
        <DebtFilterBar
          filters={filters}
          onFiltersChange={handleFiltersChange}
          isVisible={filtersVisible}
          contacts={contacts}
          debts={allDebts}
        />

        {/* Tabs */}
        <Card>
          <Tabs
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={(tab) => setActiveTab(tab as TabType)}
            className="px-4 sm:px-6"
          />
        </Card>

        {/* Debts Tab */}
        {activeTab === "debts" && (
          <Card>
            <DebtTable
              debts={paginatedDebts}
              loading={allLoading}
              currentPage={filters.page || 1}
              totalPages={totalPages}
              pageSize={filters.size || 10}
              totalItems={totalItems}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              onRowClick={openSidePanel}
              onMakePayment={(debt) => {
                setSelectedDebt(debt);
                setIsPaymentModalOpen(true);
              }}
              onEdit={(debt) => {
                setSelectedDebt(debt);
                setIsEditDebtModalOpen(true);
              }}
              onDelete={(debt) => {
                setDeleteDebtTarget(debt);
                setIsDeleteDebtModalOpen(true);
              }}
              emptyMessage={
                hasActiveFilters
                  ? t("debtPage.filters.noMatchFilters")
                  : undefined
              }
            />
          </Card>
        )}

        {/* Contacts Tab */}
        {activeTab === "contacts" && (
          <Card>
            <ContactTable
              contacts={contacts}
              contactSummaries={contactSummaries}
              loading={allLoading}
              onEdit={(contact) => {
                setSelectedContact(contact);
                setIsEditContactModalOpen(true);
              }}
              onDelete={(contact) => {
                setDeleteContactTarget(contact);
                setIsDeleteContactModalOpen(true);
              }}
              onCreateClick={() => setIsCreateContactModalOpen(true)}
            />
          </Card>
        )}

        {/* Side Panel */}
        <DebtSidePanel
          debt={sidePanelDebt}
          payments={sidePanelPayments}
          paymentsLoading={sidePanelPaymentsLoading}
          isOpen={sidePanelOpen}
          onClose={closeSidePanel}
          onMakePayment={() => {
            if (sidePanelDebt) {
              setSelectedDebt(sidePanelDebt);
              setIsPaymentModalOpen(true);
            }
          }}
          onMarkAsPaid={handleMarkAsPaid}
          onEdit={() => {
            if (sidePanelDebt) {
              setSelectedDebt(sidePanelDebt);
              setIsEditDebtModalOpen(true);
            }
          }}
          onDelete={() => {
            if (sidePanelDebt) {
              setDeleteDebtTarget(sidePanelDebt);
              setIsDeleteDebtModalOpen(true);
            }
          }}
        />

        {/* Create Debt Modal */}
        <Modal
          isOpen={isCreateDebtModalOpen}
          onClose={() => setIsCreateDebtModalOpen(false)}
          title={t("debtPage.createModalTitle")}
          size="xl"
        >
          <DebtForm
            contacts={contacts}
            categories={categories}
            onSubmit={handleCreateDebt}
            onCancel={() => setIsCreateDebtModalOpen(false)}
            mode="create"
            showCard={false}
          />
        </Modal>

        {/* Edit Debt Modal */}
        <Modal
          isOpen={isEditDebtModalOpen}
          onClose={() => {
            setIsEditDebtModalOpen(false);
            setSelectedDebt(null);
          }}
          title={t("debtPage.editModalTitle")}
          size="xl"
        >
          {selectedDebt && (
            <DebtForm
              initialData={selectedDebt}
              contacts={contacts}
              categories={categories}
              onSubmit={handleUpdateDebt}
              onCancel={() => {
                setIsEditDebtModalOpen(false);
                setSelectedDebt(null);
              }}
              mode="edit"
              showCard={false}
              paymentCount={selectedDebt.payment_count ?? 0}
            />
          )}
        </Modal>

        {/* Payment Modal */}
        <Modal
          isOpen={isPaymentModalOpen}
          onClose={() => {
            setIsPaymentModalOpen(false);
            setSelectedDebt(null);
          }}
          title={t("debtPage.paymentModalTitle")}
          size="lg"
        >
          {selectedDebt && (
            <PaymentForm
              debtId={selectedDebt.id}
              currentBalance={selectedDebt.current_balance}
              currency={selectedDebt.currency}
              onSubmit={handleMakePayment}
              onCancel={() => {
                setIsPaymentModalOpen(false);
                setSelectedDebt(null);
              }}
              showCard={false}
            />
          )}
        </Modal>

        {/* Delete Debt Confirmation Modal */}
        <Modal
          isOpen={isDeleteDebtModalOpen}
          onClose={() => {
            setIsDeleteDebtModalOpen(false);
            setDeleteDebtTarget(null);
          }}
          title={t("debtPage.deleteConfirmModal.title")}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm theme-text-secondary">
              {t("debtPage.deleteConfirmModal.message")}
            </p>
            {deleteDebtTarget && (
              <div className="theme-bg-secondary rounded-lg p-3 text-sm">
                <span className="font-medium theme-text-primary">
                  {deleteDebtTarget.name}
                </span>
                <span className="ml-2 text-red-500/80 dark:text-red-400/70 font-semibold tabular-nums">
                  {Math.abs(deleteDebtTarget.current_balance).toLocaleString(
                    "uk-UA",
                    { minimumFractionDigits: 2 },
                  )}{" "}
                  {deleteDebtTarget.currency}
                </span>
              </div>
            )}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsDeleteDebtModalOpen(false);
                  setDeleteDebtTarget(null);
                }}
              >
                {t("debtPage.deleteConfirmModal.cancel")}
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={isDeletingDebt}
                onClick={handleDeleteDebtConfirm}
              >
                {t("debtPage.deleteConfirmModal.confirm")}
              </Button>
            </div>
          </div>
        </Modal>

        {/* Create Contact Modal */}
        <Modal
          isOpen={isCreateContactModalOpen}
          onClose={() => setIsCreateContactModalOpen(false)}
          title={t("debtPage.contacts.form.createTitle")}
          size="xl"
        >
          <ContactForm
            onSubmit={handleCreateContact}
            onCancel={() => setIsCreateContactModalOpen(false)}
            mode="create"
            showCard={false}
          />
        </Modal>

        {/* Edit Contact Modal */}
        <Modal
          isOpen={isEditContactModalOpen}
          onClose={() => {
            setIsEditContactModalOpen(false);
            setSelectedContact(null);
          }}
          title={t("debtPage.contacts.form.editTitle")}
          size="xl"
        >
          {selectedContact && (
            <ContactForm
              initialData={selectedContact}
              onSubmit={handleUpdateContact}
              onCancel={() => {
                setIsEditContactModalOpen(false);
                setSelectedContact(null);
              }}
              mode="edit"
              showCard={false}
            />
          )}
        </Modal>

        {/* Delete Contact Confirmation Modal */}
        <Modal
          isOpen={isDeleteContactModalOpen}
          onClose={() => {
            setIsDeleteContactModalOpen(false);
            setDeleteContactTarget(null);
          }}
          title={t("debtPage.deleteContactModal.title")}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm theme-text-secondary">
              {t("debtPage.deleteContactModal.message")}
            </p>
            {deleteContactTarget && (
              <div className="theme-bg-secondary rounded-lg p-3 text-sm">
                <span className="font-medium theme-text-primary">
                  {deleteContactTarget.name}
                </span>
                {deleteContactTarget.company && (
                  <span className="ml-2 theme-text-tertiary">
                    {deleteContactTarget.company}
                  </span>
                )}
              </div>
            )}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsDeleteContactModalOpen(false);
                  setDeleteContactTarget(null);
                }}
              >
                {t("debtPage.deleteContactModal.cancel")}
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={isDeletingContact}
                onClick={handleDeleteContactConfirm}
              >
                {t("debtPage.deleteContactModal.confirm")}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};

export default Debts;
