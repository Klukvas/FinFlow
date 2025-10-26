import React from 'react';
import { useTranslation } from 'react-i18next';
import { DebtSummary } from '@/types/debt';
import { Card, CardContent } from '@/components/ui';
import { DollarSign, TrendingDown, CreditCard, CheckCircle } from 'lucide-react';

interface DebtStatsProps {
  summary: DebtSummary;
  actualTheme: 'light' | 'dark';
}

export const DebtStats: React.FC<DebtStatsProps> = ({ summary, actualTheme }) => {
  const { t } = useTranslation();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <Card className={`${
        actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {t('debtPage.stats.totalDebt')}
              </p>
              <p className={`text-2xl font-bold ${
                actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>
                {formatCurrency(summary.total_debt)}
              </p>
            </div>
            <div className={`p-3 rounded-full ${
              actualTheme === 'dark' ? 'bg-red-900/50' : 'bg-red-100'
            }`}>
              <TrendingDown className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className={`${
        actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {t('debtPage.stats.totalPaid')}
              </p>
              <p className={`text-2xl font-bold ${
                actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>
                {formatCurrency(summary.total_payments)}
              </p>
            </div>
            <div className={`p-3 rounded-full ${
              actualTheme === 'dark' ? 'bg-green-900/50' : 'bg-green-100'
            }`}>
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className={`${
        actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {t('debtPage.stats.activeDebts')}
              </p>
              <p className={`text-2xl font-bold ${
                actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>
                {summary.active_debts}
              </p>
            </div>
            <div className={`p-3 rounded-full ${
              actualTheme === 'dark' ? 'bg-blue-900/50' : 'bg-blue-100'
            }`}>
              <CreditCard className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className={`${
        actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${
                actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {t('debtPage.stats.paidOff')}
              </p>
              <p className={`text-2xl font-bold ${
                actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>
                {summary.paid_off_debts}
              </p>
            </div>
            <div className={`p-3 rounded-full ${
              actualTheme === 'dark' ? 'bg-green-900/50' : 'bg-green-100'
            }`}>
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

