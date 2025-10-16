import { Category, CreateExpenseRequest, AccountResponse, CategoryListResponse } from '@/types';
import React, { useCallback, useEffect, useState } from 'react';
import { CurrencySelect } from '@/components/ui/forms/CurrencySelect';
import { MoneyInput } from '@/components/ui/forms/MoneyInput';

import { useApiClients } from '@/hooks';

interface CreateExpenseProps {
    onExpenseCreated: () => void;
}

export const CreateExpense: React.FC<CreateExpenseProps> = ({ onExpenseCreated }) => {
    const {category, expense, account, currency} = useApiClients();
    
    const [formData, setFormData] = useState<CreateExpenseRequest>({
        amount: 0,
        category_id: 0,
        description: '',
        date: new Date().toISOString().split('T')[0] as string,
        account_id: undefined,
        currency: 'USD',
    });
    const [categories, setCategories] = useState<Category[]>([]);
    const [accounts, setAccounts] = useState<AccountResponse[]>([]);
    
    const [error, setError] = useState<string | null>(null);
    
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingCategories, setIsLoadingCategories] = useState(false);
    const [isLoadingAccounts, setIsLoadingAccounts] = useState(false);

    const fetchCategories = useCallback(async () => {
        setIsLoadingCategories(true);
        try {
            // Используем новый пагинированный API для получения категорий расходов
            const response = await category.getCategoriesPaginated({
                flat: true,
                page: 1,
                size: 100 // Максимальный размер страницы
            });
            
            if ('error' in response) {
                setError(response.error);
            } else {
                const paginatedResponse = response as CategoryListResponse;
                const allCategories = paginatedResponse.items || [];
                
                // Filter only expense categories
                const expenseCategories = allCategories.filter(cat => cat.type === 'EXPENSE');
                setCategories(expenseCategories);
                // Категория остается пустой по умолчанию (необязательная)
            }
        } catch (err) {
            setError('Ошибка при загрузке категорий');
            console.error('Error fetching categories:', err);
        } finally {
            setIsLoadingCategories(false);
        }
    }, [category]);

    const fetchAccounts = useCallback(async () => {
        setIsLoadingAccounts(true);
        try {
            const response = await account.getAccounts();
            if ('error' in response) {
                setError(response.error);
            } else {
                setAccounts(response);
            }
        } catch (err) {
            setError('Ошибка при загрузке аккаунтов');
            console.error('Error fetching accounts:', err);
        } finally {
            setIsLoadingAccounts(false);
        }
    }, [account]);

    useEffect(() => {
        fetchCategories();
        fetchAccounts();
    }, [fetchCategories, fetchAccounts]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        const parsedValue =
            name === 'category_id' ? (value === '' ? 0 : parseInt(value, 10)) :
            name === 'account_id' ? (value === '' ? undefined : parseInt(value, 10)) :
            value;

        setFormData(prev => ({
            ...prev,
            [name]: parsedValue
        }));
    };

    const handleAmountChange = (value: string) => {
        setFormData(prev => ({
            ...prev,
            amount: parseFloat(value) || 0
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!formData.amount || formData.amount <= 0) {
            setError('Сумма должна быть больше 0');
            return;
        }
        

        setIsLoading(true);
        setError(null);

        try {
            // Подготавливаем данные для отправки
            const expenseData = { ...formData };
            
            // Убираем category_id если категория не выбрана (значение 0 или пустая строка)
            if (!expenseData.category_id || expenseData.category_id === 0) {
                expenseData.category_id = undefined;
            }
            
            const response = await expense.createExpense(expenseData);
            if ('error' in response) {
                setError(response.error);
            } else {
                setFormData({
                    amount: 0,
                    category_id: 0,
                    description: '',
                    date: new Date().toISOString().split('T')[0] as string,
                    account_id: undefined,
                    currency: 'USD',
                });
                onExpenseCreated();
            }
        } catch (err) {
            setError('Ошибка при создании расхода');
            console.error('Error creating expense:', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full">
            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
                <div className="space-y-4 sm:space-y-6">
                    {/* Сумма */}
                    <MoneyInput
                        label="Сумма"
                        value={formData.amount || ''}
                        onChange={handleAmountChange}
                        placeholder="0.00"
                        required
                        error={!formData.amount || formData.amount <= 0 ? 'Сумма должна быть больше 0' : undefined}
                        className="w-full"
                    />

                    {/* Валюта */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="currency">
                            Валюта
                        </label>
                        <CurrencySelect
                            value={formData.currency || 'USD'}
                            onChange={(value) => handleChange({ target: { name: 'currency', value } } as any)}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-red-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
                            showFlags={true}
                        />
                    </div>

                    {/* Категория */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="category_id">
                            Категория
                            <span className="theme-text-tertiary font-normal ml-1">(необязательно)</span>
                        </label>
                        <select
                            id="category_id"
                            name="category_id"
                            value={formData.category_id}
                            onChange={handleChange}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-red-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] disabled:opacity-50"
                            disabled={isLoadingCategories}
                        >
                            <option value="">Без категории</option>
                            {isLoadingCategories ? (
                                <option>Загрузка категорий...</option>
                            ) : categories.length === 0 ? (
                                <option value="">Нет доступных категорий</option>
                            ) : (
                                categories.map(cat => (
                                    <option key={cat.id} value={cat.id}>
                                        {cat.name}
                                    </option>
                                ))
                            )}
                        </select>
                    </div>

                    {/* Аккаунт */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="account_id">
                            Аккаунт
                            <span className="theme-text-tertiary font-normal ml-1">(необязательно)</span>
                        </label>
                        <select
                            id="account_id"
                            name="account_id"
                            value={formData.account_id || ''}
                            onChange={handleChange}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-red-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] disabled:opacity-50"
                            disabled={isLoadingAccounts}
                        >
                            <option value="">Без аккаунта</option>
                            {isLoadingAccounts ? (
                                <option>Загрузка аккаунтов...</option>
                            ) : accounts.length === 0 ? (
                                <option value="">Нет доступных аккаунтов</option>
                            ) : (
                                accounts.map(account => (
                                    <option key={account.id} value={account.id}>
                                        {account.name} ({account.currency})
                                    </option>
                                ))
                            )}
                        </select>
                    </div>

                    {/* Дата */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="date">
                            Дата
                            <span className="text-red-500 ml-1">*</span>
                        </label>
                        <input
                            type="date"
                            id="date"
                            name="date"
                            value={formData.date}
                            onChange={handleChange}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-red-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
                            required
                        />
                    </div>

                    {/* Описание */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="description">
                            Описание
                            <span className="theme-text-tertiary font-normal ml-1">(необязательно)</span>
                        </label>
                        <textarea
                            id="description"
                            name="description"
                            value={formData.description}
                            onChange={handleChange}
                            placeholder="Добавьте описание расхода..."
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-red-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg resize-none text-sm sm:text-base min-h-[88px]"
                            rows={3}
                        />
                    </div>

                    {error && (
                        <div className="theme-error-light theme-border border rounded-lg sm:rounded-xl p-3 sm:p-4">
                            <div className="flex items-center gap-2 sm:gap-3">
                                <div className="w-4 h-4 sm:w-5 sm:h-5 theme-error flex-shrink-0">
                                    <svg fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                </div>
                                <p className="theme-error text-xs sm:text-sm font-medium">{error}</p>
                            </div>
                        </div>
                    )}
                </div>

                <button
                    type="submit"
                    disabled={isLoading || isLoadingCategories}
                    className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-semibold py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none min-h-[44px] text-sm sm:text-base"
                >
                    {isLoading ? (
                        <>
                            <div className="relative">
                                <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white/30"></div>
                                <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white border-t-transparent absolute top-0 left-0"></div>
                            </div>
                            Создание...
                        </>
                    ) : (
                        <>
                            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                            Добавить расход
                        </>
                    )}
                </button>
            </form>
        </div>
    );
};