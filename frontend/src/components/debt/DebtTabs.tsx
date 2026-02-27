import React from 'react';
import { useTranslation } from 'react-i18next';
import { CreditCard, Users } from 'lucide-react';

interface DebtTabsProps {
  activeTab: 'debts' | 'contacts';
  onTabChange: (tab: 'debts' | 'contacts') => void;
}

export const DebtTabs: React.FC<DebtTabsProps> = ({ activeTab, onTabChange }) => {
  const { t } = useTranslation();

  return (
    <div className="flex space-x-1 mb-8">
      <button
        onClick={() => onTabChange('debts')}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          activeTab === 'debts'
            ? 'bg-blue-600 text-white'
            : 'theme-text-tertiary hover:theme-text-primary hover:theme-surface-hover'
        }`}
      >
        <CreditCard className="w-4 h-4 inline mr-2" />
        {t('debtPage.tabs.debts')}
      </button>
      <button
        onClick={() => onTabChange('contacts')}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          activeTab === 'contacts'
            ? 'bg-blue-600 text-white'
            : 'theme-text-tertiary hover:theme-text-primary hover:theme-surface-hover'
        }`}
      >
        <Users className="w-4 h-4 inline mr-2" />
        {t('debtPage.tabs.contacts')}
      </button>
    </div>
  );
};
