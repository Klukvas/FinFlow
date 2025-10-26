from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class MCCCode(Base):
    __tablename__ = "mcc_codes"

    mcc_code = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # canonical English name
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationship to translations
    translations = relationship("MCCTranslation", back_populates="mcc_code_obj", cascade="all, delete-orphan")

class MCCTranslation(Base):
    __tablename__ = "translations"

    mcc_code = Column(Integer, ForeignKey("mcc_codes.mcc_code", ondelete="CASCADE"), primary_key=True)
    lang = Column(String(5), primary_key=True)  # language code (e.g., 'ru', 'en', 'es')
    text = Column(String, nullable=False)

    # Relationship to MCC code
    mcc_code_obj = relationship("MCCCode", back_populates="translations")
