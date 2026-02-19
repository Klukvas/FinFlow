import { CreateExpenseRequest } from '@/types';
import React, { useCallback, useState } from 'react';
import { CurrencySelect, CategorySelect } from '@/components/ui/forms';
import { FormattedNumberInput } from '@/components/ui/forms/FormattedNumberInput';
import { removeSpacesFromNumber } from '@/utils/numberFormat';
import { Button } from '@/components/ui/shared/Button';
import { useTranslation } from 'react-i18next';

import { useApiClients } from '@/hooks';
import { useAccounts } from '@/contexts/AccountsContext';
import { useErrorHandler } from '@/hooks/useErrorHandler';

interface CreateExpenseProps {
    onExpenseCreated: () => void;
}

export const CreateExpense: React.FC<CreateExpenseProps> = ({ onExpenseCreated }) => {
    const { t } = useTranslation();
    const { expense } = useApiClients();
    const { activeAccounts: accounts, isLoading: isLoadingAccounts } = useAccounts();
    const { handleExpenseError } = useErrorHandler();
    
    const [formData, setFormData] = useState<CreateExpenseRequest>({
        amount: 0,
        category_id: undefined,
        description: '',
        date: new Date().toISOString().split('T')[0] as string,
        account_id: undefined,
        currency: 'USD',
    });
    const [amountDisplay, setAmountDisplay] = useState('');
    
    const [error, setError] = useState<string | null>(null);
    const [amountTouched, setAmountTouched] = useState(false);
    
    const [isLoading, setIsLoading] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        const parsedValue =
            name === 'account_id' ? (value === '' ? undefined : parseInt(value, 10)) :
            value;

        setFormData(prev => ({
            ...prev,
            [name]: parsedValue
        }));
    };

    const handleCategoryChange = (categoryId: number | null) => {
        setFormData(prev => ({
            ...prev,
            category_id: categoryId || undefined
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
            // Подготавливаем данные для отправки
            const expenseData = { ...formData };
            
            // Убираем category_id если категория не выбрана (значение 0 или пустая строка)
            if (!expenseData.category_id || expenseData.category_id === 0) {
                expenseData.category_id = undefined;
            }
            
            const response = await expense.createExpense(expenseData);
            if ('error' in response && 'errorCode' in response) {
                // Handle API error with errorCode
                handleExpenseError(response as any);
                return;
            } else {
                setFormData({
                    amount: 0,
                    category_id: undefined,
                    description: '',
                    date: new Date().toISOString().split('T')[0] as string,
                    account_id: undefined,
                    currency: 'USD',
                });
                setAmountDisplay('');
                setAmountTouched(false);
                onExpenseCreated();
            }
        } catch (err) {
            // Handle network or other errors
            handleExpenseError(err as Error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full">
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
                            value={formData.account_id || ''}
                            onChange={handleChange}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] disabled:opacity-50"
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
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
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
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg resize-none text-sm sm:text-base min-h-[88px]"
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

                <Button type="submit" variant="primary" size="lg" fullWidth loading={isLoading}>
                    {t('expense.form.createButton')}
                </Button>
            </form>
        </div>
    );
};