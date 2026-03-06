from pathlib import Path

from services.drugbank_integration.constants import (
    DRUGBANK_INTERACTIONS_OUTPUT_FILE,
    InteractionCSVColumns,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
BASIC_INTERACTIONS_CSV_PATH = DATA_DIR / "db_drug_interactions.csv"
DRUGBANK_INTERACTIONS_CSV_PATH = DRUGBANK_INTERACTIONS_OUTPUT_FILE  # Alias

DRUG_1_COLUMN = InteractionCSVColumns.DRUG_1.value
DRUG_2_COLUMN = InteractionCSVColumns.DRUG_2.value
INTERACTION_DESCRIPTION_COLUMN = InteractionCSVColumns.INTERACTION_DESCRIPTION.value

MANDATORY_COLUMNS = [
    DRUG_1_COLUMN,
    DRUG_2_COLUMN,
    INTERACTION_DESCRIPTION_COLUMN,
]
