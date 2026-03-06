#!/usr/bin/env python3
"""Quick analysis of drug interactions from DrugBank XML."""

import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Import after path is set up (must be after sys.path modification)
from services.drugbank_integration.constants import (  # noqa: E402
    DRUGBANK_INTERACTIONS_SAMPLE_OUTPUT_FILE,
)
from services.drugbank_integration.data_extractor import (  # noqa: E402
    DrugBankInteractionsExtractor,
)


def main():
    extractor = DrugBankInteractionsExtractor()

    if not extractor.xml_file.exists():
        print(f"Error: {extractor.xml_file} not found")
        return

    file_size = extractor.xml_file.stat().st_size / (1024**3)
    print(f"Parsing {extractor.xml_file.name} ({file_size:.2f} GB)")
    print("Sample parse (first 50 drugs)...\n")

    sample_interactions = extractor.parse_interactions(max_drugs=50)
    extractor.analyze_interactions(sample_interactions)

    # Save sample to CSV
    if sample_interactions:
        extractor.save_interactions_to_csv(
            sample_interactions, DRUGBANK_INTERACTIONS_SAMPLE_OUTPUT_FILE
        )
        print(f"\nSample saved to {DRUGBANK_INTERACTIONS_SAMPLE_OUTPUT_FILE.name}")

    print("\nTo parse full database, use extract_interactions.py")


if __name__ == "__main__":
    main()
