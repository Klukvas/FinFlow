import { useState, useEffect, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "@/contexts/AuthContext";
import { useApiClients } from "@/hooks/useApiClients";
import {
  Goal,
  Milestone,
  GoalStatistics,
  CreateGoalRequest,
  UpdateGoalRequest,
  GoalProgressUpdate,
} from "@/types";
import { GoalPageHeader } from "@/components/ui/goals/GoalPageHeader";
import { GoalSummaryStrip } from "@/components/ui/goals/GoalSummaryStrip";
import { GoalFilterBar } from "@/components/ui/goals/GoalFilterBar";
import { GoalTable } from "@/components/ui/goals/GoalTable";
import { GoalSidePanel } from "@/components/ui/goals/GoalSidePanel";
import { GoalForm, GoalProgressModal } from "@/components/ui/goals";
import { GoalsPageFilters } from "@/components/ui/goals/goalsHelpers";
import { Modal } from "@/components/ui/shared/Modal";
import { Card } from "@/components/ui/shared/Card";
import { Button } from "@/components/ui/shared/Button";
import { exportGoalsCsv } from "@/utils/exportGoalsCsv";
import { toast } from "sonner";
import { logger } from "@/utils/logger";

export const Goals = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { goals: goalsApi } = useApiClients();

  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Selected items
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Goal | null>(null);
  const [progressTarget, setProgressTarget] = useState<Goal | null>(null);

  // Side panel state
  const [sidePanelGoal, setSidePanelGoal] = useState<Goal | null>(null);
  const [sidePanelMilestones, setSidePanelMilestones] = useState<Milestone[]>(
    [],
  );
  const [sidePanelMilestonesLoading, setSidePanelMilestonesLoading] =
    useState(false);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);

  // Filter state
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [filters, setFilters] = useState<GoalsPageFilters>({
    page: 1,
    size: 10,
  });

  // Data state
  const [allGoals, setAllGoals] = useState<Goal[]>([]);
  const [stats, setStats] = useState<GoalStatistics | null>(null);
  const [allLoading, setAllLoading] = useState(true);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    if (!user?.id) return;
    setAllLoading(true);
    try {
      const [firstPage, statsResult] = await Promise.all([
        goalsApi.getGoals({ size: 100, page: 1 }),
        goalsApi.getGoalStatistics(),
      ]);

      if (!("error" in firstPage)) {
        let allItems = [...firstPage.items];
        if (firstPage.pages > 1) {
          const remaining = await Promise.all(
            Array.from({ length: firstPage.pages - 1 }, (_, i) =>
              goalsApi.getGoals({ size: 100, page: i + 2 }),
            ),
          );
          for (const page of remaining) {
            if (!("error" in page)) allItems = [...allItems, ...page.items];
          }
        }
        setAllGoals(allItems);
      }
      if (!("error" in statsResult)) setStats(statsResult);
    } catch (err) {
      logger.error("Error loading goals data:", err);
    } finally {
      setAllLoading(false);
    }
  }, [user?.id, goalsApi]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  // Client-side filtering
  const filteredGoals = useMemo(() => {
    let result = [...allGoals];

    if (filters.status && filters.status !== "all") {
      result = result.filter((g) => g.status === filters.status);
    }
    if (filters.goal_type && filters.goal_type !== "all") {
      result = result.filter((g) => g.goal_type === filters.goal_type);
    }
    if (filters.priority && filters.priority !== "all") {
      result = result.filter((g) => g.priority === filters.priority);
    }
    if (filters.search && filters.search.trim()) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (g) =>
          g.title.toLowerCase().includes(q) ||
          (g.description && g.description.toLowerCase().includes(q)),
      );
    }

    return result;
  }, [allGoals, filters]);

  // Client-side pagination
  const paginatedGoals = useMemo(() => {
    const start = ((filters.page || 1) - 1) * (filters.size || 10);
    return filteredGoals.slice(start, start + (filters.size || 10));
  }, [filteredGoals, filters.page, filters.size]);

  const totalItems = filteredGoals.length;
  const totalPages = Math.ceil(totalItems / (filters.size || 10));

  // Keyboard shortcut: N to add
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "n" || e.key === "N") {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
        e.preventDefault();
        setIsCreateModalOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Side panel
  const openSidePanel = async (goal: Goal) => {
    setSidePanelGoal(goal);
    setSidePanelOpen(true);
    if (goal.is_milestone_based) {
      setSidePanelMilestonesLoading(true);
      try {
        const result = await goalsApi.getMilestones(goal.id);
        if (!("error" in result)) {
          setSidePanelMilestones(result);
        } else {
          setSidePanelMilestones([]);
        }
      } catch {
        setSidePanelMilestones([]);
      } finally {
        setSidePanelMilestonesLoading(false);
      }
    } else {
      setSidePanelMilestones([]);
    }
  };

  const closeSidePanel = () => {
    setSidePanelOpen(false);
    setTimeout(() => {
      setSidePanelGoal(null);
      setSidePanelMilestones([]);
    }, 300);
  };

  // Create handler
  const handleCreate = async (data: CreateGoalRequest | UpdateGoalRequest) => {
    const result = await goalsApi.createGoal(data as CreateGoalRequest);
    if (result && "error" in result) return;
    setIsCreateModalOpen(false);
    toast.success(t("goalsPage.messages.goalCreated"));
    fetchAllData();
  };

  // Edit handler
  const handleEdit = async (data: CreateGoalRequest | UpdateGoalRequest) => {
    if (!selectedGoal) return;
    const result = await goalsApi.updateGoal(
      selectedGoal.id,
      data as UpdateGoalRequest,
    );
    if (result && "error" in result) return;
    setIsEditModalOpen(false);
    setSelectedGoal(null);
    toast.success(t("goalsPage.messages.goalUpdated"));
    fetchAllData();
    // Refresh side panel if open for the same goal
    if (sidePanelGoal && sidePanelGoal.id === selectedGoal.id) {
      const updated = await goalsApi.getGoal(selectedGoal.id);
      if (!("error" in updated)) setSidePanelGoal(updated);
    }
  };

  // Progress handler
  const handleProgressUpdate = async (
    goalId: number,
    progressData: GoalProgressUpdate,
  ) => {
    const result = await goalsApi.updateGoalProgress(goalId, progressData);
    if (result && "error" in result) return;
    setIsProgressModalOpen(false);
    setProgressTarget(null);
    toast.success(t("goalsPage.messages.progressUpdated"));
    fetchAllData();
    // Refresh side panel if open for the same goal
    if (sidePanelGoal && sidePanelGoal.id === goalId) {
      const updated = await goalsApi.getGoal(goalId);
      if (!("error" in updated)) setSidePanelGoal(updated);
    }
  };

  // Delete handler
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const result = await goalsApi.deleteGoal(deleteTarget.id);
      if (result && "error" in result) {
        toast.error(t("goalsPage.messages.deleteFailed"));
        return;
      }
      setAllGoals((prev) => prev.filter((g) => g.id !== deleteTarget.id));
      if (sidePanelGoal?.id === deleteTarget.id) closeSidePanel();
      const statsResult = await goalsApi.getGoalStatistics();
      if (!("error" in statsResult)) setStats(statsResult);
      toast.success(t("goalsPage.messages.goalDeleted"));
    } catch (err) {
      logger.error("Error deleting goal:", err);
      toast.error(t("goalsPage.messages.deleteFailed"));
    } finally {
      setIsDeleting(false);
      setIsDeleteModalOpen(false);
      setDeleteTarget(null);
    }
  };

  // Pause/Resume handler
  const handlePauseResume = async (goal: Goal) => {
    try {
      const isPaused = goal.status === "PAUSED";
      const newStatus = isPaused ? "ACTIVE" : "PAUSED";
      const result = await goalsApi.updateGoal(goal.id, { status: newStatus });

      if (result && "error" in result) {
        toast.error(t("goalsPage.messages.statusChangeFailed"));
        return;
      }

      // Update local state
      const updatedGoal = await goalsApi.getGoal(goal.id);
      if (!("error" in updatedGoal)) {
        setAllGoals((prev) =>
          prev.map((g) => (g.id === goal.id ? updatedGoal : g)),
        );
        if (sidePanelGoal?.id === goal.id) setSidePanelGoal(updatedGoal);
      }

      const statsResult = await goalsApi.getGoalStatistics();
      if (!("error" in statsResult)) setStats(statsResult);

      toast.success(t("goalsPage.messages.statusChanged"));
    } catch (err) {
      logger.error("Error toggling goal status:", err);
      toast.error(t("goalsPage.messages.statusChangeFailed"));
    }
  };

  // Export CSV
  const handleExportCsv = () => {
    exportGoalsCsv(filteredGoals);
  };

  // Filter change
  const handleFiltersChange = (newFilters: GoalsPageFilters) => {
    setFilters(newFilters);
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handlePageSizeChange = (size: number) => {
    setFilters((prev) => ({ ...prev, size, page: 1 }));
  };

  const hasActiveFilters =
    (filters.status && filters.status !== "all") ||
    (filters.goal_type && filters.goal_type !== "all") ||
    (filters.priority && filters.priority !== "all") ||
    (filters.search && filters.search.trim() !== "");

  return (
    <div className="min-h-screen bg-surface p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-6">
        {/* Header */}
        <GoalPageHeader
          onAdd={() => setIsCreateModalOpen(true)}
          onToggleFilters={() => setFiltersVisible((v) => !v)}
          onExportCsv={handleExportCsv}
          filtersActive={Boolean(hasActiveFilters)}
        />

        {/* KPI Strip */}
        <GoalSummaryStrip stats={stats} loading={allLoading} />

        {/* Filter Bar */}
        <GoalFilterBar
          filters={filters}
          onFiltersChange={handleFiltersChange}
          isVisible={filtersVisible}
        />

        {/* Table */}
        <Card>
          <GoalTable
            goals={paginatedGoals}
            loading={allLoading}
            currentPage={filters.page || 1}
            totalPages={totalPages}
            pageSize={filters.size || 10}
            totalItems={totalItems}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
            onRowClick={openSidePanel}
            onUpdateProgress={(goal) => {
              setProgressTarget(goal);
              setIsProgressModalOpen(true);
            }}
            onEdit={(goal) => {
              setSelectedGoal(goal);
              setIsEditModalOpen(true);
            }}
            onDelete={(goal) => {
              setDeleteTarget(goal);
              setIsDeleteModalOpen(true);
            }}
            emptyMessage={
              hasActiveFilters
                ? t("goalsPage.filters.noMatchFilters")
                : undefined
            }
          />
        </Card>

        {/* Side Panel */}
        <GoalSidePanel
          goal={sidePanelGoal}
          milestones={sidePanelMilestones}
          milestonesLoading={sidePanelMilestonesLoading}
          isOpen={sidePanelOpen}
          onClose={closeSidePanel}
          onUpdateProgress={() => {
            if (sidePanelGoal) {
              setProgressTarget(sidePanelGoal);
              setIsProgressModalOpen(true);
            }
          }}
          onEdit={() => {
            if (sidePanelGoal) {
              setSelectedGoal(sidePanelGoal);
              setIsEditModalOpen(true);
            }
          }}
          onDelete={() => {
            if (sidePanelGoal) {
              setDeleteTarget(sidePanelGoal);
              setIsDeleteModalOpen(true);
            }
          }}
          onPauseResume={() => {
            if (sidePanelGoal) handlePauseResume(sidePanelGoal);
          }}
        />

        {/* Create Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title={t("goalsPage.createModalTitle")}
          size="lg"
        >
          <GoalForm
            onSubmit={handleCreate}
            onCancel={() => setIsCreateModalOpen(false)}
          />
        </Modal>

        {/* Edit Modal */}
        <Modal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false);
            setSelectedGoal(null);
          }}
          title={t("goalsPage.editModalTitle")}
          size="lg"
        >
          {selectedGoal && (
            <GoalForm
              goal={selectedGoal}
              onSubmit={handleEdit}
              onCancel={() => {
                setIsEditModalOpen(false);
                setSelectedGoal(null);
              }}
            />
          )}
        </Modal>

        {/* Progress Update Modal */}
        {progressTarget && (
          <GoalProgressModal
            goal={progressTarget}
            isOpen={isProgressModalOpen}
            onClose={() => {
              setIsProgressModalOpen(false);
              setProgressTarget(null);
            }}
            onUpdate={handleProgressUpdate}
          />
        )}

        {/* Delete Confirmation Modal */}
        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => {
            setIsDeleteModalOpen(false);
            setDeleteTarget(null);
          }}
          title={t("goalsPage.deleteConfirmModal.title")}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-sm text-content-secondary">
              {t("goalsPage.deleteConfirmModal.message")}
            </p>
            {deleteTarget && (
              <div className="bg-surface-alt rounded-lg p-3 text-sm">
                <span className="font-medium text-content">
                  {deleteTarget.title}
                </span>
                <span className="ml-2 font-semibold tabular-nums text-content">
                  {deleteTarget.target_amount.toLocaleString("uk-UA", {
                    minimumFractionDigits: 2,
                  })}{" "}
                  {deleteTarget.currency}
                </span>
              </div>
            )}
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsDeleteModalOpen(false);
                  setDeleteTarget(null);
                }}
              >
                {t("goalsPage.deleteConfirmModal.cancel")}
              </Button>
              <Button
                variant="danger"
                size="sm"
                loading={isDeleting}
                onClick={handleDeleteConfirm}
                data-testid="confirm-delete-goal-button"
              >
                {t("goalsPage.deleteConfirmModal.confirm")}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </div>
  );
};

export default Goals;
