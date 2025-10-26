import React from 'react';
import { useTranslation } from 'react-i18next';
import { DebtResponse } from '@/types/debt';
import { DebtCard } from './DebtCard';
import { Button } from '@/components/ui/shared/Button';
import { Card, CardContent } from '@/components/ui';
import { Plus, AlertCircle } from 'lucide-react';

interface DebtsListProps {
  debts: DebtResponse[];
  onEdit: (debt: DebtResponse) => void;
  onViewPayments: (debtId: number) => void;
  onMakePayment: (debtId: number) => void;
  onDelete: (debtId: number) => void;
  onCreateClick: () => void;
  actualTheme: 'light' | 'dark';
}

export const DebtsList: React.FC<DebtsListProps> = ({
  debts,
  onEdit,
  onViewPayments,
  onMakePayment,
  onDelete,
  onCreateClick,
  actualTheme
}) => {
  const { t } = useTranslation();

  if (debts.length === 0) {
    return (
      <Card className={`${
        actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
      }`}>
        <CardContent className="p-12 text-center">
          <AlertCircle className={`w-12 h-12 mx-auto mb-4 ${
            actualTheme === 'dark' ? 'text-gray-600' : 'text-gray-400'
          }`} />
          <h3 className={`text-lg font-medium mb-2 ${
            actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'
          }`}>
            {t('debtPage.emptyStates.noDebtsTitle')}
          </h3>
          <p className={`mb-6 ${
            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}>
            {t('debtPage.emptyStates.noDebtsDescription')}
          </p>
          <Button onClick={onCreateClick}>
            <Plus className="w-4 h-4 mr-2" />
            {t('debtPage.emptyStates.addFirstDebt')}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {debts.map((debt) => (
        <DebtCard
          key={debt.id}
          debt={debt}
          onEdit={onEdit}
          onViewPayments={onViewPayments}
          onMakePayment={onMakePayment}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};

