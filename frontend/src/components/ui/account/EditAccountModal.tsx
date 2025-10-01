import React, { useState, useEffect } from 'react';
import { AccountResponse } from '@/types';
import { Modal } from '../Modal';
import { Button } from '../Button';
import { Input } from '../forms/Input';
import { CurrencySelect } from '../forms/CurrencySelect';
import { FaWallet } from 'react-icons/fa';

interface EditAccountModalProps {
  account: AccountResponse;
  onClose: () => void;
  onSubmit: (id: number, data: any) => void;
}

export const EditAccountModal: React.FC<EditAccountModalProps> = ({
  account,
  onClose,
  onSubmit
}) => {
  const [formData, setFormData] = useState({
    name: account.name,
    type: account.type,
    currency: account.currency,
    balance: account.balance
  });
  const [loading, setLoading] = useState(false);

  const accountTypes = [
    { value: 'bank', label: 'Банковский счет' },
    { value: 'cash', label: 'Наличные' },
    { value: 'crypto', label: 'Криптовалюта' },
    { value: 'investment', label: 'Инвестиции' },
    { value: 'savings', label: 'Сбережения' },
    { value: 'other', label: 'Другое' }
  ];


  useEffect(() => {
    setFormData({
      name: account.name,
      type: account.type,
      currency: account.currency,
      balance: account.balance
    });
  }, [account]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      return;
    }

    setLoading(true);
    try {
      await onSubmit(account.id, {
        ...formData,
        balance: parseFloat(formData.balance.toString()) || 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Редактировать аккаунт">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Название аккаунта *
          </label>
          <Input
            type="text"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="Например: Основной счет"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Тип аккаунта
          </label>
          <select
            value={formData.type}
            onChange={(e) => handleChange('type', e.target.value)}
            className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition theme-bg theme-text-primary"
          >
            {accountTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Валюта
          </label>
          <CurrencySelect
            value={formData.currency}
            onChange={(value) => handleChange('currency', value)}
            className="w-full px-3 py-2 theme-border border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent theme-transition theme-bg theme-text-primary"
            showFlags={true}
          />
        </div>

        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            Баланс
          </label>
          <Input
            type="number"
            step="0.01"
            value={formData.balance}
            onChange={(e) => handleChange('balance', parseFloat(e.target.value) || 0)}
            placeholder="0.00"
          />
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={loading}
          >
            Отмена
          </Button>
          <Button
            type="submit"
            disabled={loading || !formData.name.trim()}
            className="flex items-center gap-2"
          >
            <FaWallet className="w-4 h-4" />
            {loading ? 'Сохранение...' : 'Сохранить изменения'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
