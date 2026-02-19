import { DebtResponse } from '../types/debt';

export function exportDebtsCsv(debts: DebtResponse[]): void {
  const header = 'Name,Type,Initial Amount,Balance,Currency,Interest Rate,Due Date,Status,Contact';
  const rows = debts.map((d) => {
    const name = (d.name || '').replace(/"/g, '""');
    const dueDate = d.due_date ? new Date(d.due_date).toLocaleDateString() : '';
    const status = d.is_paid_off ? 'Paid Off' : d.is_active ? 'Active' : 'Inactive';
    const contact = d.contact ? (d.contact.name || '').replace(/"/g, '""') : '';
    const interestRate = d.interest_rate != null ? d.interest_rate.toString() : '';
    return `"${name}",${d.debt_type},${d.initial_amount},${d.current_balance},${d.currency},${interestRate},${dueDate},${status},"${contact}"`;
  });

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `debts_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
