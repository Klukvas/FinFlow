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
 ? 'bg-accent-base text-white'
 : 'text-content-tertiary hover:text-content hover:bg-surface-alt'
 }`}
 >
 <CreditCard className="w-4 h-4 inline mr-2" />
 {t('debtPage.tabs.debts')}
 </button>
 <button
 onClick={() => onTabChange('contacts')}
 className={`px-4 py-2 rounded-lg font-medium transition-colors ${
 activeTab === 'contacts'
 ? 'bg-accent-base text-white'
 : 'text-content-tertiary hover:text-content hover:bg-surface-alt'
 }`}
 >
 <Users className="w-4 h-4 inline mr-2" />
 {t('debtPage.tabs.contacts')}
 </button>
 </div>
 );
};
