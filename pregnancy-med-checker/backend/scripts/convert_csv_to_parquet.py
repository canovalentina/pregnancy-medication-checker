#!/usr/bin/env python3
"""Convert drug interaction CSV files to Parquet format for faster reads.

Parquet format provides:
- 10-50x faster reads than CSV
- Better compression (smaller file size)
- Columnar format (better for analytics)
- Native Polars support with predicate pushdown

Usage:
    uv run python scripts/convert_csv_to_parquet.py
"""

from pathlib import Path

import polars as pl  # type: ignore[import-untyped]
from loguru import logger

from services.drug_interaction.constants import (
    BASIC_INTERACTIONS_CSV_PATH,
    DRUGBANK_INTERACTIONS_CSV_PATH,
)


def convert_csv_to_parquet(csv_path: Path, parquet_path: Path | None = None) -> Path:
    """Convert a CSV file to Parquet format.

    Args:
        csv_path: Path to the CSV file
        parquet_path: Optional output path (defaults to same location with .parquet extension)

    Returns:
        Path to the created Parquet file
    """
    if parquet_path is None:
        parquet_path = csv_path.with_suffix(".parquet")

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    if parquet_path.exists():
        logger.info(f"Parquet file already exists: {parquet_path}")
        logger.info(f"  CSV size: {csv_path.stat().st_size / 1024 / 1024:.1f} MB")
        logger.info(
            f"  Parquet size: {parquet_path.stat().st_size / 1024 / 1024:.1f} MB"
        )
        return parquet_path

    logger.info(f"Converting {csv_path.name} to Parquet format...")
    logger.info(f"  CSV size: {csv_path.stat().st_size / 1024 / 1024:.1f} MB")

    # Read CSV and convert to Parquet
    # Use streaming for large files to avoid memory issues
    df = pl.scan_csv(csv_path, infer_schema=False, low_memory=True).collect(
        engine="streaming"
    )

    logger.info(f"  Rows: {df.height:,}")
    logger.info(f"  Columns: {len(df.columns)}")

    # Write to Parquet with compression
    df.write_parquet(
        parquet_path,
        compression="zstd",  # Good balance of speed and compression
        compression_level=3,  # Moderate compression (1-22, higher = more compression)
    )

    csv_size = csv_path.stat().st_size / 1024 / 1024
    parquet_size = parquet_path.stat().st_size / 1024 / 1024
    compression_ratio = (1 - parquet_size / csv_size) * 100

    logger.info(f"✓ Conversion complete!")
    logger.info(f"  Parquet size: {parquet_size:.1f} MB")
    logger.info(f"  Compression: {compression_ratio:.1f}% smaller")
    logger.info(f"  File: {parquet_path}")

    return parquet_path


def main():
    """Convert all drug interaction CSV files to Parquet."""
    logger.info("Converting drug interaction CSV files to Parquet format...")

    converted = []

    # Convert DrugBank interactions if available
    if DRUGBANK_INTERACTIONS_CSV_PATH.exists():
        try:
            parquet_path = convert_csv_to_parquet(DRUGBANK_INTERACTIONS_CSV_PATH)
            converted.append(parquet_path)
        except Exception as e:
            logger.error(f"Failed to convert DrugBank CSV: {e}")
    else:
        logger.warning(f"DrugBank CSV not found: {DRUGBANK_INTERACTIONS_CSV_PATH}")

    # Convert basic interactions if available
    if BASIC_INTERACTIONS_CSV_PATH.exists():
        try:
            parquet_path = convert_csv_to_parquet(BASIC_INTERACTIONS_CSV_PATH)
            converted.append(parquet_path)
        except Exception as e:
            logger.error(f"Failed to convert basic CSV: {e}")
    else:
        logger.warning(f"Basic CSV not found: {BASIC_INTERACTIONS_CSV_PATH}")

    if converted:
        logger.info(f"\n✓ Successfully converted {len(converted)} file(s) to Parquet")
        logger.info("The service will automatically use Parquet files when available.")
    else:
        logger.warning("No CSV files found to convert.")


if __name__ == "__main__":
    main()
