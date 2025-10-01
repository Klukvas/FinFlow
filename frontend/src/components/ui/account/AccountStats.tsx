import React from 'react';
import { AccountSummary } from '@/types';
import { Card } from '../Card';
import { FaChartLine, FaDollarSign, FaWallet } from 'react-icons/fa';

interface AccountStatsProps {
  summaries: AccountSummary[];
}

export const AccountStats: React.FC<AccountStatsProps> = ({ summaries }) => {
  const totalBalance = summaries.reduce((sum, account) => sum + account.balance, 0);
  const totalTransactions = summaries.reduce((sum, account) => sum + account.transaction_count, 0);
  const activeAccounts = summaries.filter(account => account.balance > 0).length;

  const formatCurrency = (amount: number, currency: string = 'RUB') => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-6">
        <div className="flex items-center">
          <div className="p-3 bg-blue-100 rounded-lg">
            <FaWallet className="w-6 h-6 text-blue-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">Всего аккаунтов</p>
            <p className="text-2xl font-bold theme-text-primary">{summaries.length}</p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center">
          <div className="p-3 bg-green-100 rounded-lg">
            <FaDollarSign className="w-6 h-6 text-green-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">Общий баланс</p>
            <p className="text-2xl font-bold theme-text-primary">
              {formatCurrency(totalBalance)}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center">
          <div className="p-3 bg-purple-100 rounded-lg">
            <FaChartLine className="w-6 h-6 text-purple-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">Активных</p>
            <p className="text-2xl font-bold theme-text-primary">{activeAccounts}</p>
          </div>
        </div>
      </Card>
    </div>
  );
};
