import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useCategories } from "@/contexts/CategoriesContext";
import { DashboardKpiStrip } from "@/components/ui/dashboard/DashboardKpiStrip";
import { CashFlowChart } from "@/components/ui/dashboard/CashFlowChart";
import { MonthComparisonChart } from "@/components/ui/dashboard/MonthComparisonChart";
import { ExpenseByCategoryPie } from "@/components/ui/dashboard/ExpenseByCategoryPie";
import { IncomeByCategoryPie } from "@/components/ui/dashboard/IncomeByCategoryPie";
import { AccountBalancesCard } from "@/components/ui/dashboard/AccountBalancesCard";
import { DebtOverviewCard } from "@/components/ui/dashboard/DebtOverviewCard";
import { RecurringOverviewCard } from "@/components/ui/dashboard/RecurringOverviewCard";
import { GoalsOverview } from "@/components/ui/dashboard/GoalsOverview";
import { ProFeatureGate } from "@/components/ui/dashboard/ProFeatureGate";
import { BudgetProgressWidget } from "@/components/ui/dashboard/BudgetProgressWidget";
import { UpcomingPaymentsWidget } from "@/components/ui/dashboard/UpcomingPaymentsWidget";
import { AiInsightsWidget } from "@/components/ui/dashboard/AiInsightsWidget";
import { TopExpensesChart } from "@/components/ui/dashboard/TopExpensesChart";
import { DailySpendingChart } from "@/components/ui/dashboard/DailySpendingChart";
import { PeriodSelector } from "@/components/ui/dashboard/PeriodSelector";
import { Skeleton } from "@/components/ui/shared/Skeleton";
import {
  RefreshCw,
  PieChart,
  CalendarClock,
  BarChart3,
  TrendingUp,
  Sparkles,
} from "lucide-react";

const formatPeriodSubtitle = (
  periodMonths: number,
  language: string,
): string => {
  const now = new Date();
  if (periodMonths === 1) {
    return now.toLocaleDateString(language, {
      month: "long",
      year: "numeric",
    });
  }
  const start = new Date(now);
  start.setMonth(start.getMonth() - periodMonths + 1);
  start.setDate(1);
  const startStr = start.toLocaleDateString(language, {
    month: "long",
    year: "numeric",
  });
  const endStr = now.toLocaleDateString(language, {
    month: "long",
    year: "numeric",
  });
  return `${startStr} — ${endStr}`;
};

const Dashboard: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [periodMonths, setPeriodMonths] = useState(1);
  const {
    expenses,
    incomes,
    accounts,
    debtSummary,
    recurringStats,
    recurringPayments,
    planCode,
    loading,
    error,
    retry,
  } = useDashboardData(periodMonths);
  const { expenseCategories, incomeCategories } = useCategories();

  const periodSubtitle = useMemo(
    () => formatPeriodSubtitle(periodMonths, i18n.language),
    [periodMonths, i18n.language],
  );

  return (
    <div
      className="min-h-screen bg-surface p-2 sm:p-4 md:p-6 lg:p-8 overflow-x-hidden"
      data-testid="dashboard-page"
    >
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header with Period Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold text-content">
              {t("dashboard.title")}
            </h1>
            <p className="text-content-secondary mt-1">
              {t("dashboard.subtitle")} — {periodSubtitle}
            </p>
          </div>
          <div data-testid="dashboard-period-selector">
            <PeriodSelector
              planCode={planCode}
              value={periodMonths}
              onChange={setPeriodMonths}
            />
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-4 rounded-lg bg-[var(--danger-dim)] border border-[var(--border)] flex items-center justify-between">
            <p className="text-sm text-danger-base">{t(error)}</p>
            <button
              onClick={retry}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-danger-base hover:bg-[var(--danger-dim)] rounded-lg transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              {t("dashboard.retry")}
            </button>
          </div>
        )}

        {/* KPI Strip (5 cards) — Free */}
        <DashboardKpiStrip
          expenses={expenses}
          incomes={incomes}
          accounts={accounts}
          periodMonths={periodMonths}
          loading={loading}
        />

        {/* Cash Flow & Month Comparison */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {loading ? (
            <>
              <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
                <Skeleton variant="text" className="h-5 w-48 mb-4" />
                <Skeleton variant="rectangular" className="h-[300px] w-full" />
              </div>
              <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
                <Skeleton variant="text" className="h-5 w-48 mb-4" />
                <Skeleton variant="rectangular" className="h-[300px] w-full" />
              </div>
            </>
          ) : (
            <>
              <CashFlowChart expenses={expenses} incomes={incomes} />
              <MonthComparisonChart
                expenses={expenses}
                incomes={incomes}
                periodMonths={periodMonths}
              />
            </>
          )}
        </div>

        {/* Category Breakdown Pie Charts — Free */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {loading ? (
            <>
              <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
                <Skeleton variant="text" className="h-5 w-40 mb-4" />
                <Skeleton variant="rectangular" className="h-[300px] w-full" />
              </div>
              <div className="bg-elevated p-4 rounded-lg theme-shadow border-[var(--border)] border">
                <Skeleton variant="text" className="h-5 w-40 mb-4" />
                <Skeleton variant="rectangular" className="h-[300px] w-full" />
              </div>
            </>
          ) : (
            <>
              <ExpenseByCategoryPie
                expenses={expenses}
                categories={expenseCategories}
                periodMonths={periodMonths}
              />
              <IncomeByCategoryPie
                incomes={incomes}
                categories={incomeCategories}
                periodMonths={periodMonths}
              />
            </>
          )}
        </div>

        {/* Account Balances — Free */}
        {loading ? (
          <div className="bg-elevated p-6 rounded-lg theme-shadow border-[var(--border)] border">
            <Skeleton variant="text" className="h-5 w-40 mb-4" />
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton
                  key={i}
                  variant="rectangular"
                  className="h-12 w-full rounded-lg"
                />
              ))}
            </div>
          </div>
        ) : (
          <AccountBalancesCard accounts={accounts} />
        )}

        {/* Pro+ Section */}
        <div className="relative">
          <div
            className="absolute inset-0 flex items-center"
            aria-hidden="true"
          >
            <div className="w-full border-t border-[var(--border)]" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-surface px-3 text-sm font-medium text-content-secondary">
              {t("dashboard.proSection")}
            </span>
          </div>
        </div>

        <div>
          {loading ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Skeleton
                  variant="rectangular"
                  className="h-[200px] rounded-lg"
                />
                <Skeleton
                  variant="rectangular"
                  className="h-[200px] rounded-lg"
                />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Skeleton
                  variant="rectangular"
                  className="h-[300px] rounded-lg"
                />
                <Skeleton
                  variant="rectangular"
                  className="h-[300px] rounded-lg"
                />
              </div>
            </div>
          ) : (
            <>
              {/* Budget Progress & Upcoming Payments — Pro+ */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <ProFeatureGate
                  planCode={planCode}
                  featureTitle={t("dashboard.budget.title")}
                  featureIcon={PieChart}
                >
                  <BudgetProgressWidget
                    expenses={expenses}
                    categories={expenseCategories}
                    periodMonths={periodMonths}
                  />
                </ProFeatureGate>
                <ProFeatureGate
                  planCode={planCode}
                  featureTitle={t("dashboard.upcoming.title")}
                  featureIcon={CalendarClock}
                >
                  <UpcomingPaymentsWidget payments={recurringPayments} />
                </ProFeatureGate>
              </div>

              {/* Top Spending & Daily Spending — Pro+ */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <ProFeatureGate
                  planCode={planCode}
                  featureTitle={t("dashboard.topSpending.title")}
                  featureIcon={BarChart3}
                >
                  <TopExpensesChart
                    expenses={expenses}
                    categories={expenseCategories}
                    periodMonths={periodMonths}
                  />
                </ProFeatureGate>
                <ProFeatureGate
                  planCode={planCode}
                  featureTitle={t("dashboard.dailySpending.title")}
                  featureIcon={TrendingUp}
                >
                  <DailySpendingChart
                    expenses={expenses}
                    periodMonths={periodMonths}
                  />
                </ProFeatureGate>
              </div>

              {/* AI Insights — Pro+ */}
              <ProFeatureGate
                planCode={planCode}
                featureTitle={t("dashboard.aiInsights.title")}
                featureIcon={Sparkles}
              >
                <AiInsightsWidget />
              </ProFeatureGate>
            </>
          )}
        </div>

        {/* Bottom Section */}
        <div className="relative">
          <div
            className="absolute inset-0 flex items-center"
            aria-hidden="true"
          >
            <div className="w-full border-t border-[var(--border)]" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-surface px-3 text-sm font-medium text-content-secondary">
              {t("dashboard.planningSection")}
            </span>
          </div>
        </div>

        {/* Bottom Widgets — Free */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <GoalsOverview />
          <div className="space-y-6">
            <DebtOverviewCard debtSummary={debtSummary} />
            <RecurringOverviewCard recurringStats={recurringStats} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
