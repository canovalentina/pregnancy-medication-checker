#!/usr/bin/env python3
"""Generate summary statistics from DrugBank interactions CSV."""

import csv
import sys
from collections import defaultdict
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Import after path is set up (must be after sys.path modification)
from services.drugbank_integration.constants import (  # noqa: E402
    DRUGBANK_INTERACTIONS_OUTPUT_FILE,
    DRUGBANK_INTERACTIONS_SUMMARY_OUTPUT_FILE,
    ExternalIdentifierType,
    InteractionCSVColumns,
    generate_identifier_column_name,
)


def generate_summary() -> None:
    """Generate summary CSV with medication counts and interactions per medication."""
    input_file = DRUGBANK_INTERACTIONS_OUTPUT_FILE
    output_file = DRUGBANK_INTERACTIONS_SUMMARY_OUTPUT_FILE

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)

    # Get RXCUI column names dynamically
    rxcui_type = ExternalIdentifierType.RXCUI
    drug1_rxcui_col = generate_identifier_column_name(1, rxcui_type)
    drug2_rxcui_col = generate_identifier_column_name(2, rxcui_type)

    # Count interactions per medication
    # A medication can appear as drug_1 or drug_2
    medication_interactions = defaultdict(int)
    medication_info = {}  # Store DrugBank ID and RxCUI for each medication
    total_interactions = 0

    print(f"Reading {input_file.name}...")
    print("This may take a few minutes for large files...\n")

    with open(input_file, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            if row_num % 100000 == 0:
                print(f"  Processed {row_num:,} rows...")

            drug1 = row.get(InteractionCSVColumns.DRUG_1.value, "").strip()
            drug2 = row.get(InteractionCSVColumns.DRUG_2.value, "").strip()

            if drug1:
                medication_interactions[drug1] += 1
                # Store metadata for drug1
                if drug1 not in medication_info:
                    medication_info[drug1] = {
                        "drugbank_id": row.get(
                            InteractionCSVColumns.DRUG_1_DRUGBANK_ID.value, ""
                        ),
                        "rxcui": row.get(drug1_rxcui_col, ""),
                    }

            if drug2:
                medication_interactions[drug2] += 1
                # Store metadata for drug2
                if drug2 not in medication_info:
                    medication_info[drug2] = {
                        "drugbank_id": row.get(
                            InteractionCSVColumns.DRUG_2_DRUGBANK_ID.value, ""
                        ),
                        "rxcui": row.get(drug2_rxcui_col, ""),
                    }

            total_interactions += 1

    print(f"\nProcessed {total_interactions:,} total interactions")
    print(f"Found {len(medication_interactions):,} unique medications\n")

    # Create summary data sorted by interaction count (descending)
    summary_data = []
    for medication, count in sorted(
        medication_interactions.items(), key=lambda x: x[1], reverse=True
    ):
        info = medication_info.get(medication, {})
        summary_data.append(
            {
                "medication": medication,
                "drugbank_id": info.get("drugbank_id", ""),
                "rxcui": info.get("rxcui", ""),
                "interaction_count": count,
            }
        )

    # Write summary CSV
    print(f"Writing summary to {output_file.name}...")
    if output_file.exists():
        output_file.unlink()

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["medication", "drugbank_id", "rxcui", "interaction_count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_data)

    print(f"Saved summary with {len(summary_data):,} medications")
    print(f"\nTop 10 medications by interactions:")
    for i, row in enumerate(summary_data[:10], 1):
        print(f"  {i}. {row['medication']}: {row['interaction_count']:,} interactions")


if __name__ == "__main__":
    generate_summary()
