import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { CreateExpense } from "../components/ui/expense/createExpense";
import { EditExpense } from "../components/ui/expense/editExpense";
import { ExpenseList } from "../components/ui/expense/expenseList";

import { ExpensePageHeader } from "../components/ui/expense/ExpensePageHeader";
import { ExpenseSummaryStrip } from "../components/ui/expense/ExpenseSummaryStrip";
import { ExpenseFilterBar } from "../components/ui/expense/ExpenseFilterBar";
import { Modal } from "../components/ui/shared/Modal";
import { Card } from "../components/ui/shared/Card";
import { Button } from "../components/ui/shared/Button";

import { ExpenseResponse, ExpenseFilters } from "@/types";
import { useApiClients } from "@/hooks";
import { useCategories } from "@/contexts/CategoriesContext";
import { exportExpensesCsv } from "@/utils/exportCsv";
import { logger } from "@/utils/logger";

export const Expense = () => {
 const { t } = useTranslation();
 const { expense: expenseApi } = useApiClients();
 const { categories: categoriesList } = useCategories();

 // Modal state
 const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
 const [isEditModalOpen, setIsEditModalOpen] = useState(false);
 const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
 const [selectedExpense, setSelectedExpense] =
 useState<ExpenseResponse | null>(null);
 const [deleteTarget, setDeleteTarget] = useState<ExpenseResponse | null>(
 null,
 );
 const [isDeleting, setIsDeleting] = useState(false);

 // Filter state
 const [filtersVisible, setFiltersVisible] = useState(false);
 const [filters, setFilters] = useState<ExpenseFilters>({ page: 1, size: 10 });

 // Data state
 const [allExpenses, setAllExpenses] = useState<ExpenseResponse[]>([]);
 const [paginatedExpenses, setPaginatedExpenses] = useState<ExpenseResponse[]>(
 [],
 );
 const [allLoading, setAllLoading] = useState(true);
 const [paginatedLoading, setPaginatedLoading] = useState(false);
 const [totalItems, setTotalItems] = useState(0);
 const [totalPages, setTotalPages] = useState(0);

 // Category map for quick lookup
 const categoryMap = useMemo(() => {
 const map: Record<number, string> = {};
 categoriesList.forEach((cat) => (map[cat.id] = cat.name));
 return map;
 }, [categoriesList]);

 // Determine if client-side filtering is active
 const hasActiveFilters: boolean = Boolean(
 filters.date_from ||
 filters.date_to ||
 (filters.category_ids && filters.category_ids.length > 0) ||
 filters.account_id ||
 filters.currency,
 );

 // Fetch ALL expenses (for KPI, dashboard, and client-side filtering)
 const fetchAllExpenses = useCallback(async () => {
 setAllLoading(true);
 try {
 const response = await expenseApi.getExpenses();
 if (!("error" in response)) {
 setAllExpenses(response);
 }
 } catch (err) {
 logger.error("Error fetching all expenses:", err);
 } finally {
 setAllLoading(false);
 }
 }, [expenseApi]);

 // Fetch paginated expenses (when no filters active)
 const fetchPaginatedExpenses = useCallback(async () => {
 if (hasActiveFilters) return;
 setPaginatedLoading(true);
 try {
 const response = await expenseApi.getExpensesPaginated({
 page: filters.page ?? 1,
 size: filters.size ?? 10,
 });
 if (!("error" in response)) {
 setPaginatedExpenses(response.items);
 setTotalItems(response.total);
 setTotalPages(response.pages);
 }
 } catch (err) {
 logger.error("Error fetching paginated expenses:", err);
 } finally {
 setPaginatedLoading(false);
 }
 }, [expenseApi, filters.page, filters.size, hasActiveFilters]);

 useEffect(() => {
 fetchAllExpenses();
 }, [fetchAllExpenses]);

 useEffect(() => {
 fetchPaginatedExpenses();
 }, [fetchPaginatedExpenses]);

 // Client-side filtered + paginated expenses
 const filteredExpenses = useMemo(() => {
 if (!hasActiveFilters) return paginatedExpenses;

 let result = [...allExpenses];

 if (filters.date_from) {
 result = result.filter(
 (e) => e.date != null && e.date >= filters.date_from!,
 );
 }
 if (filters.date_to) {
 result = result.filter(
 (e) => e.date != null && e.date <= filters.date_to!,
 );
 }
 if (filters.category_ids && filters.category_ids.length > 0) {
 result = result.filter(
 (e) =>
 e.category_id != null &&
 filters.category_ids!.includes(e.category_id),
 );
 }
 if (filters.account_id) {
 result = result.filter((e) => e.account_id === filters.account_id);
 }
 if (filters.currency) {
 result = result.filter((e) => e.currency === filters.currency);
 }

 return result;
 }, [allExpenses, paginatedExpenses, filters, hasActiveFilters]);

 // Client-side pagination for filtered results
 const clientPaginatedExpenses = useMemo(() => {
 if (!hasActiveFilters) return filteredExpenses;
 const start = ((filters.page || 1) - 1) * (filters.size || 10);
 return filteredExpenses.slice(start, start + (filters.size || 10));
 }, [filteredExpenses, filters.page, filters.size, hasActiveFilters]);

 const displayedTotalItems = hasActiveFilters
 ? filteredExpenses.length
 : totalItems;
 const displayedTotalPages = hasActiveFilters
 ? Math.ceil(filteredExpenses.length / (filters.size || 10))
 : totalPages;

 // Keyboard shortcut: N to add expense
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

 const refreshData = () => {
 fetchAllExpenses();
 fetchPaginatedExpenses();
 };

 const handleExpenseCreated = () => {
 setIsCreateModalOpen(false);
 refreshData();
 };

 const handleEditExpense = (expense: ExpenseResponse) => {
 setSelectedExpense(expense);
 setIsEditModalOpen(true);
 };

 const handleExpenseUpdated = () => {
 setIsEditModalOpen(false);
 setSelectedExpense(null);
 refreshData();
 };

 const handleDeleteRequest = (expense: ExpenseResponse) => {
 setDeleteTarget(expense);
 setIsDeleteModalOpen(true);
 };

 const handleDeleteConfirm = async () => {
 if (!deleteTarget) return;
 setIsDeleting(true);
 try {
 await expenseApi.deleteExpense(deleteTarget.id);
 refreshData();
 } catch (err) {
 logger.error("Error deleting expense:", err);
 } finally {
 setIsDeleting(false);
 setIsDeleteModalOpen(false);
 setDeleteTarget(null);
 }
 };

 const handleExportCsv = () => {
 const expensesToExport = hasActiveFilters ? filteredExpenses : allExpenses;
 exportExpensesCsv(expensesToExport, categoryMap);
 };

 const handleFiltersChange = (newFilters: ExpenseFilters) => {
 setFilters(newFilters);
 };

 const handlePageChange = (page: number) => {
 setFilters((prev) => ({ ...prev, page }));
 };

 const handlePageSizeChange = (size: number) => {
 setFilters((prev) => ({ ...prev, size, page: 1 }));
 };

 return (
 <div className="min-h-screen bg-surface p-2 sm:p-4 md:p-6 lg:p-8">
 <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
 {/* Header */}
 <ExpensePageHeader
 onAddExpense={() => setIsCreateModalOpen(true)}
 onToggleFilters={() => setFiltersVisible((v) => !v)}
 onExportCsv={handleExportCsv}
 filtersActive={Boolean(hasActiveFilters)}
 />

 {/* KPI Strip */}
 <ExpenseSummaryStrip expenses={allExpenses} loading={allLoading} />

 {/* Filter Bar */}
 <ExpenseFilterBar
 filters={filters}
 onFiltersChange={handleFiltersChange}
 isVisible={filtersVisible}
 />

 {/* Expense List */}
 <Card>
 <ExpenseList
 expenses={clientPaginatedExpenses}
 loading={paginatedLoading || (hasActiveFilters && allLoading)}
 categories={categoryMap}
 currentPage={filters.page || 1}
 totalPages={displayedTotalPages}
 pageSize={filters.size || 10}
 totalItems={displayedTotalItems}
 onPageChange={handlePageChange}
 onPageSizeChange={handlePageSizeChange}
 onEditExpense={handleEditExpense}
 onDeleteRequest={handleDeleteRequest}
 emptyMessage={
 hasActiveFilters
 ? t("expensePage.filters.noMatchFilters")
 : undefined
 }
 />
 </Card>

 {/* Create Modal */}
 <Modal
 isOpen={isCreateModalOpen}
 onClose={() => setIsCreateModalOpen(false)}
 title={t("expensePage.createModalTitle")}
 size="lg"
 >
 <CreateExpense onExpenseCreated={handleExpenseCreated} />
 </Modal>

 {/* Edit Modal */}
 {selectedExpense && (
 <Modal
 isOpen={isEditModalOpen}
 onClose={() => {
 setIsEditModalOpen(false);
 setSelectedExpense(null);
 }}
 title={t("expense.editTitle")}
 size="lg"
 >
 <EditExpense
 expense={selectedExpense}
 onExpenseUpdated={handleExpenseUpdated}
 />
 </Modal>
 )}

 {/* Delete Confirmation Modal */}
 <Modal
 isOpen={isDeleteModalOpen}
 onClose={() => {
 setIsDeleteModalOpen(false);
 setDeleteTarget(null);
 }}
 title={t("expensePage.deleteConfirm.title")}
 size="sm"
 >
 <div className="space-y-4">
 <p className="text-sm text-content-secondary">
 {t("expensePage.deleteConfirm.message")}
 </p>
 {deleteTarget && (
 <div className="bg-surface-alt rounded-lg p-3 text-sm">
 <span className="font-medium text-content">
 {deleteTarget.amount.toLocaleString("uk-UA", {
 minimumFractionDigits: 2,
 })}{" "}
 {deleteTarget.currency}
 </span>
 <span className="text-content-secondary ml-2">
 {(deleteTarget.category_id != null
 ? categoryMap[deleteTarget.category_id]
 : undefined) || ""}
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
 {t("expensePage.deleteConfirm.cancel")}
 </Button>
 <Button
 variant="danger"
 size="sm"
 loading={isDeleting}
 onClick={handleDeleteConfirm}
 >
 {t("expensePage.deleteConfirm.confirm")}
 </Button>
 </div>
 </div>
 </Modal>
 </div>
 </div>
 );
};

export default Expense;
