from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    base_currency = Column(String, default="USD", nullable=False)
    default_workspace_id = Column(UUID(as_uuid=True), nullable=True, index=True)