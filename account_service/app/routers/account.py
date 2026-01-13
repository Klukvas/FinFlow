from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.dependencies import get_account_service, get_db, get_current_user_id, get_workspace_id
from app.services.account import AccountService
from app.schemas.account import (
    AccountCreate, 
    AccountUpdate, 
    AccountResponse, 
    AccountSummary,
    AccountTransactionSummary,
    AccountStatisticsResponse
)

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Create a new account. Requires 'member' role."""
    account = service.create_account(account_data, user_id, workspace_id)
    return AccountResponse.model_validate(account)

@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    include_archived: bool = Query(False, description="Include archived accounts"),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> List[AccountResponse]:
    """List all accounts in the workspace. Requires 'viewer' role."""
    accounts = service.get_user_accounts(user_id, workspace_id, include_archived)
    return [AccountResponse.model_validate(account) for account in accounts]

@router.get("/summaries", response_model=List[AccountSummary])
async def get_account_summaries(
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> List[AccountSummary]:
    """Get summaries for all accounts in workspace. Requires 'viewer' role."""
    return service.get_user_account_summaries(user_id, workspace_id)

@router.get("/statistics", response_model=AccountStatisticsResponse)
async def get_account_statistics(
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountStatisticsResponse:
    """Get account statistics with currency conversion. Requires 'viewer' role."""
    return await service.get_account_statistics(user_id, workspace_id)

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Get a specific account by ID. Requires 'viewer' role."""
    account = service.get_account(account_id, user_id, workspace_id)
    return AccountResponse.model_validate(account)

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Update an existing account. Requires 'member' role."""
    account = service.update_account(account_id, account_data, user_id, workspace_id)
    return AccountResponse.model_validate(account)

@router.patch("/{account_id}/archive", response_model=AccountResponse)
async def archive_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Archive an account (soft delete). Requires 'member' role."""
    account = service.archive_account(account_id, user_id, workspace_id)
    return AccountResponse.model_validate(account)

@router.get("/{account_id}/summary", response_model=AccountSummary)
async def get_account_summary(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountSummary:
    """Get account summary with transaction counts. Requires 'viewer' role."""
    return service.get_account_summary(account_id, user_id, workspace_id)

@router.get("/{account_id}/transactions", response_model=AccountTransactionSummary)
async def get_account_transactions(
    account_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountTransactionSummary:
    """Get account transactions from expense and income services. Requires 'viewer' role."""
    return service.get_account_transactions(account_id, user_id, workspace_id, limit, offset)

@router.patch("/{account_id}/balance", response_model=AccountResponse)
async def update_balance(
    account_id: int,
    balance: float,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Update account balance. Requires 'member' role."""
    account = service.update_balance(account_id, balance, user_id, workspace_id)
    return AccountResponse.model_validate(account)
