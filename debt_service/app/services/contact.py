from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.models.debt import Contact
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse, ContactSummary
from app.exceptions import (
    ContactNotFoundError,
    ContactValidationError,
    ExternalServiceError,
    ContactCreationFailedError,
    ContactUpdateFailedError,
    ContactDeletionFailedError,
    ContactHasAssociatedDebtsError
)
from app.utils.logger import get_logger, log_operation

logger = get_logger(__name__)

class ContactService:
    """Service for managing contacts"""
    
    def __init__(self, db: Session):
        super().__init__()  # Initialize WorkspaceAuthorizationMixin
        self.db = db
        self.logger = get_logger(__name__)

    async def create_contact(self, contact: ContactCreate, user_id: int, workspace_id: UUID) -> ContactResponse:
        """Create a new contact"""
        try:
            # Authorize workspace access
            self.authorize_workspace_access(workspace_id, user_id, "member", "create_contact")
            
            db_contact = Contact(
                user_id=user_id,
                workspace_id=workspace_id,
                name=contact.name,
                email=contact.email,
                phone=contact.phone,
                company=contact.company,
                address=contact.address,
                notes=contact.notes
            )
            
            self.db.add(db_contact)
            self.db.commit()
            self.db.refresh(db_contact)
            
            log_operation(self.logger, "Contact created", user_id, f"Contact ID: {db_contact.id}, Name: {contact.name}")
            return ContactResponse.model_validate(db_contact)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error creating contact: {e}")
            raise ContactCreationFailedError("Failed to create contact")

    def get_contacts(self, user_id: int, workspace_id: UUID, skip: int = 0, limit: int = 100) -> List[ContactResponse]:
        """Get all contacts in workspace"""
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "list_contacts")
        
        contacts = self.db.query(Contact).filter(
            Contact.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()
        
        return [ContactResponse.model_validate(contact) for contact in contacts]

    def get_contact(self, contact_id: int, user_id: int, workspace_id: UUID) -> ContactResponse:
        """Get a specific contact"""
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_contact")
        
        contact = self.db.query(Contact).filter(
            Contact.workspace_id == workspace_id,
            Contact.id == contact_id
        ).first()
        
        if not contact:
            raise ContactNotFoundError(contact_id)
        
        return ContactResponse.model_validate(contact)

    async def update_contact(self, contact_id: int, contact_update: ContactUpdate, user_id: int, workspace_id: UUID) -> ContactResponse:
        """Update a contact"""
        self.authorize_workspace_access(workspace_id, user_id, "member", "update_contact")
        
        contact = self.db.query(Contact).filter(
            Contact.workspace_id == workspace_id,
            Contact.id == contact_id
        ).first()
        
        if not contact:
            raise ContactNotFoundError(contact_id)
        
        try:
            update_data = contact_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(contact, field, value)
            
            self.db.commit()
            self.db.refresh(contact)
            
            log_operation(self.logger, "Contact updated", user_id, f"Contact ID: {contact.id}, Fields: {list(update_data.keys())}")
            return ContactResponse.model_validate(contact)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating contact: {e}")
            raise ContactUpdateFailedError("Failed to update contact")

    def delete_contact(self, contact_id: int, user_id: int, workspace_id: UUID) -> bool:
        """Delete a contact"""
        self.authorize_workspace_access(workspace_id, user_id, "member", "delete_contact")
        
        contact = self.db.query(Contact).filter(
            Contact.workspace_id == workspace_id,
            Contact.id == contact_id
        ).first()
        
        if not contact:
            raise ContactNotFoundError(contact_id)
        
        # Check if contact has associated debts
        from app.models.debt import Debt
        debt_count = self.db.query(Debt).filter(Debt.contact_id == contact_id).count()
        if debt_count > 0:
            raise ContactHasAssociatedDebtsError(contact_id, debt_count)
        
        try:
            self.db.delete(contact)
            self.db.commit()
            
            log_operation(self.logger, "Contact deleted", user_id, f"Contact ID: {contact_id}, Name: {contact.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error deleting contact: {e}")
            raise ContactDeletionFailedError("Failed to delete contact")

    def get_contact_summaries(self, user_id: int) -> List[ContactSummary]:
        """Get contact summaries with debt information"""
        contacts = self.db.query(Contact).filter(Contact.user_id == user_id).all()
        
        summaries = []
        for contact in contacts:
            from app.models.debt import Debt
            debts = self.db.query(Debt).filter(Debt.contact_id == contact.id).all()
            total_debt = sum(debt.current_balance for debt in debts)
            
            summaries.append(ContactSummary(
                id=contact.id,
                name=contact.name,
                company=contact.company,
                debts_count=len(debts),
                total_debt_amount=total_debt
            ))
        
        return summaries

    def get_contact_by_id(self, contact_id: int, user_id: int) -> Contact:
        """Get contact model by ID (internal use)"""
        contact = self.db.query(Contact).filter(
            Contact.user_id == user_id,
            Contact.id == contact_id
        ).first()
        
        if not contact:
            raise ContactNotFoundError(contact_id)
        
        return contact
