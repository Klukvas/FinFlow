import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApiClients } from '@/hooks/useApiClients';
import { Category, ExpenseResponse } from '@/types';
import { IncomeOut } from '@/types/income';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { FaArrowLeft, FaEdit, FaTrash, FaPlus } from 'react-icons/fa';
import { toast } from 'sonner';

export const CategoryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { category, expense, income } = useApiClients();
  
  const [categoryData, setCategoryData] = useState<Category | null>(null);
  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [incomes, setIncomes] = useState<IncomeOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const fetchCategoryData = useCallback(async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const [categoryResponse, expensesResponse, incomesResponse] = await Promise.all([
        category.getCategory(parseInt(id)),
        expense.getExpenses(),
        income.getIncomes()
      ]);

      if ('error' in categoryResponse) {
        setError(categoryResponse.error);
        return;
      }

      setCategoryData(categoryResponse);

      // Обрабатываем расходы
      if ('error' in expensesResponse) {
        console.error('Error fetching expenses:', expensesResponse.error);
        setExpenses([]);
      } else {
        const categoryExpenses = expensesResponse.filter(exp => exp.category_id === parseInt(id));
        setExpenses(categoryExpenses);
      }

      // Обрабатываем доходы
      if ('error' in incomesResponse) {
        console.error('Error fetching incomes:', incomesResponse.error);
        setIncomes([]);
      } else {
        const categoryIncomes = incomesResponse.filter(inc => inc.category_id === parseInt(id));
        setIncomes(categoryIncomes);
      }
    } catch (err) {
      setError('Ошибка при загрузке данных категории');
      console.error('Error fetching category data:', err);
    } finally {
      setLoading(false);
    }
  }, [id, category, expense, income]);

  useEffect(() => {
    fetchCategoryData();
  }, [fetchCategoryData]);

  const handleDeleteCategory = async () => {
    if (!categoryData) return;

    try {
      const response = await category.deleteCategory(categoryData.id);
      if (response && 'error' in response) {
        toast.error(response.error);
      } else {
        toast.success('Категория успешно удалена');
        navigate('/category');
      }
    } catch (err) {
      toast.error('Ошибка при удалении категории');
      console.error('Error deleting category:', err);
    }
  };

  const handleEditCategory = () => {
    if (categoryData) {
      navigate(`/category/${categoryData.id}/edit`);
    }
  };

  // Получаем данные в зависимости от типа категории
  const isIncomeCategory = categoryData?.type === 'INCOME';
  const items = isIncomeCategory ? incomes : expenses;
  const totalAmount = items.reduce((sum, item) => sum + item.amount, 0);
  const itemsCount = items.length;

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 theme-accent"></div>
      </div>
    );
  }

  if (error || !categoryData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => navigate('/category')}
            className="flex items-center gap-2"
          >
            <FaArrowLeft className="w-4 h-4" />
            Назад к категориям
          </Button>
        </div>
        <div className="theme-error-light theme-error-border theme-border border rounded-lg p-6">
          <p className="theme-error">{error || 'Категория не найдена'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="secondary"
            onClick={() => navigate('/category')}
            className="flex items-center gap-2"
          >
            <FaArrowLeft className="w-4 h-4" />
            Назад
          </Button>
          <div>
            <h1 className="text-2xl font-bold theme-text-primary">{categoryData.name}</h1>
            <p className="theme-text-secondary mt-1">
              Детали категории и связанные расходы
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={handleEditCategory}
            className="flex items-center gap-2"
          >
            <FaEdit className="w-4 h-4" />
            Редактировать
          </Button>
          <Button
            variant="danger"
            onClick={() => setShowDeleteModal(true)}
            className="flex items-center gap-2"
          >
            <FaTrash className="w-4 h-4" />
            Удалить
          </Button>
        </div>
      </div>

      {/* Category Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
          <h3 className="text-lg font-semibold theme-text-primary mb-4">Информация о категории</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="theme-text-secondary">Название:</span>
              <span className="theme-text-primary font-medium">{categoryData.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="theme-text-secondary">Тип:</span>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                categoryData.type === 'INCOME' 
                  ? 'theme-success-light theme-success' 
                  : 'theme-error-light theme-error'
              }`}>
                {categoryData.type === 'INCOME' ? 'Доходы' : 'Расходы'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="theme-text-secondary">ID:</span>
              <span className="theme-text-primary">#{categoryData.id}</span>
            </div>
            {categoryData.parent_id && (
              <div className="flex justify-between">
                <span className="theme-text-secondary">Родительская категория:</span>
                <span className="theme-text-primary">ID: {categoryData.parent_id}</span>
              </div>
            )}
          </div>
        </div>

        <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
          <h3 className="text-lg font-semibold theme-text-primary mb-4">
            {isIncomeCategory ? 'Статистика доходов' : 'Статистика расходов'}
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="theme-text-secondary">
                Всего {isIncomeCategory ? 'доходов' : 'расходов'}:
              </span>
              <span className="theme-text-primary font-medium">{itemsCount}</span>
            </div>
            <div className="flex justify-between">
              <span className="theme-text-secondary">Общая сумма:</span>
              <span className="theme-text-primary font-medium">{totalAmount.toFixed(2)} ₴</span>
            </div>
            <div className="flex justify-between">
              <span className="theme-text-secondary">Средняя сумма:</span>
              <span className="theme-text-primary font-medium">
                {itemsCount > 0 ? (totalAmount / itemsCount).toFixed(2) : '0.00'} ₴
              </span>
            </div>
          </div>
        </div>

        <div className="theme-surface rounded-lg theme-shadow theme-border border p-6">
          <h3 className="text-lg font-semibold theme-text-primary mb-4">Быстрые действия</h3>
          <div className="space-y-3">
            <Button
              variant="primary"
              onClick={() => navigate(isIncomeCategory ? '/income' : '/expense')}
              className="w-full flex items-center justify-center gap-2"
            >
              <FaPlus className="w-4 h-4" />
              {isIncomeCategory ? 'Добавить доход' : 'Добавить расход'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => navigate(`${isIncomeCategory ? '/income' : '/expense'}?category=${categoryData.id}`)}
              className="w-full"
            >
              Просмотреть все {isIncomeCategory ? 'доходы' : 'расходы'}
            </Button>
          </div>
        </div>
      </div>

      {/* Recent Items */}
      {items.length > 0 && (
        <div className="theme-surface rounded-lg theme-shadow theme-border border">
          <div className="theme-accent-bg px-6 py-4">
            <h3 className="text-lg font-semibold theme-text-inverse">
              Последние {isIncomeCategory ? 'доходы' : 'расходы'}
            </h3>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="min-w-full theme-border divide-y">
                <thead className="theme-surface-secondary">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Дата
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Описание
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium theme-text-tertiary uppercase tracking-wider">
                      Сумма
                    </th>
                  </tr>
                </thead>
                <tbody className="theme-surface divide-y theme-border">
                  {items.slice(0, 10).map((item) => (
                    <tr key={item.id} className="hover:theme-surface-hover theme-transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm theme-text-primary">
                          {new Date(item.date).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm theme-text-primary">
                          {item.description || 'Без описания'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-sm font-medium theme-text-primary">
                          {item.amount.toFixed(2)} ₴
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {items.length > 10 && (
              <div className="mt-4 text-center">
                <Button
                  variant="secondary"
                  onClick={() => navigate(`${isIncomeCategory ? '/income' : '/expense'}?category=${categoryData.id}`)}
                >
                  Показать все {isIncomeCategory ? 'доходы' : 'расходы'} ({items.length})
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Подтверждение удаления"
        size="md"
      >
        <div className="space-y-4">
          <p className="theme-text-primary">
            Вы уверены, что хотите удалить категорию <strong>{categoryData.name}</strong>?
          </p>
          <p className="theme-text-secondary text-sm">
            Это действие нельзя отменить. Все связанные расходы будут перемещены в категорию "Без категории".
          </p>
          <div className="flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => setShowDeleteModal(false)}
            >
              Отмена
            </Button>
            <Button
              variant="danger"
              onClick={handleDeleteCategory}
            >
              Удалить
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
