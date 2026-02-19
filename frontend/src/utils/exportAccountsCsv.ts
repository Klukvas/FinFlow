import { AccountResponse, AccountSummary } from '@/types/account';

export function exportAccountsCsv(
  accounts: AccountResponse[],
  summaries: AccountSummary[]
): void {
  const headers = [
    'Name',
    'Type',
    'Currency',
    'Balance',
    'Transactions',
    'Last Transaction',
    'Created',
    'Status',
  ];

  const summaryMap = new Map(summaries.map((s) => [s.id, s]));

  const rows = accounts.map((a) => {
    const summary = summaryMap.get(a.id);
    return [
      `"${(a.name || '').replace(/"/g, '""')}"`,
      a.type,
      a.currency,
      a.balance,
      summary?.transaction_count ?? '',
      summary?.last_transaction_date?.split('T')[0] || '',
      a.created_at?.split('T')[0] || '',
      a.is_archived ? 'Archived' : 'Active',
    ].join(',');
  });

  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const date = new Date().toISOString().split('T')[0];
  link.href = url;
  link.download = `accounts_${date}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
