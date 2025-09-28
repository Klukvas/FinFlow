import { Category, CreateExpenseRequest } from '@/types';
import React, { useCallback, useEffect, useState } from 'react';

import { useApiClients } from '@/hooks';

interface CreateExpenseProps {
    onExpenseCreated: () => void;
}

export const CreateExpense: React.FC<CreateExpenseProps> = ({ onExpenseCreated }) => {
    const {category, expense} = useApiClients();
    
    const [formData, setFormData] = useState<CreateExpenseRequest>({
        amount: 0,
        category_id: 0,
        description: '',
        date: new Date().toISOString().split('T')[0] as string,
    });
    const [categories, setCategories] = useState<Category[]>([]);
    
    const [error, setError] = useState<string | null>(null);
    
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingCategories, setIsLoadingCategories] = useState(false);

    const fetchCategories = useCallback(async () => {
        setIsLoadingCategories(true);
        try {
            const response = await category.getCategories(true); // Get flat list
            if ('error' in response) {
                setError(response.error);
            } else {
                // Filter only expense categories
                const expenseCategories = response.filter(cat => cat.type === 'EXPENSE');
                setCategories(expenseCategories);
                // Устанавливаем первую категорию по умолчанию
                if (expenseCategories.length > 0) {
                    setFormData(prev => ({
                        ...prev,
                        category_id: expenseCategories[0]?.id || 0
                    }));
                }
            }
        } catch (err) {
            setError('Ошибка при загрузке категорий');
            console.error('Error fetching categories:', err);
        } finally {
            setIsLoadingCategories(false);
        }
    }, [category]);

    useEffect(() => {
        fetchCategories();
    }, [fetchCategories]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        const parsedValue =
            name === 'amount' ? parseFloat(value) || 0 :
            name === 'category_id' ? parseInt(value, 10) || 0 :
            value;

        setFormData(prev => ({
            ...prev,
            [name]: parsedValue
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!formData.amount || formData.amount <= 0) {
            setError('Сумма должна быть больше 0');
            return;
        }
        
        if (!formData.category_id) {
            setError('Необходимо выбрать категорию');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await expense.createExpense(formData);
            if ('error' in response) {
                setError(response.error);
            } else {
                setFormData({
                    amount: 0,
                    category_id: categories[0]?.id || 0,
                    description: '',
                    date: new Date().toISOString().split('T')[0] as string,
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
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="amount">
                            Сумма
                            <span className="text-red-500 ml-1">*</span>
                        </label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="theme-text-tertiary text-lg">₴</span>
                            </div>
                            <input
                                type="number"
                                id="amount"
                                name="amount"
                                value={formData.amount || ''}
                                onChange={handleChange}
                                step="0.01"
                                min="0"
                                placeholder="0.00"
                                className="w-full pl-8 pr-3 sm:pr-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-red-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
                                required
                            />
                        </div>
                    </div>

                    {/* Категория */}
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold theme-text-primary" htmlFor="category_id">
                            Категория
                            <span className="text-red-500 ml-1">*</span>
                        </label>
                        <select
                            id="category_id"
                            name="category_id"
                            value={formData.category_id}
                            onChange={handleChange}
                            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-red-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px] disabled:opacity-50"
                            disabled={isLoadingCategories}
                            required
                        >
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
                    disabled={isLoading || isLoadingCategories || categories.length === 0}
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