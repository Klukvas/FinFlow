import React from 'react';
import { useTranslation } from 'react-i18next';
import { Card } from '../shared/Card';
import { FaChartLine, FaDollarSign, FaWallet } from 'react-icons/fa';
import { useCurrencyConversion } from '@/hooks/useCurrencyConversion';

interface AccountStatistics {
  total_accounts: number;
  active_accounts: number;
  total_balance: number;
  currency: string;
  unconvertible_accounts_count: number;
}

interface AccountStatsProps {
  statistics: AccountStatistics;
  isLoading?: boolean;
}

export const AccountStats: React.FC<AccountStatsProps> = ({ statistics, isLoading = false }) => {
  const { t } = useTranslation();
  const { formatCurrency } = useCurrencyConversion();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-24"></div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <Card className="p-6">
        <div className="flex items-center">
          <div className="p-3 bg-blue-100 rounded-lg">
            <FaWallet className="w-6 h-6 text-blue-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium theme-text-secondary">{t('accountPage.stats.totalAccounts')}</p>
            <p className="text-2xl font-bold theme-text-primary">{statistics.total_accounts}</p>
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
              {t('accountPage.stats.totalBalance')}
            </p>
            <p className="text-2xl font-bold theme-text-primary">
              {formatCurrency(statistics.total_balance, statistics.currency)}
            </p>
            {statistics.unconvertible_accounts_count > 0 && (
              <p className="text-xs text-orange-600 mt-1">
                ⚠️ {statistics.unconvertible_accounts_count} {statistics.unconvertible_accounts_count === 1 ? t('accountPage.stats.notIncludedSingle') : t('accountPage.stats.notIncludedPlural')}
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
            <p className="text-sm font-medium theme-text-secondary">{t('accountPage.stats.active')}</p>
            <p className="text-2xl font-bold theme-text-primary">{statistics.active_accounts}</p>
          </div>
        </div>
      </Card>
    </div>
  );
};
