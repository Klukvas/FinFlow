import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Goal, CreateGoalRequest, UpdateGoalRequest, GoalType, GoalPriority, GoalFormData } from '@/types';
import { Button } from '../shared/Button';
import { FormattedNumberInput } from '../forms/FormattedNumberInput';
import { CurrencySelect } from '../forms/CurrencySelect';
import { removeSpacesFromNumber } from '@/utils/numberFormat';

const GOAL_TYPES: GoalType[] = ['SAVINGS', 'DEBT_PAYOFF', 'INVESTMENT', 'EXPENSE_REDUCTION', 'INCOME_INCREASE', 'EMERGENCY_FUND'];
const GOAL_PRIORITIES: GoalPriority[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

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
  
  const [targetAmountDisplay, setTargetAmountDisplay] = useState('');
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
      setTargetAmountDisplay(goal.target_amount.toString());
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
          className={`w-full px-3 py-3 sm:py-2 text-base sm:text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-accent theme-transition touch-manipulation theme-bg theme-text-primary ${
            errors.title ? 'theme-error-light theme-border' : 'theme-border'
          }`}
          placeholder={t('goalsPage.form.titlePlaceholder')}
        />
        {errors.title && <p className="mt-1 text-sm theme-error">{errors.title}</p>}
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
          className="w-full px-3 py-3 sm:py-2 text-base sm:text-sm theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-accent theme-transition touch-manipulation theme-bg theme-text-primary"
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
            className="w-full px-3 py-3 sm:py-2 text-base sm:text-sm theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-accent theme-transition touch-manipulation theme-bg theme-text-primary"
          >
            {GOAL_TYPES.map((type) => {
              // Convert DEBT_PAYOFF -> debtPayoff
              const typeKey = type.toLowerCase().split('_').map((word, idx) => 
                idx === 0 ? word : word.charAt(0).toUpperCase() + word.slice(1)
              ).join('');
              return (
                <option key={type} value={type}>{t(`goalsPage.filters.${typeKey}`)}</option>
              );
            })}
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
            className="w-full px-3 py-3 sm:py-2 text-base sm:text-sm theme-border border rounded-md focus:outline-none focus:ring-2 focus:ring-accent theme-transition touch-manipulation theme-bg theme-text-primary"
          >
            {GOAL_PRIORITIES.map((priority) => {
              const priorityKey = priority.toLowerCase();
              return (
                <option key={priority} value={priority}>{t(`goalsPage.filters.${priorityKey}`)}</option>
              );
            })}
          </select>
        </div>
      </div>

      {/* Target Amount and Currency */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <div className="sm:col-span-2">
          <FormattedNumberInput
            label={t('goalsPage.form.targetAmount')}
            value={targetAmountDisplay}
            onChange={(value) => {
              setTargetAmountDisplay(value);
              const cleanedValue = removeSpacesFromNumber(value);
              const numValue = cleanedValue || '0';
              handleInputChange('target_amount', numValue);
            }}
            placeholder="10000"
            required
            error={errors.target_amount || ''}
            className="w-full"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="currency" className="block text-sm font-medium theme-text-primary">
            {t('goalsPage.form.currency')}
          </label>
          <CurrencySelect
            value={formData.currency}
            onChange={(value) => handleInputChange('currency', value)}
            className="w-full"
            placeholder={t('goalsPage.form.currency')}
            showFlags={true}
          />
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
          className={`w-full px-3 py-3 sm:py-2 text-base sm:text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-accent theme-transition touch-manipulation theme-bg theme-text-primary ${
            errors.target_date ? 'theme-error-light theme-border' : 'theme-border'
          }`}
        />
        {errors.target_date && <p className="mt-1 text-sm theme-error">{errors.target_date}</p>}
      </div>

      {/* Milestone Based */}
      <div className="flex items-start sm:items-center gap-3">
        <input
          type="checkbox"
          id="is_milestone_based"
          checked={formData.is_milestone_based}
          onChange={(e) => handleInputChange('is_milestone_based', e.target.checked)}
          className="h-5 w-5 mt-0.5 sm:mt-0 theme-accent focus:ring-accent theme-border border rounded touch-manipulation"
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
