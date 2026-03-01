from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.sync_service import SyncService
from app.schemas.sync import (
    SyncRequest,
    SyncStatusResponse,
    SyncPreviewRequest,
    SyncPreviewResponse,
    SyncConfirmRequest,
)
from shared.auth.dependencies import get_current_user_id, get_workspace_id

router = APIRouter()


def get_sync_service(db: Session = Depends(get_db)) -> SyncService:
    return SyncService(db)


@router.post("/{connection_id}/sync", response_model=SyncStatusResponse)
async def trigger_sync(
    connection_id: int,
    payload: SyncRequest = SyncRequest(),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    sync_log = await service.sync_connection(
        connection_id,
        user_id,
        workspace_id,
        account_ids=payload.account_ids,
        days_back=payload.days_back,
    )
    return SyncStatusResponse.model_validate(sync_log)


@router.post("/{connection_id}/sync/preview", response_model=SyncPreviewResponse)
async def preview_sync(
    connection_id: int,
    payload: SyncPreviewRequest = SyncPreviewRequest(),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    result = await service.preview_sync(
        connection_id,
        user_id,
        workspace_id,
        account_ids=payload.account_ids,
        days_back=payload.days_back,
    )
    return SyncPreviewResponse(**result)


@router.post("/{connection_id}/sync/confirm", response_model=SyncStatusResponse)
async def confirm_sync(
    connection_id: int,
    payload: SyncConfirmRequest,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    transactions = [txn.model_dump() for txn in payload.transactions]
    sync_log = await service.confirm_sync(
        connection_id,
        user_id,
        workspace_id,
        transactions=transactions,
        days_back=payload.days_back,
    )
    return SyncStatusResponse.model_validate(sync_log)


@router.get("/{connection_id}/sync/status", response_model=SyncStatusResponse | None)
def get_sync_status(
    connection_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    sync_log = service.get_sync_status(connection_id, user_id, workspace_id)
    if not sync_log:
        return None
    return SyncStatusResponse.model_validate(sync_log)


@router.get("/{connection_id}/sync/history", response_model=list[SyncStatusResponse])
def get_sync_history(
    connection_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    logs = service.get_sync_history(connection_id, user_id, workspace_id, skip, limit)
    return [SyncStatusResponse.model_validate(log) for log in logs]
