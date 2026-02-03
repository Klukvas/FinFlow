import { ExpenseResponse, ExpenseUpdate } from '@/types';
import React, { useEffect, useState } from 'react';
import { CurrencySelect, CategorySelect } from '@/components/ui/forms';
import { FormattedNumberInput } from '@/components/ui/forms/FormattedNumberInput';
import { removeSpacesFromNumber } from '@/utils/numberFormat';

import { useApiClients } from '@/hooks';
import { useAccounts } from '@/contexts/AccountsContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';

interface EditExpenseProps {
    expense: ExpenseResponse;
    onExpenseUpdated: () => void;
}

export const EditExpense: React.FC<EditExpenseProps> = ({ expense, onExpenseUpdated }) => {
    const { expense: expenseApi } = useApiClients();
    const { activeAccounts: accounts, isLoading: isLoadingAccounts } = useAccounts();
    const { handleExpenseError } = useErrorHandler();
    
    const getDateValue = (dateStr: string | undefined): string => {
        if (dateStr) {
            const datePart = dateStr.split('T')[0];
            if (datePart) return datePart;
        }
        const todayDate = new Date().toISOString().split('T')[0];
        return todayDate || new Date().toISOString().substring(0, 10);
    };

    const [formData, setFormData] = useState<ExpenseUpdate>({
        amount: expense.amount,
        category_id: expense.category_id,
        description: expense.description || null,
        date: getDateValue(expense.date),
        account_id: expense.account_id ?? null,
        currency: expense.currency || 'USD',
    });
    
    // Format amount for display (without spaces for initial load)
    const [amountDisplay, setAmountDisplay] = useState(expense.amount.toString());
    
    const [error, setError] = useState<string | null>(null);
    const [amountTouched, setAmountTouched] = useState(false);
    
    const [isLoading, setIsLoading] = useState(false);

    // Reset form when expense prop changes
    useEffect(() => {
        setFormData({
            amount: expense.amount,
            category_id: expense.category_id,
            description: expense.description || null,
            date: getDateValue(expense.date),
            account_id: expense.account_id ?? null,
            currency: expense.currency || 'USD',
        });
        setAmountDisplay(expense.amount.toString());
        setAmountTouched(false);
        setError(null);
    }, [expense]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        const parsedValue =
            name === 'account_id' ? (value === '' ? null : parseInt(value, 10)) :
            name === 'description' ? (value || null) :
            name === 'date' ? (value || null) :
            value;

        setFormData(prev => ({
            ...prev,
            [name]: parsedValue
        }));
    };

    const handleCategoryChange = (categoryId: number | null) => {
        setFormData(prev => ({
            ...prev,
            category_id: categoryId || null
        }));
    };

    const handleAmountChange = (value: string) => {
        setAmountTouched(true);
        setAmountDisplay(value);
        const cleanedValue = removeSpacesFromNumber(value);
        setFormData(prev => ({
            ...prev,
            amount: parseFloat(cleanedValue) || 0
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
            // Prepare update data
            const updateData: ExpenseUpdate = {
                amount: formData.amount,
                category_id: formData.category_id || null,
                description: formData.description || null,
                date: formData.date || null,
                account_id: formData.account_id || null,
                currency: formData.currency || null,
            };
            
            const response = await expenseApi.updateExpense(expense.id, updateData);
            if ('error' in response && 'errorCode' in response) {
                // Handle API error with errorCode
                handleExpenseError(response as any);
                return;
            } else {
                onExpenseUpdated();
            }
        } catch (err) {
            // Handle network or other errors
            handleExpenseError(err as Error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full" data-testid="edit-expense-modal">
            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
                <div className="space-y-4 sm:space-y-6">
                    {/* Сумма */}
                    <FormattedNumberInput
                        label="Сумма"
                        value={amountDisplay}
                        onChange={handleAmountChange}
                        placeholder="0"
                        required
                        error={amountTouched && (!formData.amount || formData.amount <= 0) ? 'Сумма должна быть больше 0' : ''}
                        className="w-full"
                        data-testid="expense-amount-input"
                    />

                    {/* Валюта */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="currency">
                            Валюта
                        </label>
                        <CurrencySelect
                            value={formData.currency || 'USD'}
                            onChange={(value) => handleChange({ target: { name: 'currency', value } } as any)}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
                            showFlags={true}
                        />
                    </div>

                    {/* Категория */}
                    <CategorySelect
                        value={formData.category_id || null}
                        onChange={handleCategoryChange}
                        categoryType="EXPENSE"
                        optional={true}
                        showEmptyOption={true}
                    />

                    {/* Аккаунт */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="account_id">
                            Аккаунт
                            <span className="theme-text-tertiary font-normal ml-1">(необязательно)</span>
                        </label>
                        <select
                            id="account_id"
                            name="account_id"
                            value={formData.account_id ?? ''}
                            onChange={handleChange}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] disabled:opacity-50"
                            disabled={isLoadingAccounts}
                            data-testid="expense-account-select"
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
                            value={formData.date ?? ''}
                            onChange={handleChange}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
                            required
                            data-testid="expense-date-input"
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
                            value={formData.description ?? ''}
                            onChange={handleChange}
                            placeholder="Добавьте описание расхода..."
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg resize-none text-sm sm:text-base min-h-[88px]"
                            rows={3}
                            data-testid="expense-description-input"
                        />
                    </div>

                    {error && (
                        <div className="theme-error-light theme-border border rounded-lg sm:rounded-xl p-3 sm:p-4" data-testid="edit-expense-error">
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
                    disabled={isLoading}
                    className="w-full bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-semibold py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none min-h-[44px] text-sm sm:text-base"
                    data-testid="save-expense-button"
                >
                    {isLoading ? (
                        <>
                            <div className="relative">
                                <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white/30"></div>
                                <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-white border-t-transparent absolute top-0 left-0"></div>
                            </div>
                            Сохранение...
                        </>
                    ) : (
                        <>
                            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Сохранить изменения
                        </>
                    )}
                </button>
            </form>
        </div>
    );
};

