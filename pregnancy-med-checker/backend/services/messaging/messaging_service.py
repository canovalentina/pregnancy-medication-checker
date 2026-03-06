"""Messaging service for patient-provider messaging."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger


class MessagingService:
    """Service for managing patient-provider messages."""

    def __init__(self, messages_file: Path | None = None):
        """Initialize messaging service.

        Args:
            messages_file: Path to messages storage file. Defaults to data/messages.json
        """
        self.messages_file = messages_file or Path("data/messages.json")

    def _ensure_messages_file(self) -> None:
        """Ensure the messages file exists."""
        self.messages_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.messages_file.exists():
            self.messages_file.write_text("{}", encoding="utf-8")

    def _load_messages(self) -> dict[str, list[dict[str, Any]]]:
        """Load messages from file.

        Returns:
            Dictionary mapping patient_id to list of messages
        """
        self._ensure_messages_file()
        try:
            content = self.messages_file.read_text(encoding="utf-8")
            return json.loads(content) if content.strip() else {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_messages(self, messages: dict[str, list[dict[str, Any]]]) -> None:
        """Save messages to file.

        Args:
            messages: Dictionary mapping patient_id to list of messages
        """
        self._ensure_messages_file()
        self.messages_file.write_text(json.dumps(messages, indent=2), encoding="utf-8")

    def get_patient_messages(
        self,
        patient_id: str,
        current_user_role: str,
        mark_as_read: bool = True,
    ) -> dict[str, Any]:
        """Get all messages for a specific patient.

        Args:
            patient_id: Patient ID to get messages for
            current_user_role: Role of the current user ('patient' or 'provider')
            mark_as_read: Whether to mark messages as read when viewed by recipient

        Returns:
            Dictionary with patient_id, messages list, total count, and unread count
        """
        messages = self._load_messages()
        patient_messages = messages.get(patient_id, [])

        # Sort by created_at ascending (oldest first for conversation view)
        patient_messages.sort(key=lambda x: x.get("created_at", ""))

        # Mark messages as read if viewed by the recipient
        if mark_as_read:
            now = datetime.now(UTC).isoformat()
            updated = False
            for msg in patient_messages:
                # Mark as read if the current user is the recipient (opposite role)
                is_recipient = (
                    current_user_role == "patient"
                    and msg.get("sender_role") == "provider"
                ) or (
                    current_user_role == "provider"
                    and msg.get("sender_role") == "patient"
                )
                if is_recipient and not msg.get("read", False):
                    msg["read"] = True
                    msg["read_at"] = now
                    updated = True

            if updated:
                messages[patient_id] = patient_messages
                self._save_messages(messages)

        # Calculate unread count for the current user
        unread_count = sum(
            1
            for msg in patient_messages
            if not msg.get("read", False)
            and (
                (
                    current_user_role == "patient"
                    and msg.get("sender_role") == "provider"
                )
                or (
                    current_user_role == "provider"
                    and msg.get("sender_role") == "patient"
                )
            )
        )

        return {
            "patient_id": patient_id,
            "messages": patient_messages,
            "total": len(patient_messages),
            "unread_count": unread_count,
        }

    def send_message(
        self,
        patient_id: str,
        content: str,
        sender_username: str,
        sender_role: str,
        sender_name: str,
    ) -> dict[str, Any]:
        """Send a message.

        Args:
            patient_id: Patient ID
            content: Message content
            sender_username: Username of sender
            sender_role: Role of sender ('patient' or 'provider')
            sender_name: Full name of sender

        Returns:
            Dictionary with message and created message data
        """
        messages = self._load_messages()
        patient_messages = messages.get(patient_id, [])

        # Create new message
        message_id = (
            f"msg_{datetime.now(UTC).isoformat().replace(':', '-').replace('.', '-')}"
        )
        now = datetime.now(UTC).isoformat()

        new_message = {
            "id": message_id,
            "patient_id": patient_id,
            "sender_username": sender_username,
            "sender_role": sender_role,
            "sender_name": sender_name,
            "content": content,
            "created_at": now,
            "read": False,
            "read_at": None,
        }

        patient_messages.append(new_message)
        messages[patient_id] = patient_messages
        self._save_messages(messages)

        logger.info(
            f"Message {message_id} sent from {sender_username} ({sender_role}) "
            f"to patient {patient_id}"
        )

        return {
            "message": "Message sent successfully",
            "message_data": new_message,
        }

    def get_unread_count(self, current_user_role: str) -> dict[str, Any]:
        """Get unread message count for current user.

        Args:
            current_user_role: Role of the current user ('patient' or 'provider')

        Returns:
            Dictionary with unread_count
        """
        messages = self._load_messages()
        total_unread = 0

        if current_user_role == "patient":
            # For patients, count unread messages from providers
            for patient_messages in messages.values():
                for msg in patient_messages:
                    if msg.get("sender_role") == "provider" and not msg.get(
                        "read", False
                    ):
                        total_unread += 1
        elif current_user_role == "provider":
            # For providers, count unread messages from patients
            for patient_messages in messages.values():
                for msg in patient_messages:
                    if msg.get("sender_role") == "patient" and not msg.get(
                        "read", False
                    ):
                        total_unread += 1

        return {
            "unread_count": total_unread,
        }

    def get_patient_unread_count(
        self, patient_id: str, current_user_role: str
    ) -> dict[str, Any]:
        """Get unread message count for a specific patient.

        Args:
            patient_id: Patient ID
            current_user_role: Role of the current user ('patient' or 'provider')

        Returns:
            Dictionary with patient_id and unread_count
        """
        messages = self._load_messages()
        patient_messages = messages.get(patient_id, [])

        unread_count = 0
        for msg in patient_messages:
            is_recipient = (
                current_user_role == "patient" and msg.get("sender_role") == "provider"
            ) or (
                current_user_role == "provider" and msg.get("sender_role") == "patient"
            )
            if is_recipient and not msg.get("read", False):
                unread_count += 1

        return {
            "patient_id": patient_id,
            "unread_count": unread_count,
        }
