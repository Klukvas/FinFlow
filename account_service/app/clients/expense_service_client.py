from fastapi import HTTPException
from app.clients.base import BaseHttpClient
from starlette import status
from app.exceptions import ExternalServiceError
from app.config import settings
from app.utils.logger import get_logger, log_security_event
from typing import Dict, Any, List
from app.schemas.account import AccountTransaction

class ExpenseServiceClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.expense_service_url)
        self.logger = get_logger(__name__)

    def get_expenses_by_account(self, account_id: int, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get expenses for a specific account.
        
        Args:
            account_id: The ID of the account
            user_id: The ID of the user
            limit: Maximum number of expenses to return
            offset: Number of expenses to skip
            
        Returns:
            List of expense dictionaries
            
        Raises:
            HTTPException: If the request fails
        """
        try:
            response = self.get(
                f"/internal/expenses/account/{account_id}",
                headers={"X-Internal-Token": settings.internal_secret_token},
                params={"user_id": user_id, "limit": limit, "offset": offset}
            )
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                log_security_event(
                    self.logger,
                    "Expenses not found for account",
                    user_id,
                    f"Account ID: {account_id}"
                )
                return []
            
            if response.status_code != status.HTTP_200_OK:
                self.logger.error(f"Unexpected response from expense service: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch expenses"
                )
            
            return response.json()
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during expense fetch: {e}")
            raise ExternalServiceError(
                service="expense-service",
                detail=f"Failed to fetch expenses: {str(e)}"
            )

    def validate_account_exists(self, account_id: int, user_id: int) -> bool:
        """
        Validate that an account exists and belongs to the user.
        
        Args:
            account_id: The ID of the account to validate
            user_id: The ID of the user who should own the account
            
        Returns:
            True if account exists and belongs to user, False otherwise
        """
        try:
            response = self.get(
                f"/internal/expenses/account/{account_id}/validate",
                headers={"X-Internal-Token": settings.internal_secret_token},
                params={"user_id": user_id}
            )
            
            return response.status_code == status.HTTP_200_OK
            
        except Exception as e:
            self.logger.error(f"Error validating account with expense service: {e}")
            return False
