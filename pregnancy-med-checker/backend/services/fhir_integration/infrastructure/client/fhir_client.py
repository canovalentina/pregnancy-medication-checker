"""FHIR client service for HTTP/CRUD/search operations."""

from __future__ import annotations

import asyncio
import os
import ssl
from datetime import UTC, datetime
from typing import Any

import aiohttp
import httpx
from fhirpy import AsyncFHIRClient  # type: ignore[import-untyped]
from fhirpy.base.exceptions import OperationOutcome  # type: ignore[import-untyped]
from loguru import logger

from ...domain.constants import (
    DEFAULT_FHIR_SERVER_URL,
    INGESTED_PATIENT_IDENTIFIER_SYSTEM,
    INGESTED_PATIENT_IDENTIFIER_VALUE,
    UNKNOWN_VALUE,
    ResourceType,
    ServerStatus,
)
from ...domain.models import FHIRServerStatus, PatientData
from ...utils.audit_logger import FHIRAuditLogger
from ..processing.resource_handlers import (
    ConditionHandler,
    EncounterHandler,
    LactationStageHandler,
    MedicationAdministrationHandler,
    MedicationHandler,
    MedicationRequestHandler,
    ObservationHandler,
    PatientHandler,
    PregnancyStageHandler,
    ProcedureHandler,
)


class FHIRClientService:
    """FHIR client using fhir-py for HTTP/CRUD/search transport.

    This client uses AsyncFHIRClient for async operations and supports resource validation
    using the $validate operation.
    """

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
        validate: bool = True,
        verify_ssl: bool | None = None,
        only_ingested_patients: bool = False,
    ):
        self.base_url = base_url or DEFAULT_FHIR_SERVER_URL
        self.timeout = float(os.getenv("FHIR_TIMEOUT", str(timeout)))
        self.token = token or os.getenv("FHIR_ACCESS_TOKEN")
        self.validate = validate
        self.verify_ssl = (
            verify_ssl
            if verify_ssl is not None
            else os.getenv("FHIR_VERIFY_SSL", "true").lower() == "true"
        )
        self.only_ingested_patients = only_ingested_patients

        authorization = f"Bearer {self.token}" if self.token else ""
        aiohttp_config: dict[str, Any] = {
            "timeout": aiohttp.ClientTimeout(total=self.timeout),
        }

        try:
            # Check if a custom HAPI FHIR instance is used
            if "/fhir" in self.base_url.lower():
                if not self.verify_ssl:
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                else:
                    ssl_context = True

                # Add connector to aiohttp_config
                aiohttp_config.update(
                    {"connector": aiohttp.TCPConnector(ssl=ssl_context)}
                )

            self.client = AsyncFHIRClient(
                url=self.base_url,
                authorization=authorization,
                aiohttp_config=aiohttp_config,
            )
            logger.info(
                f"Initialized async FHIR client with server: {self.base_url} "
                f"(validation: {self.validate}, timeout: {self.timeout}s, verify_ssl: {self.verify_ssl}, "
                f"only_ingested_patients: {self.only_ingested_patients})"
            )
        except Exception as e:
            logger.error(f"Error initializing fhir-py client: {e}")
            raise

    async def test_connection(self) -> FHIRServerStatus:
        """Retrieve CapabilityStatement to verify connectivity."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, verify=self.verify_ssl
            ) as c:
                r = await c.get(f"{self.base_url}/metadata?_format=json")
                r.raise_for_status()
                capability = r.json()
            fhir_version = capability.get("fhirVersion", UNKNOWN_VALUE)
            server_name = capability.get("software", {}).get("name", UNKNOWN_VALUE)
            return FHIRServerStatus(
                status=ServerStatus.CONNECTED,
                server=self.base_url,
                fhir_version=fhir_version,
                server_name=server_name,
                timestamp=datetime.now(UTC).isoformat(),
            )
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return FHIRServerStatus(
                status=ServerStatus.ERROR,
                server=self.base_url,
                timestamp=datetime.now(UTC).isoformat(),
                fhir_version=None,
                server_name=None,
            )

    async def ingest_resource(
        self,
        resource_type: ResourceType,
        data: dict[str, Any],
    ) -> str | None:
        """Create a resource of the given type. Returns the resource id or None."""
        try:
            payload = self._serialize_for_type(resource_type, data)
            resource = self.client.resource(resource_type.value)
            for k, v in payload.items():
                resource[k] = v

            # Validate resource if enabled (with fallback - continue even if validation fails)
            if self.validate:
                try:
                    is_valid = await resource.is_valid(raise_exception=True)
                    if not is_valid:
                        logger.warning(
                            f"Resource {resource_type.value} validation returned False, "
                            "but continuing with resource creation"
                        )
                except OperationOutcome as e:
                    logger.warning(
                        f"Resource {resource_type.value} validation failed: {e}. "
                        "Continuing with resource creation (validation is advisory)"
                    )
                except Exception as e:
                    logger.warning(
                        f"Resource {resource_type.value} validation error: {e}. "
                        "Continuing with resource creation"
                    )

            await resource.save()
            # Access resource ID
            rid = resource.get("id") or getattr(resource, "id", None)
            logger.info(f"Created {resource_type.value}: {rid}")
            # Log to audit log
            FHIRAuditLogger.log_create(
                resource_type=resource_type.value,
                resource_id=rid,
                success=True,
            )
            return rid
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating {resource_type.value}: {e}")
            # Log failure to audit log
            FHIRAuditLogger.log_create(
                resource_type=resource_type.value,
                resource_id=None,
                success=False,
                error=error_msg,
            )
            return None

    async def update_resource(
        self,
        resource_type: ResourceType,
        resource_id: str,
        data: dict[str, Any],
    ) -> bool:
        """Update a resource by id. Returns True on success."""
        try:
            payload = self._serialize_for_type(
                resource_type, {**data, "id": resource_id}
            )
            resource = self.client.resource(resource_type.value)
            for k, v in payload.items():
                resource[k] = v

            # Validate resource if enabled (with fallback - continue even if validation fails)
            if self.validate:
                try:
                    is_valid = await resource.is_valid(raise_exception=True)
                    if not is_valid:
                        logger.warning(
                            f"Resource {resource_type.value} validation returned False, "
                            "but continuing with resource update"
                        )
                except OperationOutcome as e:
                    logger.warning(
                        f"Resource {resource_type.value} validation failed: {e}. "
                        "Continuing with resource update (validation is advisory)"
                    )
                except Exception as e:
                    logger.warning(
                        f"Resource {resource_type.value} validation error: {e}. "
                        "Continuing with resource update"
                    )

            await resource.save()
            logger.info(f"Updated {resource_type.value}: {resource_id}")
            # Log successful update
            FHIRAuditLogger.log_update(
                resource_type=resource_type.value,
                resource_id=resource_id,
                success=True,
            )
            return True
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error updating {resource_type.value} {resource_id}: {e}")
            # Log failed update
            FHIRAuditLogger.log_update(
                resource_type=resource_type.value,
                resource_id=resource_id,
                success=False,
                error=error_msg,
            )
            return False

    async def read_resource(
        self, resource_type: ResourceType, resource_id: str
    ) -> dict[str, Any] | None:
        """Read resource JSON by id and return as dict."""
        try:
            res = await self.client.get(resource_type.value, resource_id)
            if not res:
                FHIRAuditLogger.log_read(
                    resource_type=resource_type.value,
                    resource_id=resource_id,
                    success=False,
                    error="Resource not found",
                )
                return None
            if hasattr(res, "serialize"):
                result = res.serialize()
            else:
                # Dealing with case of AttrDict
                result = dict(res)
            # Log successful read
            FHIRAuditLogger.log_read(
                resource_type=resource_type.value,
                resource_id=resource_id,
                success=True,
            )
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error reading {resource_type.value} {resource_id}: {e}")
            # Log failed read
            FHIRAuditLogger.log_read(
                resource_type=resource_type.value,
                resource_id=resource_id,
                success=False,
                error=error_msg,
            )
            return None

    async def delete_resource(
        self, resource_type: ResourceType, resource_id: str, cascade: bool = False
    ) -> bool:
        """Delete a resource by id. Returns True on success.

        Args:
            resource_type: The type of resource to delete
            resource_id: The ID of the resource to delete
            cascade: If True, use HAPI FHIR cascade delete (requires CascadingDeleteInterceptor)
                    See: https://hapifhir.io/hapi-fhir/docs/server_jpa/configuration.html#cascading-deletes
        """
        try:
            if cascade:
                # Use HAPI FHIR cascade delete with header (per HAPI FHIR docs)
                url = f"{self.base_url.rstrip('/')}/{resource_type.value}/{resource_id}"
                headers = {
                    "Accept": "application/fhir+json",
                    "X-Cascade": "delete",  # HAPI FHIR header format
                }

                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"

                async with aiohttp.ClientSession(  # noqa: SIM117
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    async with session.delete(url, headers=headers) as resp:
                        # HAPI returns 200/204 on success
                        if resp.status in (200, 204):
                            logger.info(
                                f"Cascade deleted {resource_type.value}: {resource_id}"
                            )
                            # Log successful cascade delete
                            FHIRAuditLogger.log_delete(
                                resource_type=resource_type.value,
                                resource_id=resource_id,
                                cascade=True,
                                success=True,
                            )
                            return True
                        # Cascade delete failed
                        error_text = await resp.text()
                        logger.error(
                            f"Error cascade deleting {resource_type.value} {resource_id}: "
                            f"HTTP {resp.status} - {error_text}"
                        )
                        resp.raise_for_status()
                        # Log failed cascade delete
                        FHIRAuditLogger.log_delete(
                            resource_type=resource_type.value,
                            resource_id=resource_id,
                            cascade=True,
                            success=False,
                            error=f"HTTP {resp.status}: {error_text}",
                        )
                        return False
            else:
                # Use standard fhir-py delete (no cascade)
                try:
                    await self.client.delete(resource_type.value, resource_id)
                    logger.info(f"Deleted {resource_type.value}: {resource_id}")
                    # Log successful delete
                    FHIRAuditLogger.log_delete(
                        resource_type=resource_type.value,
                        resource_id=resource_id,
                        cascade=False,
                        success=True,
                    )
                    return True
                except Exception as delete_error:
                    error_msg = str(delete_error)
                    logger.error(
                        f"Error deleting {resource_type.value} {resource_id} with fhir-py: {delete_error}"
                    )
                    # Log failed delete
                    FHIRAuditLogger.log_delete(
                        resource_type=resource_type.value,
                        resource_id=resource_id,
                        cascade=False,
                        success=False,
                        error=error_msg,
                    )
                    raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error deleting {resource_type.value} {resource_id}: {e}")
            # Log failed delete (catch-all)
            FHIRAuditLogger.log_delete(
                resource_type=resource_type.value,
                resource_id=resource_id,
                cascade=cascade,
                success=False,
                error=error_msg,
            )
            return False

    async def search_resources(
        self,
        resource_type: ResourceType,
        search_params: dict[str, Any] | None = None,
        count: int = 100,
        *,
        fetch_all: bool = False,
        retries: int = 2,
        backoff_sec: float = 1.0,
    ) -> list[dict[str, Any]]:
        """Search resources by parameters."""
        attempt = 0
        while True:
            try:
                query = self.client.resources(resource_type.value).search()
                if search_params:
                    for k, v in search_params.items():
                        query = query.search(**{k: v})
                query = query.limit(count)

                if fetch_all:
                    results = [r.serialize() for r in await query.fetch_all()]
                else:
                    bundle = await query.fetch()
                    results = [r.serialize() for r in bundle]

                logger.info(
                    f"Search {resource_type.value} returned {len(results)} items (fetch_all={fetch_all})"
                )
                # Log search operation
                FHIRAuditLogger.log_search(
                    resource_type=resource_type.value,
                    search_params=search_params,
                    result_count=len(results),
                    success=True,
                )
                return results
            except Exception as e:
                attempt += 1
                if attempt > retries:
                    logger.error(f"Search error for {resource_type.value}: {e}")
                    return []
                sleep_for = backoff_sec * attempt
                logger.warning(
                    f"Search transient error, retrying in {sleep_for:.1f}s: {e}"
                )
                await asyncio.sleep(sleep_for)

    async def create_patient(self, patient_data: dict[str, Any]) -> str | None:
        return await self.ingest_resource(ResourceType.PATIENT, patient_data)

    async def read_patient(self, patient_id: str) -> PatientData | None:
        res = await self.read_resource(ResourceType.PATIENT, patient_id)
        return PatientHandler.to_patient_data(res) if res else None

    async def _delete_patient_referencing_resources(self, patient_id: str) -> int:
        """Helper function to manually delete all resources that reference a patient.

        This is used as a fallback when HAPI FHIR cascade delete is not available.

        Args:
            patient_id: The ID of the patient whose referencing resources should be deleted

        Returns:
            Number of referencing resources deleted
        """
        # Map of ResourceTypes to their corresponding get_patient_* methods
        resource_type_methods = {
            ResourceType.MEDICATION_REQUEST: self.get_patient_medications,
            ResourceType.CONDITION: self.get_patient_conditions,
            ResourceType.OBSERVATION: self.get_patient_observations,
            ResourceType.ENCOUNTER: self.get_patient_encounters,
            ResourceType.PROCEDURE: self.get_patient_procedures,
            ResourceType.MEDICATION_ADMINISTRATION: (
                self.get_patient_medication_administrations
            ),
        }

        deleted_count = 0
        for resource_type, get_method in resource_type_methods.items():
            try:
                # Get all resources of this type for the patient
                resources = await get_method(patient_id, fetch_all=True)
                for resource in resources:
                    resource_id = resource.get("id")
                    if resource_id:
                        success = await self.delete_resource(
                            resource_type, resource_id, cascade=False
                        )
                        if success:
                            deleted_count += 1
                            logger.debug(
                                f"Deleted {resource_type.value}/{resource_id} "
                                f"referencing patient {patient_id}"
                            )
            except Exception as e:
                logger.warning(
                    f"Error deleting {resource_type.value} resources for patient {patient_id}: {e}"
                )

        if deleted_count > 0:
            logger.info(
                f"Deleted {deleted_count} resources referencing patient {patient_id}"
            )

        return deleted_count

    async def delete_patient(self, patient_id: str, cascade: bool = True) -> bool:
        """Delete a patient by id. Returns True on success.

        Args:
            patient_id: The ID of the patient to delete
            cascade: If True (default), try HAPI FHIR cascade delete first,
                    fall back to manual cascade if server doesn't support it
        """
        deleted_count = 0
        if cascade:
            # First, try HAPI FHIR's built-in cascade delete
            # (requires CascadingDeleteInterceptor to be registered on server)
            success = await self.delete_resource(
                ResourceType.PATIENT, patient_id, cascade=True
            )
            if success:
                return True

            # If HAPI cascade delete failed, manually delete referencing resources
            logger.info(
                f"HAPI FHIR cascade delete not available for patient {patient_id}. "
                "Performing manual cascade delete."
            )
            deleted_count = await self._delete_patient_referencing_resources(patient_id)

        # Now delete the patient itself
        patient_deleted = await self.delete_resource(
            ResourceType.PATIENT, patient_id, cascade=False
        )

        # Log manual cascade delete summary (if we did manual cascade)
        if cascade and deleted_count > 0:
            # Log the cascade delete operation with count of deleted resources
            FHIRAuditLogger.log_delete(
                resource_type="Patient",
                resource_id=patient_id,
                cascade=True,
                success=patient_deleted,
                deleted_referencing_resources=deleted_count,
            )

        return patient_deleted

    async def delete_all_ingested_patients(
        self, cascade: bool = True, ingestion_tag: str | None = None
    ) -> dict[str, Any]:
        """Delete all patients with the ingestion identifier.

        Args:
            cascade: If True (default), delete patient and all referencing resources
            ingestion_tag: Tag value to filter by. If None, uses default production tag.
                          Use INGESTED_PATIENT_IDENTIFIER_VALUE_TEST for test data.

        Returns:
            Dictionary with deletion summary
        """
        tag_value = ingestion_tag or INGESTED_PATIENT_IDENTIFIER_VALUE
        logger.info(
            f"Searching for all ingested patients with tag '{tag_value}' to delete..."
        )

        # Use existing search_patients method with only_ingested_patients=True
        # fetch_all=True will handle pagination and get all patients automatically
        patients = await self.search_patients(
            fetch_all=True, only_ingested_patients=True, ingestion_tag=ingestion_tag
        )

        total_found = len(patients)
        logger.info(f"Found {total_found} ingested patient(s) to delete")

        if total_found == 0:
            logger.info("No ingested patients found to delete")
            return {
                "total_found": 0,
                "total_deleted": 0,
                "failed": [],
                "deleted": [],
            }

        deleted: list[str] = []
        failed: list[str] = []

        for patient in patients:
            patient_id = patient.id
            if not patient_id:
                logger.warning("Skipping patient without ID")
                continue

            logger.info(f"Deleting patient: {patient.name} (ID: {patient_id})")

            try:
                # Use existing delete_patient method
                success = await self.delete_patient(patient_id, cascade=cascade)
                if success:
                    deleted.append(patient_id)
                    logger.success(f"Successfully deleted patient {patient_id}")
                else:
                    failed.append(patient_id)
                    logger.error(f"Failed to delete patient {patient_id}")
            except Exception as e:
                failed.append(patient_id)
                logger.error(f"Error deleting patient {patient_id}: {e}")

        logger.info(
            f"Deletion complete: {len(deleted)}/{total_found} patients deleted successfully"
        )
        if failed:
            logger.warning(f"Failed to delete {len(failed)} patient(s): {failed}")

        return {
            "total_found": total_found,
            "total_deleted": len(deleted),
            "failed": failed,
            "deleted": deleted,
        }

    async def get_ingested_patient_ids(self) -> dict[str, Any]:
        """Get count and list of IDs for all ingested patients.

        Returns:
            Dictionary with total number of IDs and IDs.
        """
        logger.info("Searching for all ingested patients...")

        # Use existing search_patients method with only_ingested_patients=True
        # fetch_all=True will handle pagination and get all patients automatically
        patients = await self.search_patients(
            fetch_all=True, only_ingested_patients=True
        )

        patient_ids = [patient.id for patient in patients if patient.id]

        logger.info(f"Found {len(patient_ids)} ingested patient(s)")

        return {
            "count": len(patient_ids),
            "patient_ids": patient_ids,
        }

    async def search_patients(
        self,
        name: str | None = None,
        birth_date: str | None = None,
        gender: str | None = None,
        count: int = 100,
        *,
        fetch_all: bool = False,
        only_ingested_patients: bool | None = None,
        ingestion_tag: str | None = None,
    ) -> list[PatientData]:
        """Search for patients in the FHIR server.

        Args:
            name: Patient name to search for
            birth_date: Patient birth date (YYYY-MM-DD)
            gender: Patient gender (male/female/other)
            count: Maximum number of results to return
            fetch_all: If True, fetch all matching patients (ignoring count limit)
            only_ingested_patients: If True, only search for patients with ingestion identifier.
                                   If None, uses the client's default (self.only_ingested_patients)
            ingestion_tag: Tag value to filter by. If None, uses default production tag.
        """
        params: dict[str, Any] = {}
        if name:
            params["name"] = name
        if birth_date:
            params["birthdate"] = birth_date
        if gender:
            params["gender"] = gender

        # Apply ingestion identifier filter if requested
        if only_ingested_patients is None:
            only_ingested_patients = self.only_ingested_patients

        if only_ingested_patients:
            # Use provided ingestion_tag or default to production tag
            tag_value = ingestion_tag or INGESTED_PATIENT_IDENTIFIER_VALUE
            identifier_param = f"{INGESTED_PATIENT_IDENTIFIER_SYSTEM}|{tag_value}"
            params["identifier"] = identifier_param
            logger.debug(
                f"Filtering search to only ingested patients "
                f"({INGESTED_PATIENT_IDENTIFIER_SYSTEM}={tag_value})"
            )

        results = await self.search_resources(
            ResourceType.PATIENT, params, count=count, fetch_all=fetch_all
        )
        return [PatientHandler.to_patient_data(res) for res in results]

    async def create_medication_request(
        self, medication_data: dict[str, Any]
    ) -> str | None:
        return await self.ingest_resource(
            ResourceType.MEDICATION_REQUEST, medication_data
        )

    async def get_patient_medications(
        self, patient_id: str, count: int = 50, *, fetch_all: bool = False
    ) -> list[dict[str, Any]]:
        params = {"subject": f"Patient/{patient_id}"}
        items = await self.search_resources(
            ResourceType.MEDICATION_REQUEST, params, count=count, fetch_all=fetch_all
        )
        results = [MedicationRequestHandler.to_dict(res) for res in items]
        logger.info(
            f"Fetched {len(results)} MedicationRequest for patient {patient_id}"
        )
        return results

    async def create_condition(self, condition_data: dict[str, Any]) -> str | None:
        return await self.ingest_resource(ResourceType.CONDITION, condition_data)

    async def get_patient_conditions(
        self, patient_id: str, count: int = 50, *, fetch_all: bool = False
    ) -> list[dict[str, Any]]:
        params = {"subject": f"Patient/{patient_id}"}
        items = await self.search_resources(
            ResourceType.CONDITION, params, count=count, fetch_all=fetch_all
        )
        results = [ConditionHandler.to_dict(res) for res in items]
        logger.info(f"Fetched {len(results)} Condition for patient {patient_id}")
        return results

    async def create_observation(self, observation_data: dict[str, Any]) -> str | None:
        return await self.ingest_resource(ResourceType.OBSERVATION, observation_data)

    async def get_patient_observations(
        self,
        patient_id: str,
        count: int = 50,
        *,
        fetch_all: bool = False,
        code_filter: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        params = {"subject": f"Patient/{patient_id}"}
        if code_filter:
            params["code"] = code_filter
        if category:
            params["category"] = category

        items = await self.search_resources(
            ResourceType.OBSERVATION, params, count=count, fetch_all=fetch_all
        )
        results = [ObservationHandler.to_dict(res) for res in items]
        logger.info(f"Fetched {len(results)} Observation for patient {patient_id}")
        return results

    async def create_medication(self, medication_data: dict[str, Any]) -> str | None:
        return await self.ingest_resource(ResourceType.MEDICATION, medication_data)

    async def get_medication(self, medication_id: str) -> dict[str, Any] | None:
        """Get a Medication resource by ID."""
        resource = await self.read_resource(ResourceType.MEDICATION, medication_id)
        if resource:
            return MedicationHandler.to_dict(resource)
        return None

    async def create_medication_administration(
        self, medication_administration_data: dict[str, Any]
    ) -> str | None:
        return await self.ingest_resource(
            ResourceType.MEDICATION_ADMINISTRATION,
            medication_administration_data,
        )

    async def get_patient_medication_administrations(
        self, patient_id: str, count: int = 50, *, fetch_all: bool = False
    ) -> list[dict[str, Any]]:
        params = {"subject": f"Patient/{patient_id}"}
        items = await self.search_resources(
            ResourceType.MEDICATION_ADMINISTRATION,
            params,
            count=count,
            fetch_all=fetch_all,
        )
        results = [MedicationAdministrationHandler.to_dict(res) for res in items]
        logger.info(
            f"Fetched {len(results)} MedicationAdministration for patient {patient_id}"
        )
        return results

    async def create_encounter(self, encounter_data: dict[str, Any]) -> str | None:
        return await self.ingest_resource(ResourceType.ENCOUNTER, encounter_data)

    async def get_patient_encounters(
        self, patient_id: str, count: int = 50, *, fetch_all: bool = False
    ) -> list[dict[str, Any]]:
        params = {"subject": f"Patient/{patient_id}"}
        items = await self.search_resources(
            ResourceType.ENCOUNTER, params, count=count, fetch_all=fetch_all
        )
        results = [EncounterHandler.to_dict(res) for res in items]
        logger.info(f"Fetched {len(results)} Encounter for patient {patient_id}")
        return results

    async def create_procedure(self, procedure_data: dict[str, Any]) -> str | None:
        return await self.ingest_resource(ResourceType.PROCEDURE, procedure_data)

    async def get_patient_procedures(
        self, patient_id: str, count: int = 50, *, fetch_all: bool = False
    ) -> list[dict[str, Any]]:
        params = {"subject": f"Patient/{patient_id}"}
        items = await self.search_resources(
            ResourceType.PROCEDURE, params, count=count, fetch_all=fetch_all
        )
        results = [ProcedureHandler.to_dict(res) for res in items]
        logger.info(f"Fetched {len(results)} Procedure for patient {patient_id}")
        return results

    def _serialize_for_type(
        self, resource_type: ResourceType, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Pass-through serializer: drop None values for cleaner payloads."""
        return {k: v for k, v in data.items() if v is not None}

    async def get_pregnancy_stage(self, patient_id: str) -> dict[str, Any] | None:
        """Get the current pregnancy stage (gestational weeks) for a patient."""
        try:
            observations = await self.get_patient_observations(
                patient_id, fetch_all=True
            )
            return PregnancyStageHandler.extract_from_observations(observations)
        except Exception as e:
            logger.error(f"Error getting pregnancy stage for patient {patient_id}: {e}")
            return None

    async def get_lactation_stage(self, patient_id: str) -> dict[str, Any] | None:
        """Get the current lactation stage for a patient."""
        try:
            observations = await self.get_patient_observations(
                patient_id, fetch_all=True
            )
            return LactationStageHandler.extract_from_observations(observations)
        except Exception as e:
            logger.error(f"Error getting lactation stage for patient {patient_id}: {e}")
            return None

    async def get_patient_medications_list(
        self, patient_id: str
    ) -> list[dict[str, Any]]:
        """Get a simplified list of medications for a patient."""
        try:
            # get_patient_medications already uses MedicationRequestHandler.to_dict()
            # which provides all the fields we need
            medications = await self.get_patient_medications(patient_id, fetch_all=True)
            return medications
        except Exception as e:
            logger.error(
                f"Error getting medications list for patient {patient_id}: {e}"
            )
            return []
