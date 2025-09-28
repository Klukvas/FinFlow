from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any
from app.models.goal import Goal, GoalStatus, GoalType, GoalPriority
from app.models.milestone import Milestone
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalProgressUpdate,
    MilestoneCreate, MilestoneUpdate, MilestoneProgressUpdate
)
from app.exceptions.goal_exceptions import (
    GoalNotFoundError, GoalValidationError, 
    MilestoneNotFoundError, MilestoneValidationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GoalService:
    def __init__(self, db: Session):
        self.db = db

    def create_goal(self, user_id: int, goal_data: GoalCreate) -> Goal:
        """Create a new financial goal"""
        try:
            goal = Goal(
                user_id=user_id,
                **goal_data.dict()
            )
            
            self.db.add(goal)
            self.db.commit()
            self.db.refresh(goal)
            
            logger.info(f"Created goal {goal.id} for user {user_id}")
            return goal
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating goal for user {user_id}: {str(e)}")
            raise GoalValidationError(f"Failed to create goal: {str(e)}")

    def get_goals(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[GoalStatus] = None,
        goal_type: Optional[GoalType] = None,
        priority: Optional[GoalPriority] = None
    ) -> List[Goal]:
        """Get user's goals with optional filtering"""
        try:
            query = self.db.query(Goal).filter(Goal.user_id == user_id)
            
            if status:
                query = query.filter(Goal.status == status)
            if goal_type:
                query = query.filter(Goal.goal_type == goal_type)
            if priority:
                query = query.filter(Goal.priority == priority)
                
            goals = query.offset(skip).limit(limit).all()
            return goals
            
        except Exception as e:
            logger.error(f"Error fetching goals for user {user_id}: {str(e)}")
            raise GoalValidationError(f"Failed to fetch goals: {str(e)}")

    def get_goal(self, user_id: int, goal_id: int) -> Goal:
        """Get a specific goal by ID"""
        goal = self.db.query(Goal).filter(
            and_(Goal.id == goal_id, Goal.user_id == user_id)
        ).first()
        
        if not goal:
            raise GoalNotFoundError(f"Goal {goal_id} not found for user {user_id}")
        
        return goal

    def update_goal(self, user_id: int, goal_id: int, goal_data: GoalUpdate) -> Goal:
        """Update an existing goal"""
        try:
            goal = self.get_goal(user_id, goal_id)
            
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
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating goal {goal_id} for user {user_id}: {str(e)}")
            raise GoalValidationError(f"Failed to update goal: {str(e)}")

    def update_goal_progress(self, user_id: int, goal_id: int, progress_data: GoalProgressUpdate) -> Goal:
        """Update goal progress"""
        try:
            goal = self.get_goal(user_id, goal_id)
            
            goal.current_amount = progress_data.current_amount
            goal.update_progress()
            
            self.db.commit()
            self.db.refresh(goal)
            
            logger.info(f"Updated progress for goal {goal_id}: {goal.progress_percentage}%")
            return goal
            
        except GoalNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating progress for goal {goal_id}: {str(e)}")
            raise GoalValidationError(f"Failed to update goal progress: {str(e)}")

    def delete_goal(self, user_id: int, goal_id: int) -> bool:
        """Delete a goal"""
        try:
            goal = self.get_goal(user_id, goal_id)
            
            self.db.delete(goal)
            self.db.commit()
            
            logger.info(f"Deleted goal {goal_id} for user {user_id}")
            return True
            
        except GoalNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting goal {goal_id} for user {user_id}: {str(e)}")
            raise GoalValidationError(f"Failed to delete goal: {str(e)}")

    def get_goal_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get goal statistics for a user"""
        try:
            goals = self.db.query(Goal).filter(Goal.user_id == user_id).all()
            
            if not goals:
                return {
                    "total_goals": 0,
                    "active_goals": 0,
                    "completed_goals": 0,
                    "total_target_amount": 0.0,
                    "total_current_amount": 0.0,
                    "overall_progress": 0.0,
                    "goals_by_type": {},
                    "goals_by_priority": {}
                }
            
            total_goals = len(goals)
            active_goals = len([g for g in goals if g.status == GoalStatus.ACTIVE])
            completed_goals = len([g for g in goals if g.status == GoalStatus.COMPLETED])
            
            total_target_amount = sum(g.target_amount for g in goals)
            total_current_amount = sum(g.current_amount for g in goals)
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
                "goals_by_type": goals_by_type,
                "goals_by_priority": goals_by_priority
            }
            
        except Exception as e:
            logger.error(f"Error getting goal statistics for user {user_id}: {str(e)}")
            raise GoalValidationError(f"Failed to get goal statistics: {str(e)}")

    # Milestone methods
    def create_milestone(self, user_id: int, goal_id: int, milestone_data: MilestoneCreate) -> Milestone:
        """Create a milestone for a goal"""
        try:
            # Verify goal ownership
            goal = self.get_goal(user_id, goal_id)
            
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
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating milestone for goal {goal_id}: {str(e)}")
            raise MilestoneValidationError(f"Failed to create milestone: {str(e)}")

    def get_milestones(self, user_id: int, goal_id: int) -> List[Milestone]:
        """Get milestones for a goal"""
        try:
            # Verify goal ownership
            goal = self.get_goal(user_id, goal_id)
            
            milestones = self.db.query(Milestone).filter(
                Milestone.goal_id == goal_id
            ).order_by(Milestone.order_index).all()
            
            return milestones
            
        except GoalNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching milestones for goal {goal_id}: {str(e)}")
            raise MilestoneValidationError(f"Failed to fetch milestones: {str(e)}")

    def update_milestone_progress(self, user_id: int, goal_id: int, milestone_id: int, progress_data: MilestoneProgressUpdate) -> Milestone:
        """Update milestone progress"""
        try:
            # Verify goal ownership
            goal = self.get_goal(user_id, goal_id)
            
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
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating milestone progress: {str(e)}")
            raise MilestoneValidationError(f"Failed to update milestone progress: {str(e)}")
