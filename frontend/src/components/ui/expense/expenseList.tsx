import React, { useCallback, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { ExpenseResponse } from '@/types';
import { useApiClients } from '@/hooks';
import { DeleteButton, EditButton, PaginationView } from '@/components/ui';

interface ExpenseListProps {
  onEditExpense?: (expense: ExpenseResponse) => void;
}

export const ExpenseList: React.FC<ExpenseListProps> = ({ onEditExpense }) => {
    const { t } = useTranslation();
    const [categories, setCategories] = useState<Record<number, string>>({});
    const [deletingId, setDeletingId] = useState<number | null>(null);
    const { category, expense } = useApiClients();

    // Load categories once
    const loadCategories = useCallback(async () => {
        try {
            const categoriesResponse = await category.getCategories(true);
            if (categoriesResponse && !('error' in categoriesResponse) && Array.isArray(categoriesResponse)) {
                const categoryMap: Record<number, string> = {};
                categoriesResponse.forEach(cat => {
                    categoryMap[cat.id] = cat.name;
                });
                setCategories(categoryMap);
            }
        } catch (err) {
            console.error('Error loading categories:', err);
        }
    }, [category]);

    // Load categories on mount
    useEffect(() => {
        loadCategories();
    }, [loadCategories]);

    const handleDelete = async (id: number) => {
        setDeletingId(id);
        try {
            const response = await expense.deleteExpense(id);
            if (!response || 'error' in response) {
                console.error('Error deleting expense:', response?.error);
            }
            // The PaginationView will handle refreshing the data
        } catch (err) {
            console.error('Error deleting expense:', err);
        } finally {
            setDeletingId(null);
        }
    };

    const handleEdit = (expense: ExpenseResponse) => {
        if (onEditExpense) {
            onEditExpense(expense);
        }
    };

    // Fetch expenses data for PaginationView
    const fetchExpenses = useCallback(async (page: number, pageSize: number) => {
        const response = await expense.getExpensesPaginated({ page, size: pageSize });
        
        if ('error' in response) {
            throw new Error(response.error);
        }
        
        return {
            items: response.items,
            total: response.total,
            pages: response.pages,
            page: response.page
        };
    }, [expense]);

    const formatDate = (dateString: string | null | undefined) => {
        if (!dateString) return t('expense.list.noDate');
        return new Date(dateString).toLocaleDateString('uk-UA');
    };

    // Render function for expenses
    const renderExpenses = (expenses: ExpenseResponse[], loading: boolean) => {
        if (loading) {
            return (
                <div className="text-center py-8 sm:py-12 lg:py-16">
                    <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 mx-auto mb-4 sm:mb-6 theme-bg-tertiary rounded-xl sm:rounded-2xl flex items-center justify-center">
                        <div className="animate-spin w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 border-2 border-red-500 border-t-transparent rounded-full"></div>
                    </div>
                    <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-2">{t('expense.list.loading')}</h3>
                    <p className="theme-text-secondary text-xs sm:text-sm max-w-md mx-auto px-4">
                        {t('expense.list.loadingSubtitle')}
                    </p>
                </div>
            );
        }

        return (
            <div className="relative w-full">
                {/* Mobile Cards View */}
                <div className="block lg:hidden space-y-3 sm:space-y-4">
                    {expenses.map((expense) => (
                        <div 
                            key={expense.id}
                            className="theme-bg-secondary rounded-lg sm:rounded-xl border theme-border p-3 sm:p-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-200"
                        >
                            <div className="flex items-start justify-between mb-2 sm:mb-3">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm sm:text-base font-semibold theme-error">
                                            {expense.amount.toLocaleString('uk-UA')} ₴
                                        </span>
                                        <span className="text-xs theme-text-secondary">
                                            {formatDate(expense.date)}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium theme-accent-light theme-accent">
                                            {categories[expense.category_id] || t('expense.list.unknownCategory')}
                                        </span>
                                    </div>
                                    <p className="text-xs sm:text-sm theme-text-secondary truncate">
                                        {expense.description || (
                                            <span className="italic">{t('expense.list.noDescription')}</span>
                                        )}
                                    </p>
                                </div>
                                <div 
                                    className="flex items-center gap-1 ml-2 sm:ml-3 flex-shrink-0"
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    <EditButton
                                        onEdit={() => handleEdit(expense)}
                                        variant="icon"
                                        size="sm"
                                    />
                                    <DeleteButton
                                        onDelete={() => handleDelete(expense.id)}
                                        disabled={deletingId === expense.id}
                                        loading={deletingId === expense.id}
                                        variant="icon"
                                        size="sm"
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Desktop Table View */}
                <div className="hidden lg:block relative w-full">
                    <div className="overflow-hidden rounded-xl border theme-border">
                        <table className="w-full">
                            <thead className="theme-bg-secondary">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                        {t('expense.list.date')}
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                        {t('expense.list.amount')}
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                        {t('expense.list.category')}
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                        {t('expense.list.description')}
                                    </th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                        {t('expense.list.actions')}
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="theme-surface divide-y theme-border">
                                {expenses.map((expense) => (
                                    <tr key={expense.id} className="hover:theme-surface-hover transition-colors duration-150 group">
                                        <td className="px-6 py-4">
                                            <div className="text-sm theme-text-secondary">
                                                {formatDate(expense.date)}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-semibold theme-error">
                                                {expense.amount.toLocaleString('uk-UA')} ₴
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium theme-accent-light theme-accent">
                                                {categories[expense.category_id] || t('expense.list.unknownCategory')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm theme-text-secondary max-w-xs truncate">
                                                {expense.description || (
                                                    <span className="theme-text-tertiary italic">{t('expense.list.noDescription')}</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div 
                                                className="flex items-center justify-end gap-2 transition-opacity duration-150"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                <EditButton
                                                    onEdit={() => handleEdit(expense)}
                                                    variant="icon"
                                                    size="sm"
                                                />
                                                <DeleteButton
                                                    onDelete={() => handleDelete(expense.id)}
                                                    disabled={deletingId === expense.id}
                                                    loading={deletingId === expense.id}
                                                    variant="icon"
                                                    size="sm"
                                                />
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        );
    };

    // Render function for empty state
    const renderEmpty = (totalItems: number) => (
        <div className="text-center py-8 sm:py-12 lg:py-16">
            <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 mx-auto mb-4 sm:mb-6 theme-bg-tertiary rounded-xl sm:rounded-2xl flex items-center justify-center">
                <svg className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 theme-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
            </div>
            <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-2">
                {totalItems === 0 ? t('expense.list.noExpensesAtAll') : t('expense.list.noExpensesOnPage')}
            </h3>
            <p className="theme-text-secondary text-xs sm:text-sm max-w-md mx-auto px-4">
                {totalItems === 0 
                    ? t('expense.list.noExpensesSubtitle')
                    : t('expense.list.noExpensesOnPageSubtitle')
                }
            </p>
        </div>
    );

    return (
        <div className="w-full">
            <div className="theme-bg-secondary px-4 sm:px-6 py-3 sm:py-4 lg:px-8 lg:py-6">
                <div className="flex items-center gap-2 sm:gap-3">
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg flex items-center justify-center">
                        <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                    </div>
                    <h2 className="text-lg sm:text-xl lg:text-2xl font-bold theme-text-primary">{t('expense.list.title')}</h2>
                </div>
            </div>
            
            <div className="p-4 sm:p-6 lg:p-8">
                <PaginationView
                    fetchData={fetchExpenses}
                    renderContent={renderExpenses}
                    renderEmpty={renderEmpty}
                    initialPageSize={10}
                    pageSizeOptions={[5, 10, 25, 50]}
                    showPageSizeSelector={true}
                    dependencies={[deletingId]} // Refresh when delete operation completes
                    data-testid="expense-list"
                />
            </div>
        </div>
    );
};