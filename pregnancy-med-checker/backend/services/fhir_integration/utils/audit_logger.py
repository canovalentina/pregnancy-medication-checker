"""FHIR operations audit logger for persistent logging of all FHIR operations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..domain.constants import BACKEND_DIR

# FHIR operations audit log directory
_LOG_DIR = BACKEND_DIR / "logs"
_LOG_DIR.mkdir(exist_ok=True)


def _get_current_log_file() -> Path:
    """Get or create the current timestamped log file."""
    # Use function attribute to avoid global variable
    if not hasattr(_get_current_log_file, "_current_log_file"):
        _get_current_log_file._current_log_file = None  # type: ignore[attr-defined]

    current_log_file = _get_current_log_file._current_log_file  # type: ignore[attr-defined]
    if current_log_file is None or not current_log_file.exists():
        timestamp = datetime.now(UTC)
        timestamp_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        current_log_file = _LOG_DIR / f"fhir_operations_{timestamp_str}.log"
        _get_current_log_file._current_log_file = current_log_file  # type: ignore[attr-defined]

    return current_log_file


class FHIRAuditLogger:
    """Logger for FHIR operations (create, read, update, delete, search)."""

    @staticmethod
    def _write_audit_log(operation: str, data: dict[str, Any]) -> None:
        """Write an audit log entry to the persistent log file."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "operation": operation,
            **data,
        }

        try:
            log_file = _get_current_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write FHIR audit log: {e}")

    @staticmethod
    def log_create(
        resource_type: str,
        resource_id: str | None,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Log a resource creation operation."""
        FHIRAuditLogger._write_audit_log(
            "create",
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "success": success,
                "error": error,
            },
        )

    @staticmethod
    def log_read(
        resource_type: str,
        resource_id: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Log a resource read operation."""
        FHIRAuditLogger._write_audit_log(
            "read",
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "success": success,
                "error": error,
            },
        )

    @staticmethod
    def log_update(
        resource_type: str,
        resource_id: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Log a resource update operation."""
        FHIRAuditLogger._write_audit_log(
            "update",
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "success": success,
                "error": error,
            },
        )

    @staticmethod
    def log_delete(
        resource_type: str,
        resource_id: str,
        cascade: bool = False,
        success: bool = True,
        error: str | None = None,
        deleted_referencing_resources: int = 0,
    ) -> None:
        """Log a resource deletion operation."""
        FHIRAuditLogger._write_audit_log(
            "delete",
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "cascade": cascade,
                "success": success,
                "error": error,
                "deleted_referencing_resources": deleted_referencing_resources,
            },
        )

    @staticmethod
    def log_search(
        resource_type: str,
        search_params: dict[str, Any] | None = None,
        result_count: int = 0,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Log a resource search operation."""
        FHIRAuditLogger._write_audit_log(
            "search",
            {
                "resource_type": resource_type,
                "search_params": search_params,
                "result_count": result_count,
                "success": success,
                "error": error,
            },
        )

    @staticmethod
    def log_ingestion(
        data_path: str,
        total_patients: int = 0,
        total_medications: int = 0,
        total_conditions: int = 0,
        total_observations: int = 0,
        total_errors: int = 0,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Log a data ingestion operation."""
        FHIRAuditLogger._write_audit_log(
            "ingest",
            {
                "data_path": str(data_path),
                "total_patients": total_patients,
                "total_medications": total_medications,
                "total_conditions": total_conditions,
                "total_observations": total_observations,
                "total_errors": total_errors,
                "success": success,
                "error": error,
            },
        )

    @staticmethod
    def get_audit_logs(
        operation: str | None = None,
        resource_type: str | None = None,
        limit: int = 100,
        date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Read audit logs from the persistent log file(s)."""
        logs = []

        # If date specified, read all log files from that date
        if date:
            # Match all log files from the specified date
            date_str = date.strftime("%Y-%m-%d")
            log_files = sorted(
                _LOG_DIR.glob(f"fhir_operations_{date_str}_*.log"),
                reverse=True,
            )
        else:
            # Read all log files, sorted by timestamp (most recent first)
            log_files = sorted(
                _LOG_DIR.glob("fhir_operations_*.log"),
                reverse=True,
            )

        try:
            for log_file in log_files:
                if not log_file.exists():
                    continue

                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            log_entry = json.loads(line)
                            # Apply filters
                            if operation and log_entry.get("operation") != operation:
                                continue
                            if (
                                resource_type
                                and log_entry.get("resource_type") != resource_type
                            ):
                                continue
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue

                # Stop if we have enough logs
                if len(logs) >= limit:
                    break

            # Sort by timestamp (most recent first) and limit
            logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return logs[:limit]
        except Exception as e:
            logger.error(f"Failed to read FHIR audit log: {e}")
            return []
