#!/usr/bin/env python3
"""Explore DrugBank dataset structure."""

import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Import after path is set up (must be after sys.path modification)
from services.drugbank_integration.data_explorer import DrugBankExplorer  # noqa: E402


def main():
    explorer = DrugBankExplorer()
    explorer.explore()


if __name__ == "__main__":
    main()
