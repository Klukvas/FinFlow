import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useApiClients } from "@/hooks/useApiClients";
import { logger } from "@/utils/logger";
import {
  ExpenseResponse,
  IncomeOut,
  AccountSummary,
  DebtSummary,
} from "@/types";
import { PaymentStatistics } from "@/services/api/recurringApi";

export interface DashboardData {
  expenses: ExpenseResponse[];
  incomes: IncomeOut[];
  accounts: AccountSummary[];
  debtSummary: DebtSummary | null;
  recurringStats: PaymentStatistics | null;
  loading: boolean;
  error: string | null;
}

export const useDashboardData = (): DashboardData => {
  const { user } = useAuth();
  const { expense, income, account, debt, recurring } = useApiClients();

  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [incomes, setIncomes] = useState<IncomeOut[]>([]);
  const [accounts, setAccounts] = useState<AccountSummary[]>([]);
  const [debtSummary, setDebtSummary] = useState<DebtSummary | null>(null);
  const [recurringStats, setRecurringStats] =
    useState<PaymentStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.id) return;

    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        const [expRes, incRes, accRes, debtRes, recRes] = await Promise.all([
          expense.getExpenses(),
          income.getIncomes(),
          account.getAccountSummaries(),
          debt.getDebtSummary(),
          recurring.getPaymentStatistics(),
        ]);

        if (!("error" in expRes)) setExpenses(expRes);
        if (!("error" in incRes)) setIncomes(incRes);
        if (!("error" in accRes)) setAccounts(accRes);
        if (!("error" in debtRes)) setDebtSummary(debtRes);
        if (!("error" in recRes)) setRecurringStats(recRes);
      } catch (err) {
        logger.error("Failed to fetch dashboard data:", err);
        setError("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [user?.id, expense, income, account, debt, recurring]);

  return {
    expenses,
    incomes,
    accounts,
    debtSummary,
    recurringStats,
    loading,
    error,
  };
};
