import { ExpenseResponse } from '../types/expense';
import { IncomeOut } from '../types/income';

export function exportExpensesCsv(
  expenses: ExpenseResponse[],
  categoryMap: Record<number, string>
): void {
  const header = 'Date,Amount,Currency,Category,Description';
  const rows = expenses.map((e) => {
    const date = e.date ? new Date(e.date).toLocaleDateString() : '';
    const category = categoryMap[e.category_id] || '';
    const description = (e.description || '').replace(/"/g, '""');
    return `${date},${e.amount},${e.currency},"${category}","${description}"`;
  });

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `expenses_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export function exportIncomeCsv(
  incomes: IncomeOut[],
  categoryMap: Record<number, string>
): void {
  const header = 'Date,Amount,Currency,Category,Description';
  const rows = incomes.map((inc) => {
    const date = inc.date ? new Date(inc.date).toLocaleDateString() : '';
    const category = inc.category_id ? (categoryMap[inc.category_id] || '') : '';
    const description = (inc.description || '').replace(/"/g, '""');
    return `${date},${inc.amount},${inc.currency},"${category}","${description}"`;
  });

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `income_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
