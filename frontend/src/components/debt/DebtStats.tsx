import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { DebtResponse } from '@/types/debt';
import { Card, CardContent } from '@/components/ui';
import { DollarSign, TrendingDown, CreditCard, CheckCircle } from 'lucide-react';
import { useCurrencyConversion } from '@/hooks/useCurrencyConversion';

interface DebtStatsProps {
  debts: DebtResponse[];
  actualTheme: 'light' | 'dark';
}

export const DebtStats: React.FC<DebtStatsProps> = ({ debts, actualTheme }) => {
  const { t } = useTranslation();
  const { formatCurrency, convertToUserCurrency, userCurrency, isLoadingRates } = useCurrencyConversion();

  // Calculate summary with currency conversion
  const summary = useMemo(() => {
    let totalDebt = 0;
    let totalPayments = 0;
    let activeDebts = 0;
    let paidOffDebts = 0;

    debts.forEach((debt) => {
      // Convert current balance to user's currency
      const convertedBalance = convertToUserCurrency(Math.abs(debt.current_balance), debt.currency);
      
      if (convertedBalance !== null) {
        totalDebt += convertedBalance;
      }

      // Calculate amount paid (difference between initial and current balance)
      // Use absolute value to handle both positive (they owe me) and negative (I owe them) debts
      const amountPaid = Math.abs(debt.initial_amount - debt.current_balance);
      
      // Convert the amount paid to user's currency
      if (amountPaid > 0) {
        const convertedPaid = convertToUserCurrency(amountPaid, debt.currency);
        if (convertedPaid !== null) {
          totalPayments += convertedPaid;
        }
      }

      if (debt.is_active) {
        activeDebts++;
      }
      if (debt.is_paid_off) {
        paidOffDebts++;
      }
    });

    return {
      total_debt: totalDebt,
      total_payments: totalPayments,
      active_debts: activeDebts,
      paid_off_debts: paidOffDebts
    };
  }, [debts, convertToUserCurrency]);

  const formatAmount = (amount: number) => {
    return formatCurrency(amount, userCurrency);
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
                {formatAmount(summary.total_debt)} {isLoadingRates && '(loading...)'}
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
                {formatAmount(summary.total_payments)} {isLoadingRates && '(loading...)'}
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

