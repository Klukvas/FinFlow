import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal } from '../shared/Modal';
import { Button } from '../shared/Button';
import { Input } from '../forms/Input';
import { CurrencySelect } from '../forms/CurrencySelect';
import { FaWallet } from 'react-icons/fa';

interface CreateAccountModalProps {
  onClose: () => void;
  onSubmit: (data: any) => void;
}

export const CreateAccountModal: React.FC<CreateAccountModalProps> = ({
  onClose,
  onSubmit
}) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    type: 'bank',
    currency: 'USD',
    balance: 0
  });
  const [loading, setLoading] = useState(false);

  const accountTypes = [
    { value: 'bank', label: t('accountPage.form.types.bank') },
    { value: 'cash', label: t('accountPage.form.types.cash') },
    { value: 'crypto', label: t('accountPage.form.types.crypto') },
    { value: 'investment', label: t('accountPage.form.types.investment') },
    { value: 'savings', label: t('accountPage.form.types.savings') },
    { value: 'other', label: t('accountPage.form.types.other') }
  ];


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      return;
    }

    setLoading(true);
    try {
      await onSubmit({
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
    <Modal isOpen={true} onClose={onClose} title={t('accountPage.createModalTitle')}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            {t('accountPage.form.name')} {t('accountPage.form.required')}
          </label>
          <Input
            type="text"
            value={formData.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder={t('accountPage.form.namePlaceholder')}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium theme-text-primary mb-2">
            {t('accountPage.form.type')}
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
            {t('accountPage.form.currency')}
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
            {t('accountPage.form.initialBalance')}
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
            {t('accountPage.form.cancel')}
          </Button>
          <Button
            type="submit"
            disabled={loading || !formData.name.trim()}
            className="flex items-center gap-2"
          >
            <FaWallet className="w-4 h-4" />
            {loading ? t('accountPage.form.creating') : t('accountPage.form.createAccount')}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
