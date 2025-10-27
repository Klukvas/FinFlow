import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { recurringApiService, CreateRecurringPaymentRequest } from '@/services/api/recurringApi';
import { useApiClients } from '@/hooks/useApiClients';
import { Category } from '@/types/category';
import { FormattedNumberInput } from '../forms/FormattedNumberInput';
import { CurrencySelect } from '../forms/CurrencySelect';
import { toast } from 'sonner';
import { removeSpacesFromNumber } from '@/utils/numberFormat';

interface CreateRecurringPaymentProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export const CreateRecurringPayment: React.FC<CreateRecurringPaymentProps> = ({
  onSuccess,
  onCancel,
}) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { category } = useApiClients();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [amountDisplay, setAmountDisplay] = useState('');
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

  // Filter categories based on payment type
  const filteredCategories = React.useMemo(() => {
    return categories.filter(cat => cat.type === formData.payment_type);
  }, [categories, formData.payment_type]);

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
      toast.success(t('recurringPage.createModal.success'));
      onSuccess();
    } catch (error) {
      console.error('Failed to create recurring payment:', error);
      toast.error(t('recurringPage.createModal.error'));
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
              {t('recurringPage.createModal.dayOfWeek')}
            </label>
            <select
              value={formData.schedule_config.day_of_week || 0}
              onChange={(e) => handleScheduleConfigChange('day_of_week', parseInt(e.target.value))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
            >
              <option value={0}>{t('common.weekDays.sunday')}</option>
              <option value={1}>{t('common.weekDays.monday')}</option>
              <option value={2}>{t('common.weekDays.tuesday')}</option>
              <option value={3}>{t('common.weekDays.wednesday')}</option>
              <option value={4}>{t('common.weekDays.thursday')}</option>
              <option value={5}>{t('common.weekDays.friday')}</option>
              <option value={6}>{t('common.weekDays.saturday')}</option>
            </select>
          </div>
        );
      case 'monthly':
        return (
          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              {t('recurringPage.createModal.dayOfMonth')}
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
                {t('recurringPage.createModal.month')}
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
                {t('recurringPage.createModal.day')}
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
          <h2 className="text-lg sm:text-xl font-bold theme-text-primary">{t('recurringPage.createModal.title')}</h2>
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
              {t('recurringPage.createModal.name')} *
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
              {t('recurringPage.createModal.description')}
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
              <FormattedNumberInput
                label={t('recurringPage.createModal.amount')}
                value={amountDisplay}
                onChange={(value) => {
                  setAmountDisplay(value);
                  const cleanedValue = removeSpacesFromNumber(value);
                  const numValue = cleanedValue ? Math.round(parseFloat(cleanedValue) * 100) / 100 : 0;
                  setFormData(prev => ({ ...prev, amount: numValue }));
                }}
                placeholder="0.00"
                required
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium leading-none theme-text-primary">
                {t('recurringPage.createModal.currency')}
              </label>
              <CurrencySelect
                value={formData.currency}
                onChange={(value) => setFormData(prev => ({ ...prev, currency: value }))}
                className="w-full"
                placeholder={t('recurringPage.createModal.currency')}
                showFlags={true}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              {t('recurringPage.createModal.category')} *
            </label>
            <select
              value={formData.category_id}
              onChange={(e) => setFormData(prev => ({ ...prev, category_id: parseInt(e.target.value) }))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
              required
            >
              <option value="">{t('recurringPage.createModal.selectCategory')}</option>
              {filteredCategories.map(category => (
                <option key={category.id} value={category.id.toString()}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              {t('recurringPage.createModal.paymentType')} *
            </label>
            <select
              value={formData.payment_type}
              onChange={(e) => setFormData(prev => ({ ...prev, payment_type: e.target.value as 'EXPENSE' | 'INCOME' }))}
              className="w-full px-3 py-2 theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-bg theme-text-primary"
            >
              <option value="EXPENSE">{t('recurringPage.createModal.expense')}</option>
              <option value="INCOME">{t('recurringPage.createModal.income')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              {t('recurringPage.createModal.scheduleType')} *
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
              <option value="daily">{t('recurringPage.createModal.daily')}</option>
              <option value="weekly">{t('recurringPage.createModal.weekly')}</option>
              <option value="monthly">{t('recurringPage.createModal.monthly')}</option>
              <option value="yearly">{t('recurringPage.createModal.yearly')}</option>
            </select>
          </div>

          {renderScheduleConfig()}

          <div>
            <label className="block text-sm font-medium theme-text-primary mb-2">
              {t('recurringPage.createModal.startDate')} *
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
              {t('recurringPage.createModal.endDate')}
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
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? t('recurringPage.createModal.creating') : t('recurringPage.createModal.create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
