"""
Validation mixins for reusable validation logic.

These mixins provide common validation patterns that can be reused
across different services and serializers.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    CategoryNotFoundError,
    CategoryOwnershipError,
    CategoryNameConflictError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryValidationError
)
from app.utils.logger import log_security_event, get_logger

T = TypeVar('T')  # Entity type
Logger = get_logger(__name__)


class OwnershipValidator(ABC):
    """Mixin for validating entity ownership."""
    
    @abstractmethod
    def get_entity_class(self):
        """Return the entity class for ownership validation."""
        pass
    
    @abstractmethod
    def get_user_id_field(self) -> str:
        """Return the name of the user_id field in the entity."""
        pass
    
    def validate_ownership(self, db: Session, entity_id: int, user_id: int, entity_name: str = "Entity") -> Any:
        """
        Validate that entity exists and belongs to user.
        
        Args:
            db: Database session
            entity_id: ID of the entity to validate
            user_id: ID of the user claiming ownership
            entity_name: Name of the entity for error messages
            
        Returns:
            The validated entity
            
        Raises:
            CategoryNotFoundError: If entity doesn't exist
            CategoryOwnershipError: If entity doesn't belong to user
        """
        entity_class = self.get_entity_class()
        user_id_field = getattr(entity_class, self.get_user_id_field())
        
        entity = db.query(entity_class).filter(entity_class.id == entity_id).first()
        
        if not entity:
            raise CategoryNotFoundError(entity_id, f"{entity_name} with ID {entity_id} not found")
        
        if getattr(entity, self.get_user_id_field()) != user_id:
            log_security_event(
                Logger,
                f"Unauthorized {entity_name.lower()} access attempt",
                user_id,
                f"Attempted to access {entity_name.lower()} {entity_id}"
            )
            raise CategoryOwnershipError(entity_id, user_id)
        
        return entity


class UniquenessValidator(ABC):
    """Mixin for validating entity uniqueness."""
    
    @abstractmethod
    def get_entity_class(self):
        """Return the entity class for uniqueness validation."""
        pass
    
    @abstractmethod
    def get_user_id_field(self) -> str:
        """Return the name of the user_id field in the entity."""
        pass
    
    @abstractmethod
    def get_unique_fields(self) -> list[str]:
        """Return list of field names that must be unique per user."""
        pass
    
    def validate_uniqueness(self, db: Session, user_id: int, data: dict, exclude_id: Optional[int] = None) -> None:
        """
        Validate that entity fields are unique for the user.
        
        Args:
            db: Database session
            user_id: ID of the user
            data: Dictionary of field values to validate
            exclude_id: ID to exclude from validation (for updates)
            
        Raises:
            CategoryNameConflictError: If uniqueness constraint is violated
        """
        entity_class = self.get_entity_class()
        user_id_field = getattr(entity_class, self.get_user_id_field())
        
        for field_name in self.get_unique_fields():
            if field_name in data:
                query = db.query(entity_class).filter(
                    getattr(entity_class, field_name) == data[field_name],
                    user_id_field == user_id
                )
                
                if exclude_id:
                    query = query.filter(entity_class.id != exclude_id)
                
                if query.first():
                    raise CategoryNameConflictError(
                        data[field_name], 
                        user_id
                    )


class HierarchyValidator(ABC):
    """Mixin for validating hierarchical relationships."""
    
    @abstractmethod
    def get_entity_class(self):
        """Return the entity class for hierarchy validation."""
        pass
    
    @abstractmethod
    def get_parent_id_field(self) -> str:
        """Return the name of the parent_id field in the entity."""
        pass
    
    @abstractmethod
    def get_user_id_field(self) -> str:
        """Return the name of the user_id field in the entity."""
        pass
    
    def validate_circular_relationship(self, db: Session, entity_id: int, parent_id: int, user_id: int) -> None:
        """
        Validate that setting parent_id doesn't create circular relationship.
        
        Args:
            db: Database session
            entity_id: ID of the entity being updated
            parent_id: ID of the proposed parent
            user_id: ID of the user
            
        Raises:
            CircularRelationshipError: If circular relationship would be created
            CategoryDepthExceededError: If maximum depth would be exceeded
        """
        if entity_id == parent_id:
            raise CircularRelationshipError(entity_id, parent_id)
        
        entity_class = self.get_entity_class()
        parent_id_field = getattr(entity_class, self.get_parent_id_field())
        user_id_field = getattr(entity_class, self.get_user_id_field())
        
        # Check if parent is a descendant of entity_id
        current_parent_id = parent_id
        depth = 0
        max_depth = 20  # Configurable maximum depth
        
        while current_parent_id and depth < max_depth:
            if current_parent_id == entity_id:
                raise CircularRelationshipError(entity_id, parent_id)
            
            parent = db.query(entity_class).filter(
                entity_class.id == current_parent_id,
                user_id_field == user_id
            ).first()
            
            if not parent:
                break
                
            current_parent_id = getattr(parent, self.get_parent_id_field())
            depth += 1
        
        if depth >= max_depth:
            raise CategoryDepthExceededError(max_depth)
    
    def get_entity_depth(self, db: Session, entity_id: int, user_id: int) -> int:
        """
        Get the current depth of an entity in the hierarchy.
        
        Args:
            db: Database session
            entity_id: ID of the entity
            user_id: ID of the user
            
        Returns:
            Depth of the entity in the hierarchy
        """
        entity_class = self.get_entity_class()
        parent_id_field = getattr(entity_class, self.get_parent_id_field())
        user_id_field = getattr(entity_class, self.get_user_id_field())
        
        depth = 0
        current_entity_id = entity_id
        max_depth = 20  # Prevent infinite loops
        
        while current_entity_id and depth < max_depth:
            entity = db.query(entity_class).filter(
                entity_class.id == current_entity_id,
                user_id_field == user_id
            ).first()
            
            if not entity or not getattr(entity, self.get_parent_id_field()):
                break
                
            current_entity_id = getattr(entity, self.get_parent_id_field())
            depth += 1
        
        return depth
