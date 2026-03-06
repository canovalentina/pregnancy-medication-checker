#!/usr/bin/env python3
"""Extract all drug interactions from DrugBank XML to CSV."""

import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Import after path is set up (must be after sys.path modification)
from services.drugbank_integration.constants import (  # noqa: E402
    DRUGBANK_INTERACTIONS_OUTPUT_FILE,
)
from services.drugbank_integration.data_extractor import (  # noqa: E402
    DrugBankInteractionsExtractor,
)


def main():
    extractor = DrugBankInteractionsExtractor()
    output_file = DRUGBANK_INTERACTIONS_OUTPUT_FILE

    if not extractor.xml_file.exists():
        print(f"Error: {extractor.xml_file} not found")
        sys.exit(1)

    file_size = extractor.xml_file.stat().st_size / (1024**3)
    print(f"Extracting interactions from DrugBank database ({file_size:.2f} GB)")
    print("This may take more than 5 minutes...\n")

    interactions = extractor.extract_to_csv(output_file)

    if interactions:
        print(f"\nExtracted {len(interactions):,} interactions to {output_file}")
        print("\nCSV includes:")
        print("  - Drug names and DrugBank IDs")
        print("  - RxCUI codes (for RxNorm integration)")
        print("  - PubChem Substance IDs")
        print("  - Interaction descriptions")


if __name__ == "__main__":
    main()
