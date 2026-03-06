"""Provider notes API endpoints."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from app.auth import User, get_current_user
from services.notes.notes_service import NotesService

# API prefix from environment variable
API_PREFIX = os.getenv("API_PREFIX", "/api")

router = APIRouter(prefix=f"{API_PREFIX}/notes", tags=["notes"])

# Initialize notes service
notes_service = NotesService()


class Note(BaseModel):
    """Provider note model."""

    id: str = Field(..., description="Note ID")
    patient_id: str = Field(..., description="Patient ID")
    content: str = Field(..., description="Note content")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    created_by: str = Field(..., description="Provider username who created the note")


class NoteCreate(BaseModel):
    """Request model for creating a note."""

    patient_id: str = Field(..., description="Patient ID")
    content: str = Field(..., description="Note content")


class NoteUpdate(BaseModel):
    """Request model for updating a note."""

    content: str = Field(..., description="Updated note content")


@router.get("/patients/{patient_id}")
async def get_patient_notes(
    patient_id: str,
    _current_user: User = Depends(
        get_current_user
    ),  # Authentication required but not used
) -> dict[str, Any]:
    """Get all notes for a specific patient."""
    return notes_service.get_patient_notes(patient_id)


@router.post("/patients/{patient_id}")
async def create_note(
    patient_id: str,
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new note for a patient."""
    # Only providers can create notes
    if current_user.role.value != "provider":
        raise HTTPException(
            status_code=403,
            detail="Only providers can create notes",
        )

    # Verify patient_id matches
    if note_data.patient_id != patient_id:
        raise HTTPException(
            status_code=400,
            detail="Patient ID in URL does not match patient ID in request body",
        )

    return notes_service.create_note(
        patient_id=patient_id,
        content=note_data.content,
        created_by=current_user.username,
    )


@router.put("/patients/{patient_id}/notes/{note_id}")
async def update_note(
    patient_id: str,
    note_id: str,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update an existing note."""
    # Only providers can update notes
    if current_user.role.value != "provider":
        raise HTTPException(
            status_code=403,
            detail="Only providers can update notes",
        )

    try:
        return notes_service.update_note(
            patient_id=patient_id,
            note_id=note_id,
            content=note_data.content,
            updated_by=current_user.username,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e


@router.delete("/patients/{patient_id}/notes/{note_id}")
async def delete_note(
    patient_id: str,
    note_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a note."""
    # Only providers can delete notes
    if current_user.role.value != "provider":
        raise HTTPException(
            status_code=403,
            detail="Only providers can delete notes",
        )

    try:
        return notes_service.delete_note(
            patient_id=patient_id,
            note_id=note_id,
            deleted_by=current_user.username,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e
