import React from 'react';
import { AccountSummary } from '@/types';
import { Card } from '../shared/Card';
import { FaChartLine, FaDollarSign, FaWallet } from 'react-icons/fa';
import { useCurrencyConversion } from '@/hooks/useCurrencyConversion';

interface AccountStatsProps {
  summaries: AccountSummary[];
}

export const AccountStats: React.FC<AccountStatsProps> = ({ summaries }) => {
  const { 
    userCurrency, 
    isLoadingRates, 
    convertToUserCurrency, 
    formatCurrency 
  } = useCurrencyConversion();
  
  const activeAccounts = summaries.filter(account => account.balance > 0).length;

  // Calculate total balance in user's currency
  const { totalBalance, unconvertibleAccounts } = summaries.reduce((acc, account) => {
    const convertedAmount = convertToUserCurrency(account.balance, account.currency);
    
    if (convertedAmount === null) {
      // Track accounts that couldn't be converted
      acc.unconvertibleAccounts.push(account);
    } else {
      acc.totalBalance += convertedAmount;
    }
    
    return acc;
  }, { totalBalance: 0, unconvertibleAccounts: [] as AccountSummary[] });

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
            <p className="text-sm font-medium theme-text-secondary">
              Общий баланс {isLoadingRates && '(загрузка...)'}
            </p>
            <p className="text-2xl font-bold theme-text-primary">
              {formatCurrency(totalBalance, userCurrency)}
            </p>
            {unconvertibleAccounts.length > 0 && (
              <p className="text-xs text-orange-600 mt-1">
                ⚠️ {unconvertibleAccounts.length} {unconvertibleAccounts.length === 1 ? 'счет' : 'счетов'} не учтен
              </p>
            )}
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
