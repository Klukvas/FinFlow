import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useApiClients } from '@/hooks/useApiClients';
import { Category, IncomeCreate, AccountResponse, CategoryListResponse } from '@/types';
import { Button } from '@/components/ui/shared/Button';
import { MoneyInput } from '@/components/ui/forms/MoneyInput';
import { CurrencySelect } from '@/components/ui/forms/CurrencySelect';
import { FormErrorHandler } from '@/utils/formErrorHandler';
// removed unused icon and config imports

interface CreateIncomeProps {
  onIncomeCreated: () => void;
}

export const CreateIncome: React.FC<CreateIncomeProps> = ({ onIncomeCreated }) => {
  const { t } = useTranslation();
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
  const [_, setFieldErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await category.getCategoriesPaginated({
          flat: true,
          page: 1,
          size: 100 // Максимальный размер страницы
        });
        
        if ('error' in response) {
          console.error('Failed to fetch categories:', response.error);
        } else {
          const paginatedResponse = response as CategoryListResponse;
          const allCategories = paginatedResponse.items || [];
          
          // Filter only income categories
          const incomeCategories = allCategories.filter(cat => cat.type === 'INCOME');
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
    FormErrorHandler.clearFieldErrors(setFieldErrors);
    setIsLoading(true);

    try {
      if (formData.amount <= 0) {
        setError(t('income.form.amountMustBePositive'));
        return;
      }

      const response = await income.createIncome(formData);

      if ('error' in response) {
        throw response;
      } else {
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
      FormErrorHandler.handleFormError(err, t('income.form.createError'), setFieldErrors);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
      <div className="space-y-4 sm:space-y-6">
        {/* Amount */}
        <MoneyInput
          label={t('income.form.amount')}
          value={formData.amount || ''}
          onChange={handleAmountChange}
          placeholder={t('income.form.amountPlaceholder')}
          required
          error={formData.amount <= 0 ? t('income.form.amountMustBePositive') : undefined}
          className="w-full"
        />

        {/* Currency */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold theme-text-primary" htmlFor="currency">
            {t('income.form.currency')}
          </label>
          <CurrencySelect
            value={formData.currency || 'USD'}
            onChange={(value) => handleInputChange({ target: { name: 'currency', value } } as any)}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
            showFlags={true}
          />
        </div>

        {/* Category */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold theme-text-primary" htmlFor="category_id">
            {t('income.form.category')}
            <span className="theme-text-tertiary font-normal ml-1">{t('income.form.optional')}</span>
          </label>
          <select
            id="category_id"
            name="category_id"
            value={formData.category_id || ''}
            onChange={handleInputChange}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
          >
            <option value="">{t('income.form.selectCategoryOptional')}</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        {/* Account */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold theme-text-primary" htmlFor="account_id">
            {t('income.form.account')}
            <span className="theme-text-tertiary font-normal ml-1">{t('income.form.optional')}</span>
          </label>
          <select
            id="account_id"
            name="account_id"
            value={formData.account_id || ''}
            onChange={handleInputChange}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg text-sm sm:text-base min-h-[44px]"
          >
            <option value="">{t('income.form.noAccount')}</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.currency})
              </option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold theme-text-primary" htmlFor="description">
            {t('income.form.description')}
            <span className="theme-text-tertiary font-normal ml-1">{t('income.form.optional')}</span>
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description || ''}
            onChange={handleInputChange}
            placeholder={t('income.form.descriptionPlaceholder')}
            className="w-full px-3 sm:px-4 py-3 theme-surface theme-border border rounded-lg sm:rounded-xl theme-text-primary placeholder-gray-400 focus:ring-2 focus:ring-green-500 focus:border-transparent theme-transition shadow-sm hover:shadow-md focus:shadow-lg resize-none text-sm sm:text-base min-h-[88px]"
            rows={3}
            maxLength={500}
          />
        </div>

        {/* Date */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold theme-text-primary" htmlFor="date">
            {t('income.form.date')}
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
            {t('income.form.creating')}
          </>
        ) : (
          <>
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            {t('income.form.createIncome')}
          </>
        )}
      </Button>
    </form>
  );
};
