from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class GoalType(str, enum.Enum):
    SAVINGS = "SAVINGS"
    DEBT_PAYOFF = "DEBT_PAYOFF"
    INVESTMENT = "INVESTMENT"
    EXPENSE_REDUCTION = "EXPENSE_REDUCTION"
    INCOME_INCREASE = "INCOME_INCREASE"
    EMERGENCY_FUND = "EMERGENCY_FUND"


class GoalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class GoalPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Basic goal information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(Enum(GoalType), nullable=False)
    priority = Column(Enum(GoalPriority), default=GoalPriority.MEDIUM)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    
    # Financial targets
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    
    # Timeline
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    target_date = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    is_milestone_based = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def calculate_progress(self):
        """Calculate progress percentage based on current vs target amount"""
        if self.target_amount <= 0:
            return 0.0
        progress = (self.current_amount / self.target_amount) * 100
        return min(progress, 100.0)
    
    def update_progress(self):
        """Update progress percentage"""
        self.progress_percentage = self.calculate_progress()
        
        # Auto-complete goal if target reached
        if self.progress_percentage >= 100.0 and self.status == GoalStatus.ACTIVE:
            self.status = GoalStatus.COMPLETED
    
    # Relationships
    milestones = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")
