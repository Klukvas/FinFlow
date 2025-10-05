import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useGoals } from '@/hooks/useGoals';
import { Goal, CreateGoalRequest, UpdateGoalRequest, GoalProgressUpdate } from '@/types';
import { 
  GoalForm, 
  GoalProgressModal, 
  GoalStatistics as GoalStatsComponent 
} from '@/components/ui/goals';
import { GoalsHeader } from '@/components/goals/GoalsHeader';
import { GoalsFilters } from '@/components/goals/GoalsFilters';
import { GoalsList } from '@/components/goals/GoalsList';
import { Modal } from '@/components/ui/Modal';
import { FaBullseye } from 'react-icons/fa';
import { toast } from 'sonner';

export const Goals: React.FC = () => {
  const { t } = useTranslation();
  const {
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
  } = useGoals();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const handleCreateGoal = async (goalData: CreateGoalRequest) => {
    const success = await createGoal(goalData);
    if (success) {
      setShowCreateModal(false);
      toast.success(t('goalsPage.messages.goalCreated'));
    }
  };

  const handleEditGoal = (goal: Goal) => {
    setSelectedGoal(goal);
    setShowEditModal(true);
  };

  const handleUpdateGoal = async (goalData: UpdateGoalRequest) => {
    if (!selectedGoal) return;
    
    const success = await updateGoal(selectedGoal.id, goalData);
    if (success) {
      setShowEditModal(false);
      setSelectedGoal(null);
      toast.success(t('goalsPage.messages.goalUpdated'));
    }
  };

  const handleDeleteGoal = async (goalId: number) => {
    const success = await deleteGoal(goalId);
    if (success) {
      toast.success(t('goalsPage.messages.goalDeleted'));
    }
  };

  const handleUpdateProgress = (goal: Goal) => {
    setSelectedGoal(goal);
    setShowProgressModal(true);
  };

  const handleProgressUpdate = async (progressData: GoalProgressUpdate) => {
    if (!selectedGoal) return;
    
    const success = await updateProgress(selectedGoal.id, progressData);
    if (success) {
      setShowProgressModal(false);
      setSelectedGoal(null);
      toast.success(t('goalsPage.messages.progressUpdated'));
    }
  };

  const handleToggleStatus = async (goalId: number) => {
    // This would need to be implemented in the useGoals hook
    // For now, just log or show a message
    console.log('Toggle status for goal:', goalId);
  };

  const filteredGoals = goals.filter(goal =>
    goal.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    goal.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FaBullseye className="text-2xl theme-text-primary" />
        <h1 className="text-2xl font-bold theme-text-primary">{t('goalsPage.title')}</h1>
      </div>

      {/* Statistics */}
      {statistics && (
        <GoalStatsComponent statistics={statistics} />
      )}

      {/* Search and Actions */}
      <GoalsHeader
        onShowCreateModal={() => setShowCreateModal(true)}
        onToggleFilters={() => setShowFilters(!showFilters)}
        showFilters={showFilters}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
      />

      {/* Filters */}
      <GoalsFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
        isVisible={showFilters}
      />

      {/* Goals List */}
      <GoalsList
        goals={filteredGoals}
        loading={loading}
        onEditGoal={handleEditGoal}
        onUpdateProgress={handleUpdateProgress}
        onDeleteGoal={handleDeleteGoal}
        onToggleStatus={handleToggleStatus}
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={handlePageChange}
      />

      {/* Create Goal Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={t('goalsPage.createModalTitle')}
        size="lg"
        data-testid="create-goal-modal"
      >
        <GoalForm
          onSubmit={handleCreateGoal}
          onCancel={() => setShowCreateModal(false)}
        />
      </Modal>

      {/* Edit Goal Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedGoal(null);
        }}
        title={t('goalsPage.editModalTitle')}
        size="lg"
        data-testid="edit-goal-modal"
      >
        {selectedGoal && (
          <GoalForm
            initialData={selectedGoal}
            onSubmit={handleUpdateGoal}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedGoal(null);
            }}
          />
        )}
      </Modal>

      {/* Progress Update Modal */}
      <Modal
        isOpen={showProgressModal}
        onClose={() => {
          setShowProgressModal(false);
          setSelectedGoal(null);
        }}
        title={t('goalsPage.progressModalTitle')}
        data-testid="progress-modal"
      >
        {selectedGoal && (
          <GoalProgressModal
            goal={selectedGoal}
            onSubmit={handleProgressUpdate}
            onCancel={() => {
              setShowProgressModal(false);
              setSelectedGoal(null);
            }}
          />
        )}
      </Modal>
    </div>
  );
};