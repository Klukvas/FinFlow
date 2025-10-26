import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Goal, CreateGoalRequest, UpdateGoalRequest, GOAL_TYPE_LABELS, GOAL_PRIORITY_LABELS, GoalFormData } from '@/types';
import { Button } from '../shared/Button';
import { MoneyInput } from '../forms/MoneyInput';

interface GoalFormProps {
  goal?: Goal;
  onSubmit: (data: CreateGoalRequest | UpdateGoalRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const GoalForm: React.FC<GoalFormProps> = ({
  goal,
  onSubmit,
  onCancel,
  isLoading = false
}) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState<GoalFormData>({
    title: '',
    description: '',
    goal_type: 'SAVINGS',
    priority: 'MEDIUM',
    target_amount: '',
    currency: 'USD',
    target_date: undefined,
    is_milestone_based: false
  });

  const [errors, setErrors] = useState<Partial<GoalFormData>>({});

  useEffect(() => {
    if (goal) {
      setFormData({
        title: goal.title,
        description: goal.description || '',
        goal_type: goal.goal_type,
        priority: goal.priority,
        target_amount: goal.target_amount.toString(),
        currency: goal.currency || 'USD',
        target_date: goal.target_date ? new Date(goal.target_date).toISOString().split('T')[0] : undefined,
        is_milestone_based: goal.is_milestone_based
      });
    }
  }, [goal]);

  const validateForm = (): boolean => {
    const newErrors: Partial<GoalFormData> = {};

    if (!formData.title.trim()) {
      newErrors.title = t('goalsPage.form.titleRequired');
    }

    if (!formData.target_amount || parseFloat(formData.target_amount) <= 0) {
      newErrors.target_amount = t('goalsPage.form.targetAmountRequired');
    }

    if (formData.target_date) {
      const targetDate = new Date(formData.target_date);
      const today = new Date();
      if (targetDate <= today) {
        newErrors.target_date = t('goalsPage.form.targetDateMustBeFuture');
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const submitData = {
      title: formData.title.trim(),
      ...(formData.description.trim() && { description: formData.description.trim() }),
      goal_type: formData.goal_type,
      priority: formData.priority,
      target_amount: parseFloat(formData.target_amount),
      currency: formData.currency,
      ...(formData.target_date && { target_date: formData.target_date }),
      is_milestone_based: formData.is_milestone_based
    };

    onSubmit(submitData);
  };

  const handleInputChange = (field: keyof GoalFormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
      {/* Title */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium theme-text-primary mb-1 sm:mb-2">
          {t('goalsPage.form.title')} *
        </label>
        <input
          type="text"
          id="title"
          value={formData.title}
          onChange={(e) => handleInputChange('title', e.target.value)}
          className={`w-full px-3 py-3 sm:py-2 text-base sm:text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-transition touch-manipulation ${
            errors.title ? 'border-red-500' : 'theme-border'
          }`}
          placeholder={t('goalsPage.form.titlePlaceholder')}
        />
        {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title}</p>}
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium theme-text-primary mb-1 sm:mb-2">
          {t('goalsPage.form.description')}
        </label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          rows={3}
          className="w-full px-3 py-3 sm:py-2 text-base sm:text-sm theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-transition touch-manipulation"
          placeholder={t('goalsPage.form.descriptionPlaceholder')}
        />
      </div>

      {/* Goal Type and Priority */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <label htmlFor="goal_type" className="block text-sm font-medium theme-text-primary mb-1 sm:mb-2">
            {t('goalsPage.form.goalType')}
          </label>
          <select
            id="goal_type"
            value={formData.goal_type}
            onChange={(e) => handleInputChange('goal_type', e.target.value)}
            className="w-full px-3 py-3 sm:py-2 text-base sm:text-sm theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-transition touch-manipulation"
          >
            {Object.entries(GOAL_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="priority" className="block text-sm font-medium theme-text-primary mb-1 sm:mb-2">
            {t('goalsPage.form.priority')}
          </label>
          <select
            id="priority"
            value={formData.priority}
            onChange={(e) => handleInputChange('priority', e.target.value)}
            className="w-full px-3 py-3 sm:py-2 text-base sm:text-sm theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-transition touch-manipulation"
          >
            {Object.entries(GOAL_PRIORITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Target Amount and Currency */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <div className="sm:col-span-2">
          <MoneyInput
            label={t('goalsPage.form.targetAmount')}
            value={formData.target_amount}
            onChange={(value) => handleInputChange('target_amount', value)}
            placeholder="10000"
            required
            error={errors.target_amount}
            className="w-full"
          />
        </div>

        <div>
          <label htmlFor="currency" className="block text-sm font-medium theme-text-primary mb-1 sm:mb-2">
            {t('goalsPage.form.currency')}
          </label>
          <select
            id="currency"
            value={formData.currency}
            onChange={(e) => handleInputChange('currency', e.target.value)}
            className="w-full px-3 py-3 sm:py-2 text-base sm:text-sm theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-transition touch-manipulation"
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="RUB">RUB</option>
            <option value="UAH">UAH</option>
          </select>
        </div>
      </div>

      {/* Target Date */}
      <div>
        <label htmlFor="target_date" className="block text-sm font-medium theme-text-primary mb-1 sm:mb-2">
          {t('goalsPage.form.targetDate')}
        </label>
        <input
          type="date"
          id="target_date"
          value={formData.target_date}
          onChange={(e) => handleInputChange('target_date', e.target.value)}
          className={`w-full px-3 py-3 sm:py-2 text-base sm:text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 theme-transition touch-manipulation ${
            errors.target_date ? 'border-red-500' : 'theme-border'
          }`}
        />
        {errors.target_date && <p className="mt-1 text-sm text-red-600">{errors.target_date}</p>}
      </div>

      {/* Milestone Based */}
      <div className="flex items-start sm:items-center gap-3">
        <input
          type="checkbox"
          id="is_milestone_based"
          checked={formData.is_milestone_based}
          onChange={(e) => handleInputChange('is_milestone_based', e.target.checked)}
          className="h-5 w-5 mt-0.5 sm:mt-0 text-blue-600 focus:ring-blue-500 theme-border border rounded touch-manipulation"
        />
        <label htmlFor="is_milestone_based" className="block text-sm theme-text-primary leading-relaxed">
          {t('goalsPage.form.useMilestones')}
        </label>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row justify-end gap-3 pt-2">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isLoading}
          className="w-full sm:w-auto min-h-[44px] touch-manipulation"
        >
          {t('common.cancel')}
        </Button>
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full sm:w-auto min-h-[44px] touch-manipulation"
        >
          {isLoading ? t('goalsPage.form.saving') : (goal ? t('goalsPage.form.update') : t('goalsPage.form.create'))}
        </Button>
      </div>
    </form>
  );
};
