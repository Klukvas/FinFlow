from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    base_currency = Column(String, default="USD", nullable=False)
    default_workspace_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    tutorial_version = Column(Integer, default=0, nullable=False)  # 0 = not completed, >0 = completed version
    role = Column(String(20), default="user", nullable=False, index=True)  # "user" | "admin"
    status = Column(String(20), default="active", nullable=False, index=True)  # "active" | "disabled"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)