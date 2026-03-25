import { Goal, GoalStatus, GoalType, GoalPriority } from "@/types/goal";

export interface GoalsPageFilters {
  page: number;
  size: number;
  status?: GoalStatus | "all";
  goal_type?: GoalType | "all";
  priority?: GoalPriority | "all";
  search?: string;
}

export type TrackStatus =
  | "on_track"
  | "slightly_behind"
  | "off_track"
  | "no_date";

// Badge variant mappings
export const getStatusBadgeVariant = (status: GoalStatus): string => {
  switch (status) {
    case "ACTIVE":
      return "success";
    case "COMPLETED":
      return "info";
    case "PAUSED":
      return "warning";
    case "CANCELLED":
      return "destructive";
  }
};

export const getPriorityBadgeVariant = (priority: GoalPriority): string => {
  switch (priority) {
    case "LOW":
      return "secondary";
    case "MEDIUM":
      return "default";
    case "HIGH":
      return "warning";
    case "CRITICAL":
      return "destructive";
  }
};

// I18n maps
export const STATUS_I18N_MAP: Record<GoalStatus, string> = {
  ACTIVE: "goalsPage.filters.active",
  COMPLETED: "goalsPage.filters.completed",
  PAUSED: "goalsPage.filters.paused",
  CANCELLED: "goalsPage.filters.cancelled",
};

export const PRIORITY_I18N_MAP: Record<GoalPriority, string> = {
  LOW: "goalsPage.filters.low",
  MEDIUM: "goalsPage.filters.medium",
  HIGH: "goalsPage.filters.high",
  CRITICAL: "goalsPage.filters.critical",
};

export const GOAL_TYPE_I18N_MAP: Record<GoalType, string> = {
  SAVINGS: "goalsPage.filters.savings",
  DEBT_PAYOFF: "goalsPage.filters.debtPayoff",
  INVESTMENT: "goalsPage.filters.investment",
  EXPENSE_REDUCTION: "goalsPage.filters.expenseReduction",
  INCOME_INCREASE: "goalsPage.filters.incomeIncrease",
  EMERGENCY_FUND: "goalsPage.filters.emergencyFund",
};

export const TRACK_STATUS_I18N_MAP: Record<TrackStatus, string> = {
  on_track: "goalsPage.table.trackStatus.onTrack",
  slightly_behind: "goalsPage.table.trackStatus.slightlyBehind",
  off_track: "goalsPage.table.trackStatus.offTrack",
  no_date: "goalsPage.table.trackStatus.noDate",
};

// On-track logic
export const getTrackStatus = (goal: Goal): TrackStatus => {
  if (!goal.target_date) return "no_date";
  if (goal.status === "COMPLETED") return "on_track";

  const now = Date.now();
  const start = new Date(goal.start_date).getTime();
  const end = new Date(goal.target_date).getTime();

  if (end <= start) return "no_date";
  if (now >= end)
    return goal.progress_percentage >= 100 ? "on_track" : "off_track";

  const timeElapsedPct = ((now - start) / (end - start)) * 100;
  const progressPct = goal.progress_percentage;

  if (progressPct >= timeElapsedPct) return "on_track";
  if (progressPct >= timeElapsedPct - 15) return "slightly_behind";
  return "off_track";
};

export const getTrackStatusColor = (status: TrackStatus): string => {
  switch (status) {
    case "on_track":
      return "text-[var(--success)]";
    case "slightly_behind":
      return "text-[var(--warning)]";
    case "off_track":
      return "text-[var(--danger)]";
    case "no_date":
      return "text-[var(--text-tertiary)]";
  }
};

export const getTrackDotColor = (status: TrackStatus): string => {
  switch (status) {
    case "on_track":
      return "bg-[var(--success)]";
    case "slightly_behind":
      return "bg-[var(--warning)]";
    case "off_track":
      return "bg-[var(--danger)]";
    case "no_date":
      return "bg-[var(--text-tertiary)]";
  }
};

export const getProgressBarColor = (percentage: number): string => {
  if (percentage >= 80) return "bg-[var(--success)]/70";
  if (percentage >= 60) return "bg-[var(--accent)]/70";
  if (percentage >= 40) return "bg-[var(--warning)]/70";
  if (percentage >= 20) return "bg-[var(--warning)]/70";
  return "bg-[var(--danger)]/70";
};

// Utility functions
export const getDaysRemaining = (targetDate?: string): number | null => {
  if (!targetDate) return null;
  const target = new Date(targetDate);
  const today = new Date();
  const diffTime = target.getTime() - today.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

export const getRequiredMonthlySaving = (goal: Goal): number | null => {
  if (!goal.target_date) return null;
  const remaining = goal.target_amount - goal.current_amount;
  if (remaining <= 0) return 0;

  const now = new Date();
  const target = new Date(goal.target_date);
  const monthsRemaining =
    (target.getFullYear() - now.getFullYear()) * 12 +
    (target.getMonth() - now.getMonth());

  if (monthsRemaining <= 0) return remaining;
  return Math.ceil((remaining / monthsRemaining) * 100) / 100;
};

export const formatAmount = (amount: number, currency: string): string => {
  return (
    new Intl.NumberFormat("uk-UA", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount) +
    " " +
    currency
  );
};

export const formatDate = (dateString?: string | null): string => {
  if (!dateString) return "\u2014";
  return new Date(dateString).toLocaleDateString("uk-UA");
};
