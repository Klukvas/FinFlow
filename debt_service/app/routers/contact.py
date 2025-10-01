from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user_id, get_contact_service
from app.services.contact import ContactService
from app.schemas.contact import (
    ContactCreate, ContactUpdate, ContactResponse, ContactSummary
)
from app.exceptions import (
    ContactNotFoundError,
    ContactValidationError
)

router = APIRouter()


# Contact Endpoints
@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    user_id: int = Depends(get_current_user_id),
    service: ContactService = Depends(get_contact_service)
):
    """Create a new contact"""
    try:
        return await service.create_contact(contact, user_id)
    except ContactValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[ContactResponse])
def get_contacts(
    skip: int = Query(0, ge=0, description="Number of contacts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of contacts to return"),
    user_id: int = Depends(get_current_user_id),
    service: ContactService = Depends(get_contact_service)
):
    """Get all contacts for the user"""
    return service.get_contacts(user_id, skip, limit)

@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    user_id: int = Depends(get_current_user_id),
    service: ContactService = Depends(get_contact_service)
):
    """Get a specific contact"""
    try:
        return service.get_contact(contact_id, user_id)
    except ContactNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact_update: ContactUpdate,
    user_id: int = Depends(get_current_user_id),
    service: ContactService = Depends(get_contact_service)
):
    """Update a contact"""
    try:
        return await service.update_contact(contact_id, contact_update, user_id)
    except ContactNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ContactValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: int,
    user_id: int = Depends(get_current_user_id),
    service: ContactService = Depends(get_contact_service)
):
    """Delete a contact"""
    try:
        service.delete_contact(contact_id, user_id)
    except ContactNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ContactValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/summaries/", response_model=List[ContactSummary])
def get_contact_summaries(
    user_id: int = Depends(get_current_user_id),
    service: ContactService = Depends(get_contact_service)
):
    """Get contact summaries with debt information"""
    return service.get_contact_summaries(user_id)
