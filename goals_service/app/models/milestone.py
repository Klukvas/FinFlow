from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    
    # Milestone information
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    
    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Ordering
    order_index = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    goal = relationship("Goal", back_populates="milestones")
    
    def calculate_progress(self):
        """Calculate milestone progress percentage"""
        if self.target_amount <= 0:
            return 0.0
        progress = (self.current_amount / self.target_amount) * 100
        return min(progress, 100.0)
    
    def update_progress(self):
        """Update milestone progress and completion status"""
        progress = self.calculate_progress()
        
        if progress >= 100.0 and not self.is_completed:
            self.is_completed = True
            self.completed_at = func.now()
