"""Base ingestor class with common functionality."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ...domain.constants import ResourceType
from ...domain.models import (
    CreatedCondition,
    CreatedEncounter,
    CreatedMedication,
    CreatedMedicationAdministration,
    CreatedMedicationResource,
    CreatedObservation,
    CreatedProcedure,
    IngestionResult,
    IngestionSummary,
)
from ...domain.protocols import FHIRClientPort
from ..processing.fhir_processor import FHIRResourceProcessor
from ..processing.resource_handlers import (
    ConditionHandler,
    EncounterHandler,
    MedicationAdministrationHandler,
    MedicationHandler,
    MedicationRequestHandler,
    ObservationHandler,
    ProcedureHandler,
)


class BaseIngestor:
    """Base class for FHIR data ingestion."""

    def __init__(
        self,
        client: FHIRClientPort,
        data_dir: Path | str | None = None,
    ):
        self.client = client
        # Convert to Path if string, store as Path | None
        self.data_dir = Path(data_dir) if isinstance(data_dir, str) else data_dir
        self.processor = FHIRResourceProcessor()
        self.results = IngestionResult(
            summary=IngestionSummary(ingestion_timestamp=datetime.now(UTC).isoformat())
        )

    def get_ingestion_status(self) -> IngestionResult:
        """Return the current ingestion result snapshot."""
        return self.results

    def _reset_results(self) -> None:
        """Reset ingestion results."""
        self.results = IngestionResult(
            summary=IngestionSummary(ingestion_timestamp=datetime.now(UTC).isoformat())
        )

    def _finalize_results(self) -> IngestionResult:
        """Generate final summary and return results."""
        self.results.summary = IngestionSummary(
            ingestion_timestamp=datetime.now(UTC).isoformat(),
            total_patients=len(self.results.patients_created),
            total_medications=len(self.results.medications_created),
            total_conditions=len(self.results.conditions_created),
            total_observations=len(self.results.observations_created),
            total_medication_resources=len(self.results.medication_resources_created),
            total_medication_administrations=len(
                self.results.medication_administrations_created
            ),
            total_encounters=len(self.results.encounters_created),
            total_procedures=len(self.results.procedures_created),
            total_errors=len(self.results.errors),
        )
        logger.info(f"Data ingestion completed: {self.results.summary}")
        return self.results

    def _add_error(self, error: str) -> None:
        """Add an error to the results."""
        self.results.errors.append(error)
        logger.error(error)

    async def _create_and_track_resource(
        self,
        resource_type: str,
        resource: dict[str, Any],
        patient_id: str | None = None,
    ) -> str | None:
        """Create a FHIR resource and track the result in ingestion results.

        Args:
            resource_type: The FHIR resource type (e.g., "MedicationRequest")
            resource: The resource data as a dictionary
            patient_id: Optional patient ID for tracking patient-specific resources

        Returns:
            The created resource ID if successful, None otherwise
        """
        match resource_type:
            case ResourceType.MEDICATION_REQUEST.value:
                resource_id = await self.client.create_medication_request(resource)
                if resource_id and patient_id:
                    name = MedicationRequestHandler.extract_name(resource)
                    code_info = MedicationRequestHandler.extract_code_info(resource)
                    self.results.medications_created.append(
                        CreatedMedication(
                            id=resource_id,
                            patient_id=patient_id,
                            medication=name,
                            medication_code=(
                                code_info.get("code") if code_info else None
                            ),
                            medication_system=(
                                code_info.get("system") if code_info else None
                            ),
                            medication_system_type=(
                                code_info.get("systemType") if code_info else None
                            ),
                            medication_display=(
                                code_info.get("display") if code_info else None
                            ),
                        )
                    )
                return resource_id

            case ResourceType.MEDICATION.value:
                resource_id = await self.client.create_medication(resource)
                if resource_id:
                    name = MedicationHandler.extract_name(resource)
                    code_info = MedicationHandler.extract_code_info(resource)
                    self.results.medication_resources_created.append(
                        CreatedMedicationResource(
                            id=resource_id,
                            medication=name,
                            medication_code=(
                                code_info.get("code") if code_info else None
                            ),
                            medication_system=(
                                code_info.get("system") if code_info else None
                            ),
                            medication_system_type=(
                                code_info.get("systemType") if code_info else None
                            ),
                            medication_display=(
                                code_info.get("display") if code_info else None
                            ),
                        )
                    )
                return resource_id

            case ResourceType.MEDICATION_ADMINISTRATION.value:
                resource_id = await self.client.create_medication_administration(
                    resource
                )
                if resource_id and patient_id:
                    name = MedicationAdministrationHandler.extract_name(resource)
                    code_info = MedicationAdministrationHandler.extract_code_info(
                        resource
                    )
                    self.results.medication_administrations_created.append(
                        CreatedMedicationAdministration(
                            id=resource_id,
                            patient_id=patient_id,
                            medication=name,
                            medication_code=(
                                code_info.get("code") if code_info else None
                            ),
                            medication_system=(
                                code_info.get("system") if code_info else None
                            ),
                            medication_system_type=(
                                code_info.get("systemType") if code_info else None
                            ),
                            medication_display=(
                                code_info.get("display") if code_info else None
                            ),
                        )
                    )
                return resource_id

            case ResourceType.CONDITION.value:
                resource_id = await self.client.create_condition(resource)
                if resource_id and patient_id:
                    name = ConditionHandler.extract_name(resource)
                    code_info = ConditionHandler.extract_code_info(resource)
                    self.results.conditions_created.append(
                        CreatedCondition(
                            id=resource_id,
                            patient_id=patient_id,
                            condition=name,
                            condition_code=code_info.get("code") if code_info else None,
                            condition_system=(
                                code_info.get("system") if code_info else None
                            ),
                            condition_system_type=(
                                code_info.get("systemType") if code_info else None
                            ),
                            condition_display=(
                                code_info.get("display") if code_info else None
                            ),
                        )
                    )
                return resource_id

            case ResourceType.OBSERVATION.value:
                resource_id = await self.client.create_observation(resource)
                if resource_id and patient_id:
                    name = ObservationHandler.extract_name(resource)
                    code_info = ObservationHandler.extract_code_info(resource)
                    self.results.observations_created.append(
                        CreatedObservation(
                            id=resource_id,
                            patient_id=patient_id,
                            observation=name,
                            observation_code=(
                                code_info.get("code") if code_info else None
                            ),
                            observation_system=(
                                code_info.get("system") if code_info else None
                            ),
                            observation_system_type=(
                                code_info.get("systemType") if code_info else None
                            ),
                            observation_display=(
                                code_info.get("display") if code_info else None
                            ),
                        )
                    )
                return resource_id

            case ResourceType.ENCOUNTER.value:
                resource_id = await self.client.create_encounter(resource)
                if resource_id and patient_id:
                    name = EncounterHandler.extract_name(resource)
                    type_code_info = EncounterHandler.extract_type_code_info(resource)
                    reason_codes = EncounterHandler.extract_reason_codes(resource)
                    self.results.encounters_created.append(
                        CreatedEncounter(
                            id=resource_id,
                            patient_id=patient_id,
                            encounter=name,
                            type_code=(
                                type_code_info.get("code") if type_code_info else None
                            ),
                            type_system=(
                                type_code_info.get("system") if type_code_info else None
                            ),
                            type_system_type=(
                                type_code_info.get("systemType")
                                if type_code_info
                                else None
                            ),
                            type_display=(
                                type_code_info.get("display")
                                if type_code_info
                                else None
                            ),
                            reason_codes=reason_codes,
                        )
                    )
                return resource_id

            case ResourceType.PROCEDURE.value:
                resource_id = await self.client.create_procedure(resource)
                if resource_id and patient_id:
                    name = ProcedureHandler.extract_name(resource)
                    code_info = ProcedureHandler.extract_code_info(resource)
                    self.results.procedures_created.append(
                        CreatedProcedure(
                            id=resource_id,
                            patient_id=patient_id,
                            procedure=name,
                            procedure_code=code_info.get("code") if code_info else None,
                            procedure_system=(
                                code_info.get("system") if code_info else None
                            ),
                            procedure_system_type=(
                                code_info.get("systemType") if code_info else None
                            ),
                            procedure_display=(
                                code_info.get("display") if code_info else None
                            ),
                        )
                    )
                return resource_id
            case _:
                patient_msg = f" for patient {patient_id}" if patient_id else ""
                logger.warning(
                    f"Unsupported resource type: {resource_type}{patient_msg}"
                )
                return None
