# DrugBank Integration Scripts

CLI scripts for exploring and extracting data from the DrugBank database.

## Scripts

- **`explore_drugbank_data.py`**: Explore dataset structure and available files
- **`extract_interactions_sample.py`**: Quick sample analysis (first 50 drugs)
- **`extract_interactions.py`**: Extract all interactions to CSV
- **`generate_interactions_summary.py`**: Generate summary of the interactions

## Usage

First, must save the full DrugBank XML to `pregnancy-med-checker/backend/services/drugbank_integration/data/DrugBank/full_database.xml` (with _ in name)

Run from the `backend/` directory:

**Important:** Use `uv run python` to ensure all dependencies (like `loguru`) are available from the virtual environment.

```bash
# If not in backend folder yet, navigate to it
cd pregnancy-med-checker/backend/

# Explore dataset
uv run python services/drugbank_integration/scripts/explore_drugbank_data.py

# Quick sample analysis
uv run python services/drugbank_integration/scripts/extract_interactions_sample.py

# Full extraction
uv run python services/drugbank_integration/scripts/extract_interactions.py

# Create summary of full extraction
uv run python services/drugbank_integration/scripts/generate_interactions_summary.py
```

**Note:** If you get a `ModuleNotFoundError` (e.g., "No module named 'loguru'"), make sure you're using `uv run python` instead of `python3` or `python`. The project uses `uv` for dependency management, and all dependencies are installed in the virtual environment managed by `uv`.

If getting error that file is not executable, run:
```bash
chmod +x services/drugbank_integration/scripts/explore_drugbank_data.py
```

## Output

The `extract_interactions.py` script generates `drugbank_interactions.csv` with:
- Drug names and DrugBank IDs
- RxCUI codes (RxNorm identifiers)
- PubChem Compound/Substance IDs
- ChEBI IDs
- Interaction descriptions

All columns use lowercase snake_case format (e.g., `drug_1`, `drug_1_rxcui`).