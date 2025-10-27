import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useApiClients } from '@/hooks/useApiClients';
import { IncomeOut, Category, CategoryListResponse } from '@/types';
import { DeleteButton } from '@/components/ui';

export const IncomeList: React.FC = () => {
  const { t } = useTranslation();
  const { income, category } = useApiClients();
  const [incomes, setIncomes] = useState<IncomeOut[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [incomesResponse, categoriesResponse] = await Promise.all([
          income.getIncomes(),
          category.getCategoriesPaginated({
            flat: true,
            page: 1,
            size: 100 // Максимальный размер страницы
          })
        ]);

        if ('error' in incomesResponse) {
          setError(incomesResponse.error);
        } else {
          setIncomes(incomesResponse);
        }

        if ('error' in categoriesResponse) {
          console.error('Failed to fetch categories:', categoriesResponse.error);
        } else {
          const paginatedResponse = categoriesResponse as CategoryListResponse;
          setCategories(paginatedResponse.items || []);
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Ошибка при загрузке данных');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [income, category]);

  const getCategoryName = (categoryId: number | null | undefined) => {
    if (!categoryId) return 'Без категории';
    const cat = categories.find(c => c.id === categoryId);
    return cat ? cat.name : 'Неизвестная категория';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('uk-UA');
  };

  const totalIncomes = incomes.reduce((sum, income) => sum + income.amount, 0);

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    try {
      const response = await income.deleteIncome(id);
      if (!response || 'error' in response) {
        setError(response?.error || 'Ошибка при удалении дохода');
      } else {
        setIncomes(prev => prev.filter(inc => inc.id !== id));
      }
    } catch (err) {
      setError('Ошибка при удалении дохода');
      console.error('Error deleting income:', err);
    } finally {
      setDeletingId(null);
    }
  };


  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8 sm:py-12">
        <div className="relative">
          <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 theme-border"></div>
          <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 theme-success border-t-transparent absolute top-0 left-0"></div>
        </div>
        <span className="ml-3 theme-text-secondary text-sm sm:text-base">Загрузка доходов...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="theme-error-light theme-border border rounded-lg sm:rounded-xl p-4 sm:p-6 mx-4 sm:mx-6 my-4 sm:my-6">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 theme-error flex-shrink-0">
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="theme-error text-sm font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-4 sm:px-6 py-4 sm:py-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 sm:gap-4">
          <h2 className="text-lg sm:text-xl font-bold text-white">Список доходов</h2>
          <div className="text-white text-sm sm:text-base">
            Всего: <span className="font-bold text-lg sm:text-xl">{totalIncomes.toLocaleString('uk-UA')}</span>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="p-4 sm:p-6">
        {incomes.length === 0 ? (
          <div className="text-center py-8 sm:py-12">
            <div className="text-6xl sm:text-7xl mb-4 sm:mb-6">💰</div>
            <p className="theme-text-primary text-base sm:text-lg font-medium mb-2">Доходы пока не добавлены</p>
            <p className="theme-text-secondary text-sm sm:text-base">Добавьте первый доход, используя кнопку выше</p>
          </div>
        ) : (
          <>
            {/* Desktop Table View */}
            <div className="hidden lg:block overflow-x-auto">
              <table className="min-w-full divide-y theme-border">
                <thead className="theme-bg-secondary">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Дата
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Сумма
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      {t('income.list.currency')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Категория
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Описание
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="theme-surface divide-y theme-border">
                  {incomes.map((income) => (
                    <tr key={income.id} className="hover:theme-surface-hover theme-transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm theme-text-primary">
                          {formatDate(income.date)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold theme-success">
                          +{income.amount.toLocaleString('uk-UA')}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm theme-text-secondary">
                          {income.currency}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium theme-success-light theme-success">
                          {getCategoryName(income.category_id)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm theme-text-secondary max-w-xs truncate">
                          {income.description || (
                            <span className="theme-text-tertiary italic">Без описания</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <DeleteButton
                          onDelete={() => handleDelete(income.id)}
                          disabled={deletingId === income.id}
                          loading={deletingId === income.id}
                          variant="filled"
                          size="sm"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="block lg:hidden space-y-3 sm:space-y-4">
              {incomes.map((income) => (
                <div key={income.id} className="theme-surface theme-border border rounded-lg sm:rounded-xl p-4 sm:p-5 theme-shadow hover:theme-shadow-hover theme-transition">
                  <div className="flex items-start justify-between gap-3 sm:gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
                        <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg sm:rounded-xl flex items-center justify-center shadow-sm">
                          <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <div className="text-base sm:text-lg font-bold theme-success truncate">
                              +{income.amount.toLocaleString('uk-UA')}
                            </div>
                            <div className="text-xs theme-text-secondary px-2 py-1 rounded theme-bg-secondary">
                              {income.currency}
                            </div>
                          </div>
                          <div className="text-xs sm:text-sm theme-text-tertiary mt-1">
                            {formatDate(income.date)}
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-2 sm:space-y-3">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center px-2 sm:px-3 py-1 sm:py-1.5 rounded-full text-xs sm:text-sm font-medium theme-success-light theme-success">
                            {getCategoryName(income.category_id)}
                          </span>
                        </div>
                        
                        {income.description && (
                          <div className="text-sm sm:text-base theme-text-secondary line-clamp-2">
                            {income.description}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex-shrink-0">
                      <DeleteButton
                        onDelete={() => handleDelete(income.id)}
                        disabled={deletingId === income.id}
                        loading={deletingId === income.id}
                        variant="filled"
                        size="sm"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
