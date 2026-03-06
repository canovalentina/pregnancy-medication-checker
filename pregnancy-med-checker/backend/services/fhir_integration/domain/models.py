"""Pydantic data models FHIR API integration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .constants import ResourceType, ServerStatus


class PatientData(BaseModel):
    """Patient data model for API responses and created patients."""

    id: str = Field(..., description="Patient ID")
    name: str = Field(..., description="Patient's full name")
    birth_date: str | None = Field(None, description="Patient's birth date")
    gender: str | None = Field(None, description="Patient's gender")
    resource_type: str = Field(
        default=ResourceType.PATIENT.value, description="FHIR resource type"
    )

    class Config:
        populate_by_name = True


class APIResponse(BaseModel):
    """Base API response model."""

    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(None, description="Response data")


class FHIRServerStatus(BaseModel):
    """FHIR server connection status model."""

    status: ServerStatus = Field(..., description="Connection status")
    server: str = Field(..., description="FHIR server URL")
    fhir_version: str | None = Field(default=None, description="FHIR version")
    server_name: str | None = Field(default=None, description="Server name")
    timestamp: str | None = Field(default=None, description="Status check timestamp")

    class Config:
        populate_by_name = True


class ResourceResponse(BaseModel):
    """Generic resource response model for searches."""

    resources: list[dict[str, Any]] = Field(default_factory=list)
    total: int = Field(0, description="Total number of resources found")
    server: str = Field(..., description="FHIR server URL")
    patient_id: str | None = Field(
        default=None, description="Patient ID (for patient-specific searches)"
    )


class CreatedMedication(BaseModel):
    """Model for created medication data."""

    id: str = Field(..., description="Medication ID")
    patient_id: str = Field(..., description="Patient ID")
    medication: str = Field(..., description="Medication name")
    medication_code: str | None = Field(
        None, description="Medication code (e.g., RxNorm)"
    )
    medication_system: str | None = Field(None, description="Coding system URI")
    medication_system_type: str | None = Field(
        None, description="Coding system type (e.g., rxnorm)"
    )
    medication_display: str | None = Field(None, description="Medication display name")


class CreatedCondition(BaseModel):
    """Model for created condition data."""

    id: str = Field(..., description="Condition ID")
    patient_id: str = Field(..., description="Patient ID")
    condition: str = Field(..., description="Condition name")
    condition_code: str | None = Field(
        None, description="Condition code (e.g., SNOMED)"
    )
    condition_system: str | None = Field(None, description="Coding system URI")
    condition_system_type: str | None = Field(
        None, description="Coding system type (e.g., snomed)"
    )
    condition_display: str | None = Field(None, description="Condition display name")


class CreatedObservation(BaseModel):
    """Model for created observation data."""

    id: str = Field(..., description="Observation ID")
    patient_id: str = Field(..., description="Patient ID")
    observation: str = Field(..., description="Observation name")
    observation_code: str | None = Field(
        None, description="Observation code (e.g., LOINC, SNOMED)"
    )
    observation_system: str | None = Field(None, description="Coding system URI")
    observation_system_type: str | None = Field(
        None, description="Coding system type (e.g., loinc, snomed)"
    )
    observation_display: str | None = Field(
        None, description="Observation display name"
    )


class CreatedMedicationResource(BaseModel):
    """Model for created Medication resource data."""

    id: str = Field(..., description="Medication resource ID")
    medication: str = Field(..., description="Medication name")
    medication_code: str | None = Field(
        None, description="Medication code (e.g., RxNorm)"
    )
    medication_system: str | None = Field(None, description="Coding system URI")
    medication_system_type: str | None = Field(
        None, description="Coding system type (e.g., rxnorm)"
    )
    medication_display: str | None = Field(None, description="Medication display name")


class CreatedMedicationAdministration(BaseModel):
    """Model for created MedicationAdministration data."""

    id: str = Field(..., description="MedicationAdministration ID")
    patient_id: str = Field(..., description="Patient ID")
    medication: str = Field(..., description="Medication name")
    medication_code: str | None = Field(
        None, description="Medication code (e.g., RxNorm)"
    )
    medication_system: str | None = Field(None, description="Coding system URI")
    medication_system_type: str | None = Field(
        None, description="Coding system type (e.g., rxnorm)"
    )
    medication_display: str | None = Field(None, description="Medication display name")


class CreatedEncounter(BaseModel):
    """Model for created Encounter data."""

    id: str = Field(..., description="Encounter ID")
    patient_id: str = Field(..., description="Patient ID")
    encounter: str = Field(..., description="Encounter type/description")
    type_code: str | None = Field(
        None, description="Encounter type code (e.g., SNOMED)"
    )
    type_system: str | None = Field(None, description="Coding system URI")
    type_system_type: str | None = Field(
        None, description="Coding system type (e.g., snomed)"
    )
    type_display: str | None = Field(None, description="Encounter type display name")
    reason_codes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Encounter reason codes (e.g., pregnancy-related codes)",
    )


class CreatedProcedure(BaseModel):
    """Model for created Procedure data."""

    id: str = Field(..., description="Procedure ID")
    patient_id: str = Field(..., description="Patient ID")
    procedure: str = Field(..., description="Procedure name")
    procedure_code: str | None = Field(
        None, description="Procedure code (e.g., SNOMED)"
    )
    procedure_system: str | None = Field(None, description="Coding system URI")
    procedure_system_type: str | None = Field(
        None, description="Coding system type (e.g., snomed)"
    )
    procedure_display: str | None = Field(None, description="Procedure display name")


class IngestionSummary(BaseModel):
    """Summary of data ingestion results."""

    total_patients: int = Field(
        default=0, description="Total number of patients created"
    )
    total_medications: int = Field(
        default=0, description="Total number of medications created"
    )
    total_conditions: int = Field(
        default=0, description="Total number of conditions created"
    )
    total_observations: int = Field(
        default=0, description="Total number of observations created"
    )
    total_medication_resources: int = Field(
        default=0, description="Total number of Medication resources created"
    )
    total_medication_administrations: int = Field(
        default=0,
        description="Total number of MedicationAdministration resources created",
    )
    total_encounters: int = Field(
        default=0, description="Total number of Encounter resources created"
    )
    total_procedures: int = Field(
        default=0, description="Total number of Procedure resources created"
    )
    total_errors: int = Field(
        default=0, description="Total number of errors encountered"
    )
    ingestion_timestamp: str = Field(
        ...,
        description="Timestamp when ingestion completed",
    )

    class Config:
        populate_by_name = True


class IngestionResult(BaseModel):
    """Data ingestion result model."""

    patients_created: list[PatientData] = Field(default_factory=list)
    medications_created: list[CreatedMedication] = Field(default_factory=list)
    conditions_created: list[CreatedCondition] = Field(default_factory=list)
    observations_created: list[CreatedObservation] = Field(default_factory=list)
    medication_resources_created: list[CreatedMedicationResource] = Field(
        default_factory=list
    )
    medication_administrations_created: list[CreatedMedicationAdministration] = Field(
        default_factory=list
    )
    encounters_created: list[CreatedEncounter] = Field(default_factory=list)
    procedures_created: list[CreatedProcedure] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    summary: IngestionSummary = Field(..., description="Summary of ingestion results")
