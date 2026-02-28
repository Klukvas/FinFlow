from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.sync_service import SyncService
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    LinkedAccountResponse,
    LinkAccountRequest,
)
from shared.auth.dependencies import get_current_user_id, get_workspace_id

router = APIRouter()


def get_sync_service(db: Session = Depends(get_db)) -> SyncService:
    return SyncService(db)


@router.post("/", response_model=ConnectionResponse, status_code=201)
async def connect_bank(
    payload: ConnectionCreate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    connection = await service.connect(user_id, workspace_id, payload.token)
    return ConnectionResponse(
        id=connection.id,
        bank_type=connection.bank_type,
        client_name=connection.client_name,
        is_active=connection.is_active,
        last_sync_at=connection.last_sync_at,
        created_at=connection.created_at,
        accounts=[
            LinkedAccountResponse.model_validate(acc)
            for acc in connection.linked_accounts
        ],
    )


@router.get("/", response_model=list[ConnectionResponse])
def list_connections(
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    connections = service.get_connections(user_id, workspace_id)
    return [
        ConnectionResponse(
            id=c.id,
            bank_type=c.bank_type,
            client_name=c.client_name,
            is_active=c.is_active,
            last_sync_at=c.last_sync_at,
            created_at=c.created_at,
            accounts=[
                LinkedAccountResponse.model_validate(acc)
                for acc in c.linked_accounts
            ],
        )
        for c in connections
    ]


@router.delete("/{connection_id}", status_code=204)
def disconnect_bank(
    connection_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    service.disconnect(connection_id, user_id, workspace_id)


@router.put("/{connection_id}/accounts/{linked_account_id}/link", response_model=LinkedAccountResponse)
def link_account(
    connection_id: int,
    linked_account_id: int,
    payload: LinkAccountRequest,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    linked = service.link_account(
        connection_id, linked_account_id, payload.finflow_account_id, user_id, workspace_id
    )
    return LinkedAccountResponse.model_validate(linked)


@router.put("/{connection_id}/accounts/{linked_account_id}/toggle", response_model=LinkedAccountResponse)
def toggle_account_sync(
    connection_id: int,
    linked_account_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: SyncService = Depends(get_sync_service),
):
    linked = service.toggle_account_sync(
        connection_id, linked_account_id, user_id, workspace_id
    )
    return LinkedAccountResponse.model_validate(linked)
