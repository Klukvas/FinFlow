import React, { useState, useEffect } from 'react';
import { AccountResponse, AccountSummary } from '@/types';
import { useApiClients } from '@/hooks/useApiClients';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { CreateAccountModal } from '@/components/ui/account/CreateAccountModal';
import { EditAccountModal } from '@/components/ui/account/EditAccountModal';
import { AccountCard } from '@/components/ui/account/AccountCard';
import { AccountStats } from '@/components/ui/account/AccountStats';
import { FaPlus, FaWallet, FaDollarSign, FaChartLine } from 'react-icons/fa';

export const Account: React.FC = () => {
  const { account: accountApiClient } = useApiClients();
  const [accounts, setAccounts] = useState<AccountResponse[]>([]);
  const [summaries, setSummaries] = useState<AccountSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState<AccountResponse | null>(null);

  // Debug: Log when editingAccount changes
  React.useEffect(() => {
    console.log('editingAccount changed:', editingAccount);
  }, [editingAccount]);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [accountsResult, summariesResult] = await Promise.all([
        accountApiClient.getAccounts(),
        accountApiClient.getAccountSummaries()
      ]);

      if ('error' in accountsResult) {
        const errorMessage = typeof accountsResult.error === 'string' 
          ? accountsResult.error 
          : 'Ошибка при загрузке аккаунтов';
        setError(errorMessage);
        return;
      }

      if ('error' in summariesResult) {
        const errorMessage = typeof summariesResult.error === 'string' 
          ? summariesResult.error 
          : 'Ошибка при загрузке сводок аккаунтов';
        setError(errorMessage);
        return;
      }

      setAccounts(accountsResult);
      setSummaries(summariesResult);
    } catch (err) {
      setError('Ошибка при загрузке аккаунтов');
      console.error('Error loading accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

  const handleCreateAccount = async (accountData: any) => {
    try {
      const result = await accountApiClient.createAccount(accountData);
      
      if ('error' in result) {
        const errorMessage = typeof result.error === 'string' 
          ? result.error 
          : 'Ошибка при операции с аккаунтом';
        setError(errorMessage);
        return;
      }

      setShowCreateModal(false);
      await loadAccounts();
    } catch (err) {
      setError('Ошибка при создании аккаунта');
      console.error('Error creating account:', err);
    }
  };

  const handleUpdateAccount = async (id: number, accountData: any) => {
    try {
      const result = await accountApiClient.updateAccount(id, accountData);
      
      if ('error' in result) {
        const errorMessage = typeof result.error === 'string' 
          ? result.error 
          : 'Ошибка при операции с аккаунтом';
        setError(errorMessage);
        return;
      }

      setEditingAccount(null);
      await loadAccounts();
    } catch (err) {
      setError('Ошибка при обновлении аккаунта');
      console.error('Error updating account:', err);
    }
  };

  const handleArchiveAccount = async (id: number) => {
    try {
      const result = await accountApiClient.archiveAccount(id);
      
      if ('error' in result) {
        const errorMessage = typeof result.error === 'string' 
          ? result.error 
          : 'Ошибка при операции с аккаунтом';
        setError(errorMessage);
        return;
      }

      await loadAccounts();
    } catch (err) {
      setError('Ошибка при архивировании аккаунта');
      console.error('Error archiving account:', err);
    }
  };

  const totalBalance = summaries.reduce((sum, account) => sum + account.balance, 0);
  const activeAccounts = accounts.filter(account => !account.is_archived);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold theme-text-primary">Аккаунты</h1>
          <p className="text-sm theme-text-secondary mt-1">
            Управляйте своими финансовыми аккаунтами
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2"
        >
          <FaPlus className="w-4 h-4" />
          Создать аккаунт
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FaWallet className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium theme-text-secondary">Всего аккаунтов</p>
              <p className="text-2xl font-bold theme-text-primary">{activeAccounts.length}</p>
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
                {totalBalance.toLocaleString('ru-RU', {
                  style: 'currency',
                  currency: 'RUB'
                })}
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
              <p className="text-2xl font-bold theme-text-primary">
                {summaries.filter(s => s.balance > 0).length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Accounts List */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold theme-text-primary">Мои аккаунты</h2>
        
        {activeAccounts.length === 0 ? (
          <Card className="p-8 text-center">
            <FaWallet className="w-12 h-12 theme-text-tertiary mx-auto mb-4" />
            <h3 className="text-lg font-medium theme-text-primary mb-2">
              У вас пока нет аккаунтов
            </h3>
            <p className="text-sm theme-text-secondary mb-4">
              Создайте свой первый аккаунт для отслеживания финансов
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              Создать аккаунт
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeAccounts.map((account) => (
              <AccountCard
                key={account.id}
                account={account}
                summary={summaries.find(s => s.id === account.id)}
                onEdit={setEditingAccount}
                onArchive={handleArchiveAccount}
              />
            ))}
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreateAccountModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateAccount}
        />
      )}

      {editingAccount && (
        <EditAccountModal
          account={editingAccount}
          onClose={() => {
            console.log('Closing edit modal');
            setEditingAccount(null);
          }}
          onSubmit={handleUpdateAccount}
        />
      )}
    </div>
  );
};
