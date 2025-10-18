"""
Category serializer with centralized validation logic.

This serializer provides all validation logic for category operations
including ownership, uniqueness, and hierarchical relationship validation.
"""

from typing import Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryType
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CategoryNameConflictError,
    CategoryDepthExceededError
)
from .validation_mixins import OwnershipValidator, UniquenessValidator, HierarchyValidator
from app.utils.logger import get_logger

Logger = get_logger(__name__)


class CategorySerializer(OwnershipValidator, UniquenessValidator, HierarchyValidator):
    """
    Centralized serializer for category validation and serialization.
    
    This class provides all validation logic for category operations
    and can be reused across different services and endpoints.
    """
    
    def get_entity_class(self):
        """Return the Category model class."""
        return Category
    
    def get_user_id_field(self) -> str:
        """Return the name of the user_id field."""
        return "user_id"
    
    def get_parent_id_field(self) -> str:
        """Return the name of the parent_id field."""
        return "parent_id"
    
    def get_unique_fields(self) -> List[str]:
        """Return list of fields that must be unique per user."""
        return ["name"]
    
    def validate_category_data(self, db: Session, data: CategoryCreate, user_id: int, exclude_id: Optional[int] = None) -> None:
        """
        Comprehensive validation of category data.
        
        Args:
            db: Database session
            data: Category data to validate
            user_id: ID of the user
            exclude_id: ID to exclude from uniqueness validation (for updates)
            
        Raises:
            CategoryValidationError: If validation fails
            CategoryNameConflictError: If name uniqueness is violated
            CircularRelationshipError: If circular relationship would be created
            CategoryDepthExceededError: If maximum depth would be exceeded
        """
        # Validate category type
        self.validate_category_type(data.type)
        
        # Validate name uniqueness
        data_dict = {
            "name": data.name
        }
        self.validate_uniqueness(db, user_id, data_dict, exclude_id)
        
        # Validate parent category if provided
        if data.parent_id:
            self.validate_parent_category(db, data.parent_id, user_id)
            
            # Validate circular relationship for updates
            if exclude_id:
                self.validate_circular_relationship(db, exclude_id, data.parent_id, user_id)
    
    def validate_category_type(self, category_type: CategoryType) -> None:
        """
        Validate category type.
        
        Args:
            category_type: Category type to validate
            
        Raises:
            CategoryValidationError: If type is invalid
        """
        if category_type not in [CategoryType.EXPENSE, CategoryType.INCOME]:
            raise CategoryValidationError(f"Invalid category type: {category_type}")
    
    def validate_parent_category(self, db: Session, parent_id: int, user_id: int) -> Category:
        """
        Validate that parent category exists, belongs to user, and doesn't exceed max depth.
        
        Args:
            db: Database session
            parent_id: ID of the parent category
            user_id: ID of the user
            
        Returns:
            The validated parent category
            
        Raises:
            CategoryNotFoundError: If parent category doesn't exist
            CategoryOwnershipError: If parent category doesn't belong to user
            CategoryDepthExceededError: If parent category is at maximum depth
        """
        parent_category = self.validate_ownership(db, parent_id, user_id, "Parent category")
        
        # Check if parent category is at maximum depth (2)
        # We need to check if adding a child would exceed the max depth of 2
        parent_depth = self.get_entity_depth(db, parent_id, user_id)
        if parent_depth >= 1:  # If parent is at depth 1 or more, we can't add another level
            raise CategoryDepthExceededError(2)
        
        return parent_category
    
    def serialize_category_for_create(self, data: CategoryCreate, user_id: int) -> Dict[str, Any]:
        """
        Serialize category data for creation.
        
        Args:
            data: Category creation data
            user_id: ID of the user
            
        Returns:
            Dictionary with serialized data for category creation
        """
        return {
            "name": data.name,
            "user_id": user_id,
            "parent_id": data.parent_id,
            "type": CategoryType(data.type)
        }
    
    def serialize_category_for_update(self, data: CategoryCreate) -> Dict[str, Any]:
        """
        Serialize category data for update.
        
        Args:
            data: Category update data
            
        Returns:
            Dictionary with serialized data for category update
        """
        update_data = {}
        
        if data.name is not None:
            update_data["name"] = data.name
        
        if data.parent_id is not None:
            update_data["parent_id"] = data.parent_id
            
        if data.type is not None:
            update_data["type"] = CategoryType(data.type)
        
        return update_data
    
    def get_category_children(self, db: Session, category_id: int, user_id: int) -> List[Category]:
        """
        Get direct children of a category with ownership validation.
        
        Args:
            db: Database session
            category_id: ID of the parent category
            user_id: ID of the user
            
        Returns:
            List of child categories
            
        Raises:
            CategoryNotFoundError: If parent category doesn't exist
            CategoryOwnershipError: If parent category doesn't belong to user
        """
        # Validate ownership first
        self.validate_ownership(db, category_id, user_id, "Category")
        
        # Get children
        return db.query(Category).filter(
            Category.parent_id == category_id,
            Category.user_id == user_id
        ).all()
    
    def validate_category_deletion(self, db: Session, category_id: int, user_id: int) -> None:
        """
        Validate that category can be deleted.
        
        Args:
            db: Database session
            category_id: ID of the category to delete
            user_id: ID of the user
            
        Raises:
            CategoryNotFoundError: If category doesn't exist
            CategoryOwnershipError: If category doesn't belong to user
            CategoryValidationError: If category has children
        """
        # Validate ownership
        category = self.validate_ownership(db, category_id, user_id, "Category")
        
        # Check if category has children
        children = self.get_category_children(db, category_id, user_id)
        if children:
            raise CategoryValidationError(
                "Cannot delete category with children. Delete children first."
            )
    
    def get_categories_for_user(self, db: Session, user_id: int, page: int = 1, size: int = 50, flat: bool = False) -> tuple[List[Category], int]:
        """
        Get categories for user with pagination.
        
        Args:
            db: Database session
            user_id: ID of the user
            page: Page number
            size: Page size
            flat: Whether to return flat list or hierarchical
            
        Returns:
            Tuple of (categories, total_count)
        """
        if flat:
            # Get flat list
            total = db.query(Category).filter(Category.user_id == user_id).count()
            categories = db.query(Category).filter(
                Category.user_id == user_id
            ).offset((page - 1) * size).limit(size).all()
        else:
            # Get hierarchical (root categories with children)
            query = db.query(Category).filter(
                Category.user_id == user_id,
                Category.parent_id.is_(None)
            )
            total = query.count()
            from sqlalchemy.orm import joinedload
            categories = query.options(joinedload(Category.children)).offset((page - 1) * size).limit(size).all()
        
        return categories, total
