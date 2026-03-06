#!/usr/bin/env python3
"""Script to delete all ingested patients from FHIR server.

This will find and delete all patients with the ingestion identifier,
along with all their associated resources (cascade delete).

Usage:
    python scripts/fhir-delete-all-ingested.py
    python scripts/fhir-delete-all-ingested.py --no-cascade
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from services.fhir_integration import (
    INGESTED_PATIENT_IDENTIFIER_VALUE_TEST,
    FHIRAPIHandlers,
)


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Delete all ingested patients from FHIR server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--no-cascade",
        action="store_true",
        help="Don't cascade delete (only delete patient resources, not referencing resources)",
    )
    parser.add_argument(
        "--test-tag",
        action="store_true",
        help="Delete patients with test ingestion tag instead of production tag",
    )

    args = parser.parse_args()
    cascade = not args.no_cascade
    ingestion_tag = INGESTED_PATIENT_IDENTIFIER_VALUE_TEST if args.test_tag else None

    tag_display = ingestion_tag or "production"
    logger.info(f"Deleting all ingested patients (tag: {tag_display})...")
    if cascade:
        logger.info(
            "Cascade delete enabled (will delete patient and all referencing resources)"
        )
    else:
        logger.info("Cascade delete disabled (will only delete patient resources)")

    fhir_handlers = FHIRAPIHandlers()

    try:
        result = await fhir_handlers.delete_all_ingested_patients(
            cascade=cascade, ingestion_tag=ingestion_tag
        )

        # Extract data safely
        data = result.data if result.data else {}

        total_found = data.get("total_found", 0)
        total_deleted = data.get("total_deleted", 0)
        failed = data.get("failed", [])

        logger.info(
            f"Deletion summary: Total found: {total_found}, "
            f"Total deleted: {total_deleted}, Failed: {len(failed)}"
        )

        if failed:
            logger.warning(f"Failed to delete {len(failed)} patient(s):")
            for patient_id in failed[:10]:
                logger.warning(f"  - {patient_id}")
            if len(failed) > 10:
                logger.warning(f"  ... and {len(failed) - 10} more")

        if result.status == "success":
            logger.success(
                f"Successfully deleted all {total_deleted} ingested patient(s)"
            )
        elif result.status == "partial":
            logger.warning(f"Partially deleted: {total_deleted}/{total_found} patients")
        else:
            logger.error(f"Failed to delete patients: {result.message}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error deleting ingested patients: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
