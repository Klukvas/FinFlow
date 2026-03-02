from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.goal import Goal, GoalStatus, GoalType, GoalPriority
from app.models.milestone import Milestone
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalProgressUpdate,
    MilestoneCreate, MilestoneUpdate, MilestoneProgressUpdate
)
from shared.clients import SubscriptionClient
from shared.clients import UserServiceClient
from shared.clients import CurrencyServiceClient
from shared.auth import WorkspaceAuthorizationMixin
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, GoalCreationError, GoalUpdateError,
    GoalDeletionError, GoalRetrievalError, GoalStatisticsError, GoalProgressError,
    MilestoneNotFoundError, MilestoneValidationError, MilestoneCreationError,
    MilestoneRetrievalError, MilestoneProgressUpdateError, GoalLimitExceededError,
    GoalReadOnlyExcessError
)
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class GoalService(WorkspaceAuthorizationMixin):
    def __init__(self, db: Session):
        super().__init__(
            access_denied_error=GoalValidationError,
            workspace_mismatch_error=GoalValidationError,
        )
        self.db = db
        self.subscription_client = SubscriptionClient.get_instance()
        self.user_client = UserServiceClient.get_instance()
        self.currency_client = CurrencyServiceClient.get_instance()

    def create_goal(self, user_id: int, workspace_id: UUID, goal_data: GoalCreate) -> Goal:
        """Create a new financial goal"""
        try:
            # Authorize workspace access (member role required for creating)
            self.authorize_workspace_access(workspace_id, user_id, "member", "create_goal")
            
            # Check subscription limits before creating
            current_count = self.db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.workspace_id == workspace_id
            ).count()
            can_create, limit = self.subscription_client.check_limit(user_id, current_count, "goals")
            if not can_create:
                raise GoalLimitExceededError(current_count, limit or 0)
            
            goal = Goal(
                user_id=user_id,
                workspace_id=workspace_id,
                **goal_data.dict()
            )
            
            self.db.add(goal)
            self.db.commit()
            self.db.refresh(goal)
            
            logger.info(f"Created goal {goal.id} for user {user_id} in workspace {workspace_id}")
            return goal
            
        except GoalValidationError:
            raise
        except GoalLimitExceededError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating goal for user {user_id}: {str(e)}")
            raise GoalCreationError(f"Failed to create goal: {str(e)}")

    def get_goals(
        self, 
        user_id: int,
        workspace_id: UUID,
        skip: int = 0, 
        limit: int = 100,
        status: Optional[GoalStatus] = None,
        goal_type: Optional[GoalType] = None,
        priority: Optional[GoalPriority] = None
    ) -> List[Goal]:
        """Get user's goals with optional filtering"""
        try:
            # Authorize workspace access (viewer role sufficient for reading)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_goals")
            
            query = self.db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.workspace_id == workspace_id
            )
            
            if status:
                query = query.filter(Goal.status == status)
            if goal_type:
                query = query.filter(Goal.goal_type == goal_type)
            if priority:
                query = query.filter(Goal.priority == priority)
                
            goals = query.offset(skip).limit(limit).all()
            return goals
            
        except GoalValidationError:
            raise
        except Exception as e:
            logger.error(f"Error fetching goals for user {user_id}: {str(e)}")
            raise GoalRetrievalError(f"Failed to fetch goals: {str(e)}")

    def get_goal(self, user_id: int, workspace_id: UUID, goal_id: int) -> Goal:
        """Get a specific goal by ID"""
        # Authorize workspace access (viewer role sufficient for reading)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_goal")
        
        goal = self.db.query(Goal).filter(
            and_(
                Goal.id == goal_id, 
                Goal.user_id == user_id,
                Goal.workspace_id == workspace_id
            )
        ).first()
        
        if not goal:
            raise GoalNotFoundError(f"Goal {goal_id} not found for user {user_id}")
        
        return goal

    def _get_ordered_ids(self, workspace_id: UUID) -> list:
        rows = self.db.query(Goal.id).filter(
            Goal.workspace_id == workspace_id
        ).order_by(Goal.created_at.asc(), Goal.id.asc()).all()
        return [row[0] for row in rows]

    def _check_modify_allowed(self, record_id: int, user_id: int, workspace_id: UUID):
        ordered_ids = self._get_ordered_ids(workspace_id)
        if not self.subscription_client.check_modify_allowed(user_id, record_id, "goals", ordered_ids):
            features = self.subscription_client.get_user_features(user_id) or {}
            limit = features.get("goals", {}).get("limit_value", 0)
            raise GoalReadOnlyExcessError(record_id, len(ordered_ids), limit)

    def update_goal(self, user_id: int, workspace_id: UUID, goal_id: int, goal_data: GoalUpdate) -> Goal:
        """Update an existing goal"""
        try:
            # Authorize workspace access (member role required for updating)
            self.authorize_workspace_access(workspace_id, user_id, "member", "update_goal")

            goal = self._get_goal_internal(user_id, workspace_id, goal_id)

            self._check_modify_allowed(goal_id, user_id, workspace_id)

            update_data = goal_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(goal, field, value)
            
            goal.update_progress()
            self.db.commit()
            self.db.refresh(goal)
            
            logger.info(f"Updated goal {goal_id} for user {user_id}")
            return goal
            
        except GoalNotFoundError:
            raise
        except GoalValidationError:
            raise
        except GoalReadOnlyExcessError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating goal {goal_id} for user {user_id}: {str(e)}")
            raise GoalUpdateError(f"Failed to update goal: {str(e)}")

    def _get_goal_internal(self, user_id: int, workspace_id: UUID, goal_id: int) -> Goal:
        """Get a specific goal by ID (internal, no authorization check)"""
        goal = self.db.query(Goal).filter(
            and_(
                Goal.id == goal_id, 
                Goal.user_id == user_id,
                Goal.workspace_id == workspace_id
            )
        ).first()
        
        if not goal:
            raise GoalNotFoundError(f"Goal {goal_id} not found for user {user_id}")
        
        return goal

    def update_goal_progress(self, user_id: int, workspace_id: UUID, goal_id: int, progress_data: GoalProgressUpdate) -> Goal:
        """Update goal progress"""
        try:
            # Authorize workspace access (member role required for updating)
            self.authorize_workspace_access(workspace_id, user_id, "member", "update_goal_progress")
            
            goal = self._get_goal_internal(user_id, workspace_id, goal_id)

            self._check_modify_allowed(goal_id, user_id, workspace_id)

            goal.current_amount = progress_data.current_amount
            goal.update_progress()
            
            self.db.commit()
            self.db.refresh(goal)
            
            logger.info(f"Updated progress for goal {goal_id}: {goal.progress_percentage}%")
            return goal
            
        except GoalNotFoundError:
            raise
        except GoalValidationError:
            raise
        except GoalReadOnlyExcessError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating progress for goal {goal_id}: {str(e)}")
            raise GoalProgressError(f"Failed to update goal progress: {str(e)}")

    def delete_goal(self, user_id: int, workspace_id: UUID, goal_id: int) -> bool:
        """Delete a goal"""
        try:
            # Authorize workspace access (member role required for deleting)
            self.authorize_workspace_access(workspace_id, user_id, "member", "delete_goal")
            
            goal = self._get_goal_internal(user_id, workspace_id, goal_id)
            
            self.db.delete(goal)
            self.db.commit()
            
            logger.info(f"Deleted goal {goal_id} for user {user_id}")
            return True
            
        except GoalNotFoundError:
            raise
        except GoalValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting goal {goal_id} for user {user_id}: {str(e)}")
            raise GoalDeletionError(f"Failed to delete goal: {str(e)}")

    def get_goal_statistics(self, user_id: int, workspace_id: UUID) -> Dict[str, Any]:
        """Get goal statistics for a user"""
        try:
            # Authorize workspace access (viewer role sufficient for reading stats)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_goal_statistics")
            
            goals = self.db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.workspace_id == workspace_id
            ).all()
            
            # Get user's base currency
            try:
                user_currency = self.user_client.get_user_base_currency(user_id)
            except Exception as e:
                logger.warning(f"Could not fetch user currency for user {user_id}: {str(e)}, defaulting to USD")
                user_currency = settings.DEFAULT_CURRENCY
            
            if not goals:
                return {
                    "total_goals": 0,
                    "active_goals": 0,
                    "completed_goals": 0,
                    "total_target_amount": 0.0,
                    "total_current_amount": 0.0,
                    "overall_progress": 0.0,
                    "currency": user_currency,
                    "goals_by_type": {},
                    "goals_by_priority": {}
                }
            
            total_goals = len(goals)
            active_goals = len([g for g in goals if g.status == GoalStatus.ACTIVE])
            completed_goals = len([g for g in goals if g.status == GoalStatus.COMPLETED])
            
            # Convert and sum amounts to user's base currency
            total_target_amount = Decimal('0.0')
            total_current_amount = Decimal('0.0')
            
            for goal in goals:
                # Convert target amount if needed
                goal_target = goal.target_amount
                goal_current = goal.current_amount
                goal_currency = goal.currency or settings.DEFAULT_CURRENCY
                
                if goal_currency != user_currency:
                    # Convert target amount
                    converted_target = self.currency_client.convert_amount(
                        goal_target, goal_currency, user_currency
                    )
                    if converted_target is not None:
                        goal_target = converted_target
                    
                    # Convert current amount
                    converted_current = self.currency_client.convert_amount(
                        goal_current, goal_currency, user_currency
                    )
                    if converted_current is not None:
                        goal_current = converted_current
                
                total_target_amount += goal_target
                total_current_amount += goal_current
            
            overall_progress = (total_current_amount / total_target_amount * 100) if total_target_amount > 0 else 0.0
            
            # Group by type
            goals_by_type = {}
            for goal_type in GoalType:
                count = len([g for g in goals if g.goal_type == goal_type])
                if count > 0:
                    goals_by_type[goal_type.value] = count
            
            # Group by priority
            goals_by_priority = {}
            for priority in GoalPriority:
                count = len([g for g in goals if g.priority == priority])
                if count > 0:
                    goals_by_priority[priority.value] = count
            
            return {
                "total_goals": total_goals,
                "active_goals": active_goals,
                "completed_goals": completed_goals,
                "total_target_amount": round(total_target_amount, 2),
                "total_current_amount": round(total_current_amount, 2),
                "overall_progress": round(overall_progress, 2),
                "currency": user_currency,
                "goals_by_type": goals_by_type,
                "goals_by_priority": goals_by_priority
            }
            
        except GoalValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting goal statistics for user {user_id}: {str(e)}")
            raise GoalStatisticsError(f"Failed to get goal statistics: {str(e)}")

    # Milestone methods
    def create_milestone(self, user_id: int, workspace_id: UUID, goal_id: int, milestone_data: MilestoneCreate) -> Milestone:
        """Create a milestone for a goal"""
        try:
            # Authorize workspace access (member role required for creating)
            self.authorize_workspace_access(workspace_id, user_id, "member", "create_milestone")
            
            # Verify goal ownership
            goal = self._get_goal_internal(user_id, workspace_id, goal_id)
            
            milestone = Milestone(
                goal_id=goal_id,
                **milestone_data.dict()
            )
            
            self.db.add(milestone)
            self.db.commit()
            self.db.refresh(milestone)
            
            logger.info(f"Created milestone {milestone.id} for goal {goal_id}")
            return milestone
            
        except GoalNotFoundError:
            raise
        except GoalValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating milestone for goal {goal_id}: {str(e)}")
            raise MilestoneCreationError(f"Failed to create milestone: {str(e)}")

    def get_milestones(self, user_id: int, workspace_id: UUID, goal_id: int) -> List[Milestone]:
        """Get milestones for a goal"""
        try:
            # Authorize workspace access (viewer role sufficient for reading)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_milestones")
            
            # Verify goal ownership
            goal = self._get_goal_internal(user_id, workspace_id, goal_id)
            
            milestones = self.db.query(Milestone).filter(
                Milestone.goal_id == goal_id
            ).order_by(Milestone.order_index).all()
            
            return milestones
            
        except GoalNotFoundError:
            raise
        except GoalValidationError:
            raise
        except Exception as e:
            logger.error(f"Error fetching milestones for goal {goal_id}: {str(e)}")
            raise MilestoneRetrievalError(f"Failed to fetch milestones: {str(e)}")

    def update_milestone_progress(self, user_id: int, workspace_id: UUID, goal_id: int, milestone_id: int, progress_data: MilestoneProgressUpdate) -> Milestone:
        """Update milestone progress"""
        try:
            # Authorize workspace access (member role required for updating)
            self.authorize_workspace_access(workspace_id, user_id, "member", "update_milestone_progress")
            
            # Verify goal ownership
            goal = self._get_goal_internal(user_id, workspace_id, goal_id)
            
            milestone = self.db.query(Milestone).filter(
                and_(Milestone.id == milestone_id, Milestone.goal_id == goal_id)
            ).first()
            
            if not milestone:
                raise MilestoneNotFoundError(f"Milestone {milestone_id} not found for goal {goal_id}")
            
            milestone.current_amount = progress_data.current_amount
            milestone.update_progress()
            
            self.db.commit()
            self.db.refresh(milestone)
            
            logger.info(f"Updated progress for milestone {milestone_id}: {milestone.calculate_progress()}%")
            return milestone
            
        except (GoalNotFoundError, MilestoneNotFoundError):
            raise
        except GoalValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating milestone progress: {str(e)}")
            raise MilestoneProgressUpdateError(f"Failed to update milestone progress: {str(e)}")
