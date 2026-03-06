"""FHIR integration endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, Query  # type: ignore[import-untyped]

from services.fhir_integration import FHIRAPIHandlers

# API prefix from environment variable
API_PREFIX = os.getenv("API_PREFIX", "/api")

# Initialize router
router = APIRouter(prefix=f"{API_PREFIX}/fhir", tags=["FHIR"])

# Initialize handlers
fhir_handlers = FHIRAPIHandlers()


@router.get("/status")
async def fhir_status():
    """Check FHIR server connection status."""
    return await fhir_handlers.get_fhir_status()


@router.get("/patients")
async def search_patients(
    name: str | None = Query(None, description="Patient name to search for"),
    birth_date: str | None = Query(None, description="Patient birth date (YYYY-MM-DD)"),
    gender: str | None = Query(None, description="Patient gender (male/female/other)"),
    only_ingested_patients: bool | None = Query(
        None,
        description="If True, only search for patients with ingestion identifier. "
        "If not provided, uses the client's default setting (default: True).",
    ),
):
    """Search for patients in the FHIR server."""
    return await fhir_handlers.search_patients(
        name=name,
        birth_date=birth_date,
        gender=gender,
        only_ingested_patients=only_ingested_patients,
    )


@router.get("/patients/{patient_id}/medications")
async def get_patient_medications(patient_id: str):
    """Get patient's medications."""
    return await fhir_handlers.get_patient_medications(patient_id)


@router.get("/patients/{patient_id}/conditions")
async def get_patient_conditions(patient_id: str):
    """Get patient's conditions."""
    return await fhir_handlers.get_patient_conditions(patient_id)


@router.get("/patients/{patient_id}/pregnancy-observations")
async def get_pregnancy_observations(patient_id: str):
    """Get pregnancy-related observations for a patient."""
    return await fhir_handlers.get_pregnancy_observations(patient_id)


@router.get("/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    """Get comprehensive patient summary."""
    return await fhir_handlers.get_patient_summary(patient_id)


@router.post("/ingest-resource-data")
async def ingest_resource_data(
    data_path: str = Query(
        ...,
        description="Path to a single FHIR Bundle file or directory containing bundle files",
    ),
    max_bundles: int | None = Query(
        None,
        description="Maximum number of bundles to process (for directories, default: all). "
        "Each file = 1 bundle.",
    ),
    ingestion_tag: str | None = Query(
        None,
        description="Tag value to use for identifying ingested patients. "
        "Use 'pregnancy-med-checker-ingestion-test' for test data. "
        "If None, uses default production tag.",
    ),
):
    """Ingest FHIR resource data from a file or directory."""
    return await fhir_handlers.ingest_resource_data(
        data_path=data_path, max_bundles=max_bundles, ingestion_tag=ingestion_tag
    )


@router.get("/ingestion-status")
def get_ingestion_status():
    """Get current data ingestion status."""
    return fhir_handlers.get_ingestion_status()


@router.get("/ingested-patients")
async def get_ingested_patients():
    """Get count and list of IDs for demo/assigned patients.

    Uses stored IDs from startup ingest, or name-only search (no identifier/tag filter).
    """
    from app.demo_patients import get_demo_patient_ids

    return await fhir_handlers.get_ingested_patient_ids(
        stored_ids=get_demo_patient_ids(),
        # Must match last names in synthea/test bundles (x suffix to avoid overlap on public server)
        fallback_names=[
            "Sarah Williamsx",
            "Maria Martinezx",
            "Jennifer Chenx",
        ],
    )


@router.delete("/ingested-patients")
async def delete_all_ingested_patients(
    cascade: bool = Query(
        default=True,
        description="If True (default), delete patient and all referencing resources (cascade delete). "
        "If False, only delete the patient resource.",
    ),
):
    """Delete all patients with the ingestion identifier.

    This will find and delete all patients that were ingested by this application,
    along with all their associated resources (if cascade=True).
    """
    return await fhir_handlers.delete_all_ingested_patients(cascade=cascade)


@router.post("/validate-data")
def validate_ingested_data():
    """Validate ingested FHIR data."""
    return fhir_handlers.validate_ingested_data()


@router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete a patient by id."""
    return await fhir_handlers.delete_patient(patient_id)


@router.delete("/resources/{resource_type}/{resource_id}")
async def delete_resource(resource_type: str, resource_id: str):
    """Delete a resource by type and id."""
    return await fhir_handlers.delete_resource(resource_type, resource_id)


@router.get("/patients/{patient_id}/pregnancy-stage")
async def get_pregnancy_stage(patient_id: str):
    """Get the current pregnancy stage (gestational weeks) for a patient."""
    return await fhir_handlers.get_pregnancy_stage(patient_id)


@router.get("/patients/{patient_id}/lactation-stage")
async def get_lactation_stage(patient_id: str):
    """Get the current lactation stage for a patient."""
    return await fhir_handlers.get_lactation_stage(patient_id)


@router.get("/patients/{patient_id}/medications-list")
async def get_patient_medications_list(patient_id: str):
    """Get a simplified list of medications for a patient."""
    return await fhir_handlers.get_patient_medications_list(patient_id)
