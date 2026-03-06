"""Domain ports (protocols) for FHIR integration."""

from __future__ import annotations

from collections.abc import Coroutine
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .constants import ResourceType
from .models import FHIRServerStatus, IngestionResult, PatientData


@runtime_checkable
class FHIRClientPort(Protocol):
    """Port interface for FHIR client operations used by application/infrastructure."""

    base_url: str
    validate: bool  # Client-level validation setting

    # Server utilities
    def test_connection(self) -> Coroutine[Any, Any, FHIRServerStatus]: ...

    # Patient operations
    def create_patient(
        self, patient_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...
    def read_patient(
        self, patient_id: str
    ) -> Coroutine[Any, Any, PatientData | None]: ...
    def delete_patient(
        self, patient_id: str, cascade: bool = True
    ) -> Coroutine[Any, Any, bool]: ...
    def delete_all_ingested_patients(
        self, cascade: bool = True, ingestion_tag: str | None = None
    ) -> Coroutine[Any, Any, dict[str, Any]]: ...
    def get_ingested_patient_ids(
        self,
    ) -> Coroutine[Any, Any, dict[str, Any]]: ...
    def search_patients(
        self,
        name: str | None = None,
        birth_date: str | None = None,
        gender: str | None = None,
        count: int = 100,
        *,
        fetch_all: bool = False,
        only_ingested_patients: bool | None = None,
    ) -> Coroutine[Any, Any, list[PatientData]]: ...

    # MedicationRequest operations
    def create_medication_request(
        self, medication_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...
    def get_patient_medications(
        self, patient_id: str, count: int = 50, *, fetch_all: bool = False
    ) -> Coroutine[Any, Any, list[dict[str, Any]]]: ...

    # Condition operations
    def create_condition(
        self, condition_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...
    def get_patient_conditions(
        self, patient_id: str, count: int = 50, *, fetch_all: bool = False
    ) -> Coroutine[Any, Any, list[dict[str, Any]]]: ...

    # Observation operations
    def create_observation(
        self, observation_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...
    def get_patient_observations(
        self,
        patient_id: str,
        count: int = 50,
        *,
        fetch_all: bool = False,
        code_filter: str | None = None,
        category: str | None = None,
    ) -> Coroutine[Any, Any, list[dict[str, Any]]]: ...

    # Pregnancy and lactation stage operations
    def get_pregnancy_stage(
        self, patient_id: str
    ) -> Coroutine[Any, Any, dict[str, Any] | None]: ...
    def get_lactation_stage(
        self, patient_id: str
    ) -> Coroutine[Any, Any, dict[str, Any] | None]: ...
    def get_patient_medications_list(
        self, patient_id: str
    ) -> Coroutine[Any, Any, list[dict[str, Any]]]: ...

    # Medication operations
    def create_medication(
        self, medication_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...

    # MedicationAdministration operations
    def create_medication_administration(
        self, medication_administration_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...

    # Encounter operations
    def create_encounter(
        self, encounter_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...

    # Procedure operations
    def create_procedure(
        self, procedure_data: dict[str, Any]
    ) -> Coroutine[Any, Any, str | None]: ...

    # Generic resource operations
    def read_resource(
        self, resource_type: ResourceType, resource_id: str
    ) -> Coroutine[Any, Any, dict[str, Any] | None]: ...
    def delete_resource(
        self, resource_type: ResourceType, resource_id: str, cascade: bool = False
    ) -> Coroutine[Any, Any, bool]: ...


@runtime_checkable
class IngestionServicePort(Protocol):
    """Port interface for ingestion services used by the application layer."""

    def ingest_resource_data(
        self,
        data_path: Path | str,
        max_bundles: int | None = None,
        ingestion_tag: str | None = None,
    ) -> Coroutine[Any, Any, IngestionResult]: ...

    def get_ingestion_status(self) -> IngestionResult: ...
