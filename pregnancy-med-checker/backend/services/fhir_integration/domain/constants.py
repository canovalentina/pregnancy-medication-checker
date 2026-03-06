"""Constants and enums for FHIR integration."""

import os
from enum import Enum
from pathlib import Path

UNKNOWN_VALUE = "Unknown"

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.parent.parent.parent

# Default paths for data ingestion
DEFAULT_SYNTHEA_DATA_PATH = BACKEND_DIR / "services" / "synthea" / "output" / "fhir"
DEFAULT_TEST_DATA_PATH = BACKEND_DIR / "services" / "synthea" / "test"

# Default FHIR server URL
DEFAULT_FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL", "http://hapi.fhir.org/baseR4")

# Custom identifier system for tracking ingested patients
# This allows identifying patients ingested by this application on public FHIR servers
INGESTED_PATIENT_IDENTIFIER_SYSTEM = (
    "https://pregnancy-med-checker.org/identifier/ingested-by"
)
# Default production ingestion tag
INGESTED_PATIENT_IDENTIFIER_VALUE = "pregnancy-med-checker-ingestion"
# Test ingestion tag for test data
INGESTED_PATIENT_IDENTIFIER_VALUE_TEST = "pregnancy-med-checker-ingestion-test"

# Enums


class ServerStatus(str, Enum):
    """Server connection status."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ResourceType(str, Enum):
    """FHIR resource types."""

    CONDITION = "Condition"
    ENCOUNTER = "Encounter"
    MEDICATION = "Medication"
    MEDICATION_ADMINISTRATION = "MedicationAdministration"
    MEDICATION_REQUEST = "MedicationRequest"
    OBSERVATION = "Observation"
    PATIENT = "Patient"
    PROCEDURE = "Procedure"


# Resource types that should be ingested from bundles
SUPPORTED_INGESTION_TYPES = {
    ResourceType.CONDITION,
    ResourceType.ENCOUNTER,
    ResourceType.MEDICATION,
    ResourceType.MEDICATION_ADMINISTRATION,
    ResourceType.MEDICATION_REQUEST,
    ResourceType.OBSERVATION,
    ResourceType.PROCEDURE,
}


class Gender(str, Enum):
    """FHIR Administrative Gender values."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class MedicationCategory(str, Enum):
    """Medication category codes (placeholder values for now)."""

    PREGNANCY = "pregnancy"
    ROUTINE = "routine"
    EMERGENCY = "emergency"
    SUPPLEMENT = "supplement"


class PregnancyTrimester(str, Enum):
    """Pregnancy trimester and lactation states (placeholder values for now)."""

    FIRST_TRIMESTER = "first_trimester"
    SECOND_TRIMESTER = "second_trimester"
    THIRD_TRIMESTER = "third_trimester"
    LACTATING = "lactating"
    NOT_APPLICABLE = "not_applicable"


class SystemType(str, Enum):
    """Coding system types for FHIR codes."""

    RXNORM = "rxnorm"
    SNOMED = "snomed"
    LOINC = "loinc"
    NDC = "ndc"
    UNKNOWN = "unknown"


class ObservationCode(str, Enum):
    """FHIR observation codes for pregnancy and lactation."""

    GESTATIONAL_AGE = "11778-8"  # LOINC: Gestational age
    LACTATION_STATUS = "225747004"  # SNOMED: Lactation status


class ObservationCodeSystem(str, Enum):
    """FHIR observation code system URIs."""

    LOINC = "http://loinc.org"
    SNOMED = "http://snomed.info/sct"


class LactationStatus(str, Enum):
    """Lactation status values."""

    LACTATING = "Lactating"
    NOT_LACTATING = "Not lactating"


# SNOMED codes for pregnancy-related conditions and procedures
PREGNANCY_CODE = "77386006"  # Pregnancy
PRETERM_BIRTH_CODE = "67811000119102"  # Preterm birth
BIRTH_PROCEDURE_CODES = [
    "116680003",  # Delivery
    "699870008",  # Cesarean section
    "236985000",  # Vaginal delivery
]
