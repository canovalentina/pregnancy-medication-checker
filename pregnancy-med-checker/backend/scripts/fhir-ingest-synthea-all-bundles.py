#!/usr/bin/env python3
"""Script to ingest all Synthea bundles into FHIR server.

Usage:
    python scripts/fhir-ingest-synthea-all-bundles.py
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
    DEFAULT_SYNTHEA_DATA_PATH,
    DEFAULT_TEST_DATA_PATH,
    INGESTED_PATIENT_IDENTIFIER_VALUE_TEST,
    FHIRAPIHandlers,
)


async def main() -> None:
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="Ingest Synthea bundles into FHIR server"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Path to FHIR bundle files (default: production data path)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Ingest from test data directory with test tag",
    )

    args = parser.parse_args()

    # Determine data path and ingestion tag
    if args.test:
        data_path = DEFAULT_TEST_DATA_PATH
        ingestion_tag = INGESTED_PATIENT_IDENTIFIER_VALUE_TEST
        logger.info("Ingesting TEST data with test ingestion tag...")
    elif args.data_path:
        data_path = Path(args.data_path)
        # Auto-detect if it's the test directory
        test_path_str = str(DEFAULT_TEST_DATA_PATH)
        data_path_str = str(data_path.resolve())
        if test_path_str in data_path_str or "test" in data_path_str.lower():
            ingestion_tag = INGESTED_PATIENT_IDENTIFIER_VALUE_TEST
            logger.info("Auto-detected test directory, using test ingestion tag...")
        else:
            ingestion_tag = None  # Use default production tag
            logger.info("Using production ingestion tag...")
    else:
        data_path = DEFAULT_SYNTHEA_DATA_PATH
        ingestion_tag = None  # Use default production tag
        logger.info("Ingesting PRODUCTION data with production ingestion tag...")

    logger.info(f"Data path: {data_path}")

    fhir_handlers = FHIRAPIHandlers()

    try:
        result = await fhir_handlers.ingest_resource_data(
            data_path=data_path, max_bundles=None, ingestion_tag=ingestion_tag
        )

        summary_text = (
            f"Ingestion complete! Summary: "
            f"Patients: {result.summary.total_patients}, "
            f"Medications: {result.summary.total_medications}, "
            f"Conditions: {result.summary.total_conditions}, "
            f"Observations: {result.summary.total_observations}, "
            f"Encounters: {result.summary.total_encounters}, "
            f"Procedures: {result.summary.total_procedures}, "
            f"Errors: {result.summary.total_errors}"
        )
        logger.info(summary_text)

        if result.summary.total_errors > 0:
            logger.warning(f"Completed with {result.summary.total_errors} error(s)")
            if result.errors:
                logger.warning("First few errors:")
                for error in result.errors[:5]:
                    logger.warning(f"  - {error}")
        else:
            logger.success("All bundles ingested successfully!")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
