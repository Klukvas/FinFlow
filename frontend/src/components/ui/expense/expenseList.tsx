import { useCallback, useEffect, useState } from 'react';

import { ExpenseResponse } from '@/types';
import { useApiClients } from '@/hooks';
import { DeleteButton } from '@/components/ui';

export const ExpenseList = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
    const [categories, setCategories] = useState<Record<number, string>>({});
    const { category, expense } = useApiClients();
    const [error, setError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    const handleDelete = async (id: number) => {
        setDeletingId(id);
        try {
            const response = await expense.deleteExpense(id);
            if (!response || 'error' in response) {
                setError(response?.error || 'Ошибка при удалении расхода');
            } else {
                setExpenses(prev => prev.filter(exp => exp.id !== id));
            }
        } catch (err) {
            setError('Ошибка при удалении расхода');
            console.error('Error deleting expense:', err);
        } finally {
            setDeletingId(null);
        }
    };

    const fetchAllData = useCallback(async () => {
        setIsLoading(true);
        try {
            const [categoriesResponse, expensesResponse] = await Promise.all([
                category.getCategories(true), // Get flat list
                expense.getExpenses()
            ]);

            if (categoriesResponse && !('error' in categoriesResponse)) {
                const categoryMap: Record<number, string> = {};
                categoriesResponse.forEach(cat => {
                    categoryMap[cat.id] = cat.name;
                });
                setCategories(categoryMap);
            } else {
                setError('Ошибка при загрузке категорий');
            }

            if (expensesResponse && !('error' in expensesResponse)) {
                setExpenses(expensesResponse);
            } else {
                setError('Ошибка при загрузке расходов');
            }
        } catch (err) {
            setError('Ошибка при загрузке данных');
            console.error('Error fetching data:', err);
        } finally {
            setIsLoading(false);
        }
    }, [category, expense]);

    useEffect(() => {
        fetchAllData();
    }, [fetchAllData]);

    const formatDate = (dateString: string | null | undefined) => {
        if (!dateString) return 'Не указана';
        return new Date(dateString).toLocaleDateString('uk-UA');
    };

    if (isLoading) {
        return (
            <div className="w-full">
                <div className="theme-bg-secondary px-4 sm:px-6 py-3 sm:py-4 lg:px-8 lg:py-6">
                    <div className="flex items-center gap-2 sm:gap-3">
                        <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg flex items-center justify-center">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                        </div>
                        <h2 className="text-lg sm:text-xl lg:text-2xl font-bold theme-text-primary">Список расходов</h2>
                    </div>
                </div>
                <div className="p-4 sm:p-6 lg:p-8">
                    <div className="flex items-center justify-center py-6 sm:py-8">
                        <div className="relative">
                            <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 theme-border"></div>
                            <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 theme-error border-t-transparent absolute top-0 left-0"></div>
                        </div>
                        <span className="ml-3 theme-text-secondary text-sm sm:text-base">Загрузка данных...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="w-full">
                <div className="theme-bg-secondary px-4 sm:px-6 py-3 sm:py-4 lg:px-8 lg:py-6">
                    <div className="flex items-center gap-2 sm:gap-3">
                        <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg flex items-center justify-center">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                        </div>
                        <h2 className="text-lg sm:text-xl lg:text-2xl font-bold theme-text-primary">Список расходов</h2>
                    </div>
                </div>
                <div className="p-4 sm:p-6 lg:p-8">
                    <div className="theme-error-light border theme-border rounded-lg sm:rounded-xl p-3 sm:p-4">
                        <div className="flex items-center gap-2 sm:gap-3">
                            <div className="w-4 h-4 sm:w-5 sm:h-5 theme-error flex-shrink-0">
                                <svg fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <p className="theme-error text-xs sm:text-sm font-medium">{error}</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Calculate total expenses
    const totalExpenses = expenses.reduce((sum, expense) => sum + expense.amount, 0);

    return (
        <div className="w-full">
            <div className="theme-bg-secondary px-4 sm:px-6 py-3 sm:py-4 lg:px-8 lg:py-6">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 sm:gap-4">
                    <div className="flex items-center gap-2 sm:gap-3">
                        <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg flex items-center justify-center">
                            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                        </div>
                        <h2 className="text-lg sm:text-xl lg:text-2xl font-bold theme-text-primary">Список расходов</h2>
                    </div>
                    <div className="theme-surface theme-text-secondary text-xs sm:text-sm px-2 sm:px-3 py-1 rounded-full">
                        Всего: <span className="font-bold text-sm sm:text-base theme-error">{totalExpenses.toLocaleString('uk-UA')} ₴</span>
                    </div>
                </div>
            </div>
            
            <div className="p-4 sm:p-6 lg:p-8">
                {expenses.length === 0 ? (
                    <div className="text-center py-8 sm:py-12 lg:py-16">
                        <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 mx-auto mb-4 sm:mb-6 theme-bg-tertiary rounded-xl sm:rounded-2xl flex items-center justify-center">
                            <svg className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 theme-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                        </div>
                        <h3 className="text-base sm:text-lg font-semibold theme-text-primary mb-2">Расходы пока не добавлены</h3>
                        <p className="theme-text-secondary text-xs sm:text-sm max-w-md mx-auto px-4">
                            Добавьте первый расход для начала отслеживания ваших трат
                        </p>
                    </div>
                ) : (
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
                                                    {categories[expense.category_id] || 'Неизвестно'}
                                                </span>
                                            </div>
                                            <p className="text-xs sm:text-sm theme-text-secondary truncate">
                                                {expense.description || (
                                                    <span className="italic">Без описания</span>
                                                )}
                                            </p>
                                        </div>
                                        <div className="flex-shrink-0 ml-2 sm:ml-3">
                                            <DeleteButton
                                                onDelete={() => handleDelete(expense.id)}
                                                disabled={deletingId === expense.id}
                                                loading={deletingId === expense.id}
                                                variant="filled"
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
                                                Дата
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                                Сумма
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                                Категория
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                                Описание
                                            </th>
                                            <th className="px-6 py-4 text-right text-xs font-semibold theme-text-secondary uppercase tracking-wider">
                                                Действия
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
                                                        {categories[expense.category_id] || 'Неизвестно'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="text-sm theme-text-secondary max-w-xs truncate">
                                                        {expense.description || (
                                                            <span className="theme-text-tertiary italic">Без описания</span>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                                                        <DeleteButton
                                                            onDelete={() => handleDelete(expense.id)}
                                                            disabled={deletingId === expense.id}
                                                            loading={deletingId === expense.id}
                                                            variant="filled"
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
                )}
            </div>
        </div>
    );
};