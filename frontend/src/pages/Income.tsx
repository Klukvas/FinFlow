import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { CreateIncome } from '../components/ui/income/CreateIncome';
import { IncomeList } from '../components/ui/income/IncomeList';
import { IncomeDashboard } from '../components/ui/income/IncomeDashboard';
import { IncomePageHeader } from '../components/ui/income/IncomePageHeader';
import { IncomeSummaryStrip } from '../components/ui/income/IncomeSummaryStrip';
import { IncomeFilterBar } from '../components/ui/income/IncomeFilterBar';
import { Modal } from '../components/ui/shared/Modal';
import { Card } from '../components/ui/shared/Card';
import { Button } from '../components/ui/shared/Button';
import { Tabs } from '../components/ui/shared/Tabs';
import { FaTable, FaChartBar } from 'react-icons/fa';
import { IncomeOut, IncomeFilters } from '@/types';
import { useApiClients } from '@/hooks';
import { useCategories } from '@/contexts/CategoriesContext';
import { exportIncomeCsv } from '@/utils/exportCsv';

export const Income = () => {
  const { t } = useTranslation();
  const { income: incomeApi } = useApiClients();
  const { categories: categoriesList } = useCategories();

  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<IncomeOut | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Tab & filter state
  const [activeTab, setActiveTab] = useState('table');
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [filters, setFilters] = useState<IncomeFilters>({ page: 1, size: 10 });

  // Data state
  const [allIncomes, setAllIncomes] = useState<IncomeOut[]>([]);
  const [paginatedIncomes, setPaginatedIncomes] = useState<IncomeOut[]>([]);
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
  const hasActiveFilters =
    filters.date_from ||
    filters.date_to ||
    (filters.category_ids && filters.category_ids.length > 0) ||
    filters.account_id ||
    filters.currency;

  // Fetch ALL incomes (for KPI, dashboard, and client-side filtering)
  const fetchAllIncomes = useCallback(async () => {
    setAllLoading(true);
    try {
      const response = await incomeApi.getIncomes(0, 10000);
      if (!('error' in response)) {
        setAllIncomes(response);
      }
    } catch (err) {
      console.error('Error fetching all incomes:', err);
    } finally {
      setAllLoading(false);
    }
  }, [incomeApi]);

  // Fetch paginated incomes (when no filters active)
  const fetchPaginatedIncomes = useCallback(async () => {
    if (hasActiveFilters) return;
    setPaginatedLoading(true);
    try {
      const response = await incomeApi.getIncomesPaginated({
        page: filters.page ?? 1,
        size: filters.size ?? 10,
      });
      if (!('error' in response)) {
        setPaginatedIncomes(response.items);
        setTotalItems(response.total);
        setTotalPages(response.pages);
      }
    } catch (err) {
      console.error('Error fetching paginated incomes:', err);
    } finally {
      setPaginatedLoading(false);
    }
  }, [incomeApi, filters.page, filters.size, hasActiveFilters]);

  useEffect(() => {
    fetchAllIncomes();
  }, [fetchAllIncomes]);

  useEffect(() => {
    fetchPaginatedIncomes();
  }, [fetchPaginatedIncomes]);

  // Client-side filtered incomes
  const filteredIncomes = useMemo(() => {
    if (!hasActiveFilters) return paginatedIncomes;

    let result = [...allIncomes];

    if (filters.date_from) {
      result = result.filter((e) => e.date >= filters.date_from!);
    }
    if (filters.date_to) {
      result = result.filter((e) => e.date <= filters.date_to!);
    }
    if (filters.category_ids && filters.category_ids.length > 0) {
      result = result.filter((e) => e.category_id != null && filters.category_ids!.includes(e.category_id));
    }
    if (filters.account_id) {
      result = result.filter((e) => e.account_id === filters.account_id);
    }
    if (filters.currency) {
      result = result.filter((e) => e.currency === filters.currency);
    }

    return result;
  }, [allIncomes, paginatedIncomes, filters, hasActiveFilters]);

  // Client-side pagination for filtered results
  const clientPaginatedIncomes = useMemo(() => {
    if (!hasActiveFilters) return filteredIncomes;
    const start = ((filters.page || 1) - 1) * (filters.size || 10);
    return filteredIncomes.slice(start, start + (filters.size || 10));
  }, [filteredIncomes, filters.page, filters.size, hasActiveFilters]);

  const displayedTotalItems = hasActiveFilters ? filteredIncomes.length : totalItems;
  const displayedTotalPages = hasActiveFilters
    ? Math.ceil(filteredIncomes.length / (filters.size || 10))
    : totalPages;

  // Keyboard shortcut: N to add income
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'n' || e.key === 'N') {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        e.preventDefault();
        setIsCreateModalOpen(true);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const tabs = [
    { id: 'table', label: t('incomePage.tabs.table'), icon: <FaTable className="w-4 h-4" /> },
    { id: 'dashboard', label: t('incomePage.tabs.dashboard'), icon: <FaChartBar className="w-4 h-4" /> },
  ];

  const refreshData = () => {
    fetchAllIncomes();
    fetchPaginatedIncomes();
  };

  const handleIncomeCreated = () => {
    setIsCreateModalOpen(false);
    refreshData();
  };

  const handleDeleteRequest = (income: IncomeOut) => {
    setDeleteTarget(income);
    setIsDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await incomeApi.deleteIncome(deleteTarget.id);
      refreshData();
    } catch (err) {
      console.error('Error deleting income:', err);
    } finally {
      setIsDeleting(false);
      setIsDeleteModalOpen(false);
      setDeleteTarget(null);
    }
  };

  const handleExportCsv = () => {
    const incomesToExport = hasActiveFilters ? filteredIncomes : allIncomes;
    exportIncomeCsv(incomesToExport, categoryMap);
  };

  const handleFiltersChange = (newFilters: IncomeFilters) => {
    setFilters(newFilters);
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handlePageSizeChange = (size: number) => {
    setFilters((prev) => ({ ...prev, size, page: 1 }));
  };

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <IncomePageHeader
          onAddIncome={() => setIsCreateModalOpen(true)}
          onToggleFilters={() => setFiltersVisible((v) => !v)}
          onExportCsv={handleExportCsv}
          filtersActive={Boolean(hasActiveFilters)}
        />

        {/* KPI Strip */}
        <IncomeSummaryStrip incomes={allIncomes} loading={allLoading} />

        {/* Filter Bar */}
        <IncomeFilterBar
          filters={filters}
          onFiltersChange={handleFiltersChange}
          isVisible={filtersVisible}
        />

        {/* Tabs */}
        <Card>
          <Tabs
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            className="px-4 sm:px-6"
          />
        </Card>

        {/* Tab Content */}
        {activeTab === 'table' && (
          <Card>
            <IncomeList
              incomes={clientPaginatedIncomes}
              loading={paginatedLoading || (hasActiveFilters ? allLoading : false)}
              categories={categoryMap}
              currentPage={filters.page || 1}
              totalPages={displayedTotalPages}
              pageSize={filters.size || 10}
              totalItems={displayedTotalItems}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              onDeleteRequest={handleDeleteRequest}
              emptyMessage={hasActiveFilters ? t('incomePage.filters.noMatchFilters') : undefined}
            />
          </Card>
        )}

        {activeTab === 'dashboard' && (
          <IncomeDashboard incomes={allIncomes} loading={allLoading} />
        )}

        {/* Create Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={t('incomePage.createModalTitle')}
          size="lg"
        >
          <CreateIncome onIncomeCreated={handleIncomeCreated} />
        </Modal>

        {/* Delete Confirmation Modal */}
        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => {
            setIsDeleteModalOpen(false);
            setDeleteTarget(null);
          }}
          title={t('incomePage.deleteConfirm.title')}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm theme-text-secondary">
              {t('incomePage.deleteConfirm.message')}
            </p>
            {deleteTarget && (
              <div className="theme-bg-secondary rounded-lg p-3 text-sm">
                <span className="font-medium text-green-600/80 dark:text-green-400/70">
                  +{deleteTarget.amount.toLocaleString('uk-UA', { minimumFractionDigits: 2 })}{' '}
                  {deleteTarget.currency}
                </span>
                <span className="theme-text-secondary ml-2">
                  {categoryMap[deleteTarget.category_id ?? 0] || ''}
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
                {t('incomePage.deleteConfirm.cancel')}
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={isDeleting}
                onClick={handleDeleteConfirm}
              >
                {t('incomePage.deleteConfirm.confirm')}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};
