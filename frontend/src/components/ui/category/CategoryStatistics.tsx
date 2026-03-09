import React, { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { useApiClients } from "@/hooks";
import { useAuth } from "@/contexts/AuthContext";

interface CategoryStatisticsProps {
 refreshTrigger?: number;
}

export const CategoryStatistics: React.FC<CategoryStatisticsProps> = ({
 refreshTrigger,
}) => {
 const { t } = useTranslation();
 const { isAuthenticated, isLoading: authLoading } = useAuth();
 const [stats, setStats] = useState({
 totalCategories: 0,
 expenseCategories: 0,
 incomeCategories: 0,
 parentCategories: 0,
 childCategories: 0,
 });
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);
 const { category } = useApiClients();

 const fetchStatistics = useCallback(async () => {
 // Don't fetch if not authenticated or auth is still loading
 if (!isAuthenticated || authLoading) {
 return;
 }

 try {
 setLoading(true);
 setError(null);

 // Fetch statistics from the dedicated backend endpoint
 const statsResponse = await category.getCategoryStatistics();

 if ("error" in statsResponse) {
 logger.error(
 "CategoryStatistics: Error response:",
 statsResponse.error,
 );
 setError(statsResponse.error);
 } else {
 setStats({
 totalCategories: statsResponse.total_categories,
 expenseCategories: statsResponse.expense_categories,
 incomeCategories: statsResponse.income_categories,
 parentCategories: statsResponse.parent_categories,
 childCategories: statsResponse.child_categories,
 });
 }
 } catch (err) {
 logger.error("CategoryStatistics: Exception during fetch:", err);
 setError(t("category.statistics.loadError"));
 } finally {
 setLoading(false);
 }
 }, [category, t, isAuthenticated, authLoading]);

 useEffect(() => {
 fetchStatistics();
 }, [fetchStatistics, refreshTrigger]);

 if (loading) {
 return (
 <div className="bg-elevated backdrop-blur-sm rounded-xl sm:rounded-2xl border border-[var(--color-border)] shadow-xl p-4 sm:p-6 lg:p-8">
 <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
 <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-accent-base to-purple-600 rounded-lg flex items-center justify-center">
 <svg
 className="w-4 h-4 sm:w-5 sm:h-5 text-white"
 fill="none"
 stroke="currentColor"
 viewBox="0 0 24 24"
 >
 <path
 strokeLinecap="round"
 strokeLinejoin="round"
 strokeWidth={2}
 d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
 />
 </svg>
 </div>
 <h3 className="text-lg sm:text-xl font-bold text-content">
 {t("category.statistics.title")}
 </h3>
 </div>
 <div className="flex justify-center items-center py-6 sm:py-8">
 <div className="relative">
 <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 border-[var(--color-border)]"></div>
 <div className="animate-spin rounded-full h-6 w-6 sm:h-8 sm:w-8 border-2 sm:border-3 text-accent-base border-t-transparent absolute top-0 left-0"></div>
 </div>
 </div>
 </div>
 );
 }

 if (error) {
 return (
 <div className="bg-elevated backdrop-blur-sm rounded-xl sm:rounded-2xl border border-[var(--color-border)] shadow-xl p-4 sm:p-6 lg:p-8">
 <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
 <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-danger-base to-pink-600 rounded-lg flex items-center justify-center">
 <svg
 className="w-4 h-4 sm:w-5 sm:h-5 text-white"
 fill="none"
 stroke="currentColor"
 viewBox="0 0 24 24"
 >
 <path
 strokeLinecap="round"
 strokeLinejoin="round"
 strokeWidth={2}
 d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
 />
 </svg>
 </div>
 <h3 className="text-lg sm:text-xl font-bold text-content">
 {t("category.statistics.title")}
 </h3>
 </div>
 <div className="bg-[var(--color-danger-light)] border border-[var(--color-border)] rounded-lg sm:rounded-xl p-3 sm:p-4">
 <p className="text-danger-base text-xs sm:text-sm font-medium">{error}</p>
 </div>
 </div>
 );
 }

 const statItems = [
 {
 label: t("category.statistics.totalCategories"),
 value: stats.totalCategories,
 color: "from-accent-base to-accent-base",
 bgColor: "bg-[var(--color-accent-light)]",
 icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
 testId: "total-categories-stat",
 },
 {
 label: t("category.statistics.expenseCategories"),
 value: stats.expenseCategories,
 color: "from-danger-base to-danger-base",
 bgColor: "bg-[var(--color-danger-light)]",
 icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1",
 testId: "expense-categories-stat",
 },
 {
 label: t("category.statistics.incomeCategories"),
 value: stats.incomeCategories,
 color: "from-success-base to-success-base",
 bgColor: "bg-[var(--color-success-light)]",
 icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1",
 testId: "income-categories-stat",
 },
 {
 label: t("category.statistics.parentCategories"),
 value: stats.parentCategories,
 color: "from-purple-500 to-purple-600",
 bgColor: "bg-[var(--color-accent-light)]",
 icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z",
 testId: "parent-categories-stat",
 },
 {
 label: t("category.statistics.childCategories"),
 value: stats.childCategories,
 color: "from-warning-base to-warning-base",
 bgColor: "bg-[var(--color-warning-light)]",
 icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
 testId: "child-categories-stat",
 },
 ];

 return (
 <div className="bg-elevated backdrop-blur-sm rounded-xl sm:rounded-2xl border border-[var(--color-border)] shadow-xl p-4 sm:p-6 lg:p-8">
 <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
 <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-accent-base to-purple-600 rounded-lg flex items-center justify-center">
 <svg
 className="w-4 h-4 sm:w-5 sm:h-5 text-white"
 fill="none"
 stroke="currentColor"
 viewBox="0 0 24 24"
 >
 <path
 strokeLinecap="round"
 strokeLinejoin="round"
 strokeWidth={2}
 d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
 />
 </svg>
 </div>
 <h3 className="text-lg sm:text-xl font-bold text-content">
 {t("category.statistics.title")}
 </h3>
 </div>
 <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4 lg:gap-6">
 {statItems.map((item, index) => (
 <div
 key={index}
 data-testid={item.testId}
 className={`relative ${item.bgColor} rounded-lg sm:rounded-xl p-3 sm:p-4 lg:p-6 border border-[var(--color-border)] hover:shadow-lg transition-all duration-200 hover:-translate-y-1 group`}
 >
 <div className="flex items-center justify-between mb-2 sm:mb-3">
 <div
 className={`w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10 bg-gradient-to-br ${item.color} rounded-lg flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200`}
 >
 <svg
 className="w-3 h-3 sm:w-4 sm:h-4 lg:w-5 lg:h-5 text-white"
 fill="none"
 stroke="currentColor"
 viewBox="0 0 24 24"
 >
 <path
 strokeLinecap="round"
 strokeLinejoin="round"
 strokeWidth={2}
 d={item.icon}
 />
 </svg>
 </div>
 </div>
 <div
 data-testid={`${item.testId}-value`}
 className={`text-xl sm:text-2xl lg:text-3xl xl:text-4xl font-bold bg-gradient-to-r ${item.color} bg-clip-text text-transparent mb-1 sm:mb-2`}
 >
 {item.value}
 </div>
 <div
 data-testid={`${item.testId}-label`}
 className="text-xs sm:text-sm font-medium text-content-secondary leading-tight"
 >
 {item.label}
 </div>
 </div>
 ))}
 </div>
 </div>
 );
};
