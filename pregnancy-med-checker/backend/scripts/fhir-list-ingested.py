#!/usr/bin/env python3
"""Script to list all ingested patients from FHIR server.

Usage:
    python scripts/fhir-list-ingested.py
    python scripts/fhir-list-ingested.py --json
    python scripts/fhir-list-ingested.py --limit 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from services.fhir_integration import FHIRAPIHandlers


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List all ingested patients from FHIR server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of patient IDs to display (default: all)",
    )

    args = parser.parse_args()

    logger.info("Getting ingested patient IDs...")

    fhir_handlers = FHIRAPIHandlers()

    try:
        result = await fhir_handlers.get_ingested_patient_ids()

        # Extract data safely
        data = result.data if result.data else {}

        count = data.get("count", 0)
        patient_ids = data.get("patient_ids", [])

        if args.json:
            output = {
                "count": count,
                "patient_ids": patient_ids[: args.limit] if args.limit else patient_ids,
            }
            print(json.dumps(output, indent=2))
        else:
            logger.info(f"Found {count} ingested patient(s)")

            if patient_ids:
                display_ids = patient_ids[: args.limit] if args.limit else patient_ids
                logger.info("Patient IDs:")
                for patient_id in display_ids:
                    logger.info(f"  - {patient_id}")

                if args.limit and len(patient_ids) > args.limit:
                    logger.info(f"  ... and {len(patient_ids) - args.limit} more")
            else:
                logger.info("No patient IDs found")

            logger.success(f"Successfully retrieved {count} ingested patient ID(s)")

    except Exception as e:
        logger.error(f"Error getting ingested patient IDs: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
