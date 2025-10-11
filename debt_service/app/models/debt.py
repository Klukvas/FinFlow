from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Contact(Base):
    """Contact model for debt creditors/lenders"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    debts = relationship("Debt", back_populates="contact")

class Debt(Base):
    """Debt model for managing debts"""
    __tablename__ = "debts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    category_id = Column(Integer, nullable=True)  # Reference to category service
    
    # Debt details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    debt_type = Column(String(50), nullable=False)  # CREDIT_CARD, LOAN, MORTGAGE, etc.
    
    # Financial details
    initial_amount = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=True)  # Annual percentage rate
    minimum_payment = Column(Float, nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    last_payment_date = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_paid_off = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    contact = relationship("Contact", back_populates="debts")
    payments = relationship("DebtPayment", back_populates="debt")

class DebtPayment(Base):
    """Debt payment model for tracking individual payments"""
    __tablename__ = "debt_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    debt_id = Column(Integer, ForeignKey("debts.id"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    principal_amount = Column(Float, nullable=True)  # Amount that reduces principal
    interest_amount = Column(Float, nullable=True)   # Interest portion
    payment_date = Column(Date, nullable=False)
    description = Column(String(500), nullable=True)
    
    # Payment method/type
    payment_method = Column(String(50), nullable=True)  # CASH, CARD, TRANSFER, etc.
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    debt = relationship("Debt", back_populates="payments")
