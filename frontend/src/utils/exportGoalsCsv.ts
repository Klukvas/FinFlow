import { Goal } from '@/types/goal';

export function exportGoalsCsv(goals: Goal[]): void {
  const headers = [
    'Title',
    'Type',
    'Priority',
    'Status',
    'Current Amount',
    'Target Amount',
    'Currency',
    'Progress %',
    'Start Date',
    'Target Date',
    'Days Remaining',
    'Description',
  ];

  const rows = goals.map((g) => {
    const daysRemaining = g.target_date
      ? Math.ceil((new Date(g.target_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
      : '';

    return [
      `"${(g.title || '').replace(/"/g, '""')}"`,
      g.goal_type,
      g.priority,
      g.status,
      g.current_amount,
      g.target_amount,
      g.currency,
      g.progress_percentage.toFixed(1),
      g.start_date?.split('T')[0] || '',
      g.target_date?.split('T')[0] || '',
      daysRemaining,
      `"${(g.description || '').replace(/"/g, '""')}"`,
    ].join(',');
  });

  const csv = [headers.join(','), ...rows].join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const date = new Date().toISOString().split('T')[0];
  link.href = url;
  link.download = `goals_${date}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
