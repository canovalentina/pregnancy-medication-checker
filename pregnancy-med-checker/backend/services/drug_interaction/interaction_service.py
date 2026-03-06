from pathlib import Path

import polars as pl  # type: ignore[import-untyped]
from cachetools import LRUCache
from loguru import logger

from .constants import (
    BASIC_INTERACTIONS_CSV_PATH,
    DRUG_1_COLUMN,
    DRUG_2_COLUMN,
    DRUGBANK_INTERACTIONS_CSV_PATH,
    INTERACTION_DESCRIPTION_COLUMN,
    MANDATORY_COLUMNS,
)

# Module-level cache for drug interactions (avoids memory leaks from instance method caching)
# Cache stores up to 10,000 recent drug pair lookups (~1-2MB memory)
_interaction_cache: LRUCache[tuple[str, str], str | None] = LRUCache(maxsize=10000)


class DrugInteractionChecker:
    """Service for checking drug interactions from CSV data using lazy loading.

    This service uses Polars LazyFrames to avoid loading the entire dataset
    into memory. Only filtered results are collected when queried.
    """

    def __init__(self, csv_path: str | Path, data_source: str = "Unknown"):
        """Initialize the checker with a CSV file path."""
        self.csv_path = Path(csv_path)
        self.data_source = data_source  # Track data source (DrugBank, Basic, etc.)
        self._lazy_frame: pl.LazyFrame | None = None
        self.drug_1_col: str | None = None
        self.drug_2_col: str | None = None
        self.interaction_col: str | None = None
        self._row_count: int = 0
        self._setup_lazy_frame()

    def _normalize_column_name(self, col_name: str) -> str:
        """Normalize column name: lowercase, strip, replace spaces and hyphens with underscores."""
        return col_name.lower().strip().replace(" ", "_").replace("-", "_")

    def _validate_columns(self, columns: list[str]) -> None:
        """Validate that all required columns exist."""
        df_columns = {self._normalize_column_name(c) for c in columns}
        missing_columns = []
        for col in MANDATORY_COLUMNS:
            normalized_col = self._normalize_column_name(col)
            if normalized_col not in df_columns:
                missing_columns.append(col)

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}. "
                f"Found columns: {sorted(df_columns)}"
            )

    def _setup_lazy_frame(self) -> None:
        """Set up lazy frame for memory-efficient querying.

        Uses Polars LazyFrame to avoid loading the entire dataset into memory.
        Prefers Parquet format if available (10-50x faster), falls back to CSV.
        The data is only read and filtered when get_interaction() is called.
        """
        # Check for Parquet version (much faster than CSV)
        parquet_path = self.csv_path.with_suffix(".parquet")
        if parquet_path.exists():
            logger.info(f"Using Parquet format for faster reads: {parquet_path.name}")
            lazy_frame = pl.scan_parquet(parquet_path)
        else:
            logger.info(
                f"Using CSV format: {self.csv_path.name} "
                f"(consider converting to Parquet for 10-50x speedup)"
            )
            # Create a lazy frame - this doesn't load data into memory
            # Only reads schema/metadata
            lazy_frame = pl.scan_csv(
                self.csv_path,
                infer_schema=False,
                low_memory=True,
                rechunk=False,  # Don't rechunk for better streaming performance
            )

        # Get column names from schema (doesn't load data)
        schema_columns = lazy_frame.collect_schema().names()

        # Normalize column names mapping
        normalized_cols = {
            col: self._normalize_column_name(col) for col in schema_columns
        }

        # Validate required columns exist
        self._validate_columns(schema_columns)

        # Set column references using normalized names
        self.drug_1_col = self._normalize_column_name(DRUG_1_COLUMN)
        self.drug_2_col = self._normalize_column_name(DRUG_2_COLUMN)
        self.interaction_col = self._normalize_column_name(
            INTERACTION_DESCRIPTION_COLUMN
        )

        # Apply transformations lazily (no data loaded yet)
        self._lazy_frame = lazy_frame.rename(normalized_cols).with_columns(
            [
                pl.col(self.drug_1_col)
                .cast(pl.Utf8)
                .str.to_lowercase()
                .str.strip_chars()
                .alias(self.drug_1_col),
                pl.col(self.drug_2_col)
                .cast(pl.Utf8)
                .str.to_lowercase()
                .str.strip_chars()
                .alias(self.drug_2_col),
                pl.col(self.interaction_col).cast(pl.Utf8).alias(self.interaction_col),
            ]
        )

        # Get row count efficiently (reads file but doesn't store in memory)
        # Use a separate scan to count rows without keeping data
        self._row_count = pl.scan_csv(self.csv_path).select(pl.len()).collect().item()

        logger.info(
            f"✓ Lazy frame ready for {self._row_count:,} interaction records from {self.data_source} "
            f"({self.csv_path.name}) - memory-efficient mode"
        )

    @staticmethod
    def normalize_drug_name(drug_name: str) -> str:
        """Normalize a drug name for consistent matching."""
        return str(drug_name).lower().strip()

    def get_interaction(self, drug_a: str, drug_b: str) -> str | None:
        """Get interaction description between two drugs (bidirectional lookup).

        Uses lazy evaluation to filter data without loading entire dataset.
        Results are cached for faster repeated lookups.
        """
        # Normalize input drug names and sort for consistent cache keys
        a = self.normalize_drug_name(drug_a)
        b = self.normalize_drug_name(drug_b)

        # Sort drug names for bidirectional cache key (A,B == B,A)
        # Use explicit tuple construction to preserve type (tuple[str, str])
        cache_key: tuple[str, str] = (a, b) if a <= b else (b, a)

        # Check module-level cache first
        if cache_key in _interaction_cache:
            return _interaction_cache[cache_key]

        # Cache miss - query the database
        result = self._query_interaction(a, b)

        # Store in cache
        _interaction_cache[cache_key] = result

        return result

    def _query_interaction(self, a: str, b: str) -> str | None:
        """Query interaction from database (uncached).

        This method performs the actual database query without caching.
        """
        error_str = "Lazy frame not initialized. Call _setup_lazy_frame() first."
        if (
            self._lazy_frame is None
            or self.drug_1_col is None
            or self.drug_2_col is None
            or self.interaction_col is None
        ):
            raise RuntimeError(error_str)

        logger.debug(
            f"Querying interaction between '{a}' and '{b}' "
            f"from {self.data_source} (cache miss)"
        )

        # Filter lazily and only collect the matching result
        # Optimized: Use streaming mode for large files, early termination with head(1)
        # This streams through the file and only loads matching rows into memory
        result = (
            self._lazy_frame.filter(
                ((pl.col(self.drug_1_col) == a) & (pl.col(self.drug_2_col) == b))
                | ((pl.col(self.drug_1_col) == b) & (pl.col(self.drug_2_col) == a))
            )
            .select(self.interaction_col)
            .head(1)  # Early termination - stop after first match
            .collect(engine="streaming")  # Use streaming for large files
        )

        # No match found
        if result.height == 0:
            logger.debug(
                f"No interaction found between '{a}' and '{b}' "
                f"in {self.data_source} database"
            )
            return None

        # Return the interaction description from the first matching row
        interaction_desc = result.item()
        logger.debug(
            f"Found interaction between '{a}' and '{b}' "
            f"in {self.data_source} database"
        )
        return interaction_desc

    def get_interactions_batch(
        self, drug_pairs: list[tuple[str, str]]
    ) -> dict[tuple[str, str], str | None]:
        """Get interactions for multiple drug pairs efficiently.

        This is more efficient than calling get_interaction() multiple times
        because it can batch queries and leverage cache better.

        Args:
            drug_pairs: List of (drug_a, drug_b) tuples

        Returns:
            Dictionary mapping (drug_a, drug_b) -> interaction description or None
        """
        results = {}
        for drug_a, drug_b in drug_pairs:
            results[(drug_a, drug_b)] = self.get_interaction(drug_a, drug_b)
        return results

    def clear_cache(self) -> None:
        """Clear the interaction lookup cache."""
        _interaction_cache.clear()
        logger.debug("Cleared interaction cache")

    def cache_info(self) -> dict:
        """Get cache statistics."""
        # Note: LRUCache doesn't track hits/misses, so we estimate from size
        return {
            "size": len(_interaction_cache),
            "maxsize": _interaction_cache.maxsize,
            "usage": f"{len(_interaction_cache) / _interaction_cache.maxsize * 100:.1f}%",
        }


def _get_default_csv_path() -> tuple[Path, str]:
    """Get default CSV path, preferring DrugBank interactions if available.

    Returns:
        Tuple of (csv_path, data_source_name)
    """
    # Try DrugBank interactions
    if DRUGBANK_INTERACTIONS_CSV_PATH.exists():
        logger.info(
            f"✓ Using DrugBank interactions database: {DRUGBANK_INTERACTIONS_CSV_PATH.name} "
            f"({DRUGBANK_INTERACTIONS_CSV_PATH})"
        )
        return DRUGBANK_INTERACTIONS_CSV_PATH, "DrugBank"
    # Fallback to basic interactions
    if BASIC_INTERACTIONS_CSV_PATH.exists():
        logger.warning(
            f"⚠ DrugBank interactions file not found at {DRUGBANK_INTERACTIONS_CSV_PATH}. "
            f"Falling back to basic interactions file: {BASIC_INTERACTIONS_CSV_PATH.name}. "
            f"To use DrugBank interactions, add the file to: {DRUGBANK_INTERACTIONS_CSV_PATH}"
        )
        return BASIC_INTERACTIONS_CSV_PATH, "Basic"
    raise FileNotFoundError(
        f"Neither DrugBank interactions nor basic interactions file found. "
        f"Tried: {DRUGBANK_INTERACTIONS_CSV_PATH}, "
        f"{BASIC_INTERACTIONS_CSV_PATH}"
    )


def _get_cached_checker() -> DrugInteractionChecker | None:
    """Get or create cached DrugInteractionChecker instance.

    Returns None if CSV files are not available (allows app to start without data).
    """
    if not hasattr(_get_cached_checker, "_cached_instance"):
        try:
            csv_path, data_source = _get_default_csv_path()
            _get_cached_checker._cached_instance = DrugInteractionChecker(
                csv_path, data_source=data_source
            )
            instance = _get_cached_checker._cached_instance
            if instance._lazy_frame is not None:
                logger.info(
                    f"✓ Drug interaction service initialized with {data_source} database: "
                    f"{instance._row_count:,} interaction records available (lazy loading)"
                )
        except FileNotFoundError as e:
            logger.error(
                f"⚠ Drug interaction CSV files not found. "
                f"Interaction checking will be unavailable. Error: {e}"
            )
            _get_cached_checker._cached_instance = None
        except Exception as e:
            logger.error(
                f"⚠ Failed to initialize drug interaction checker: {e}. "
                f"Interaction checking will be unavailable."
            )
            _get_cached_checker._cached_instance = None
    return _get_cached_checker._cached_instance


def get_interaction(drug_a: str, drug_b: str) -> str | None:
    """Get interaction between two drugs using the default CSV file (cached).

    Uses DrugBank database if available, otherwise falls back to basic interactions.
    Returns None if CSV files are not available (allows app to start without data).
    """
    checker = _get_cached_checker()
    if checker is None:
        logger.warning(
            f"Drug interaction checker not available - CSV files missing. "
            f"Cannot check interaction between '{drug_a}' and '{drug_b}'"
        )
        return None
    return checker.get_interaction(drug_a, drug_b)
