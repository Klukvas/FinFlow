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
import { GoalsList } from '@/components/goals/GoalsList';
import { Modal } from '@/components/ui/shared/Modal';
import { FaBullseye } from 'react-icons/fa';
import { toast } from 'sonner';

export const Goals: React.FC = () => {
  const { t } = useTranslation();
  const {
    goals,
    statistics,
    loading,
    currentPage,
    totalPages,
    createGoal,
    updateGoal,
    deleteGoal,
    updateProgress,
    handlePageChange,
  } = useGoals();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);

  const handleCreateGoal = (goalData: CreateGoalRequest | UpdateGoalRequest) => {
    (async () => {
      const success = await createGoal(goalData as CreateGoalRequest);
      if (success) {
        setShowCreateModal(false);
        toast.success(t('goalsPage.messages.goalCreated'));
      }
    })();
  };

  const handleEditGoal = (goal: Goal) => {
    setSelectedGoal(goal);
    setShowEditModal(true);
  };

  const handleUpdateGoal = (goalData: CreateGoalRequest | UpdateGoalRequest) => {
    if (!selectedGoal) return;
    
    (async () => {
      const success = await updateGoal(selectedGoal.id, goalData as UpdateGoalRequest);
      if (success) {
        setShowEditModal(false);
        setSelectedGoal(null);
        toast.success(t('goalsPage.messages.goalUpdated'));
      }
    })();
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

  const handleProgressUpdate = (goalId: number, progressData: GoalProgressUpdate) => {
    (async () => {
      const success = await updateProgress(goalId, progressData);
      if (success) {
        setShowProgressModal(false);
        setSelectedGoal(null);
        toast.success(t('goalsPage.messages.progressUpdated'));
      }
    })();
  };

  const handleToggleStatus = async (goalId: number) => {
    // This would need to be implemented in the useGoals hook
    // For now, just log or show a message
    console.log('Toggle status for goal:', goalId);
  };

  return (
    <div className="space-y-4 sm:space-y-6 mobile-padding">
      {/* Header */}
      <div className="flex items-center gap-2 sm:gap-3">
        <FaBullseye className="text-xl sm:text-2xl theme-text-primary flex-shrink-0" />
        <h1 className="text-xl sm:text-2xl font-bold theme-text-primary truncate">{t('goalsPage.title')}</h1>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="overflow-x-auto">
          <GoalStatsComponent statistics={statistics} />
        </div>
      )}

      {/* Actions */}
      <GoalsHeader
        onShowCreateModal={() => setShowCreateModal(true)}
      />

      {/* Goals List */}
      <GoalsList
        goals={goals}
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
            goal={selectedGoal}
            onSubmit={handleUpdateGoal}
            onCancel={() => {
              setShowEditModal(false);
              setSelectedGoal(null);
            }}
          />
        )}
      </Modal>

      {/* Progress Update Modal */}
      {selectedGoal && (
        <GoalProgressModal
          goal={selectedGoal}
          isOpen={showProgressModal}
          onClose={() => {
            setShowProgressModal(false);
            setSelectedGoal(null);
          }}
          onUpdate={handleProgressUpdate}
        />
      )}
    </div>
  );
};