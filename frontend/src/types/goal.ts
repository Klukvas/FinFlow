export type GoalType = 'SAVINGS' | 'DEBT_PAYOFF' | 'INVESTMENT' | 'EXPENSE_REDUCTION' | 'INCOME_INCREASE' | 'EMERGENCY_FUND';

export type GoalStatus = 'ACTIVE' | 'COMPLETED' | 'PAUSED' | 'CANCELLED';

export type GoalPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Goal {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  goal_type: GoalType;
  priority: GoalPriority;
  status: GoalStatus;
  target_amount: number;
  current_amount: number;
  currency: string;
  progress_percentage: number;
  start_date: string;
  target_date?: string;
  is_milestone_based: boolean;
  created_at: string;
  updated_at?: string;
  milestones?: Milestone[];
}

export interface Milestone {
  id: number;
  goal_id: number;
  title: string;
  description?: string;
  target_amount: number;
  current_amount: number;
  is_completed: boolean;
  completed_at?: string;
  order_index: number;
  created_at: string;
  updated_at?: string;
}

export interface CreateGoalRequest {
  title: string;
  description?: string;
  goal_type: GoalType;
  priority: GoalPriority;
  target_amount: number;
  currency: string;
  target_date?: string;
  is_milestone_based: boolean;
}

export interface UpdateGoalRequest {
  title?: string;
  description?: string;
  goal_type?: GoalType;
  priority?: GoalPriority;
  target_amount?: number;
  currency?: string;
  target_date?: string;
  status?: GoalStatus;
  is_milestone_based?: boolean;
}

export interface GoalProgressUpdate {
  current_amount: number;
}

export interface CreateMilestoneRequest {
  title: string;
  description?: string;
  target_amount: number;
  order_index: number;
}

export interface UpdateMilestoneRequest {
  title?: string;
  description?: string;
  target_amount?: number;
  order_index?: number;
}

export interface MilestoneProgressUpdate {
  current_amount: number;
}

export interface GoalListResponse {
  items: Goal[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface GoalStatistics {
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  total_target_amount: number;
  total_current_amount: number;
  overall_progress: number;
  goals_by_type: Record<string, number>;
  goals_by_priority: Record<string, number>;
}

export interface GoalFilters {
  status?: GoalStatus;
  goal_type?: GoalType;
  priority?: GoalPriority;
  search?: string;
}

// Helper types for UI
export interface GoalWithProgress extends Goal {
  daysRemaining?: number;
  isOverdue?: boolean;
  progressColor?: string;
}

export interface GoalFormData {
  title: string;
  description: string;
  goal_type: GoalType;
  priority: GoalPriority;
  target_amount: string;
  currency: string;
  target_date: string;
  is_milestone_based: boolean;
}

export interface MilestoneFormData {
  title: string;
  description: string;
  target_amount: string;
  order_index: number;
}

// Constants for UI
export const GOAL_TYPE_LABELS: Record<GoalType, string> = {
  SAVINGS: 'Накопления',
  DEBT_PAYOFF: 'Погашение долга',
  INVESTMENT: 'Инвестиции',
  EXPENSE_REDUCTION: 'Сокращение расходов',
  INCOME_INCREASE: 'Увеличение дохода',
  EMERGENCY_FUND: 'Резервный фонд'
};

export const GOAL_STATUS_LABELS: Record<GoalStatus, string> = {
  ACTIVE: 'Активная',
  COMPLETED: 'Завершена',
  PAUSED: 'Приостановлена',
  CANCELLED: 'Отменена'
};

export const GOAL_PRIORITY_LABELS: Record<GoalPriority, string> = {
  LOW: 'Низкий',
  MEDIUM: 'Средний',
  HIGH: 'Высокий',
  CRITICAL: 'Критический'
};

export const GOAL_PRIORITY_COLORS: Record<GoalPriority, string> = {
  LOW: 'text-gray-500',
  MEDIUM: 'text-blue-500',
  HIGH: 'text-orange-500',
  CRITICAL: 'text-red-500'
};

export const GOAL_STATUS_COLORS: Record<GoalStatus, string> = {
  ACTIVE: 'text-green-500',
  COMPLETED: 'text-blue-500',
  PAUSED: 'text-yellow-500',
  CANCELLED: 'text-gray-500'
};
