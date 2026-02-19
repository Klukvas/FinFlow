import { DebtType, DebtResponse } from '@/types/debt';

export type DebtStatus = 'active' | 'paid_off' | 'inactive';

export const getProgressPercentage = (debt: DebtResponse): number => {
  const initial = Math.abs(debt.initial_amount);
  if (initial === 0) return 0;
  const current = Math.abs(debt.current_balance);
  const paidOff = initial - current;
  return Math.max(0, Math.min(100, (paidOff / initial) * 100));
};

export const getDebtStatus = (debt: DebtResponse): DebtStatus => {
  if (debt.is_paid_off) return 'paid_off';
  if (debt.is_active) return 'active';
  return 'inactive';
};

export const getStatusBadgeVariant = (status: DebtStatus): string => {
  switch (status) {
    case 'active':
      return 'success';
    case 'paid_off':
      return 'info';
    case 'inactive':
      return 'secondary';
  }
};

export const DEBT_TYPE_I18N_MAP: Record<DebtType, string> = {
  CREDIT_CARD: 'debtPage.types.creditCard',
  LOAN: 'debtPage.types.generalLoan',
  MORTGAGE: 'debtPage.types.mortgage',
  PERSONAL_LOAN: 'debtPage.types.personalLoan',
  AUTO_LOAN: 'debtPage.types.autoLoan',
  STUDENT_LOAN: 'debtPage.types.studentLoan',
  OTHER: 'debtPage.types.other',
};

export const STATUS_I18N_MAP: Record<DebtStatus, string> = {
  active: 'debtPage.status.active',
  paid_off: 'debtPage.status.paidOff',
  inactive: 'debtPage.status.inactive',
};

export interface DebtFilters {
  page: number;
  size: number;
  status?: 'active' | 'paid_off' | 'all';
  debt_type?: DebtType;
  contact_id?: number;
  currency?: string;
  date_from?: string;
  date_to?: string;
}
