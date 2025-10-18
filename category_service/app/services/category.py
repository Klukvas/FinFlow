from sqlalchemy.orm import Session, joinedload, query
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import time
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
from app.serializers import CategorySerializer

class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
        self.serializer = CategorySerializer()

    # Validation methods are now handled directly by the serializer
    # No need for wrapper methods

    def create(self, data: CategoryCreate, user_id: int) -> Category:
        """Create a new category with proper validation and transaction management"""
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Starting category creation for user {user_id}",
                category="business",
                operation="category_create_start",
                user_id=user_id,
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type
            )
            
            # Comprehensive validation using serializer
            self.serializer.validate_category_data(self.db, data, user_id)
            
            # Serialize data for creation
            category_data = self.serializer.serialize_category_for_create(data, user_id)
            
            category = Category(**category_data)
            
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"Category created successfully",
                category="business",
                operation="category_created",
                user_id=user_id,
                resource_id=str(category.id),
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms
            )
            
            return category
            
        except (CategoryNotFoundError, CategoryValidationError, CategoryNameConflictError, 
                CircularRelationshipError, CategoryOwnershipError, CategoryDepthExceededError) as e:
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"Category creation failed: {str(e)}",
                category="business",
                operation="category_create_failed",
                user_id=user_id,
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms
            )
            raise
        except IntegrityError as e:
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"Category creation failed due to database constraint: {str(e)}",
                category="database",
                operation="category_create_integrity_error",
                user_id=user_id,
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms
            )
            raise CategoryValidationError("Database constraint violation")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"Unexpected error during category creation: {str(e)}",
                category="system",
                operation="category_create_unexpected_error",
                user_id=user_id,
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms
            )
            raise CategoryValidationError("Failed to create category")

    def get_all(self, user_id: int, page: int = 1, size: int = 50) -> tuple[List[Category], int]:
        """Get root categories with their full hierarchy (paginated)"""
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Retrieving categories for user {user_id}",
                category="business",
                operation="category_list_start",
                user_id=user_id,
                page=page,
                size=size
            )
            
            result = self.serializer.get_categories_for_user(self.db, user_id, page, size, flat=False)
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"Categories retrieved successfully",
                category="business",
                operation="category_list_success",
                user_id=user_id,
                page=page,
                size=size,
                count=len(result[0]) if result[0] else 0,
                total=result[1] if len(result) > 1 else 0,
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"Error getting categories for user {user_id}: {str(e)}",
                category="business",
                operation="category_list_failed",
                user_id=user_id,
                page=page,
                size=size,
                duration_ms=duration_ms
            )
            raise CategoryValidationError("Failed to retrieve categories")

    def get_all_flat(self, user_id: int, page: int = 1, size: int = 50) -> tuple[List[Category], int]:
        """Get all categories in a flat list (paginated)"""
        try:
            return self.serializer.get_categories_for_user(self.db, user_id, page, size, flat=True)
        except Exception as e:
            self.logger.error(f"Error retrieving flat categories: {e}")
            raise CategoryValidationError("Failed to retrieve categories")

    def get(self, category_id: int, user_id: int) -> Category:
        """Get a specific category by ID"""
        return self.serializer.validate_ownership(self.db, category_id, user_id, "Category")

    def get_children(self, category_id: int, user_id: int) -> List[Category]:
        """Get direct children of a category"""
        try:
            return self.serializer.get_category_children(self.db, category_id, user_id)
        except Exception as e:
            self.logger.error(f"Error retrieving category children: {e}")
            raise CategoryValidationError("Failed to retrieve category children")

    def update(self, category_id: int, data: CategoryCreate, user_id: int) -> Category:
        """Update a category with proper validation and transaction management"""
        try:
            # Get category for ownership validation and logging
            category = self.serializer.validate_ownership(self.db, category_id, user_id, "Category")
            
            # Comprehensive validation using serializer (with exclude_id for updates)
            self.serializer.validate_category_data(self.db, data, user_id, exclude_id=category_id)
            
            # Serialize data for update
            update_data = self.serializer.serialize_category_for_update(data)
            
            # Update category fields
            old_name = category.name
            old_parent = category.parent_id
            
            for field, value in update_data.items():
                setattr(category, field, value)
            
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
                CircularRelationshipError, CategoryOwnershipError, CategoryDepthExceededError):
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
            # Get category with ownership validation
            category = self.serializer.validate_ownership(self.db, category_id, user_id, "Category")
            
            # Check if category has children
            children = self.serializer.get_category_children(self.db, category_id, user_id)
            if children:
                raise CategoryValidationError(
                    "Cannot delete category with children. Delete children first.",
                    "CATEGORY_HAS_CHILDREN"
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
            return self.serializer.validate_ownership(self.db, category_id, user_id, "Category")
        except Exception as e:
            self.logger.error(f"Error in internal category retrieval: {e}")
            raise CategoryValidationError("Failed to retrieve category for internal validation")