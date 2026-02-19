import { RecurringPayment } from '@/services/api/recurringApi';

export function exportRecurringCsv(payments: RecurringPayment[]): void {
  const header = 'Name,Type,Amount,Currency,Schedule,Status,Next Execution,Last Executed,Start Date,End Date,Description';
  const rows = payments.map((p) => {
    const name = (p.name || '').replace(/"/g, '""');
    const description = (p.description || '').replace(/"/g, '""');
    const nextExec = p.next_execution ? new Date(p.next_execution).toLocaleDateString() : '';
    const lastExec = p.last_executed ? new Date(p.last_executed).toLocaleDateString() : '';
    const startDate = p.start_date ? new Date(p.start_date).toLocaleDateString() : '';
    const endDate = p.end_date ? new Date(p.end_date).toLocaleDateString() : '';
    return `"${name}",${p.payment_type},${p.amount},${p.currency},${p.schedule_type},${p.status},${nextExec},${lastExec},${startDate},${endDate},"${description}"`;
  });

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `recurring_payments_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
