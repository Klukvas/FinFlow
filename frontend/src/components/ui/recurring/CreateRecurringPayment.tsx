import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { recurringApiService, CreateRecurringPaymentRequest } from '@/services/api/recurringApi';
import { useApiClients } from '@/hooks/useApiClients';
import { Category } from '@/types/category';
import { MoneyInput } from '../forms/MoneyInput';
import { toast } from 'sonner';

interface CreateRecurringPaymentProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export const CreateRecurringPayment: React.FC<CreateRecurringPaymentProps> = ({
  onSuccess,
  onCancel,
}) => {
  const { user } = useAuth();
  const { category } = useApiClients();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState<CreateRecurringPaymentRequest>({
    name: '',
    description: '',
    amount: 0,
    currency: 'RUB',
    category_id: 0,
    payment_type: 'EXPENSE',
    schedule_type: 'monthly',
    schedule_config: { day_of_month: 1 },
    start_date: new Date().toISOString().split('T')[0] as string,
  } as CreateRecurringPaymentRequest);

  React.useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await category.getCategories();
        if (Array.isArray(response)) {
          setCategories(response);
        }
      } catch (error) {
        console.error('Failed to fetch categories:', error);
      }
    };

    if (user?.id) {
      fetchCategories();
    }
  }, [user?.id, category]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.id) return;

    setLoading(true);
    try {
      await recurringApiService.createRecurringPayment(user.id, formData);
      toast.success('Повторяющийся платеж успешно создан');
      onSuccess();
    } catch (error) {
      console.error('Failed to create recurring payment:', error);
      toast.error('Ошибка при создании повторяющегося платежа');
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleConfigChange = (key: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      schedule_config: {
        ...prev.schedule_config,
        [key]: value,
      },
    }));
  };

  const renderScheduleConfig = () => {
    switch (formData.schedule_type) {
      case 'weekly':
        return (
          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              День недели
            </label>
            <select
              value={formData.schedule_config.day_of_week || 0}
              onChange={(e) => handleScheduleConfigChange('day_of_week', parseInt(e.target.value))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
            >
              <option value={0}>Воскресенье</option>
              <option value={1}>Понедельник</option>
              <option value={2}>Вторник</option>
              <option value={3}>Среда</option>
              <option value={4}>Четверг</option>
              <option value={5}>Пятница</option>
              <option value={6}>Суббота</option>
            </select>
          </div>
        );
      case 'monthly':
        return (
          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              День месяца
            </label>
            <input
              type="number"
              min="1"
              max="31"
              value={formData.schedule_config.day_of_month || 1}
              onChange={(e) => handleScheduleConfigChange('day_of_month', parseInt(e.target.value))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
            />
          </div>
        );
      case 'yearly':
        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium theme-text-primary mb-2">
                Месяц
              </label>
              <select
                value={formData.schedule_config.month || 1}
                onChange={(e) => handleScheduleConfigChange('month', parseInt(e.target.value))}
                className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              >
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {new Date(0, i).toLocaleString('ru', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium theme-text-primary mb-2">
                День
              </label>
              <input
                type="number"
                min="1"
                max="31"
                value={formData.schedule_config.day || 1}
                onChange={(e) => handleScheduleConfigChange('day', parseInt(e.target.value))}
                className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onCancel();
        }
      }}
    >
      <div className="theme-surface rounded-lg p-4 sm:p-6 w-full max-w-md max-h-[90vh] overflow-y-auto theme-border border">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg sm:text-xl font-bold theme-text-primary">Создать повторяющийся платеж</h2>
          <button
            type="button"
            onClick={onCancel}
            className="theme-text-tertiary hover:theme-text-primary theme-transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              Название *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              Описание
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <MoneyInput
                label="Сумма"
                value={formData.amount}
                onChange={(value) => setFormData(prev => ({ ...prev, amount: parseFloat(value) || 0 }))}
                placeholder="0.00"
                required
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium theme-text-primary mb-2">
                Валюта
              </label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData(prev => ({ ...prev, currency: e.target.value }))}
                className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              >
                <option value="RUB">RUB</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              Категория *
            </label>
            <select
              value={formData.category_id}
              onChange={(e) => setFormData(prev => ({ ...prev, category_id: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              required
            >
              <option value="">Выберите категорию</option>
              {categories.map(category => (
                <option key={category.id} value={category.id.toString()}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              Тип платежа *
            </label>
            <select
              value={formData.payment_type}
              onChange={(e) => setFormData(prev => ({ ...prev, payment_type: e.target.value as 'EXPENSE' | 'INCOME' }))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
            >
              <option value="EXPENSE">Расход</option>
              <option value="INCOME">Доход</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              Тип расписания *
            </label>
            <select
              value={formData.schedule_type}
              onChange={(e) => {
                const newScheduleType = e.target.value as any;
                let defaultConfig = {};
                
                // Set default config based on schedule type
                if (newScheduleType === 'weekly') {
                  defaultConfig = { day_of_week: 0 };
                } else if (newScheduleType === 'monthly') {
                  defaultConfig = { day_of_month: 1 };
                } else if (newScheduleType === 'yearly') {
                  defaultConfig = { month: 1, day: 1 };
                }
                
                setFormData(prev => ({ 
                  ...prev, 
                  schedule_type: newScheduleType, 
                  schedule_config: defaultConfig 
                }));
              }}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
            >
              <option value="daily">Ежедневно</option>
              <option value="weekly">Еженедельно</option>
              <option value="monthly">Ежемесячно</option>
              <option value="yearly">Ежегодно</option>
            </select>
          </div>

          {renderScheduleConfig()}

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              Дата начала *
            </label>
            <input
              type="date"
              value={formData.start_date}
              onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              Дата окончания (опционально)
            </label>
            <input
              type="date"
              value={formData.end_date || ''}
              onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value || undefined } as CreateRecurringPaymentRequest))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
            />
          </div>

          <div className="flex flex-col sm:flex-row justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="w-full sm:w-auto px-4 py-2 theme-text-secondary theme-bg-tertiary rounded-md hover:theme-surface-hover theme-transition"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Создание...' : 'Создать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
