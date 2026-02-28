import React from "react";
import { useTranslation } from "react-i18next";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useCategories } from "@/contexts/CategoriesContext";
import { DashboardKpiStrip } from "@/components/ui/dashboard/DashboardKpiStrip";
import { CashFlowChart } from "@/components/ui/dashboard/CashFlowChart";
import { ExpenseByCategoryPie } from "@/components/ui/dashboard/ExpenseByCategoryPie";
import { IncomeByCategoryPie } from "@/components/ui/dashboard/IncomeByCategoryPie";
import { AccountBalancesCard } from "@/components/ui/dashboard/AccountBalancesCard";
import { DebtOverviewCard } from "@/components/ui/dashboard/DebtOverviewCard";
import { RecurringOverviewCard } from "@/components/ui/dashboard/RecurringOverviewCard";
import { GoalsOverview } from "@/components/ui/dashboard/GoalsOverview";
import { Skeleton } from "@/components/ui/shared/Skeleton";

const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const {
    expenses,
    incomes,
    accounts,
    debtSummary,
    recurringStats,
    loading,
    error,
  } = useDashboardData();
  const { expenseCategories, incomeCategories } = useCategories();

  return (
    <div className="min-h-screen theme-bg p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold theme-text-primary">
            {t("dashboard.title")}
          </h1>
          <p className="theme-text-secondary mt-1">{t("dashboard.subtitle")}</p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* KPI Strip */}
        <DashboardKpiStrip
          expenses={expenses}
          incomes={incomes}
          accounts={accounts}
          loading={loading}
        />

        {/* Cash Flow Chart */}
        {loading ? (
          <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
            <Skeleton variant="text" className="h-5 w-48 mb-4" />
            <Skeleton variant="rectangular" className="h-[300px] w-full" />
          </div>
        ) : (
          <CashFlowChart expenses={expenses} incomes={incomes} />
        )}

        {/* Category Breakdown Pie Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {loading ? (
            <>
              <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
                <Skeleton variant="text" className="h-5 w-40 mb-4" />
                <Skeleton variant="rectangular" className="h-[300px] w-full" />
              </div>
              <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
                <Skeleton variant="text" className="h-5 w-40 mb-4" />
                <Skeleton variant="rectangular" className="h-[300px] w-full" />
              </div>
            </>
          ) : (
            <>
              <ExpenseByCategoryPie
                expenses={expenses}
                categories={expenseCategories}
              />
              <IncomeByCategoryPie
                incomes={incomes}
                categories={incomeCategories}
              />
            </>
          )}
        </div>

        {/* Account Balances */}
        {loading ? (
          <div className="theme-surface p-4 rounded-lg theme-shadow theme-border border">
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

        {/* Bottom Widgets */}
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
