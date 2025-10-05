import React from 'react';
import { AccountResponse, AccountSummary } from '@/types';
import { Card } from '../Card';
import { EditButton } from '../EditButton';
import { DeleteButton } from '../DeleteButton';
import { FaWallet, FaDollarSign, FaChartLine } from 'react-icons/fa';

interface AccountCardProps {
  account: AccountResponse;
  summary?: AccountSummary | undefined;
  onEdit: (account: AccountResponse) => void;
  onArchive: (id: number) => void;
}

export const AccountCard: React.FC<AccountCardProps> = ({
  account,
  summary,
  onEdit,
  onArchive
}) => {
  const getAccountTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'bank':
        return <FaWallet className="w-5 h-5" />;
      case 'cash':
        return <FaDollarSign className="w-5 h-5" />;
      case 'crypto':
        return <FaChartLine className="w-5 h-5" />;
      default:
        return <FaWallet className="w-5 h-5" />;
    }
  };

  const getAccountTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'bank':
        return 'text-blue-600 bg-blue-100';
      case 'cash':
        return 'text-green-600 bg-green-100';
      case 'crypto':
        return 'text-purple-600 bg-purple-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatBalance = (balance: number, currency: string) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency || 'RUB'
    }).format(balance);
  };

  return (
    <Card className="p-6 hover:theme-surface-hover theme-transition">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <div className={`p-2 rounded-lg ${getAccountTypeColor(account.type)}`}>
            {getAccountTypeIcon(account.type)}
          </div>
          <div className="ml-3">
            <h3 className="font-semibold theme-text-primary">{account.name}</h3>
            <p className="text-sm theme-text-secondary capitalize">{account.type}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <EditButton onEdit={() => {
            onEdit(account);
          }} />
          <DeleteButton 
            onDelete={() => onArchive(account.id)}
          />
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm theme-text-secondary">Баланс:</span>
          <span className="font-semibold theme-text-primary">
            {formatBalance(account.balance, account.currency)}
          </span>
        </div>

        {summary && (
          <>
            <div className="flex justify-between items-center">
              <span className="text-sm theme-text-secondary">Транзакций:</span>
              <span className="text-sm theme-text-primary">{summary.transaction_count}</span>
            </div>

            {summary.last_transaction_date && (
              <div className="flex justify-between items-center">
                <span className="text-sm theme-text-secondary">Последняя операция:</span>
                <span className="text-sm theme-text-primary">
                  {new Date(summary.last_transaction_date).toLocaleDateString('ru-RU')}
                </span>
              </div>
            )}
          </>
        )}

        <div className="pt-3 border-t theme-border">
          <div className="flex justify-between items-center">
            <span className="text-xs theme-text-tertiary">Создан:</span>
            <span className="text-xs theme-text-tertiary">
              {new Date(account.created_at).toLocaleDateString('ru-RU')}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};
