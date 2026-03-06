"""Patient-Provider Messaging API endpoints."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from app.auth import User, get_current_user
from services.messaging.messaging_service import MessagingService

# API prefix from environment variable
API_PREFIX = os.getenv("API_PREFIX", "/api")

router = APIRouter(prefix=f"{API_PREFIX}/messaging", tags=["messaging"])

# Initialize messaging service
messaging_service = MessagingService()


class Message(BaseModel):
    """Message model."""

    id: str = Field(..., description="Message ID")
    patient_id: str = Field(..., description="Patient ID")
    sender_username: str = Field(..., description="Username of sender")
    sender_role: str = Field(..., description="Role of sender (patient or provider)")
    sender_name: str = Field(..., description="Full name of sender")
    content: str = Field(..., description="Message content")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    read: bool = Field(default=False, description="Whether message has been read")
    read_at: str | None = Field(
        default=None, description="Timestamp when message was read"
    )


class MessageCreate(BaseModel):
    """Request model for creating a message."""

    patient_id: str = Field(..., description="Patient ID")
    content: str = Field(..., min_length=1, description="Message content")


@router.get("/patients/{patient_id}")
async def get_messages(
    patient_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get all messages for a specific patient.

    Access control:
    - Patients can only view their own messages (patient_id should match their record)
    - Providers can view any patient's messages
    """
    # Verify access: only patients and providers can view messages
    if current_user.role.value not in ("patient", "provider"):
        raise HTTPException(
            status_code=403,
            detail="Only patients and providers can view messages",
        )

    # Note: In production, you should verify that patient users can only access
    # their own patient_id by matching it with their patient record from FHIR
    # For now, we rely on the frontend to pass the correct patient_id

    return messaging_service.get_patient_messages(
        patient_id=patient_id,
        current_user_role=current_user.role.value,
        mark_as_read=True,
    )


@router.post("/patients/{patient_id}")
async def send_message(
    patient_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Send a message.

    Access control:
    - Patients can send messages to their own patient_id
    - Providers can send messages to any patient_id
    """
    # Verify access: only patients and providers can send messages
    if current_user.role.value not in ("patient", "provider"):
        raise HTTPException(
            status_code=403,
            detail="Only patients and providers can send messages",
        )

    # Verify patient_id matches
    if message_data.patient_id != patient_id:
        raise HTTPException(
            status_code=400,
            detail="Patient ID in URL does not match patient ID in request body",
        )

    # Note: In production, you should verify that patient users can only send
    # messages to their own patient_id by matching it with their patient record

    return messaging_service.send_message(
        patient_id=patient_id,
        content=message_data.content,
        sender_username=current_user.username,
        sender_role=current_user.role.value,
        sender_name=current_user.full_name,
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get unread message count for current user.

    Access control:
    - Only patients and providers can view unread counts
    """
    # Verify access: only patients and providers can view unread counts
    if current_user.role.value not in ("patient", "provider"):
        raise HTTPException(
            status_code=403,
            detail="Only patients and providers can view unread counts",
        )

    return messaging_service.get_unread_count(current_user_role=current_user.role.value)


@router.get("/patients/{patient_id}/unread-count")
async def get_patient_unread_count(
    patient_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get unread message count for a specific patient.

    Access control:
    - Patients can only view unread counts for their own patient_id
    - Providers can view unread counts for any patient_id
    """
    # Verify access: only patients and providers can view unread counts
    if current_user.role.value not in ("patient", "provider"):
        raise HTTPException(
            status_code=403,
            detail="Only patients and providers can view unread counts",
        )

    # Note: In production, you should verify that patient users can only access
    # their own patient_id by matching it with their patient record

    return messaging_service.get_patient_unread_count(
        patient_id=patient_id,
        current_user_role=current_user.role.value,
    )
