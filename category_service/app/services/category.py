from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryType
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryNameConflictError,
    CategoryOwnershipError
)
from app.utils.logger import get_logger, log_operation, log_security_event
from app.config import settings

class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

    def _validate_category_ownership(self, category_id: int, user_id: int) -> Category:
        """Validate that category exists and belongs to user"""
        category = self.db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise CategoryNotFoundError(category_id)
        if category.user_id != user_id:
            log_security_event(
                self.logger, 
                "Unauthorized category access attempt", 
                user_id, 
                f"Attempted to access category {category_id}"
            )
            raise CategoryOwnershipError(category_id, user_id)
        return category

    def _validate_name_uniqueness(self, name: str, user_id: int, exclude_id: Optional[int] = None) -> None:
        """Validate that category name is unique for the user"""
        query = self.db.query(Category).filter(
            Category.name == name,
            Category.user_id == user_id
        )
        if exclude_id:
            query = query.filter(Category.id != exclude_id)
        
        if query.first():
            raise CategoryNameConflictError(name, user_id)

    def _get_category_depth(self, category_id: int, user_id: int) -> int:
        """Get the current depth of a category in the hierarchy"""
        depth = 0
        current_category_id = category_id
        
        while current_category_id:
            category = self.db.query(Category).filter(
                Category.id == current_category_id,
                Category.user_id == user_id
            ).first()
            
            if not category or not category.parent_id:
                break
                
            current_category_id = category.parent_id
            depth += 1
            
            # Prevent infinite loops
            if depth > settings.MAX_CATEGORY_DEPTH * 2:
                break
                
        return depth

    def _validate_circular_relationship(self, category_id: int, parent_id: int, user_id: int) -> None:
        """Validate that setting parent_id doesn't create circular relationship"""
        if category_id == parent_id:
            raise CircularRelationshipError(category_id, parent_id)
        
        # Check if parent is a descendant of category_id
        current_parent_id = parent_id
        depth = 0
        max_depth = settings.MAX_CATEGORY_DEPTH
        
        while current_parent_id and depth < max_depth:
            if current_parent_id == category_id:
                raise CircularRelationshipError(category_id, parent_id)
            
            parent = self.db.query(Category).filter(
                Category.id == current_parent_id,
                Category.user_id == user_id
            ).first()
            
            if not parent:
                break
                
            current_parent_id = parent.parent_id
            depth += 1
        
        if depth >= max_depth:
            raise CategoryDepthExceededError(max_depth)

    def _validate_parent_category(self, parent_id: int, user_id: int) -> Category:
        """Validate parent category exists and belongs to user"""
        parent = self.db.query(Category).filter(
            Category.id == parent_id,
            Category.user_id == user_id
        ).first()
        if not parent:
            raise CategoryNotFoundError(parent_id, "Parent category not found")
        return parent

    def _validate_category_type(self, type: CategoryType) -> None:
        """Validate category type"""
        if type not in [CategoryType.EXPENSE, CategoryType.INCOME]:
            raise CategoryValidationError("Invalid category type")

    def create(self, data: CategoryCreate, user_id: int) -> Category:
        """Create a new category with proper validation and transaction management"""
        try:
            # Validate name uniqueness
            self._validate_name_uniqueness(data.name, user_id)

            # Validate category type
            self._validate_category_type(data.type)
            
            # Validate parent category if provided
            if data.parent_id:
                parent = self._validate_parent_category(data.parent_id, user_id)
                # Note: We don't validate circular relationship for new categories
                # as they can't be their own parent yet
            
            category = Category(
                name=data.name,
                user_id=user_id,
                parent_id=data.parent_id,
                type=CategoryType(data.type)
            )
            
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            
            log_operation(
                self.logger, 
                "Category created", 
                user_id, 
                category.id, 
                f"Name: {data.name}, Parent: {data.parent_id}, Type: {data.type}"
            )
            
            return category
            
        except (CategoryNotFoundError, CategoryValidationError, CategoryNameConflictError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error during category creation: {e}")
            raise CategoryValidationError("Database constraint violation")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during category creation: {e}")
            raise CategoryValidationError("Failed to create category")

    def get_all(self, user_id: int, page: int = 1, size: int = 50) -> tuple[List[Category], int]:
        """Get root categories with their full hierarchy (paginated)"""
        try:
            # Get total count
            total = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.parent_id.is_(None)
            ).count()
            
            # Get paginated results
            categories = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.parent_id.is_(None)
            ).options(joinedload(Category.children)).offset((page - 1) * size).limit(size).all()
            
            return categories, total
        except Exception as e:
            self.logger.error(f"Error retrieving categories: {e}")
            raise CategoryValidationError("Failed to retrieve categories")

    def get_all_flat(self, user_id: int, page: int = 1, size: int = 50) -> tuple[List[Category], int]:
        """Get all categories in a flat list (paginated)"""
        try:
            # Get total count
            total = self.db.query(Category).filter(Category.user_id == user_id).count()
            
            # Get paginated results
            categories = self.db.query(Category).filter(
                Category.user_id == user_id
            ).offset((page - 1) * size).limit(size).all()
            
            return categories, total
        except Exception as e:
            self.logger.error(f"Error retrieving flat categories: {e}")
            raise CategoryValidationError("Failed to retrieve categories")

    def get(self, category_id: int, user_id: int) -> Category:
        """Get a specific category by ID"""
        return self._validate_category_ownership(category_id, user_id)

    def get_children(self, category_id: int, user_id: int) -> List[Category]:
        """Get direct children of a category"""
        try:
            # First validate ownership
            self._validate_category_ownership(category_id, user_id)
            
            return self.db.query(Category).filter(
                Category.parent_id == category_id,
                Category.user_id == user_id
            ).all()
        except Exception as e:
            self.logger.error(f"Error retrieving category children: {e}")
            raise CategoryValidationError("Failed to retrieve category children")

    def update(self, category_id: int, data: CategoryCreate, user_id: int) -> Category:
        """Update a category with proper validation and transaction management"""
        try:
            category = self._validate_category_ownership(category_id, user_id)
            
            # Validate name uniqueness (excluding current category)
            if data.name != category.name:
                self._validate_name_uniqueness(data.name, user_id, category_id)
            
            # Validate parent category if provided
            if data.parent_id:
                if data.parent_id == category_id:
                    raise CircularRelationshipError(category_id, data.parent_id)
                
                self._validate_parent_category(data.parent_id, user_id)
                self._validate_circular_relationship(category_id, data.parent_id, user_id)
            
            # Update category
            old_name = category.name
            old_parent = category.parent_id
            category.name = data.name
            category.parent_id = data.parent_id
            
            self.db.commit()
            self.db.refresh(category)
            
            log_operation(
                self.logger, 
                "Category updated", 
                user_id, 
                category_id, 
                f"Name: {old_name} -> {data.name}, Parent: {old_parent} -> {data.parent_id}"
            )
            
            return category
            
        except (CategoryNotFoundError, CategoryValidationError, CategoryNameConflictError, 
                CircularRelationshipError, CategoryOwnershipError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error during category update: {e}")
            raise CategoryValidationError("Database constraint violation")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during category update: {e}")
            raise CategoryValidationError("Failed to update category")

    def delete(self, category_id: int, user_id: int) -> dict:
        """Delete a category with proper validation and transaction management"""
        try:
            category = self._validate_category_ownership(category_id, user_id)
            
            # Check if category has children
            children = self.get_children(category_id, user_id)
            if children:
                raise CategoryValidationError(
                    "Cannot delete category with children. Delete children first."
                )
            
            category_name = category.name
            self.db.delete(category)
            self.db.commit()
            
            log_operation(
                self.logger, 
                "Category deleted", 
                user_id, 
                category_id, 
                f"Name: {category_name}"
            )
            
            return {"detail": "Category deleted successfully"}
            
        except (CategoryNotFoundError, CategoryValidationError, CategoryOwnershipError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during category deletion: {e}")
            raise CategoryValidationError("Failed to delete category")

    def get_by_id_internal(self, category_id: int, user_id: int) -> Category:
        """Internal method to get category by ID for internal service calls"""
        try:
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise CategoryNotFoundError(category_id)
            
            if category.user_id != user_id:
                log_security_event(
                    self.logger,
                    "Internal service unauthorized category access",
                    user_id,
                    f"Attempted to access category {category_id} owned by user {category.user_id}"
                )
                raise CategoryOwnershipError(category_id, user_id)
            
            return category
            
        except Exception as e:
            self.logger.error(f"Error in internal category retrieval: {e}")
            raise CategoryValidationError("Failed to retrieve category for internal validation")