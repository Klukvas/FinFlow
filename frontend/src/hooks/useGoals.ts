import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useApiClients } from "@/hooks/useApiClients";
import {
  Goal,
  CreateGoalRequest,
  UpdateGoalRequest,
  GoalProgressUpdate,
  GoalStatistics,
  GoalFilters,
} from "@/types";
import { ErrorHandler } from "@/utils/errorHandler";

export const useGoals = () => {
  const { user } = useAuth();
  const { goals: goalsApi } = useApiClients();

  const [goals, setGoals] = useState<Goal[]>([]);
  const [statistics, setStatistics] = useState<GoalStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<GoalFilters>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchGoals = useCallback(async () => {
    if (!user?.id) return;

    try {
      setLoading(true);
      const response = await goalsApi.getGoals({
        ...filters,
        page: currentPage,
        size: 10,
      });

      if ("error" in response) {
        throw new Error(response.error);
      }

      setGoals(response.items);
      setTotalPages(response.pages);
    } catch (error) {
      ErrorHandler.handleApiError(error, "Ошибка при загрузке целей");
    } finally {
      setLoading(false);
    }
  }, [user?.id, goalsApi, filters, currentPage]);

  const fetchStatistics = useCallback(async () => {
    if (!user?.id) return;

    try {
      const stats = await goalsApi.getGoalStatistics();
      if ("error" in stats) {
        throw new Error(stats.error);
      }
      setStatistics(stats);
    } catch (error) {
      ErrorHandler.handleApiError(error, "Ошибка при загрузке статистики");
    }
  }, [user?.id, goalsApi]);

  const createGoal = useCallback(
    async (goalData: CreateGoalRequest): Promise<boolean> => {
      if (!user?.id) return false;

      try {
        const response = await goalsApi.createGoal(goalData);
        if ("error" in response) {
          throw new Error(response.error);
        }

        // Optimistic update: add new goal to the list and only refetch statistics
        setGoals((prev) => [...prev, response]);
        await fetchStatistics();
        return true;
      } catch (error) {
        ErrorHandler.handleApiError(error, "Ошибка при создании цели");
        // On error, refetch to ensure consistency
        await fetchGoals();
        return false;
      }
    },
    [user?.id, goalsApi, fetchGoals, fetchStatistics],
  );

  const updateGoal = useCallback(
    async (goalId: number, goalData: UpdateGoalRequest): Promise<boolean> => {
      try {
        const response = await goalsApi.updateGoal(goalId, goalData);
        if ("error" in response) {
          throw new Error(response.error);
        }

        // Optimistic update: update the goal in the list and only refetch statistics
        setGoals((prev) => prev.map((g) => (g.id === goalId ? response : g)));
        await fetchStatistics();
        return true;
      } catch (error) {
        ErrorHandler.handleApiError(error, "Ошибка при обновлении цели");
        // On error, refetch to ensure consistency
        await fetchGoals();
        return false;
      }
    },
    [goalsApi, fetchGoals, fetchStatistics],
  );

  const deleteGoal = useCallback(
    async (goalId: number): Promise<boolean> => {
      try {
        const response = await goalsApi.deleteGoal(goalId);
        if (response && "error" in response) {
          throw new Error(response.error);
        }

        // Optimistic update: remove the goal from the list and only refetch statistics
        setGoals((prev) => prev.filter((g) => g.id !== goalId));
        await fetchStatistics();
        return true;
      } catch (error) {
        ErrorHandler.handleApiError(error, "Ошибка при удалении цели");
        // On error, refetch to ensure consistency
        await fetchGoals();
        return false;
      }
    },
    [goalsApi, fetchGoals, fetchStatistics],
  );

  const updateProgress = useCallback(
    async (
      goalId: number,
      progressData: GoalProgressUpdate,
    ): Promise<boolean> => {
      try {
        const response = await goalsApi.updateGoalProgress(
          goalId,
          progressData,
        );
        if ("error" in response) {
          throw new Error(response.error);
        }

        // Optimistic update: update the goal in the list and only refetch statistics
        setGoals((prev) => prev.map((g) => (g.id === goalId ? response : g)));
        await fetchStatistics();
        return true;
      } catch (error) {
        ErrorHandler.handleApiError(error, "Ошибка при обновлении прогресса");
        // On error, refetch to ensure consistency
        await fetchGoals();
        return false;
      }
    },
    [goalsApi, fetchGoals, fetchStatistics],
  );

  const handleFiltersChange = useCallback((newFilters: GoalFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  useEffect(() => {
    if (user?.id) {
      Promise.all([fetchGoals(), fetchStatistics()]);
    }
  }, [user?.id, fetchGoals, fetchStatistics]);

  return {
    goals,
    statistics,
    loading,
    filters,
    currentPage,
    totalPages,
    createGoal,
    updateGoal,
    deleteGoal,
    updateProgress,
    handleFiltersChange,
    handlePageChange,
    refetch: fetchGoals,
  };
};
