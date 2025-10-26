from sqlalchemy.orm import Session, joinedload, query
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
import time
from app.models.category import Category
from app.models.mcc import MCCCode, MCCTranslation
from app.schemas.category import CategoryCreate, CategoryCreateFromMCC, CategoryCreateFromMCCBatch, CategoryBatchCreateResult, CategoryBatchCreateResponse, CategoryType
from app.exceptions import (
    CategoryNotFoundError,
    CategoryValidationError,
    CircularRelationshipError,
    CategoryDepthExceededError,
    CategoryNameConflictError,
    CategoryOwnershipError,
    CategoryLimitExceededError
)
from app.utils.logger import get_logger, log_operation, log_security_event
from app.config import settings
from app.serializers import CategorySerializer
from app.clients.subscription import SubscriptionClient

class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
        self.serializer = CategorySerializer()
        self.subscription_client = SubscriptionClient()

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
            
            # Check subscription limits before creating
            current_count = self.db.query(Category).filter(Category.user_id == user_id).count()
            self.logger.info(
                f"Checking subscription limits for user {user_id}, current count: {current_count}",
                category="business",
                operation="subscription_limit_check",
                user_id=user_id,
                current_count=current_count
            )
            
            try:
                if not self.subscription_client.check_category_limit(user_id, current_count):
                    features = self.subscription_client.get_user_features(user_id)
                    category_feature = features.get("categories", {})
                    limit = category_feature.get("limit_value", 0)
                    raise CategoryLimitExceededError(current_count, limit)
            except Exception as e:
                self.logger.error(
                    f"Subscription client error: {str(e)}",
                    category="business",
                    operation="subscription_client_error",
                    user_id=user_id,
                    error=str(e)
                )
                raise CategoryValidationError(f"Subscription validation failed: {str(e)}")
            
            # Comprehensive validation using serializer
            self.logger.info(
                f"Starting serializer validation for category: {data.name}",
                category="business",
                operation="serializer_validation_start",
                user_id=user_id,
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type
            )
            
            try:
                self.serializer.validate_category_data(self.db, data, user_id)
                self.logger.info(
                    f"Serializer validation passed for category: {data.name}",
                    category="business",
                    operation="serializer_validation_success",
                    user_id=user_id,
                    category_name=data.name
                )
            except Exception as e:
                self.logger.error(
                    f"Serializer validation failed for category: {data.name}, error: {str(e)}",
                    category="business",
                    operation="serializer_validation_failed",
                    user_id=user_id,
                    category_name=data.name,
                    error=str(e)
                )
                raise
            
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

    def create_from_mcc(self, data: CategoryCreateFromMCC, user_id: int, language: Optional[str] = None) -> Category:
        """Create a new category from an MCC code with proper validation and transaction management"""
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Starting MCC-based category creation for user {user_id}",
                category="business",
                operation="mcc_category_create_start",
                user_id=user_id,
                mcc_code=data.mcc_code,
                parent_id=data.parent_id,
                category_type=data.type,
                custom_name=data.custom_name,
                language=language
            )
            
            # Check if MCC code exists
            mcc_code_obj = self.db.query(MCCCode).filter(MCCCode.mcc_code == data.mcc_code).first()
            if not mcc_code_obj:
                raise CategoryValidationError(f"MCC code {data.mcc_code} not found")
            
            self.logger.info(
                f"MCC code {data.mcc_code} found: {mcc_code_obj.name}",
                category="business",
                operation="mcc_code_lookup",
                user_id=user_id,
                mcc_code=data.mcc_code,
                mcc_name=mcc_code_obj.name
            )
            
            # Check if user already has a category for this MCC code
            existing_category = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.mcc_code == data.mcc_code
            ).first()
            
            if existing_category:
                raise CategoryNameConflictError(f"Category already exists for MCC code {data.mcc_code}")
            
            # Check subscription limits before creating
            current_count = self.db.query(Category).filter(Category.user_id == user_id).count()
            if not self.subscription_client.check_category_limit(user_id, current_count):
                features = self.subscription_client.get_user_features(user_id)
                category_feature = features.get("categories", {})
                limit = category_feature.get("limit_value", 0)
                raise CategoryLimitExceededError(current_count, limit)
            
            # Determine category name
            category_name = data.custom_name
            if not category_name:
                # Try to get translation if language is provided and not English
                if language and language != "en":
                    translation = self.db.query(MCCTranslation).filter(
                        MCCTranslation.mcc_code == data.mcc_code,
                        MCCTranslation.lang == language
                    ).first()
                    if translation:
                        category_name = translation.text
                
                # Fallback to English name
                if not category_name:
                    category_name = mcc_code_obj.name
                
                # Ensure we have a valid name
                if not category_name or not category_name.strip():
                    raise CategoryValidationError(f"No valid name found for MCC code {data.mcc_code}")
            
            self.logger.info(
                f"Resolved category name for MCC {data.mcc_code}: '{category_name}'",
                category="business",
                operation="category_name_resolution",
                user_id=user_id,
                mcc_code=data.mcc_code,
                resolved_name=category_name,
                custom_name=data.custom_name,
                language=language
            )
            
            # Create CategoryCreate object for validation
            category_data = CategoryCreate(
                name=category_name,
                parent_id=data.parent_id,
                type=data.type
            )
            
            # Validate using existing serializer
            self.serializer.validate_category_data(self.db, category_data, user_id)
            
            # Serialize data for creation
            serialized_data = self.serializer.serialize_category_for_create(category_data, user_id)
            
            # Add MCC-specific fields
            from app.models.category import CategoryCreatedBy
            serialized_data.update({
                'mcc_code': data.mcc_code,
                'created_by': CategoryCreatedBy.SYSTEM  # Categories created from MCC are marked as system-created
            })
            
            category = Category(**serialized_data)
            
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"MCC-based category created successfully",
                category="business",
                operation="mcc_category_created",
                user_id=user_id,
                resource_id=str(category.id),
                mcc_code=data.mcc_code,
                category_name=category_name,
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
                f"MCC-based category creation failed: {str(e)}",
                category="business",
                operation="mcc_category_create_failed",
                user_id=user_id,
                mcc_code=data.mcc_code,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms
            )
            raise
        except IntegrityError as e:
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"MCC-based category creation failed due to integrity error: {str(e)}",
                category="business",
                operation="mcc_category_create_integrity_error",
                user_id=user_id,
                mcc_code=data.mcc_code,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms
            )
            raise CategoryValidationError("Failed to create category due to data constraints")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"Unexpected error during MCC-based category creation: {str(e)}",
                category="business",
                operation="mcc_category_create_unexpected_error",
                user_id=user_id,
                mcc_code=data.mcc_code,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms
            )
            raise CategoryValidationError("Failed to create category")

    def create_from_mcc_batch(self, data: CategoryCreateFromMCCBatch, user_id: int) -> CategoryBatchCreateResponse:
        """Create multiple categories from MCC codes with comprehensive error handling"""
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Starting batch MCC-based category creation for user {user_id}",
                category="business",
                operation="mcc_category_batch_create_start",
                user_id=user_id,
                total_categories=len(data.categories),
                language=data.language.value if data.language else None
            )
            
            results = []
            successful = 0
            failed = 0
            
            # Process each category in the batch
            for category_data in data.categories:
                try:
                    # Use the batch language if no individual language is specified
                    language = data.language.value if data.language else None
                    
                    # Create the category using the existing single creation method
                    created_category = self.create_from_mcc(category_data, user_id, language)
                    
                    result = CategoryBatchCreateResult(
                        mcc_code=category_data.mcc_code,
                        success=True,
                        category_id=created_category.id,
                        category_name=created_category.name,
                        error=None
                    )
                    successful += 1
                    
                    self.logger.info(
                        f"Successfully created category from MCC {category_data.mcc_code}",
                        category="business",
                        operation="mcc_category_batch_item_success",
                        user_id=user_id,
                        mcc_code=category_data.mcc_code,
                        category_id=created_category.id,
                        category_name=created_category.name
                    )
                    
                except Exception as e:
                    result = CategoryBatchCreateResult(
                        mcc_code=category_data.mcc_code,
                        success=False,
                        category_id=None,
                        category_name=None,
                        error=str(e)
                    )
                    failed += 1
                    
                    self.logger.error(
                        f"Failed to create category from MCC {category_data.mcc_code}: {str(e)}",
                        category="business",
                        operation="mcc_category_batch_item_failed",
                        user_id=user_id,
                        mcc_code=category_data.mcc_code,
                        error=str(e)
                    )
                
                results.append(result)
            
            duration_ms = (time.time() - start_time) * 1000
            
            response = CategoryBatchCreateResponse(
                results=results,
                total_requested=len(data.categories),
                successful=successful,
                failed=failed,
                language=data.language
            )
            
            self.logger.info(
                f"Batch MCC-based category creation completed",
                category="business",
                operation="mcc_category_batch_create_completed",
                user_id=user_id,
                total_requested=len(data.categories),
                successful=successful,
                failed=failed,
                duration_ms=duration_ms
            )
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"Unexpected error during batch MCC-based category creation: {str(e)}",
                category="business",
                operation="mcc_category_batch_create_unexpected_error",
                user_id=user_id,
                total_categories=len(data.categories),
                duration_ms=duration_ms
            )
            
            # Return a response with all failures if there's a critical error
            results = []
            for category_data in data.categories:
                result = CategoryBatchCreateResult(
                    mcc_code=category_data.mcc_code,
                    success=False,
                    category_id=None,
                    category_name=None,
                    error=f"Batch operation failed: {str(e)}"
                )
                results.append(result)
            
            return CategoryBatchCreateResponse(
                results=results,
                total_requested=len(data.categories),
                successful=0,
                failed=len(data.categories),
                language=data.language
            )

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

    def check_category_exists_by_mcc(self, mcc_code: int, user_id: int) -> bool:
        """Check if user already has a category with the given MCC code"""
        try:
            category = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.mcc_code == mcc_code
            ).first()
            
            exists = category is not None
            
            log_operation(
                self.logger,
                "MCC category existence check",
                user_id,
                mcc_code,
                f"Category with MCC {mcc_code} {'exists' if exists else 'does not exist'}"
            )
            
            return exists
            
        except Exception as e:
            self.logger.error(f"Error checking category existence by MCC: {e}")
            return False

    def get_category_by_mcc(self, mcc_code: int, user_id: int) -> dict:
        """Get category information by MCC code including category ID"""
        try:
            category = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.mcc_code == mcc_code
            ).first()
            
            if category:
                result = {
                    "exists": True,
                    "category_id": category.id
                }
                
                log_operation(
                    self.logger,
                    "MCC category retrieval",
                    user_id,
                    mcc_code,
                    f"Category with MCC {mcc_code} found with ID {category.id}"
                )
                
                return result
            else:
                result = {
                    "exists": False,
                    "category_id": None
                }
                
                log_operation(
                    self.logger,
                    "MCC category retrieval",
                    user_id,
                    mcc_code,
                    f"Category with MCC {mcc_code} not found"
                )
                
                return result
            
        except Exception as e:
            self.logger.error(f"Error getting category by MCC: {e}")
            return {
                "exists": False,
                "category_id": None
            }

    def check_categories_exist_by_mcc_batch(self, mcc_codes: List[int], user_id: int) -> List[Dict[str, Any]]:
        """Check multiple MCC codes for user categories in a single query"""
        try:
            self.logger.info(
                f"Starting batch MCC category existence check for user {user_id}",
                category="business",
                operation="mcc_category_batch_check_start",
                user_id=user_id,
                mcc_codes=mcc_codes
            )
            
            # Single query to check all MCC codes at once
            existing_categories = self.db.query(Category).filter(
                Category.user_id == user_id,
                Category.mcc_code.in_(mcc_codes)
            ).all()
            
            # Create a map of mcc_code -> category for quick lookup
            mcc_to_category = {cat.mcc_code: cat for cat in existing_categories}
            
            # Build results for all requested MCC codes
            results = []
            for mcc_code in mcc_codes:
                if mcc_code in mcc_to_category:
                    category = mcc_to_category[mcc_code]
                    results.append({
                        "mcc_code": mcc_code,
                        "exists": True,
                        "category_id": category.id
                    })
                else:
                    results.append({
                        "mcc_code": mcc_code,
                        "exists": False,
                        "category_id": None
                    })
            
            self.logger.info(
                f"Batch MCC category existence check completed",
                category="business",
                operation="mcc_category_batch_check_completed",
                user_id=user_id,
                total_checked=len(mcc_codes),
                existing_count=len(existing_categories)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch MCC category existence check: {e}")
            # Return all as not existing on error
            return [
                {
                    "mcc_code": mcc_code,
                    "exists": False,
                    "category_id": None
                }
                for mcc_code in mcc_codes
            ]