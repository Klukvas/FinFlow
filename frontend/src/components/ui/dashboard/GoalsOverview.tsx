import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { logger } from "@/utils/logger";
import { useAuth } from "@/contexts/AuthContext";
import { useApiClients } from "@/hooks/useApiClients";
import { Goal, GoalStatistics as GoalStatisticsType } from "@/types";
import {
 FaBullseye,
 FaCheckCircle,
 FaPlay,
 FaChartPie,
 FaDollarSign,
 FaArrowRight,
} from "react-icons/fa";
import { Link } from "react-router-dom";

export const GoalsOverview: React.FC = () => {
 const { t } = useTranslation();
 const { user } = useAuth();
 const { goals: goalsApi } = useApiClients();
 const [goals, setGoals] = useState<Goal[]>([]);
 const [statistics, setStatistics] = useState<GoalStatisticsType | null>(null);
 const [loading, setLoading] = useState(true);

 useEffect(() => {
 const fetchData = async () => {
 if (!user?.id) return;

 try {
 setLoading(true);
 const [goalsResponse, statsResponse] = await Promise.all([
 goalsApi.getGoals({ page: 1, size: 3 }),
 goalsApi.getGoalStatistics(),
 ]);

 if ("error" in goalsResponse) {
 throw new Error(goalsResponse.error);
 }
 if ("error" in statsResponse) {
 throw new Error(statsResponse.error);
 }

 setGoals(goalsResponse.items);
 setStatistics(statsResponse);
 } catch (error) {
 logger.error("Failed to fetch goals data:", error);
 } finally {
 setLoading(false);
 }
 };

 fetchData();
 }, [user?.id, goalsApi]);

 const getProgressColor = (percentage: number) => {
 if (percentage >= 80) return "bg-success-base";
 if (percentage >= 60) return "bg-accent-base";
 if (percentage >= 40) return "bg-warning-base";
 if (percentage >= 20) return "bg-warning-base";
 return "bg-danger-base";
 };

 const getDaysRemaining = (targetDate: string) => {
 const target = new Date(targetDate);
 const today = new Date();
 const diffTime = target.getTime() - today.getTime();
 const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
 return diffDays;
 };

 if (loading) {
 return (
 <div className="bg-elevated rounded-lg theme-shadow border-[var(--color-border)] border p-6">
 <div className="animate-pulse">
 <div className="h-4 bg-surface-alt rounded w-1/4 mb-4"></div>
 <div className="space-y-3">
 <div className="h-3 bg-surface-alt rounded"></div>
 <div className="h-3 bg-surface-alt rounded w-5/6"></div>
 </div>
 </div>
 </div>
 );
 }

 if (!statistics || statistics.total_goals === 0) {
 return (
 <div className="bg-elevated rounded-lg theme-shadow border-[var(--color-border)] border p-6">
 <div className="text-center">
 <FaBullseye className="mx-auto h-12 w-12 text-content-tertiary mb-4" />
 <h3 className="text-lg font-semibold text-content mb-2">
 {t("dashboard.goalsOverview.noGoals")}
 </h3>
 <p className="text-content-secondary mb-4">
 {t("dashboard.goalsOverview.createFirstGoal")}
 </p>
 <Link
 to="/goals"
 className="inline-flex items-center px-4 py-2 bg-accent-base text-content-inverse rounded-md hover:bg-accent-base-hover transition-colors"
 >
 {t("dashboard.goalsOverview.createGoal")}
 <FaArrowRight className="ml-2 w-4 h-4" />
 </Link>
 </div>
 </div>
 );
 }

 return (
 <div className="bg-elevated rounded-lg theme-shadow border-[var(--color-border)] border p-6">
 {/* Header */}
 <div className="flex items-center justify-between mb-6">
 <div className="flex items-center">
 <FaBullseye className="h-6 w-6 text-accent-base mr-2" />
 <h3 className="text-lg font-semibold text-content">
 {t("dashboard.goalsOverview.title")}
 </h3>
 </div>
 <Link
 to="/goals"
 className="text-accent-base hover:text-accent-base text-sm font-medium flex items-center transition-colors"
 >
 {t("dashboard.goalsOverview.viewAll")}
 <FaArrowRight className="ml-1 w-3 h-3" />
 </Link>
 </div>

 {/* Statistics */}
 <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
 <div className="text-center">
 <div className="flex items-center justify-center mb-2">
 <FaBullseye className="h-5 w-5 text-accent-base" />
 </div>
 <p className="text-2xl font-bold text-content">
 {statistics.total_goals}
 </p>
 <p className="text-xs text-content-tertiary">
 {t("dashboard.goalsOverview.totalGoals")}
 </p>
 </div>

 <div className="text-center">
 <div className="flex items-center justify-center mb-2">
 <FaPlay className="h-5 w-5 text-success-base" />
 </div>
 <p className="text-2xl font-bold text-content">
 {statistics.active_goals}
 </p>
 <p className="text-xs text-content-tertiary">
 {t("dashboard.goalsOverview.activeGoals")}
 </p>
 </div>

 <div className="text-center">
 <div className="flex items-center justify-center mb-2">
 <FaCheckCircle className="h-5 w-5 text-accent-base" />
 </div>
 <p className="text-2xl font-bold text-content">
 {statistics.completed_goals}
 </p>
 <p className="text-xs text-content-tertiary">
 {t("dashboard.goalsOverview.completedGoals")}
 </p>
 </div>

 <div className="text-center">
 <div className="flex items-center justify-center mb-2">
 <FaChartPie className="h-5 w-5 text-accent-base" />
 </div>
 <p className="text-2xl font-bold text-content">
 {statistics.overall_progress.toFixed(0)}%
 </p>
 <p className="text-xs text-content-tertiary">
 {t("dashboard.goalsOverview.overallProgress")}
 </p>
 </div>
 </div>

 {/* Financial Summary */}
 <div className="bg-surface-alt rounded-lg p-4 mb-6">
 <div className="flex items-center mb-3">
 <FaDollarSign className="h-5 w-5 text-success-base mr-2" />
 <h4 className="font-semibold text-content">
 {t("dashboard.goalsOverview.financialSummary")}
 </h4>
 </div>
 <div className="grid grid-cols-2 gap-4">
 <div>
 <p className="text-sm text-content-tertiary">
 {t("dashboard.goalsOverview.totalSaved")}
 </p>
 <p className="text-lg font-bold text-success-base">
 {statistics.total_current_amount.toLocaleString()} USD
 </p>
 </div>
 <div>
 <p className="text-sm text-content-tertiary">
 {t("dashboard.goalsOverview.targetAmount")}
 </p>
 <p className="text-lg font-bold text-content">
 {statistics.total_target_amount.toLocaleString()} USD
 </p>
 </div>
 </div>
 <div className="mt-3">
 <div className="w-full bg-surface-alt rounded-full h-2">
 <div
 className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(statistics.overall_progress)}`}
 style={{
 width: `${Math.min(statistics.overall_progress, 100)}%`,
 }}
 />
 </div>
 </div>
 </div>

 {/* Recent Goals */}
 {goals.length > 0 && (
 <div>
 <h4 className="font-semibold text-content mb-4">
 {t("dashboard.goalsOverview.recentGoals")}
 </h4>
 <div className="space-y-3">
 {goals.map((goal) => {
 const daysRemaining = goal.target_date
 ? getDaysRemaining(goal.target_date)
 : null;
 const isOverdue = daysRemaining !== null && daysRemaining < 0;

 return (
 <div
 key={goal.id}
 className="flex items-center justify-between p-3 bg-surface-alt rounded-lg"
 >
 <div className="flex-1">
 <h5 className="font-medium text-content text-sm">
 {goal.title}
 </h5>
 <div className="flex items-center mt-1">
 <div className="w-16 bg-surface-alt rounded-full h-1.5 mr-3">
 <div
 className={`h-1.5 rounded-full ${getProgressColor(goal.progress_percentage)}`}
 style={{
 width: `${Math.min(goal.progress_percentage, 100)}%`,
 }}
 />
 </div>
 <span className="text-xs text-content-tertiary">
 {goal.progress_percentage.toFixed(0)}%
 </span>
 </div>
 </div>
 <div className="text-right">
 <p className="text-sm font-medium text-content">
 {goal.current_amount.toLocaleString()} /{" "}
 {goal.target_amount.toLocaleString()}
 </p>
 {goal.target_date && (
 <p
 className={`text-xs ${isOverdue ? "text-danger-base" : "text-content-tertiary"}`}
 >
 {isOverdue
 ? t("dashboard.goalsOverview.overdueDays", {
 days: Math.abs(daysRemaining!),
 })
 : t("dashboard.goalsOverview.daysRemaining", {
 days: daysRemaining,
 })}
 </p>
 )}
 </div>
 </div>
 );
 })}
 </div>
 </div>
 )}
 </div>
 );
};
