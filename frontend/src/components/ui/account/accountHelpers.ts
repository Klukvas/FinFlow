import { AccountResponse } from '@/types/account';

export interface AccountsPageFilters {
  page: number;
  size: number;
  type?: string | 'all';
  currency?: string | 'all';
  search?: string;
  groupBy?: 'none' | 'currency' | 'type';
}

export const ACCOUNT_TYPES = ['bank', 'cash', 'crypto', 'investment', 'savings', 'other'] as const;

export const ACCOUNT_TYPE_I18N_MAP: Record<string, string> = {
  bank: 'accountPage.form.types.bank',
  cash: 'accountPage.form.types.cash',
  crypto: 'accountPage.form.types.crypto',
  investment: 'accountPage.form.types.investment',
  savings: 'accountPage.form.types.savings',
  other: 'accountPage.form.types.other',
};

export const getTypeBadgeVariant = (type: string): string => {
  switch (type.toLowerCase()) {
    case 'bank': return 'info';
    case 'cash': return 'success';
    case 'crypto': return 'warning';
    case 'investment': return 'default';
    case 'savings': return 'secondary';
    case 'other': return 'outline';
    default: return 'secondary';
  }
};

export const getStatusBadgeVariant = (isArchived: boolean): string => {
  return isArchived ? 'secondary' : 'success';
};

export const formatBalance = (balance: number, currency: string): string => {
  return (
    new Intl.NumberFormat('uk-UA', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(balance) + ' ' + currency
  );
};

export const formatDate = (dateString?: string | null): string => {
  if (!dateString) return '\u2014';
  return new Date(dateString).toLocaleDateString('uk-UA');
};

export const getUniqueCurrencies = (accounts: AccountResponse[]): string[] => {
  return [...new Set(accounts.map((a) => a.currency))].sort();
};

export const groupAccounts = (
  accounts: AccountResponse[],
  groupBy: 'none' | 'currency' | 'type'
): Record<string, AccountResponse[]> => {
  if (groupBy === 'none') return { all: accounts };

  const groups: Record<string, AccountResponse[]> = {};
  for (const account of accounts) {
    const key = groupBy === 'currency' ? account.currency : account.type;
    if (!groups[key]) groups[key] = [];
    groups[key].push(account);
  }

  // Sort group keys
  return Object.keys(groups)
    .sort()
    .reduce((sorted, key) => {
      sorted[key] = groups[key];
      return sorted;
    }, {} as Record<string, AccountResponse[]>);
};
