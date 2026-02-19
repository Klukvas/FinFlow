import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Category as CategoryType, CategoryStatisticsResponse } from '@/types';
import { useApiClients } from '@/hooks/useApiClients';
import { useErrorHandler } from '@/hooks/useErrorHandler';
import { useCategories } from '@/contexts/CategoriesContext';
import { CategoryPageHeader } from '@/components/ui/category/CategoryPageHeader';
import { CategorySummaryStrip } from '@/components/ui/category/CategorySummaryStrip';
import { CategoryFilterBar } from '@/components/ui/category/CategoryFilterBar';
import { CategoryTree } from '@/components/ui/category/CategoryTree';
import { CategoryTable } from '@/components/ui/category/CategoryTable';
import { CategorySidePanel } from '@/components/ui/category/CategorySidePanel';
import { CreateCategory } from '@/components/ui/category/CreateCategory';
import { EditCategory } from '@/components/ui/category/EditCategory';
import { CategoryPageFilters, CategoryUsageData, buildCategoryTree } from '@/components/ui/category/categoryHelpers';
import { Modal } from '@/components/ui/shared/Modal';
import { Card } from '@/components/ui/shared/Card';
import { Button } from '@/components/ui/shared/Button';
import { Badge } from '@/components/ui/shared/Badge';
import { toast } from 'sonner';

export const Category: React.FC = () => {
  const { t } = useTranslation();
  const { category: categoryApi, expense: expenseApi, income: incomeApi } = useApiClients();
  const { handleCategoryError } = useErrorHandler();
  const { refreshCategories } = useCategories();

  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Selected items
  const [editingCategory, setEditingCategory] = useState<CategoryType | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CategoryType | null>(null);

  // Side panel state
  const [sidePanelCategory, setSidePanelCategory] = useState<CategoryType | null>(null);
  const [sidePanelUsage, setSidePanelUsage] = useState<CategoryUsageData | null>(null);
  const [sidePanelUsageLoading, setSidePanelUsageLoading] = useState(false);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  // Filter state
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [filters, setFilters] = useState<CategoryPageFilters>({
    page: 1,
    size: 25,
    viewMode: 'tree',
  });

  // Tree state
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());

  // Data state
  const [allCategories, setAllCategories] = useState<CategoryType[]>([]);
  const [treeCategories, setTreeCategories] = useState<CategoryType[]>([]);
  const [stats, setStats] = useState<CategoryStatisticsResponse | null>(null);
  const [allLoading, setAllLoading] = useState(true);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setAllLoading(true);
    try {
      const [flatResult, treeResult, statsResult] = await Promise.all([
        categoryApi.getCategories(true),
        categoryApi.getCategories(false),
        categoryApi.getCategoryStatistics(),
      ]);

      if (!('error' in flatResult)) setAllCategories(flatResult);
      if (!('error' in treeResult)) setTreeCategories(treeResult);
      if (!('error' in statsResult)) setStats(statsResult);
    } catch (err) {
      console.error('Error loading categories data:', err);
    } finally {
      setAllLoading(false);
    }
  }, [categoryApi]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Client-side filtering
  const filteredCategories = useMemo(() => {
    let result = [...allCategories];

    if (filters.type && filters.type !== 'all') {
      result = result.filter((c) => c.type === filters.type);
    }
    if (filters.search && filters.search.trim()) {
      const q = filters.search.toLowerCase();
      result = result.filter((c) => c.name.toLowerCase().includes(q));
    }

    return result;
  }, [allCategories, filters]);

  // For tree view: rebuild tree from filtered results
  const filteredTree = useMemo(() => {
    const hasFilters =
      (filters.type && filters.type !== 'all') ||
      (filters.search && filters.search.trim());

    if (!hasFilters) return treeCategories;

    // Include matching categories and their parents to maintain tree structure
    const matchIds = new Set(filteredCategories.map((c) => c.id));
    const withParents = allCategories.filter(
      (c) =>
        matchIds.has(c.id) ||
        allCategories.some((child) => child.parent_id === c.id && matchIds.has(child.id)),
    );
    return buildCategoryTree(withParents);
  }, [filteredCategories, treeCategories, allCategories, filters]);

  // Client-side pagination (table view only)
  const paginatedCategories = useMemo(() => {
    const start = ((filters.page || 1) - 1) * (filters.size || 25);
    return filteredCategories.slice(start, start + (filters.size || 25));
  }, [filteredCategories, filters.page, filters.size]);

  const totalItems = filteredCategories.length;
  const totalPages = Math.ceil(totalItems / (filters.size || 25));

  // Keyboard shortcut: N to add
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

  // Side panel
  const openSidePanel = async (cat: CategoryType) => {
    setSidePanelCategory(cat);
    setSidePanelOpen(true);
    setSidePanelUsageLoading(true);
    try {
      const [expResult, incResult] = await Promise.all([
        expenseApi.getExpensesByCategory(cat.id),
        incomeApi.getIncomesByCategory(cat.id),
      ]);

      const usage: CategoryUsageData = {
        expenseCount: 0,
        incomeCount: 0,
        totalAmount: 0,
        averageAmount: 0,
        currency: '',
        recentExpenses: [],
        recentIncomes: [],
      };

      if (!('error' in expResult)) {
        usage.expenseCount = expResult.statistics.count;
        usage.totalAmount += expResult.statistics.total_amount;
        usage.currency = expResult.statistics.currency;
        usage.recentExpenses = expResult.expenses.slice(0, 5);
      }
      if (!('error' in incResult)) {
        usage.incomeCount = incResult.statistics.count;
        usage.totalAmount += incResult.statistics.total_amount;
        if (!usage.currency) usage.currency = incResult.statistics.currency;
        usage.recentIncomes = incResult.incomes.slice(0, 5);
      }

      const total = usage.expenseCount + usage.incomeCount;
      usage.averageAmount = total > 0 ? usage.totalAmount / total : 0;
      setSidePanelUsage(usage);
    } catch {
      setSidePanelUsage(null);
    } finally {
      setSidePanelUsageLoading(false);
    }
  };

  const closeSidePanel = () => {
    setSidePanelOpen(false);
    setTimeout(() => {
      setSidePanelCategory(null);
      setSidePanelUsage(null);
    }, 300);
  };

  // Get child categories for side panel
  const sidePanelChildren = useMemo(() => {
    if (!sidePanelCategory) return [];
    return allCategories.filter((c) => c.parent_id === sidePanelCategory.id);
  }, [sidePanelCategory, allCategories]);

  // Create handler
  const handleCategoryCreated = async () => {
    setIsCreateModalOpen(false);
    await refreshCategories();
    fetchAllData();
    toast.success(t('categoryPage.messages.categoryCreated'));
  };

  // Edit handler
  const handleCategoryUpdated = async () => {
    const editId = editingCategory?.id;
    setIsEditModalOpen(false);
    setEditingCategory(null);
    await refreshCategories();
    fetchAllData();
    toast.success(t('categoryPage.messages.categoryUpdated'));
    // Refresh side panel if open for same category
    if (sidePanelCategory && editId && sidePanelCategory.id === editId) {
      const updated = await categoryApi.getCategory(editId);
      if (!('error' in updated)) {
        setSidePanelCategory(updated);
      }
    }
  };

  const handleCancelEdit = () => {
    setIsEditModalOpen(false);
    setEditingCategory(null);
  };

  // Delete handler
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const result = await categoryApi.deleteCategory(deleteTarget.id);
      if (result && 'error' in result) {
        handleCategoryError(result, true);
        return;
      }
      await refreshCategories();
      fetchAllData();
      if (sidePanelCategory?.id === deleteTarget.id) closeSidePanel();
      toast.success(t('categoryPage.messages.categoryDeleted'));
    } catch (err) {
      handleCategoryError(err as Error, true);
    } finally {
      setIsDeleting(false);
      setIsDeleteModalOpen(false);
      setDeleteTarget(null);
    }
  };

  // Toggle tree node
  const handleToggleExpand = (id: number) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Filter change
  const handleFiltersChange = (newFilters: CategoryPageFilters) => {
    setFilters(newFilters);
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handlePageSizeChange = (size: number) => {
    setFilters((prev) => ({ ...prev, size, page: 1 }));
  };

  const hasActiveFilters =
    (filters.type && filters.type !== 'all') ||
    (filters.search && filters.search.trim() !== '');

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <CategoryPageHeader
          onAdd={() => setIsCreateModalOpen(true)}
          onToggleFilters={() => setFiltersVisible((v) => !v)}
          filtersActive={Boolean(hasActiveFilters)}
        />

        {/* KPI Strip */}
        <CategorySummaryStrip stats={stats} loading={allLoading} />

        {/* Filter Bar */}
        <CategoryFilterBar
          filters={filters}
          onFiltersChange={handleFiltersChange}
          isVisible={filtersVisible}
        />

        {/* Content */}
        <Card>
          {filters.viewMode === 'tree' ? (
            <CategoryTree
              categories={filteredTree}
              loading={allLoading}
              onRowClick={openSidePanel}
              onEdit={(cat) => {
                setEditingCategory(cat);
                setIsEditModalOpen(true);
              }}
              onDelete={(cat) => {
                setDeleteTarget(cat);
                setIsDeleteModalOpen(true);
              }}
              expandedNodes={expandedNodes}
              onToggleExpand={handleToggleExpand}
              emptyMessage={hasActiveFilters ? t('categoryPage.filters.noMatchFilters') : undefined}
            />
          ) : (
            <CategoryTable
              categories={paginatedCategories}
              allCategories={allCategories}
              loading={allLoading}
              currentPage={filters.page || 1}
              totalPages={totalPages}
              pageSize={filters.size || 25}
              totalItems={totalItems}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              onRowClick={openSidePanel}
              onEdit={(cat) => {
                setEditingCategory(cat);
                setIsEditModalOpen(true);
              }}
              onDelete={(cat) => {
                setDeleteTarget(cat);
                setIsDeleteModalOpen(true);
              }}
              emptyMessage={hasActiveFilters ? t('categoryPage.filters.noMatchFilters') : undefined}
            />
          )}
        </Card>

        {/* Side Panel */}
        <CategorySidePanel
          category={sidePanelCategory}
          usageData={sidePanelUsage}
          usageLoading={sidePanelUsageLoading}
          childCategories={sidePanelChildren}
          isOpen={sidePanelOpen}
          onClose={closeSidePanel}
          onEdit={() => {
            if (sidePanelCategory) {
              setEditingCategory(sidePanelCategory);
              setIsEditModalOpen(true);
            }
          }}
          onDelete={() => {
            if (sidePanelCategory) {
              setDeleteTarget(sidePanelCategory);
              setIsDeleteModalOpen(true);
            }
          }}
          onChildClick={(child) => {
            openSidePanel(child);
          }}
        />

        {/* Create Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={t('categoryPage.createModalTitle')}
          size="md"
        >
          <CreateCategory onCategoryCreated={handleCategoryCreated} />
        </Modal>

        {/* Edit Modal */}
        {editingCategory && (
          <Modal
            isOpen={isEditModalOpen}
            onClose={handleCancelEdit}
            title={t('categoryPage.editModalTitle')}
            size="md"
          >
            <EditCategory
              category={editingCategory}
              onCategoryUpdated={handleCategoryUpdated}
              onCancel={handleCancelEdit}
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
          title={t('categoryPage.deleteConfirmModal.title')}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm theme-text-secondary">
              {t('categoryPage.deleteConfirmModal.message')}
            </p>
            {deleteTarget && (
              <div className="theme-bg-secondary rounded-lg p-3 text-sm">
                <span className="font-medium theme-text-primary">{deleteTarget.name}</span>
                <Badge
                  variant={deleteTarget.type === 'INCOME' ? 'success' : 'destructive'}
                  size="sm"
                  className="ml-2"
                >
                  {t(deleteTarget.type === 'INCOME' ? 'category.income' : 'category.expense')}
                </Badge>
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
                {t('categoryPage.deleteConfirmModal.cancel')}
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={isDeleting}
                onClick={handleDeleteConfirm}
              >
                {t('categoryPage.deleteConfirmModal.confirm')}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};
