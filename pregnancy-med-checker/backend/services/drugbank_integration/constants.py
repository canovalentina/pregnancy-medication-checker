"""Constants for DrugBank integration."""

from enum import Enum
from pathlib import Path

UNKNOWN_VALUE = "Unknown"

# Base directory for this service
SERVICE_DIR = Path(__file__).resolve().parent

# DrugBank Data directory
DATA_DIR = SERVICE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# DrugBank data directory
DRUGBANK_DATA_DIR = SERVICE_DIR / "data" / "DrugBank"

# Main DrugBank XML database file
DRUGBANK_XML_FILE = DRUGBANK_DATA_DIR / "full_database.xml"

# DrugBank namespace
DRUGBANK_NS = "{http://www.drugbank.ca}"

# DrugBank Interactions Output Files
DRUGBANK_INTERACTIONS_OUTPUT_FILE = DATA_DIR / "drugbank_interactions.csv"
DRUGBANK_INTERACTIONS_SAMPLE_OUTPUT_FILE = DATA_DIR / "drugbank_interactions_sample.csv"
DRUGBANK_INTERACTIONS_SUMMARY_OUTPUT_FILE = (
    DATA_DIR / "drugbank_interactions_summary.csv"
)


class ExternalIdentifierType(str, Enum):
    """External identifier resource types from DrugBank."""

    RXCUI = "RxCUI"
    PUBCHEM_SUBSTANCE = "PubChem Substance"
    PUBCHEM_COMPOUND = "PubChem Compound"
    CHEBI = "ChEBI"
    KEGG_DRUG = "KEGG Drug"
    KEGG_COMPOUND = "KEGG Compound"
    PDB = "PDB"
    UNIPROT = "UniProt"
    WIKIPEDIA = "Wikipedia"
    GENBANK = "GenBank"
    PHARMGKB = "PharmGKB"
    HET = "HET"
    CHEMSPIDER = "ChemSpider"
    BINDINGDB = "BindingDB"
    METABOLIGHTS = "MetaboLights"


# List of accepted identifier types for CSV columns
ACCEPTED_IDENTIFIER_TYPES = [ExternalIdentifierType.RXCUI]


def generate_identifier_column_name(
    drug_num: int, identifier_type: ExternalIdentifierType
) -> str:
    """Generate column name for identifier (e.g., 'drug_1_rxcui')."""
    identifier_name = identifier_type.value.lower().replace(" ", "_")
    return f"drug_{drug_num}_{identifier_name}"


class InteractionCSVColumns(str, Enum):
    """CSV column names for drug interaction data."""

    DRUG_1 = "drug_1"
    DRUG_1_DRUGBANK_ID = "drug_1_drugbank_id"
    DRUG_2 = "drug_2"
    DRUG_2_DRUGBANK_ID = "drug_2_drugbank_id"
    INTERACTION_DESCRIPTION = "interaction_description"

    @classmethod
    def get_all_columns(cls) -> list[str]:
        """Get all column names including dynamically generated identifier columns."""
        base_columns = [col.value for col in cls]
        identifier_columns = [
            generate_identifier_column_name(drug_num, identifier_type)
            for drug_num in [1, 2]
            for identifier_type in ACCEPTED_IDENTIFIER_TYPES
        ]
        return base_columns + identifier_columns
