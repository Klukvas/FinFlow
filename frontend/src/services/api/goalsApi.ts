import { 
  Goal, 
  CreateGoalRequest, 
  UpdateGoalRequest, 
  GoalProgressUpdate,
  GoalListResponse, 
  GoalStatistics,
  GoalFilters,
  Milestone,
  CreateMilestoneRequest,
  UpdateMilestoneRequest,
  MilestoneProgressUpdate
} from '@/types';
import { AuthHttpClient, ApiError } from './AuthHttpClient';
import { config } from '@/config/env';

export class GoalsApiClient {
  private httpClient: AuthHttpClient;

  constructor(
    getToken: () => string | null,
    refreshToken: () => Promise<boolean>
  ) {
    this.httpClient = new AuthHttpClient(
      `${config.api.goalsServiceUrl}/api/v1/goals`,
      getToken,
      refreshToken
    );
  }

  async getGoals(
    filters?: GoalFilters & { page?: number; size?: number }
  ): Promise<GoalListResponse | ApiError> {
    const params = new URLSearchParams();
    
    if (filters?.page) params.append('skip', String((filters.page - 1) * (filters.size || 10)));
    if (filters?.size) params.append('limit', String(filters.size));
    if (filters?.status) params.append('status', filters.status);
    if (filters?.goal_type) params.append('goal_type', filters.goal_type);
    if (filters?.priority) params.append('priority', filters.priority);
    
    return this.httpClient.get<GoalListResponse>(`/?${params.toString()}`);
  }

  async getGoal(goalId: number): Promise<Goal | ApiError> {
    return this.httpClient.get<Goal>(`/${goalId}`);
  }

  async createGoal(goalData: CreateGoalRequest): Promise<Goal | ApiError> {
    return this.httpClient.post<Goal>('/', goalData);
  }

  async updateGoal(goalId: number, goalData: UpdateGoalRequest): Promise<Goal | ApiError> {
    return this.httpClient.put<Goal>(`/${goalId}`, goalData);
  }

  async updateGoalProgress(goalId: number, progressData: GoalProgressUpdate): Promise<Goal | ApiError> {
    return this.httpClient.patch<Goal>(`/${goalId}/progress`, progressData);
  }

  async deleteGoal(goalId: number): Promise<void | ApiError> {
    return this.httpClient.delete<void>(`/${goalId}`);
  }

  async getGoalStatistics(): Promise<GoalStatistics | ApiError> {
    return this.httpClient.get<GoalStatistics>('/statistics/overview');
  }

  // Milestones
  async getMilestones(goalId: number): Promise<Milestone[] | ApiError> {
    return this.httpClient.get<Milestone[]>(`/${goalId}/milestones`);
  }

  async createMilestone(goalId: number, milestoneData: CreateMilestoneRequest): Promise<Milestone | ApiError> {
    return this.httpClient.post<Milestone>(`/${goalId}/milestones`, milestoneData);
  }

  async updateMilestone(goalId: number, milestoneId: number, milestoneData: UpdateMilestoneRequest): Promise<Milestone | ApiError> {
    return this.httpClient.put<Milestone>(`/${goalId}/milestones/${milestoneId}`, milestoneData);
  }

  async updateMilestoneProgress(goalId: number, milestoneId: number, progressData: MilestoneProgressUpdate): Promise<Milestone | ApiError> {
    return this.httpClient.patch<Milestone>(`/${goalId}/milestones/${milestoneId}/progress`, progressData);
  }

  async deleteMilestone(goalId: number, milestoneId: number): Promise<void | ApiError> {
    return this.httpClient.delete<void>(`/${goalId}/milestones/${milestoneId}`);
  }
}

