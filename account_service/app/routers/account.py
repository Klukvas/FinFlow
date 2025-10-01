from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_account_service, get_db, get_current_user_id
from app.services.account import AccountService
from app.schemas.account import (
    AccountCreate, 
    AccountUpdate, 
    AccountResponse, 
    AccountSummary,
    AccountTransactionSummary
)
from app.exceptions import AccountNotFoundError, AccountValidationError, AccountArchivedError

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Create a new account"""
    try:
        account = service.create_account(account_data, user_id)
        return AccountResponse.model_validate(account)
    except AccountValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    include_archived: bool = Query(False, description="Include archived accounts"),
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> List[AccountResponse]:
    """List all accounts for the authenticated user"""
    accounts = service.get_user_accounts(user_id, include_archived)
    return [AccountResponse.model_validate(account) for account in accounts]

@router.get("/summaries", response_model=List[AccountSummary])
async def get_account_summaries(
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> List[AccountSummary]:
    """Get summaries for all user accounts"""
    try:
        return service.get_user_account_summaries(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch account summaries: {str(e)}"
        )

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Get a specific account by ID"""
    try:
        account = service.get_account(account_id, user_id)
        return AccountResponse.model_validate(account)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Update an existing account"""
    try:
        account = service.update_account(account_id, account_data, user_id)
        return AccountResponse.model_validate(account)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except AccountArchivedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except AccountValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.patch("/{account_id}/archive", response_model=AccountResponse)
async def archive_account(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Archive an account (soft delete)"""
    try:
        account = service.archive_account(account_id, user_id)
        return AccountResponse.model_validate(account)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except AccountArchivedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.get("/{account_id}/summary", response_model=AccountSummary)
async def get_account_summary(
    account_id: int,
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> AccountSummary:
    """Get account summary with transaction counts"""
    try:
        return service.get_account_summary(account_id, user_id)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )

@router.get("/{account_id}/transactions", response_model=AccountTransactionSummary)
async def get_account_transactions(
    account_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> AccountTransactionSummary:
    """Get account transactions from expense and income services"""
    try:
        return service.get_account_transactions(account_id, user_id, limit, offset)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except AccountValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )

@router.patch("/{account_id}/balance", response_model=AccountResponse)
async def update_balance(
    account_id: int,
    balance: float,
    user_id: int = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:
    """Update account balance"""
    try:
        account = service.update_balance(account_id, balance, user_id)
        return AccountResponse.model_validate(account)
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except AccountArchivedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except AccountValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
