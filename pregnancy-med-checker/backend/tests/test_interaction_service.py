"""Tests for drug interaction service.
To run: uv run pytest tests/test_interaction_service.py -v
"""

import csv
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest  # type: ignore[import-untyped]

from services.drug_interaction.constants import (
    BASIC_INTERACTIONS_CSV_PATH,
    DRUGBANK_INTERACTIONS_CSV_PATH,
)
from services.drug_interaction.interaction_service import (
    DrugInteractionChecker,
    get_interaction,
)


@pytest.fixture
def sample_csv_with_underscores():
    """Create a temporary CSV with underscore column names (drug_1, drug_2, interaction_description)."""
    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["drug_1", "drug_2", "interaction_description"])
        writer.writerow(
            [
                "Aspirin",
                "Warfarin",
                "Aspirin may increase the anticoagulant activities of Warfarin.",
            ]
        )
        writer.writerow(
            [
                "Ibuprofen",
                "Aspirin",
                "Ibuprofen may increase the risk of bleeding when combined with Aspirin.",
            ]
        )
        writer.writerow(
            [
                "Acetaminophen",
                "Warfarin",
                "Acetaminophen may increase the anticoagulant activities of Warfarin.",
            ]
        )
        csv_path = Path(f.name)
    yield csv_path
    csv_path.unlink(missing_ok=True)


@pytest.fixture
def sample_csv_with_spaces():
    """Create a temporary CSV with space column names (drug 1, drug 2, interaction description)."""
    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["drug 1", "drug 2", "interaction description"])
        writer.writerow(
            [
                "Aspirin",
                "Warfarin",
                "Aspirin may increase the anticoagulant activities of Warfarin.",
            ]
        )
        writer.writerow(
            [
                "Ibuprofen",
                "Aspirin",
                "Ibuprofen may increase the risk of bleeding when combined with Aspirin.",
            ]
        )
        csv_path = Path(f.name)
    yield csv_path
    csv_path.unlink(missing_ok=True)


@pytest.fixture
def sample_csv_with_mixed_case():
    """Create a temporary CSV with mixed case column names."""
    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Drug_1", "Drug-2", "Interaction_Description"])
        writer.writerow(
            [
                "Aspirin",
                "Warfarin",
                "Aspirin may increase the anticoagulant activities of Warfarin.",
            ]
        )
        csv_path = Path(f.name)
    yield csv_path
    csv_path.unlink(missing_ok=True)


def test_normalize_drug_name():
    """Test drug name normalization."""
    assert DrugInteractionChecker.normalize_drug_name("Aspirin") == "aspirin"
    assert DrugInteractionChecker.normalize_drug_name("  Aspirin  ") == "aspirin"
    assert (
        DrugInteractionChecker.normalize_drug_name("ACETAMINOPHEN") == "acetaminophen"
    )
    assert DrugInteractionChecker.normalize_drug_name("  Ibuprofen  ") == "ibuprofen"


def test_checker_with_underscore_columns(sample_csv_with_underscores):
    """Test checker with CSV using underscore column names."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)
    assert checker._lazy_frame is not None
    assert checker.drug_1_col == "drug_1"
    assert checker.drug_2_col == "drug_2"
    assert checker.interaction_col == "interaction_description"


def test_checker_with_space_columns(sample_csv_with_spaces):
    """Test checker with CSV using space column names."""
    checker = DrugInteractionChecker(sample_csv_with_spaces)
    assert checker._lazy_frame is not None
    assert checker.drug_1_col is not None
    assert checker.drug_2_col is not None
    assert checker.interaction_col is not None
    assert (
        "drug 1" in checker.drug_1_col.lower() or "drug_1" in checker.drug_1_col.lower()
    )
    assert (
        "drug 2" in checker.drug_2_col.lower() or "drug_2" in checker.drug_2_col.lower()
    )
    assert "interaction" in checker.interaction_col.lower()
    assert "description" in checker.interaction_col.lower()


def test_checker_with_mixed_case_columns(sample_csv_with_mixed_case):
    """Test checker with CSV using mixed case column names."""
    checker = DrugInteractionChecker(sample_csv_with_mixed_case)
    assert checker._lazy_frame is not None
    assert checker.drug_1_col is not None
    assert checker.drug_2_col is not None
    assert checker.interaction_col is not None


def test_get_interaction_found(sample_csv_with_underscores):
    """Test getting interaction when it exists."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)
    result = checker.get_interaction("Aspirin", "Warfarin")
    assert result is not None
    assert "Aspirin" in result or "aspirin" in result.lower()
    assert "Warfarin" in result or "warfarin" in result.lower()


def test_get_interaction_bidirectional(sample_csv_with_underscores):
    """Test that interaction lookup works in both directions."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)
    result1 = checker.get_interaction("Aspirin", "Warfarin")
    result2 = checker.get_interaction("Warfarin", "Aspirin")
    assert result1 == result2
    assert result1 is not None


def test_get_interaction_not_found(sample_csv_with_underscores):
    """Test getting interaction when it doesn't exist."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)
    result = checker.get_interaction("NonExistentDrug1", "NonExistentDrug2")
    assert result is None


def test_get_interaction_case_insensitive(sample_csv_with_underscores):
    """Test that interaction lookup is case-insensitive."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)
    result1 = checker.get_interaction("aspirin", "warfarin")
    result2 = checker.get_interaction("ASPIRIN", "WARFARIN")
    result3 = checker.get_interaction("Aspirin", "Warfarin")
    assert result1 == result2 == result3
    assert result1 is not None


def test_get_interaction_with_whitespace(sample_csv_with_underscores):
    """Test that interaction lookup handles whitespace correctly."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)
    result1 = checker.get_interaction("  Aspirin  ", "  Warfarin  ")
    result2 = checker.get_interaction("Aspirin", "Warfarin")
    assert result1 == result2
    assert result1 is not None


def test_backward_compatibility_function():
    """Test the backward compatibility get_interaction function."""
    if not BASIC_INTERACTIONS_CSV_PATH.exists():
        pytest.skip(f"Default CSV file not found: {BASIC_INTERACTIONS_CSV_PATH}")

    # Test with actual data from the default CSV
    result = get_interaction("Trioxsalen", "Verteporfin")
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


def test_backward_compatibility_function_not_found():
    """Test backward compatibility function when interaction not found."""
    if not BASIC_INTERACTIONS_CSV_PATH.exists():
        pytest.skip(f"Default CSV file not found: {BASIC_INTERACTIONS_CSV_PATH}")

    result = get_interaction("NonExistentDrug1", "NonExistentDrug2")
    assert result is None


def test_checker_with_basic_interactions_csv():
    """Test checker with the default CSV file."""
    if not BASIC_INTERACTIONS_CSV_PATH.exists():
        pytest.skip(
            f"Basic interactions CSV file not found: {BASIC_INTERACTIONS_CSV_PATH}"
        )

    checker = DrugInteractionChecker(BASIC_INTERACTIONS_CSV_PATH)
    assert checker._lazy_frame is not None
    assert checker._row_count > 0
    assert checker.drug_1_col is not None
    assert checker.drug_2_col is not None
    assert checker.interaction_col is not None


def test_checker_with_drugbank_interactions_csv():
    """Test checker with the default CSV file."""
    if not DRUGBANK_INTERACTIONS_CSV_PATH.exists():
        pytest.skip(
            f"DrugBank interactions CSV file not found: {DRUGBANK_INTERACTIONS_CSV_PATH}"
        )

    checker = DrugInteractionChecker(DRUGBANK_INTERACTIONS_CSV_PATH)
    assert checker._lazy_frame is not None
    assert checker._row_count > 0
    assert checker.drug_1_col is not None
    assert checker.drug_2_col is not None
    assert checker.interaction_col is not None


def test_checker_with_invalid_path():
    """Test checker with invalid CSV path."""
    with pytest.raises(FileNotFoundError):
        DrugInteractionChecker("/nonexistent/path/file.csv")


def test_checker_with_missing_columns():
    """Test checker with CSV missing required columns."""
    with NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["wrong_col_1", "wrong_col_2"])
        writer.writerow(["Aspirin", "Warfarin"])
        csv_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Missing required columns"):
            DrugInteractionChecker(csv_path)
    finally:
        csv_path.unlink(missing_ok=True)


def test_same_drug_pair(sample_csv_with_underscores):
    """Test that same drug pair lookup works."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)
    result = checker.get_interaction("Aspirin", "Aspirin")
    # If no self-interaction exists, should return None
    # If it exists in the data, will return the description
    assert result is None or isinstance(result, str)


# =============================================================================
# Batch Interaction Tests
# =============================================================================


def test_get_interactions_batch_basic(sample_csv_with_underscores):
    """Test basic batch interaction checking."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)

    # Check multiple pairs at once
    pairs = [
        ("Aspirin", "Warfarin"),
        ("Ibuprofen", "Aspirin"),
        ("Acetaminophen", "Warfarin"),
    ]

    results = checker.get_interactions_batch(pairs)

    # Should return dictionary with all pairs
    assert len(results) == 3
    assert ("Aspirin", "Warfarin") in results
    assert ("Ibuprofen", "Aspirin") in results
    assert ("Acetaminophen", "Warfarin") in results

    # All should have interactions
    assert results[("Aspirin", "Warfarin")] is not None
    assert results[("Ibuprofen", "Aspirin")] is not None
    assert results[("Acetaminophen", "Warfarin")] is not None


def test_get_interactions_batch_empty_list(sample_csv_with_underscores):
    """Test batch checking with empty list."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)

    results = checker.get_interactions_batch([])

    assert isinstance(results, dict)
    assert len(results) == 0


def test_get_interactions_batch_mixed_results(sample_csv_with_underscores):
    """Test batch checking with mix of found and not found interactions."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)

    pairs = [
        ("Aspirin", "Warfarin"),  # Should find
        ("NonExistent1", "NonExistent2"),  # Should not find
        ("Ibuprofen", "Aspirin"),  # Should find
    ]

    results = checker.get_interactions_batch(pairs)

    assert len(results) == 3
    assert results[("Aspirin", "Warfarin")] is not None
    assert results[("NonExistent1", "NonExistent2")] is None
    assert results[("Ibuprofen", "Aspirin")] is not None


def test_get_interactions_batch_matches_individual_calls(sample_csv_with_underscores):
    """Test that batch results match individual get_interaction calls."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)

    pairs = [
        ("Aspirin", "Warfarin"),
        ("Ibuprofen", "Aspirin"),
        ("Acetaminophen", "Warfarin"),
    ]

    # Get batch results
    batch_results = checker.get_interactions_batch(pairs)

    # Get individual results
    individual_results = {}
    for drug_a, drug_b in pairs:
        individual_results[(drug_a, drug_b)] = checker.get_interaction(drug_a, drug_b)

    # Results should match
    assert batch_results == individual_results


def test_get_interactions_batch_bidirectional(sample_csv_with_underscores):
    """Test that batch checking works bidirectionally."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)

    # Test same pair in both directions
    pairs = [
        ("Aspirin", "Warfarin"),
        ("Warfarin", "Aspirin"),  # Reverse order
    ]

    results = checker.get_interactions_batch(pairs)

    # Both should return the same interaction
    assert results[("Aspirin", "Warfarin")] == results[("Warfarin", "Aspirin")]
    assert results[("Aspirin", "Warfarin")] is not None


def test_get_interactions_batch_large_list(sample_csv_with_underscores):
    """Test batch checking with many pairs."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)

    # Create many pairs (some duplicates, some unique)
    pairs = [
        ("Aspirin", "Warfarin"),
        ("Ibuprofen", "Aspirin"),
        ("Acetaminophen", "Warfarin"),
        ("Aspirin", "Warfarin"),  # Duplicate
        ("NonExistent1", "NonExistent2"),
        ("Ibuprofen", "Aspirin"),  # Duplicate
    ]

    results = checker.get_interactions_batch(pairs)

    # Dictionary will have unique keys (duplicates are overwritten)
    # So we expect 4 unique pairs, not 6
    assert len(results) == 4

    # All unique pairs should be present
    assert ("Aspirin", "Warfarin") in results
    assert ("Ibuprofen", "Aspirin") in results
    assert ("Acetaminophen", "Warfarin") in results
    assert ("NonExistent1", "NonExistent2") in results

    # Results should be correct
    assert results[("Aspirin", "Warfarin")] is not None
    assert results[("Ibuprofen", "Aspirin")] is not None
    assert results[("Acetaminophen", "Warfarin")] is not None
    assert results[("NonExistent1", "NonExistent2")] is None


def test_get_interactions_batch_cache_usage(sample_csv_with_underscores):
    """Test that batch checking leverages cache efficiently."""
    checker = DrugInteractionChecker(sample_csv_with_underscores)

    # Clear cache first
    checker.clear_cache()

    # First batch call - should populate cache
    pairs1 = [("Aspirin", "Warfarin"), ("Ibuprofen", "Aspirin")]
    results1 = checker.get_interactions_batch(pairs1)

    # Second batch call with overlapping pairs - should use cache
    pairs2 = [("Aspirin", "Warfarin"), ("Acetaminophen", "Warfarin")]
    results2 = checker.get_interactions_batch(pairs2)

    # Results should be consistent
    assert results1[("Aspirin", "Warfarin")] == results2[("Aspirin", "Warfarin")]

    # Cache should have entries
    cache_info = checker.cache_info()
    assert cache_info["size"] > 0
