from sqlalchemy.orm import Session, joinedload, query
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from uuid import UUID
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
from shared.clients import SubscriptionClient
from shared.auth import WorkspaceAuthorizationMixin

class CategoryService(WorkspaceAuthorizationMixin):
    def __init__(self, db: Session):
        super().__init__(
            access_denied_error=CategoryOwnershipError,
            workspace_mismatch_error=CategoryOwnershipError,
        )
        self.db = db
        self.logger = get_logger(__name__)
        self.serializer = CategorySerializer()
        self.subscription_client = SubscriptionClient()

    # Validation methods are now handled directly by the serializer
    # No need for wrapper methods

    def create(self, data: CategoryCreate, user_id: int, workspace_id: UUID) -> Category:
        """Create a new category with proper validation and transaction management"""
        start_time = time.time()

        self.logger.info(
            f"Creating category '{data.name}'",
            category="business",
            operation="category_create",
            user_id=user_id,
            workspace_id=str(workspace_id),
            category_name=data.name,
            parent_id=data.parent_id
        )

        try:
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="member",
                operation="create_category"
            )

            # Validate parent belongs to same workspace (if parent_id provided)
            if data.parent_id:
                parent = self.db.query(Category).filter(Category.id == data.parent_id).first()
                if not parent:
                    raise CategoryNotFoundError(data.parent_id)

                self.validate_workspace_match(
                    parent.workspace_id,
                    workspace_id,
                    parent.id
                )

            # Check subscription limits before creating (filtered by workspace)
            current_count = self.db.query(Category).filter(
                Category.workspace_id == workspace_id
            ).count()

            try:
                if not self.subscription_client.check_limit(user_id, current_count, "categories"):
                    features = self.subscription_client.get_user_features(user_id) or {}
                    category_feature = features.get("categories", {})
                    limit = category_feature.get("limit_value", 0)
                    raise CategoryLimitExceededError(current_count, limit)
            except (CategoryLimitExceededError, CategoryValidationError):
                raise
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
            self.serializer.validate_category_data(self.db, data, user_id, workspace_id=workspace_id)
            
            # Serialize data for creation
            category_data = self.serializer.serialize_category_for_create(data, user_id)
            category_data['workspace_id'] = workspace_id
            
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
            
        except (
            CategoryNotFoundError, 
            CategoryValidationError, 
            CategoryNameConflictError, 
            CategoryLimitExceededError,
            CircularRelationshipError, 
            CategoryOwnershipError, 
            CategoryDepthExceededError
        ) as e:
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"[CREATE CATEGORY] FAILED - {e.__class__.__name__}: {str(e)}",
                category="business",
                operation="category_create_failed",
                exception_type=e.__class__.__name__,
                exception_message=str(e),
                user_id=user_id,
                workspace_id=str(workspace_id),
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms,
                error_code=getattr(e, 'error_code', None),
                data_dict=data.dict() if hasattr(data, 'dict') else str(data)
            )
            raise
        except IntegrityError as e:
            import traceback
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"[CREATE CATEGORY] DATABASE INTEGRITY ERROR: {str(e)}",
                category="database",
                operation="category_create_integrity_error",
                exception_type="IntegrityError",
                exception_message=str(e),
                user_id=user_id,
                workspace_id=str(workspace_id),
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms,
                data_dict=data.dict() if hasattr(data, 'dict') else str(data),
                traceback=traceback.format_exc()
            )
            raise CategoryValidationError("Database constraint violation")
        except Exception as e:
            import traceback
            duration_ms = (time.time() - start_time) * 1000
            self.db.rollback()
            
            self.logger.error(
                f"[CREATE CATEGORY] UNEXPECTED ERROR: {e.__class__.__name__} - {str(e)}",
                category="system",
                operation="category_create_unexpected_error",
                exception_type=e.__class__.__name__,
                exception_message=str(e),
                user_id=user_id,
                workspace_id=str(workspace_id),
                category_name=data.name,
                parent_id=data.parent_id,
                category_type=data.type,
                duration_ms=duration_ms,
                data_dict=data.dict() if hasattr(data, 'dict') else str(data),
                traceback=traceback.format_exc()
            )
            raise CategoryValidationError("Failed to create category")

    def create_from_mcc(self, data: CategoryCreateFromMCC, user_id: int, workspace_id: UUID, language: Optional[str] = None) -> Category:
        """Create a new category from an MCC code with proper validation and transaction management"""
        start_time = time.time()
        
        try:
            # Authorize user in workspace (requires 'member' role for POST)
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="member",
                operation="create_category_from_mcc"
            )
            
            self.logger.info(
                f"Creating category from MCC {data.mcc_code}",
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

            # Validate parent belongs to same workspace (if parent_id provided)
            if data.parent_id:
                parent = self.db.query(Category).filter(Category.id == data.parent_id).first()
                if not parent:
                    raise CategoryNotFoundError(data.parent_id)
                
                self.validate_workspace_match(
                    parent.workspace_id,
                    workspace_id,
                    parent.id
                )
            
            # Check if user already has a category for this MCC code in this workspace
            existing_category = self.db.query(Category).filter(
                Category.workspace_id == workspace_id,
                Category.user_id == user_id,
                Category.mcc_code == data.mcc_code
            ).first()
            
            if existing_category:
                raise CategoryNameConflictError(f"Category already exists for MCC code {data.mcc_code}")
            
            # Check subscription limits before creating (filtered by workspace)
            current_count = self.db.query(Category).filter(
                Category.workspace_id == workspace_id
            ).count()
            if not self.subscription_client.check_limit(user_id, current_count, "categories"):
                features = self.subscription_client.get_user_features(user_id) or {}
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

            # Create CategoryCreate object for validation
            category_data = CategoryCreate(
                name=category_name,
                parent_id=data.parent_id,
                type=data.type
            )

            # Validate using existing serializer
            self.serializer.validate_category_data(self.db, category_data, user_id, workspace_id=workspace_id)

            # Serialize data for creation
            serialized_data = self.serializer.serialize_category_for_create(category_data, user_id)
            
            # Add MCC-specific fields and workspace_id
            from app.models.category import CategoryCreatedBy
            serialized_data.update({
                'mcc_code': data.mcc_code,
                'created_by': CategoryCreatedBy.SYSTEM,  # Categories created from MCC are marked as system-created
                'workspace_id': workspace_id
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
            
            # Add more context to the error message
            error_msg = f"MCC-based category creation failed: {str(e)}"
            if hasattr(e, 'detail') and isinstance(e.detail, dict):
                error_msg += f" (errorCode: {e.detail.get('errorCode', 'N/A')})"
            
            self.logger.error(
                error_msg,
                category="business",
                operation="mcc_category_create_failed",
                user_id=user_id,
                mcc_code=data.mcc_code,
                parent_id=data.parent_id,
                category_type=data.type,
                error_type=type(e).__name__,
                duration_ms=duration_ms
            )
            
            # Re-raise with more context if possible
            if hasattr(e, 'detail') and isinstance(e.detail, dict):
                # Update the detail with more information
                e.detail['error'] = f"Failed to create category: {e.detail.get('error', str(e))}"
            
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

    def create_from_mcc_batch(self, data: CategoryCreateFromMCCBatch, user_id: int, workspace_id: UUID) -> CategoryBatchCreateResponse:
        """Create multiple categories from MCC codes with comprehensive error handling"""
        start_time = time.time()
        
        try:
            # Authorization is checked in create_from_mcc for each category
            self.logger.info(
                f"Starting batch MCC-based category creation for user {user_id} in workspace {workspace_id}",
                category="business",
                operation="mcc_category_batch_create_start",
                user_id=user_id,
                workspace_id=str(workspace_id),
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
                    created_category = self.create_from_mcc(category_data, user_id, workspace_id, language)
                    
                    result = CategoryBatchCreateResult(
                        mcc_code=category_data.mcc_code,
                        success=True,
                        category_id=created_category.id,
                        category_name=created_category.name,
                        error=None
                    )
                    successful += 1

                except Exception as e:
                    # Extract more detailed error information
                    error_detail = str(e)
                    
                    # If it's an HTTPException, try to extract the error message
                    if hasattr(e, 'detail'):
                        if isinstance(e.detail, dict):
                            error_detail = e.detail.get('error', error_detail)
                        elif isinstance(e.detail, str):
                            error_detail = e.detail
                    
                    # Include error code if available
                    if hasattr(e, 'detail') and isinstance(e.detail, dict):
                        error_code = e.detail.get('errorCode', 'UNKNOWN_ERROR')
                        error_detail = f"{error_code}: {error_detail}"
                    
                    result = CategoryBatchCreateResult(
                        mcc_code=category_data.mcc_code,
                        success=False,
                        category_id=None,
                        category_name=None,
                        error=error_detail
                    )
                    failed += 1
                    
                    self.logger.error(
                        f"Failed to create category from MCC {category_data.mcc_code}: {str(e)}",
                        category="business",
                        operation="mcc_category_batch_item_failed",
                        user_id=user_id,
                        mcc_code=category_data.mcc_code,
                        error=str(e),
                        error_type=type(e).__name__
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

    def get_all(self, user_id: int, workspace_id: UUID, page: int = 1, size: int = 50) -> tuple[List[Category], int]:
        """Get root categories with their full hierarchy (paginated, filtered by workspace)"""
        start_time = time.time()
        
        try:
            # Authorize user (requires 'viewer' role for GET)
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="viewer",
                operation="list_categories"
            )

            # Query categories filtered by workspace_id
            query = self.db.query(Category).options(joinedload(Category.children)).filter(
                Category.workspace_id == workspace_id,
                Category.parent_id == None  # Root categories only
            ).order_by(Category.created_at.desc())
            
            total = query.count()
            categories = query.offset((page - 1) * size).limit(size).all()
            
            result = (categories, total)
            
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"Categories retrieved successfully",
                category="business",
                operation="category_list_success",
                user_id=user_id,
                count=len(categories),
                total=total,
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

    def get_all_flat(self, user_id: int, workspace_id: UUID, page: int = 1, size: int = 50) -> tuple[List[Category], int]:
        """Get all categories in a flat list (paginated, filtered by workspace)"""
        try:
            # Authorize user (requires 'viewer' role for GET)
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="viewer",
                operation="list_categories_flat"
            )
            
            # Query all categories filtered by workspace_id (flat list)
            query = self.db.query(Category).filter(
                Category.workspace_id == workspace_id
            ).order_by(Category.created_at.desc())
            
            total = query.count()
            categories = query.offset((page - 1) * size).limit(size).all()
            
            return categories, total
        except Exception as e:
            self.logger.error(f"Error retrieving flat categories: {e}")
            raise CategoryValidationError("Failed to retrieve categories")

    def get(self, category_id: int, user_id: int, workspace_id: UUID) -> Category:
        """Get a specific category by ID with workspace validation"""
        # Authorize user in workspace
        self.authorize_workspace_access(
            workspace_id,
            user_id,
            required_role="viewer",
            operation="get_category"
        )
        
        # Get category
        category = self.db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise CategoryNotFoundError(category_id)
        
        # Validate workspace match
        self.validate_workspace_match(
            category.workspace_id,
            workspace_id,
            category_id
        )
        
        # Validate ownership
        if category.user_id != user_id:
            raise CategoryOwnershipError("Category belongs to another user")
        
        return category

    def get_children(self, category_id: int, user_id: int, workspace_id: UUID) -> List[Category]:
        """Get direct children of a category with workspace validation"""
        try:
            # Authorize user in workspace
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="viewer",
                operation="get_category_children"
            )
            
            # Get parent category and validate
            parent = self.db.query(Category).filter(Category.id == category_id).first()
            if not parent:
                raise CategoryNotFoundError(category_id)
            
            self.validate_workspace_match(
                parent.workspace_id,
                workspace_id,
                category_id
            )
            
            # Get children filtered by workspace
            children = self.db.query(Category).filter(
                Category.parent_id == category_id,
                Category.workspace_id == workspace_id
            ).all()
            
            return children
        except Exception as e:
            self.logger.error(f"Error retrieving category children: {e}")
            raise CategoryValidationError("Failed to retrieve category children")

    def update(self, category_id: int, data: CategoryCreate, user_id: int, workspace_id: UUID) -> Category:
        """Update a category with proper validation and transaction management"""
        try:
            # Authorize user (requires 'member' role for PATCH)
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="member",
                operation="update_category"
            )
            
            # Get and validate category
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise CategoryNotFoundError(category_id)
            
            self.validate_workspace_match(category.workspace_id, workspace_id, category_id)
            
            if category.user_id != user_id:
                raise CategoryOwnershipError("Category belongs to another user")
            
            # If changing parent, validate new parent is in same workspace
            if data.parent_id and data.parent_id != category.parent_id:
                new_parent = self.db.query(Category).filter(Category.id == data.parent_id).first()
                if not new_parent:
                    raise CategoryNotFoundError(data.parent_id)
                
                self.validate_workspace_match(new_parent.workspace_id, workspace_id, data.parent_id)
            
            # Comprehensive validation using serializer (with exclude_id for updates)
            self.serializer.validate_category_data(self.db, data, user_id, exclude_id=category_id, workspace_id=workspace_id)
            
            # Serialize data for update
            update_data = self.serializer.serialize_category_for_update(data)
            
            # Update category fields (workspace_id cannot be changed)
            old_name = category.name
            old_parent = category.parent_id
            
            for field, value in update_data.items():
                if field != 'workspace_id':  # Prevent workspace change
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

    def delete(self, category_id: int, user_id: int, workspace_id: UUID) -> dict:
        """Delete a category with proper validation and transaction management"""
        try:
            # Authorize user (requires 'member' role for DELETE)
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="member",
                operation="delete_category"
            )
            
            # Get and validate category
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise CategoryNotFoundError(category_id)
            
            self.validate_workspace_match(category.workspace_id, workspace_id, category_id)
            
            if category.user_id != user_id:
                raise CategoryOwnershipError("Category belongs to another user")
            
            # Check for children in the same workspace
            children_count = self.db.query(Category).filter(
                Category.parent_id == category_id,
                Category.workspace_id == workspace_id
            ).count()
            
            if children_count > 0:
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

    def get_by_id_internal(self, category_id: int, user_id: int, workspace_id: UUID) -> Category:
        """Internal method to get category by ID for internal service calls"""
        try:
            category = self.db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise CategoryNotFoundError(category_id)
            
            # Validate workspace match
            if category.workspace_id != workspace_id:
                raise CategoryOwnershipError("Category not in specified workspace")
            
            # Validate user ownership
            if category.user_id != user_id:
                raise CategoryOwnershipError("Category belongs to another user")
            
            return category
        except Exception as e:
            self.logger.error(f"Error in internal category retrieval: {e}")
            raise CategoryValidationError("Failed to retrieve category for internal validation")

    def check_category_exists_by_mcc(self, mcc_code: int, user_id: int, workspace_id: UUID) -> bool:
        """Check if user already has a category with the given MCC code in workspace"""
        try:
            category = self.db.query(Category).filter(
                Category.workspace_id == workspace_id,
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

    def get_category_by_mcc(self, mcc_code: int, user_id: int, workspace_id: UUID) -> dict:
        """Get category information by MCC code including category ID in workspace"""
        try:
            category = self.db.query(Category).filter(
                Category.workspace_id == workspace_id,
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

    def check_categories_exist_by_mcc_batch(self, mcc_codes: List[int], user_id: int, workspace_id: UUID) -> List[Dict[str, Any]]:
        """Check multiple MCC codes for user categories in a single query within workspace"""
        try:
            self.logger.info(
                f"Starting batch MCC category existence check for user {user_id} in workspace {workspace_id}",
                category="business",
                operation="mcc_category_batch_check_start",
                user_id=user_id,
                workspace_id=str(workspace_id),
                mcc_codes=mcc_codes
            )
            
            # Single query to check all MCC codes at once in workspace
            existing_categories = self.db.query(Category).filter(
                Category.workspace_id == workspace_id,
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

    def get_statistics(self, user_id: int, workspace_id: UUID) -> dict:
        """Get category statistics for a user in a workspace"""
        try:
            # Authorize user
            self.authorize_workspace_access(
                workspace_id,
                user_id,
                required_role="viewer",
                operation="get_statistics"
            )
            
            self.logger.info(
                f"Retrieving category statistics for user {user_id} in workspace {workspace_id}",
                category="business",
                operation="category_statistics_start",
                user_id=user_id,
                workspace_id=str(workspace_id)
            )
            
            # Query all categories for the workspace
            categories = self.db.query(Category).filter(
                Category.workspace_id == workspace_id
            ).all()
            
            # Calculate statistics
            total_categories = len(categories)
            expense_categories = sum(1 for cat in categories if cat.type == CategoryType.EXPENSE)
            income_categories = sum(1 for cat in categories if cat.type == CategoryType.INCOME)
            parent_categories = sum(1 for cat in categories if cat.parent_id is None)
            child_categories = sum(1 for cat in categories if cat.parent_id is not None)
            
            statistics = {
                "total_categories": total_categories,
                "expense_categories": expense_categories,
                "income_categories": income_categories,
                "parent_categories": parent_categories,
                "child_categories": child_categories
            }
            
            self.logger.info(
                f"Category statistics retrieved successfully",
                category="business",
                operation="category_statistics_success",
                user_id=user_id,
                **statistics
            )
            
            return statistics
            
        except Exception as e:
            self.logger.error(
                f"Error retrieving category statistics for user {user_id}: {str(e)}",
                category="business",
                operation="category_statistics_failed",
                user_id=user_id
            )
            raise CategoryValidationError("Failed to retrieve category statistics")