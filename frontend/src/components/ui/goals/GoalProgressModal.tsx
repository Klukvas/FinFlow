import React, { useState } from 'react';
import { Goal, GoalProgressUpdate } from '@/types';
import { Modal } from '../shared/Modal';
import { Button } from '../shared/Button';
import { FaDollarSign } from 'react-icons/fa';

interface GoalProgressModalProps {
  goal: Goal;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (goalId: number, progress: GoalProgressUpdate) => void;
  isLoading?: boolean;
}

export const GoalProgressModal: React.FC<GoalProgressModalProps> = ({
  goal,
  isOpen,
  onClose,
  onUpdate,
  isLoading = false
}) => {
  const [currentAmount, setCurrentAmount] = useState(goal.current_amount.toString());
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const amount = parseFloat(currentAmount);
    
    if (isNaN(amount) || amount < 0) {
      setError('Введите корректную сумму');
      return;
    }

    if (amount > goal.target_amount) {
      setError('Текущая сумма не может превышать целевую');
      return;
    }

    onUpdate(goal.id, { current_amount: amount });
  };

  const handleClose = () => {
    setCurrentAmount(goal.current_amount.toString());
    setError('');
    onClose();
  };

  const getProgressPercentage = () => {
    const amount = parseFloat(currentAmount);
    if (isNaN(amount) || goal.target_amount === 0) return 0;
    return Math.min((amount / goal.target_amount) * 100, 100);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Обновить прогресс цели"
      size="md"
    >
      <div className="space-y-6">
        {/* Goal Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">{goal.title}</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Текущая сумма:</span>
              <p className="font-medium">{goal.current_amount.toLocaleString()} {goal.currency}</p>
            </div>
            <div>
              <span className="text-gray-500">Целевая сумма:</span>
              <p className="font-medium">{goal.target_amount.toLocaleString()} {goal.currency}</p>
            </div>
          </div>
        </div>

        {/* Progress Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="current_amount" className="block text-sm font-medium text-gray-700 mb-2">
              Новая текущая сумма
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FaDollarSign className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="number"
                id="current_amount"
                value={currentAmount}
                onChange={(e) => {
                  setCurrentAmount(e.target.value);
                  setError('');
                }}
                step="0.01"
                min="0"
                max={goal.target_amount}
                className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  error ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="0.00"
              />
            </div>
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
          </div>

          {/* Progress Preview */}
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Новый прогресс</span>
              <span className="text-sm font-bold text-blue-600">
                {getProgressPercentage().toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Осталось: {(goal.target_amount - parseFloat(currentAmount || '0')).toLocaleString()} {goal.currency}
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={isLoading}
            >
              Отмена
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !!error}
            >
              {isLoading ? 'Обновление...' : 'Обновить прогресс'}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
