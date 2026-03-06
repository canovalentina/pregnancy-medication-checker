"""API handlers for FHIR endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException  # type: ignore[import-untyped]
from loguru import logger

from ..domain.constants import PREGNANCY_CODE, ResourceType, ServerStatus
from ..domain.models import (
    APIResponse,
    FHIRServerStatus,
    IngestionResult,
    ResourceResponse,
)
from ..domain.protocols import FHIRClientPort, IngestionServicePort
from ..infrastructure.client.fhir_client import FHIRClientService
from ..infrastructure.ingestion.fhir_ingestor import FHIRResourceIngestor


class FHIRAPIHandlers:
    """Handler class for FHIR-related API endpoints."""

    def __init__(
        self,
        client: FHIRClientPort | None = None,
        ingestion_service: IngestionServicePort | None = None,
    ):
        """Initialize API handlers with FHIR services.

        Allows dependency injection for testing and alternate implementations.
        """
        self.client: FHIRClientPort = client or FHIRClientService()
        self.ingestion_service: IngestionServicePort = (
            ingestion_service or FHIRResourceIngestor(self.client)
        )

    @staticmethod
    def _raise_not_found_error(message: str) -> None:
        """Raise HTTP 404 exception."""
        raise HTTPException(status_code=404, detail=message) from None

    async def get_fhir_status(self) -> FHIRServerStatus:
        """Get FHIR server connection status."""
        try:
            return await self.client.test_connection()
        except Exception as e:
            logger.error(f"FHIR status check failed: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def is_server_connected(self) -> bool:
        """Check if FHIR server is connected (helper method for testing)."""
        try:
            status = await self.client.test_connection()
            return status.status == ServerStatus.CONNECTED
        except Exception:
            return False

    async def search_patients(
        self,
        name: str | None = None,
        birth_date: str | None = None,
        gender: str | None = None,
        only_ingested_patients: bool | None = None,
    ) -> ResourceResponse:
        """Search for patients in the FHIR server.

        Args:
            name: Patient name to search for
            birth_date: Patient birth date (YYYY-MM-DD)
            gender: Patient gender (male/female/other)
            only_ingested_patients: If True, only search for patients with ingestion identifier.
                                   If None, uses the client's default setting.
        """
        try:
            result = await self.client.search_patients(
                name=name,
                birth_date=birth_date,
                gender=gender,
                only_ingested_patients=only_ingested_patients,
            )
            return ResourceResponse(
                resources=[patient.model_dump() for patient in result],
                total=len(result),
                server=self.client.base_url,
            )
        except Exception as e:
            logger.error(f"Patient search failed: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_patient_medications(self, patient_id: str) -> ResourceResponse:
        """Get patient's medications."""
        try:
            medications = await self.client.get_patient_medications(patient_id)
            return ResourceResponse(
                resources=medications,
                total=len(medications),
                patient_id=patient_id,
                server=self.client.base_url,
            )
        except Exception as e:
            logger.error(f"Failed to get medications for patient {patient_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_patient_conditions(self, patient_id: str) -> ResourceResponse:
        """Get patient's conditions."""
        try:
            conditions = await self.client.get_patient_conditions(patient_id)
            return ResourceResponse(
                resources=conditions,
                total=len(conditions),
                patient_id=patient_id,
                server=self.client.base_url,
            )
        except Exception as e:
            logger.error(f"Failed to get conditions for patient {patient_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_pregnancy_observations(self, patient_id: str) -> ResourceResponse:
        """Get pregnancy-related observations for a patient."""
        try:
            observations = await self.client.get_patient_observations(
                patient_id, category="procedure"
            )
            return ResourceResponse(
                resources=observations,
                total=len(observations),
                patient_id=patient_id,
                server=self.client.base_url,
            )
        except Exception as e:
            logger.error(
                f"Failed to get pregnancy observations for patient {patient_id}: {e}"
            )
            raise HTTPException(status_code=500, detail=str(e)) from e

    def _calculate_pregnancy_history(
        self, conditions: list[dict[str, Any]], observations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate pregnancy history statistics from conditions and observations.

        Args:
            conditions: List of patient conditions
            observations: List of patient observations

        Returns:
            Dictionary with pregnancy history statistics
        """
        pregnancies = []
        total_births = 0
        preterm_births = 0

        # Find all pregnancy conditions
        for condition in conditions:
            code = condition.get("code", {})
            codings = code.get("coding", []) if isinstance(code, dict) else []

            is_pregnancy = False
            for coding in codings:
                code_value = coding.get("code", "")
                system = coding.get("system", "")

                # Check if this is a pregnancy condition
                if (
                    code_value == PREGNANCY_CODE
                    or "pregnancy" in coding.get("display", "").lower()
                ):
                    is_pregnancy = True
                    break

            if is_pregnancy:
                onset = condition.get("onsetDateTime")
                abatement = condition.get("abatementDateTime")

                # Check condition text for pre-term indicators
                condition_text = (
                    code.get("text", "").lower() if isinstance(code, dict) else ""
                )
                text_indicates_preterm = (
                    "pre-term" in condition_text
                    or "preterm" in condition_text
                    or "premature" in condition_text
                    or "prematurity" in condition_text
                )

                # If abatement exists, pregnancy ended (likely a birth)
                is_preterm = text_indicates_preterm
                if abatement:
                    total_births += 1

                    # Check if it was preterm (less than 37 weeks)
                    # Calculate gestational age at abatement
                    if onset and abatement:
                        try:
                            # Normalize date strings to ensure timezone-aware datetimes
                            onset_str = (
                                onset.replace("Z", "+00:00") if "Z" in onset else onset
                            )
                            abatement_str = (
                                abatement.replace("Z", "+00:00")
                                if "Z" in abatement
                                else abatement
                            )

                            onset_date = datetime.fromisoformat(onset_str)
                            abatement_date = datetime.fromisoformat(abatement_str)

                            # Ensure both are timezone-aware (use UTC if naive)
                            if onset_date.tzinfo is None:
                                onset_date = onset_date.replace(tzinfo=UTC)
                            if abatement_date.tzinfo is None:
                                abatement_date = abatement_date.replace(tzinfo=UTC)

                            weeks_pregnant = (abatement_date - onset_date).days / 7

                            # Mark as preterm if either text indicates it OR calculated weeks < 37
                            if weeks_pregnant < 37:
                                if (
                                    not is_preterm
                                ):  # Only increment if not already marked from text
                                    preterm_births += 1
                                is_preterm = True
                            elif (
                                is_preterm
                            ):  # If text says preterm but calculation doesn't, trust text
                                preterm_births += 1
                        except (ValueError, AttributeError, TypeError):
                            # If date calculation fails but text indicates preterm, use text
                            if is_preterm:
                                preterm_births += 1

                # Get related observations for this pregnancy
                pregnancy_obs = []
                if onset:
                    for obs in observations:
                        obs_date = obs.get("effectiveDateTime") or obs.get("issued")
                        if obs_date and onset:
                            try:
                                # Normalize date strings to ensure timezone-aware datetimes
                                obs_date_str = (
                                    obs_date.replace("Z", "+00:00")
                                    if "Z" in obs_date
                                    else obs_date
                                )
                                onset_str = (
                                    onset.replace("Z", "+00:00")
                                    if "Z" in onset
                                    else onset
                                )

                                obs_dt = datetime.fromisoformat(obs_date_str)
                                onset_dt = datetime.fromisoformat(onset_str)

                                # Ensure both are timezone-aware (use UTC if naive)
                                if obs_dt.tzinfo is None:
                                    obs_dt = obs_dt.replace(tzinfo=UTC)
                                if onset_dt.tzinfo is None:
                                    onset_dt = onset_dt.replace(tzinfo=UTC)

                                if obs_dt >= onset_dt:
                                    # Check if this is a gestational age observation
                                    obs_code = obs.get("code", {})
                                    obs_codings = (
                                        obs_code.get("coding", [])
                                        if isinstance(obs_code, dict)
                                        else []
                                    )
                                    for oc in obs_codings:
                                        if (
                                            "gestational"
                                            in oc.get("display", "").lower()
                                            or oc.get("code") == "57036006"
                                        ):
                                            value = obs.get("valueQuantity", {}).get(
                                                "value"
                                            )
                                            pregnancy_obs.append(
                                                {
                                                    "id": obs.get("id", ""),
                                                    "date": obs_date,
                                                    "type": "gestational_age",
                                                    "value": value,
                                                    "unit": obs.get(
                                                        "valueQuantity", {}
                                                    ).get("unit", "weeks"),
                                                }
                                            )
                                            break
                            except (ValueError, AttributeError):
                                pass

                pregnancies.append(
                    {
                        "id": condition.get("id", f"pregnancy_{len(pregnancies) + 1}"),
                        "startDate": onset or "",
                        "endDate": abatement or None,
                        "observations": pregnancy_obs,
                        "outcome": "birth" if abatement else "ongoing",
                        "isPreterm": is_preterm,
                    }
                )

        return {
            "totalBirths": total_births,
            "pretermBirths": preterm_births,
            "pregnancies": pregnancies,
        }

    async def get_patient_summary(self, patient_id: str) -> ResourceResponse:
        """Get comprehensive patient summary."""
        try:
            patient = await self.client.read_patient(patient_id)
            if not patient:
                self._raise_not_found_error(f"Patient {patient_id} not found")
                return ResourceResponse(  # type: ignore[unreachable]
                    resources=[],
                    total=0,
                    patient_id=patient_id,
                    server=self.client.base_url,
                )

            # Fetch all resources for the patient (not just first 50)
            medications = await self.client.get_patient_medications(
                patient_id, fetch_all=True
            )
            conditions = await self.client.get_patient_conditions(
                patient_id, fetch_all=True
            )
            observations = await self.client.get_patient_observations(
                patient_id, fetch_all=True
            )

            logger.info(
                f"Patient summary for {patient_id}: "
                f"{len(medications)} medications, {len(conditions)} conditions, "
                f"{len(observations)} observations"
            )

            # Calculate pregnancy history
            pregnancy_history = self._calculate_pregnancy_history(
                conditions, observations
            )

            summary = {
                "patient": patient.model_dump(),
                "medications": medications,
                "conditions": conditions,
                "observations": observations,
                "pregnancyHistory": pregnancy_history,
            }

            return ResourceResponse(
                resources=[summary],
                total=1,
                patient_id=patient_id,
                server=self.client.base_url,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get summary for patient {patient_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def ingest_resource_data(
        self,
        data_path: Path | str,
        max_bundles: int | None = None,
        ingestion_tag: str | None = None,
    ) -> IngestionResult:
        """Ingest FHIR resource data from a file or directory.

        Automatically detects FHIR Bundle format. Handles both single files
        and directories containing multiple bundle files.

        Args:
            data_path: Path to a single FHIR Bundle file or directory
            max_bundles: Maximum number of bundles to process (for directories).
                        Each file = 1 bundle. If None, processes all.
            ingestion_tag: Tag value to use for identifying ingested patients.
                         If None, uses default production tag.
        """
        try:
            return await self.ingestion_service.ingest_resource_data(
                data_path=data_path,
                max_bundles=max_bundles,
                ingestion_tag=ingestion_tag,
            )
        except Exception as e:
            logger.error(f"Resource data ingestion failed: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    def get_ingestion_status(self) -> IngestionResult:
        """Get current data ingestion status."""
        try:
            # Return the most recent ingestion results
            return self.ingestion_service.get_ingestion_status()
        except Exception as e:
            logger.error(f"Failed to get ingestion status: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    def validate_ingested_data(self) -> APIResponse:
        """Validate ingested FHIR data - TODO: Implement in next sprint."""
        return APIResponse(
            status="placeholder",
            message="Data validation not yet implemented - planned for next sprint",
            data={"status": "placeholder"},
        )

    async def delete_patient(self, patient_id: str) -> APIResponse:
        """Delete a patient by id using cascade delete.

        This will delete the patient and all resources that reference it
        (Conditions, MedicationRequests, Encounters, Observations, etc.).
        """
        try:
            # Verify patient exists before deletion
            patient = await self.client.read_patient(patient_id)
            if not patient:
                self._raise_not_found_error(f"Patient {patient_id} not found")

            # Delete with cascade (default behavior)
            success = await self.client.delete_patient(patient_id, cascade=True)
            if not success:
                raise HTTPException(
                    status_code=500, detail=f"Failed to delete patient {patient_id}"
                )

            # Verify deletion by attempting to read the patient
            # Should raise an exception or return None if deleted successfully
            try:
                deleted_patient = await self.client.read_patient(patient_id)
                if deleted_patient:
                    raise RuntimeError(
                        f"Patient {patient_id} still exists after deletion"
                    )
            except Exception:
                # Not found means deletion succeeded
                pass

            return APIResponse(
                status="success",
                message=f"Patient {patient_id} deleted successfully",
                data={"patient_id": patient_id, "deleted": True},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete patient {patient_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def delete_all_ingested_patients(
        self, cascade: bool = True, ingestion_tag: str | None = None
    ) -> APIResponse:
        """Delete all patients with the ingestion identifier.

        This will find and delete all patients that were ingested by this application,
        along with all their associated resources (if cascade=True).

        Args:
            cascade: If True, delete patient and all referencing resources
            ingestion_tag: Tag value to filter by. If None, uses default production tag.
        """
        try:
            result = await self.client.delete_all_ingested_patients(
                cascade=cascade, ingestion_tag=ingestion_tag
            )

            if result["total_found"] == 0:
                return APIResponse(
                    status="success",
                    message="No ingested patients found to delete",
                    data=result,
                )

            if result["total_deleted"] == result["total_found"]:
                return APIResponse(
                    status="success",
                    message=f"Successfully deleted {result['total_deleted']} ingested patient(s)",
                    data=result,
                )
            elif result["total_deleted"] > 0:
                return APIResponse(
                    status="partial",
                    message=(
                        f"Deleted {result['total_deleted']}/{result['total_found']} patients. "
                        f"{len(result['failed'])} deletion(s) failed."
                    ),
                    data=result,
                )
            else:
                return APIResponse(
                    status="error",
                    message=f"Failed to delete any patients. {len(result['failed'])} deletion(s) failed.",
                    data=result,
                )
        except Exception as e:
            logger.error(f"Failed to delete ingested patients: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_ingested_patient_ids(self) -> APIResponse:
        """Get count and list of IDs for all ingested patients."""
        try:
            result = await self.client.get_ingested_patient_ids()

            return APIResponse(
                status="success",
                message=f"Found {result['count']} ingested patient(s)",
                data=result,
            )
        except Exception as e:
            logger.error(f"Failed to get ingested patient IDs: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def delete_resource(
        self, resource_type: str, resource_id: str
    ) -> APIResponse:
        """Delete a resource by type and id."""
        try:
            # Validate resource type
            try:
                rt = ResourceType(resource_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid resource type: {resource_type}",
                ) from None

            # Verify resource exists before deletion
            resource = await self.client.read_resource(rt, resource_id)
            if not resource:
                self._raise_not_found_error(f"{resource_type} {resource_id} not found")

            success = await self.client.delete_resource(rt, resource_id)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete {resource_type} {resource_id}",
                )

            return APIResponse(
                status="success",
                message=f"{resource_type} {resource_id} deleted successfully",
                data={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "deleted": True,
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete {resource_type} {resource_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_pregnancy_stage(self, patient_id: str) -> APIResponse:
        """Get the current pregnancy stage (gestational weeks) for a patient."""
        try:
            # Verify patient exists
            patient = await self.client.read_patient(patient_id)
            if not patient:
                self._raise_not_found_error(f"Patient {patient_id} not found")

            pregnancy_stage = await self.client.get_pregnancy_stage(patient_id)

            if pregnancy_stage is None:
                return APIResponse(
                    status="success",
                    message=f"No pregnancy stage data found for patient {patient_id}",
                    data=None,
                )

            return APIResponse(
                status="success",
                message=f"Pregnancy stage retrieved for patient {patient_id}",
                data=pregnancy_stage,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get pregnancy stage for patient {patient_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_lactation_stage(self, patient_id: str) -> APIResponse:
        """Get the current lactation stage for a patient."""
        try:
            # Verify patient exists
            patient = await self.client.read_patient(patient_id)
            if not patient:
                self._raise_not_found_error(f"Patient {patient_id} not found")

            lactation_stage = await self.client.get_lactation_stage(patient_id)

            if lactation_stage is None:
                return APIResponse(
                    status="success",
                    message=f"No lactation stage data found for patient {patient_id}",
                    data=None,
                )

            return APIResponse(
                status="success",
                message=f"Lactation stage retrieved for patient {patient_id}",
                data=lactation_stage,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get lactation stage for patient {patient_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def get_patient_medications_list(self, patient_id: str) -> ResourceResponse:
        """Get a simplified list of medications for a patient."""
        try:
            # Verify patient exists
            patient = await self.client.read_patient(patient_id)
            if not patient:
                self._raise_not_found_error(f"Patient {patient_id} not found")

            medications = await self.client.get_patient_medications_list(patient_id)

            return ResourceResponse(
                resources=medications,
                total=len(medications),
                patient_id=patient_id,
                server=self.client.base_url,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to get medications list for patient {patient_id}: {e}"
            )
            raise HTTPException(status_code=500, detail=str(e)) from e
