"""Notes service for managing provider notes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger


class NotesService:
    """Service for managing provider notes."""

    def __init__(self, notes_file: Path | None = None):
        """Initialize notes service.

        Args:
            notes_file: Path to notes storage file. Defaults to data/notes.json
        """
        self.notes_file = notes_file or Path("data/notes.json")

    def _ensure_notes_file(self) -> None:
        """Ensure the notes file exists."""
        self.notes_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.notes_file.exists():
            self.notes_file.write_text("{}", encoding="utf-8")

    def _load_notes(self) -> dict[str, list[dict[str, Any]]]:
        """Load notes from file.

        Returns:
            Dictionary mapping patient_id to list of notes
        """
        self._ensure_notes_file()
        try:
            content = self.notes_file.read_text(encoding="utf-8")
            return json.loads(content) if content.strip() else {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_notes(self, notes: dict[str, list[dict[str, Any]]]) -> None:
        """Save notes to file.

        Args:
            notes: Dictionary mapping patient_id to list of notes
        """
        self._ensure_notes_file()
        self.notes_file.write_text(json.dumps(notes, indent=2), encoding="utf-8")

    def get_patient_notes(self, patient_id: str) -> dict[str, Any]:
        """Get all notes for a specific patient.

        Args:
            patient_id: Patient ID to get notes for

        Returns:
            Dictionary with patient_id, notes list, and total count
        """
        notes = self._load_notes()
        patient_notes = notes.get(patient_id, [])

        # Sort by updated_at descending (most recent first)
        patient_notes.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return {
            "patient_id": patient_id,
            "notes": patient_notes,
            "total": len(patient_notes),
        }

    def create_note(
        self,
        patient_id: str,
        content: str,
        created_by: str,
    ) -> dict[str, Any]:
        """Create a new note for a patient.

        Args:
            patient_id: Patient ID
            content: Note content
            created_by: Username of provider creating the note

        Returns:
            Dictionary with message and created note data
        """
        notes = self._load_notes()
        patient_notes = notes.get(patient_id, [])

        # Create new note
        note_id = f"note_{datetime.now(UTC).isoformat().replace(':', '-')}"
        now = datetime.now(UTC).isoformat()

        new_note = {
            "id": note_id,
            "patient_id": patient_id,
            "content": content,
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
        }

        patient_notes.append(new_note)
        notes[patient_id] = patient_notes
        self._save_notes(notes)

        logger.info(f"Created note {note_id} for patient {patient_id} by {created_by}")

        return {
            "message": "Note created successfully",
            "note": new_note,
        }

    def update_note(
        self,
        patient_id: str,
        note_id: str,
        content: str,
        updated_by: str,
    ) -> dict[str, Any]:
        """Update an existing note.

        Args:
            patient_id: Patient ID
            note_id: Note ID to update
            content: Updated note content
            updated_by: Username of provider updating the note

        Returns:
            Dictionary with message and updated note data

        Raises:
            ValueError: If note not found
        """
        notes = self._load_notes()
        patient_notes = notes.get(patient_id, [])

        # Find and update the note
        note_found = False
        for note in patient_notes:
            if note["id"] == note_id:
                note["content"] = content
                note["updated_at"] = datetime.now(UTC).isoformat()
                note_found = True
                break

        if not note_found:
            raise ValueError(f"Note {note_id} not found for patient {patient_id}")

        notes[patient_id] = patient_notes
        self._save_notes(notes)

        logger.info(f"Updated note {note_id} for patient {patient_id} by {updated_by}")

        return {
            "message": "Note updated successfully",
            "note": next(n for n in patient_notes if n["id"] == note_id),
        }

    def delete_note(
        self,
        patient_id: str,
        note_id: str,
        deleted_by: str,
    ) -> dict[str, Any]:
        """Delete a note.

        Args:
            patient_id: Patient ID
            note_id: Note ID to delete
            deleted_by: Username of provider deleting the note

        Returns:
            Dictionary with success message

        Raises:
            ValueError: If note not found
        """
        notes = self._load_notes()
        patient_notes = notes.get(patient_id, [])

        # Find and remove the note
        original_length = len(patient_notes)
        patient_notes = [n for n in patient_notes if n["id"] != note_id]

        if len(patient_notes) == original_length:
            raise ValueError(f"Note {note_id} not found for patient {patient_id}")

        notes[patient_id] = patient_notes
        self._save_notes(notes)

        logger.info(f"Deleted note {note_id} for patient {patient_id} by {deleted_by}")

        return {
            "message": "Note deleted successfully",
        }
