from fastapi import HTTPException
from shared.clients import BaseHttpClient
from starlette import status
from shared.clients.base import ExternalServiceError
from app.exceptions import CategoryValidationError
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Dict, Any, Optional
from uuid import UUID

class CategoryServiceClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.CATEGORY_SERVICE_URL)
        self.logger = get_logger(__name__)

    def validate_category(self, category_id: Optional[int], user_id: int, workspace_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Validate that a category exists and belongs to the user in the workspace.
        
        Args:
            category_id: The ID of the category to validate
            user_id: The ID of the user who should own the category
            workspace_id: The UUID of the workspace (required for workspace-scoped validation)
            
        Returns:
            Dict containing category information if valid
            
        Raises:
            HTTPException: If category validation fails
        """
        # If category_id is None, return empty dict (no validation needed)
        if category_id is None:
            return {}
        
        # workspace_id is required for validation
        if workspace_id is None:
            self.logger.error("workspace_id is required for category validation")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="workspace_id is required for category validation"
            )
            
        try:
            response = self.get(
                f"/internal/categories/{category_id}?user_id={user_id}&workspace_id={str(workspace_id)}",
                headers={"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}
            )
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                log_security_event(
                    self.logger,
                    "Category validation failed - not found",
                    user_id,
                    f"Category ID: {category_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=CategoryValidationError.NOT_FOUND.value
                )
            
            if response.status_code == status.HTTP_403_FORBIDDEN:
                log_security_event(
                    self.logger,
                    "Category validation failed - unauthorized access",
                    user_id,
                    f"Category ID: {category_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=CategoryValidationError.NOT_OWNED.value
                )
            
            if response.status_code != status.HTTP_200_OK:
                self.logger.error(f"Unexpected response from category service: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=CategoryValidationError.SERVICE_ERROR.value
                )
            
            # Parse and return category data
            category_data = response.json()
            self.logger.info(f"Category {category_id} validated successfully for user {user_id}")
            return category_data
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during category validation: {e}")
            raise ExternalServiceError(
                service="category-service",
                detail=f"Failed to validate category: {str(e)}"
            )
