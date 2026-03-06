#!/usr/bin/env python3
"""Script to view FHIR audit logs.

Usage:
    python scripts/view_fhir_audit_logs.py
    python scripts/view_fhir_audit_logs.py --operation create
    python scripts/view_fhir_audit_logs.py --operation delete --resource-type Patient
    python scripts/view_fhir_audit_logs.py --limit 50
    python scripts/view_fhir_audit_logs.py --date 2025-11-12
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.fhir_integration.utils.audit_logger import FHIRAuditLogger


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View FHIR audit logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--operation",
        choices=["create", "read", "update", "delete", "search", "ingest"],
        help="Filter by operation type",
    )
    parser.add_argument(
        "--resource-type",
        help="Filter by resource type (e.g., Patient, Observation)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of log entries to show (default: 100)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text",
    )
    parser.add_argument(
        "--date",
        help="Filter by date (YYYY-MM-DD format). If not specified, reads all log files.",
    )

    args = parser.parse_args()

    # Parse date if provided
    date_obj = None
    if args.date:
        try:
            date_obj = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
            return

    logs = FHIRAuditLogger.get_audit_logs(
        operation=args.operation,
        resource_type=args.resource_type,
        limit=args.limit,
        date=date_obj,
    )

    if args.json:
        print(json.dumps(logs, indent=2))
    else:
        if not logs:
            print("No audit logs found.")
            return

        print(f"Found {len(logs)} audit log entries:\n")
        for log in logs:
            timestamp = log.get("timestamp", "unknown")
            operation = log.get("operation", "unknown")
            resource_type = log.get("resource_type", "N/A")
            success = log.get("success", False)

            status = "✓" if success else "✗"
            print(f"[{timestamp}] {status} {operation.upper()} {resource_type}", end="")

            if "resource_id" in log:
                print(f" (ID: {log['resource_id']})", end="")
            if "result_count" in log:
                print(f" (Results: {log['result_count']})", end="")
            if "deleted_referencing_resources" in log:
                print(
                    f" (Deleted {log['deleted_referencing_resources']} referencing resources)",
                    end="",
                )
            if "error" in log:
                print(f" - ERROR: {log['error']}", end="")
            print()


if __name__ == "__main__":
    main()
