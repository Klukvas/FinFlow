import { useState, useEffect } from 'react';
import { useApiClients } from '@/hooks/useApiClients';
import { Category, IncomeCreate, AccountResponse } from '@/types';
import { Button } from '@/components/ui/Button';
import { FormField } from '@/components/ui/forms/FormField';
import { Input } from '@/components/ui/forms/Input';
import { MoneyInput } from '@/components/ui/MoneyInput';
import { CurrencySelect } from '@/components/ui/forms/CurrencySelect';
import { FaDollarSign, FaCalendarAlt, FaFileAlt, FaFolder } from 'react-icons/fa';
import { config } from '@/config/env';

interface CreateIncomeProps {
  onIncomeCreated: () => void;
}

export const CreateIncome: React.FC<CreateIncomeProps> = ({ onIncomeCreated }) => {
  const { income, category, account } = useApiClients();
  const [formData, setFormData] = useState<IncomeCreate>({
    amount: 0,
    category_id: null,
    description: '',
    date: new Date().toISOString().split('T')[0] as string,
    account_id: null,
    currency: 'USD'
  });
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<AccountResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await category.getCategories();
        if ('error' in response) {
          console.error('Failed to fetch categories:', response.error);
        } else {
          // Filter only income categories
          const incomeCategories = response.filter(cat => cat.type === 'INCOME');
          setCategories(incomeCategories);
        }
      } catch (err) {
        console.error('Error fetching categories:', err);
      }
    };

    const fetchAccounts = async () => {
      try {
        const response = await account.getAccounts();
        if ('error' in response) {
          console.error('Failed to fetch accounts:', response.error);
        } else {
          setAccounts(response);
        }
      } catch (err) {
        console.error('Error fetching accounts:', err);
      }
    };

    fetchCategories();
    fetchAccounts();
  }, [category, account]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name === 'category_id') {
      setFormData(prev => ({ ...prev, [name]: value ? parseInt(value) : null }));
    } else if (name === 'account_id') {
      setFormData(prev => ({ ...prev, [name]: value ? parseInt(value) : null }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleAmountChange = (value: string) => {
    setFormData(prev => ({ ...prev, amount: parseFloat(value) || 0 }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (formData.amount <= 0) {
        setError('Сумма должна быть больше 0');
        return;
      }

      if (config.debug) {
        console.log('Creating income with data:', formData);
      }

      const response = await income.createIncome(formData);

      if ('error' in response) {
        setError(response.error);
        if (config.debug) {
          console.error('Income creation error:', response.error);
        }
      } else {
        if (config.debug) {
          console.log('Income created successfully:', response);
        }
        onIncomeCreated();
        setFormData({
          amount: 0,
          category_id: null,
          description: '',
          date: new Date().toISOString().split('T')[0],
          account_id: null,
          currency: 'USD'
        });
      }
    } catch (err) {
      console.error('Failed to create income:', err);
      setError('Ошибка при создании дохода');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
      <div className="space-y-4 sm:space-y-6">
        {/* Сумма */}
        <MoneyInput
          label="Сумма"
          value={formData.amount || ''}
          onChange={handleAmountChange}
          placeholder="Введите сумму дохода"
          required
          error={formData.amount <= 0 ? 'Сумма должна быть больше 0' : undefined}
          className="w-full"
        />

        {/* Валюта */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold theme-text-primary" htmlFor="currency">
            Валюта
          </label>
          <CurrencySelect
            value={formData.currency || 'USD'}
            onChange={(value) => handleInputChange({ target: { name: 'currency', value } } as any)}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
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
            value={formData.category_id || ''}
            onChange={handleInputChange}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
          >
            <option value="">Выберите категорию (необязательно)</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
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
            onChange={handleInputChange}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
          >
            <option value="">Без аккаунта</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.currency})
              </option>
            ))}
          </select>
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
            value={formData.description || ''}
            onChange={handleInputChange}
            placeholder="Описание дохода (необязательно)"
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg resize-none text-sm sm:text-base min-h-[88px]"
            rows={3}
            maxLength={500}
          />
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
            value={formData.date || ''}
            onChange={handleInputChange}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
            required
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

      <Button
        type="submit"
        disabled={isLoading}
        className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none min-h-[44px] text-sm sm:text-base"
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
            Создать доход
          </>
        )}
      </Button>
    </form>
  );
};
