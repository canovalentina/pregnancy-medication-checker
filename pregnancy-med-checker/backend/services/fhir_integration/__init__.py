"""FHIR Integration Service Package."""

from .application.api_handlers import FHIRAPIHandlers
from .domain.constants import (
    DEFAULT_SYNTHEA_DATA_PATH,
    DEFAULT_TEST_DATA_PATH,
    INGESTED_PATIENT_IDENTIFIER_VALUE_TEST,
    ServerStatus,
)
from .domain.models import (
    APIResponse,
    FHIRServerStatus,
    IngestionResult,
    ResourceResponse,
)
from .domain.protocols import FHIRClientPort, IngestionServicePort
from .infrastructure.client.fhir_client import FHIRClientService
from .infrastructure.ingestion.fhir_ingestor import FHIRResourceIngestor

__all__ = [
    "DEFAULT_SYNTHEA_DATA_PATH",
    "DEFAULT_TEST_DATA_PATH",
    "INGESTED_PATIENT_IDENTIFIER_VALUE_TEST",
    "APIResponse",
    "FHIRAPIHandlers",
    "FHIRClientPort",
    "FHIRClientService",
    "FHIRResourceIngestor",
    "FHIRServerStatus",
    "IngestionResult",
    "IngestionServicePort",
    "ResourceResponse",
    "ServerStatus",
]
