import React from 'react';
import { useTranslation } from 'react-i18next';
import { CreditCard, Users } from 'lucide-react';

interface DebtTabsProps {
  activeTab: 'debts' | 'contacts';
  onTabChange: (tab: 'debts' | 'contacts') => void;
  actualTheme: 'light' | 'dark';
}

export const DebtTabs: React.FC<DebtTabsProps> = ({ activeTab, onTabChange, actualTheme }) => {
  const { t } = useTranslation();

  return (
    <div className="flex space-x-1 mb-8">
      <button
        onClick={() => onTabChange('debts')}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          activeTab === 'debts'
            ? actualTheme === 'dark'
              ? 'bg-blue-600 text-white'
              : 'bg-blue-500 text-white'
            : actualTheme === 'dark'
            ? 'text-gray-400 hover:text-white hover:bg-gray-700'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }`}
      >
        <CreditCard className="w-4 h-4 inline mr-2" />
        {t('debtPage.tabs.debts')}
      </button>
      <button
        onClick={() => onTabChange('contacts')}
        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
          activeTab === 'contacts'
            ? actualTheme === 'dark'
              ? 'bg-blue-600 text-white'
              : 'bg-blue-500 text-white'
            : actualTheme === 'dark'
            ? 'text-gray-400 hover:text-white hover:bg-gray-700'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
        }`}
      >
        <Users className="w-4 h-4 inline mr-2" />
        {t('debtPage.tabs.contacts')}
      </button>
    </div>
  );
};

