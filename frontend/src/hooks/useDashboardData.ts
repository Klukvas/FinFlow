import { useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useApiClients } from "@/hooks/useApiClients";
import { logger } from "@/utils/logger";
import {
  ExpenseResponse,
  IncomeOut,
  AccountSummary,
  DebtSummary,
} from "@/types";
import {
  PaymentStatistics,
  RecurringPayment,
} from "@/services/api/recurringApi";

export interface DashboardData {
  expenses: ExpenseResponse[];
  incomes: IncomeOut[];
  accounts: AccountSummary[];
  debtSummary: DebtSummary | null;
  recurringStats: PaymentStatistics | null;
  recurringPayments: RecurringPayment[];
  planCode: string;
  periodMonths: number;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

const formatDate = (d: Date): string => d.toISOString().split("T")[0];

export const useDashboardData = (periodMonths: number = 1): DashboardData => {
  const { user } = useAuth();
  const { expense, income, account, debt, recurring, subscription } =
    useApiClients();

  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [incomes, setIncomes] = useState<IncomeOut[]>([]);
  const [accounts, setAccounts] = useState<AccountSummary[]>([]);
  const [debtSummary, setDebtSummary] = useState<DebtSummary | null>(null);
  const [recurringStats, setRecurringStats] =
    useState<PaymentStatistics | null>(null);
  const [recurringPayments, setRecurringPayments] = useState<
    RecurringPayment[]
  >([]);
  const [planCode, setPlanCode] = useState("basic");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { startDate, endDate } = useMemo(() => {
    const now = new Date();
    const end = formatDate(now);
    // Fetch max(2x period, 6 months) so comparison charts and CashFlowChart have data
    const fetchMonths = Math.max(periodMonths * 2, 6);
    const start = new Date(now);
    start.setMonth(start.getMonth() - fetchMonths);
    start.setDate(1);
    return { startDate: formatDate(start), endDate: end };
  }, [periodMonths]);

  const fetchAll = useCallback(async () => {
    if (!user?.id) return;

    setLoading(true);
    setError(null);
    try {
      const [expRes, incRes, accRes, debtRes, recRes, recPayRes, subRes] =
        await Promise.all([
          expense.getExpensesByDateRange(startDate, endDate),
          income.getIncomesByDateRange(startDate, endDate),
          account.getAccountSummaries(),
          debt.getDebtSummary(),
          recurring.getPaymentStatistics(),
          recurring.getRecurringPayments({ status: "active", size: 100 }),
          subscription.getUserSubscription(user.id),
        ]);

      if (!("error" in expRes)) setExpenses(expRes);
      if (!("error" in incRes)) setIncomes(incRes);
      if (!("error" in accRes)) setAccounts(accRes);
      if (!("error" in debtRes)) setDebtSummary(debtRes);
      if (!("error" in recRes)) setRecurringStats(recRes);
      if (!("error" in recPayRes)) setRecurringPayments(recPayRes.items);
      if ("error" in subRes) {
        logger.warn("Subscription check failed, defaulting to basic plan");
        setPlanCode("basic");
      } else {
        setPlanCode(
          typeof subRes.plan_code === "string" ? subRes.plan_code : "basic",
        );
      }
    } catch (err) {
      logger.error("Failed to fetch dashboard data:", err);
      setError("dashboard.loadError");
    } finally {
      setLoading(false);
    }
  }, [
    user?.id,
    expense,
    income,
    account,
    debt,
    recurring,
    subscription,
    startDate,
    endDate,
  ]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    expenses,
    incomes,
    accounts,
    debtSummary,
    recurringStats,
    recurringPayments,
    planCode,
    periodMonths,
    loading,
    error,
    retry: fetchAll,
  };
};
