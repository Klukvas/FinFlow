import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { AccountResponse, AccountSummary } from '@/types';
import { useApiClients } from '@/hooks/useApiClients';
import { Card } from '@/components/ui/shared/Card';
import { Button } from '@/components/ui/shared/Button';
import { LoadingSpinner } from '@/components/ui/shared/LoadingSpinner';
import { CreateAccountModal } from '@/components/ui/account/CreateAccountModal';
import { EditAccountModal } from '@/components/ui/account/EditAccountModal';
import { AccountCard } from '@/components/ui/account/AccountCard';
import { AccountStats } from '@/components/ui/account/AccountStats';
import { FaPlus, FaWallet } from 'react-icons/fa';

export const Account: React.FC = () => {
  const { t } = useTranslation();
  const { account: accountApiClient } = useApiClients();
  const [accounts, setAccounts] = useState<AccountResponse[]>([]);
  const [summaries, setSummaries] = useState<AccountSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState<AccountResponse | null>(null);

  // Debug: Log when editingAccount changes
  React.useEffect(() => {
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
          : t('accountPage.errors.loadAccounts');
        setError(errorMessage);
        return;
      }

      if ('error' in summariesResult) {
        const errorMessage = typeof summariesResult.error === 'string' 
          ? summariesResult.error 
          : t('accountPage.errors.loadSummaries');
        setError(errorMessage);
        return;
      }

      setAccounts(accountsResult);
      setSummaries(summariesResult);
    } catch (err) {
      setError(t('accountPage.errors.loadAccounts'));
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
          : t('accountPage.errors.operationError');
        setError(errorMessage);
        return;
      }

      setShowCreateModal(false);
      await loadAccounts();
    } catch (err) {
      setError(t('accountPage.errors.createAccount'));
      console.error('Error creating account:', err);
    }
  };

  const handleUpdateAccount = async (id: number, accountData: any) => {
    try {
      const result = await accountApiClient.updateAccount(id, accountData);
      
      if ('error' in result) {
        const errorMessage = typeof result.error === 'string' 
          ? result.error 
          : t('accountPage.errors.operationError');
        setError(errorMessage);
        return;
      }

      setEditingAccount(null);
      await loadAccounts();
    } catch (err) {
      setError(t('accountPage.errors.updateAccount'));
      console.error('Error updating account:', err);
    }
  };

  const handleArchiveAccount = async (id: number) => {
    try {
      const result = await accountApiClient.archiveAccount(id);
      
      if ('error' in result) {
        const errorMessage = typeof result.error === 'string' 
          ? result.error 
          : t('accountPage.errors.operationError');
        setError(errorMessage);
        return;
      }

      await loadAccounts();
    } catch (err) {
      setError(t('accountPage.errors.archiveAccount'));
      console.error('Error archiving account:', err);
    }
  };

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
          <h1 className="text-2xl font-bold theme-text-primary">{t('accountPage.title')}</h1>
          <p className="text-sm theme-text-secondary mt-1">
            {t('accountPage.subtitle')}
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2"
        >
          <FaPlus className="w-4 h-4" />
          {t('accountPage.createButton')}
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Stats Cards */}
      <AccountStats summaries={summaries} />

      {/* Accounts List */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold theme-text-primary">{t('accountPage.myAccounts')}</h2>
        
        {activeAccounts.length === 0 ? (
          <Card className="p-8 text-center">
            <FaWallet className="w-12 h-12 theme-text-tertiary mx-auto mb-4" />
            <h3 className="text-lg font-medium theme-text-primary mb-2">
              {t('accountPage.emptyState.title')}
            </h3>
            <p className="text-sm theme-text-secondary mb-4">
              {t('accountPage.emptyState.subtitle')}
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              {t('accountPage.emptyState.button')}
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
            setEditingAccount(null);
          }}
          onSubmit={handleUpdateAccount}
        />
      )}
    </div>
  );
};
