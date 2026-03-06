"""FHIR Bundle ingestion service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from ...domain.constants import (
    INGESTED_PATIENT_IDENTIFIER_SYSTEM,
    INGESTED_PATIENT_IDENTIFIER_VALUE,
    SUPPORTED_INGESTION_TYPES,
    ResourceType,
)
from ...domain.models import IngestionResult, IngestionSummary
from ...domain.protocols import IngestionServicePort
from ...utils.audit_logger import FHIRAuditLogger
from ..processing.resource_handlers import PatientHandler
from .base_ingestor import BaseIngestor


class FHIRResourceIngestor(BaseIngestor, IngestionServicePort):
    """Ingests FHIR Resource bundles from files or directories.

    Handles both single FHIR Bundle files and directories containing multiple bundle files.
    Automatically detects FHIR Bundle format.
    """

    SUPPORTED_TYPES = {rt.value for rt in SUPPORTED_INGESTION_TYPES}

    async def ingest_resource_data(
        self,
        data_path: Path | str,
        max_bundles: int | None = None,
        ingestion_tag: str | None = None,
    ) -> IngestionResult:
        """Ingest FHIR resource data from a file or directory.

        Automatically detects FHIR Bundle format and processes accordingly.
        Handles both single files and directories containing multiple bundle files.

        Args:
            data_path: Path to a single FHIR Bundle file or directory containing bundle files
            max_bundles: Maximum number of bundles to process (for directories).
                        Each file = 1 bundle. If None, processes all.
            ingestion_tag: Tag value to use for identifying ingested patients.
                         If None, uses default production tag.
                         Use INGESTED_PATIENT_IDENTIFIER_VALUE_TEST for test data.

        Returns:
            IngestionResult with summary of ingested resources
        """
        # Set ingestion tag (default to production, or use provided/test tag)
        self.ingestion_tag = (
            ingestion_tag
            if ingestion_tag is not None
            else INGESTED_PATIENT_IDENTIFIER_VALUE
        )
        data_path = Path(data_path) if isinstance(data_path, str) else data_path

        if not data_path.exists():
            error_msg = f"Data path not found: {data_path}"
            logger.error(error_msg)
            # Log failed ingestion
            FHIRAuditLogger.log_ingestion(
                data_path=str(data_path),
                success=False,
                error=error_msg,
            )
            return IngestionResult(
                summary=IngestionSummary(ingestion_timestamp=""),
                errors=[error_msg],
            )

        # Handle single file
        if data_path.is_file():
            if not self._is_fhir_bundle(data_path):
                error_msg = f"File {data_path} is not a FHIR Bundle"
                logger.error(error_msg)
                # Log failed ingestion
                FHIRAuditLogger.log_ingestion(
                    data_path=str(data_path),
                    success=False,
                    error=error_msg,
                )
                return IngestionResult(
                    summary=IngestionSummary(ingestion_timestamp=""),
                    errors=[error_msg],
                )
            logger.info(f"Starting ingestion of bundle file: {data_path.name}")
            logger.info(f"Ingesting single FHIR Bundle file: {data_path}")
            self._reset_results()
            await self._ingest_bundle(data_path)
            result = self._finalize_results()
            # Log ingestion to audit log
            FHIRAuditLogger.log_ingestion(
                data_path=str(data_path),
                total_patients=result.summary.total_patients,
                total_medications=result.summary.total_medications,
                total_conditions=result.summary.total_conditions,
                total_observations=result.summary.total_observations,
                total_errors=result.summary.total_errors,
                success=result.summary.total_errors == 0,
            )
            return result

        # Handle directory
        if data_path.is_dir():
            logger.info(f"Ingesting FHIR Bundles from directory: {data_path}")
            result = await self._ingest_directory(data_path, max_bundles)
            # Log ingestion to audit log
            FHIRAuditLogger.log_ingestion(
                data_path=str(data_path),
                total_patients=result.summary.total_patients,
                total_medications=result.summary.total_medications,
                total_conditions=result.summary.total_conditions,
                total_observations=result.summary.total_observations,
                total_errors=result.summary.total_errors,
                success=result.summary.total_errors == 0,
            )
            return result

        error_msg = f"Path is neither a file nor directory: {data_path}"
        logger.error(error_msg)
        # Log failed ingestion
        FHIRAuditLogger.log_ingestion(
            data_path=str(data_path),
            success=False,
            error=error_msg,
        )
        return IngestionResult(
            summary=IngestionSummary(ingestion_timestamp=""),
            errors=[error_msg],
        )

    async def _ingest_directory(
        self,
        data_dir: Path,
        max_bundles: int | None = None,
    ) -> IngestionResult:
        """Ingest FHIR bundles from a directory.

        Args:
            data_dir: Directory containing FHIR Bundle files
            max_bundles: Maximum number of bundles to process. If None, processes all.
        """
        logger.info(f"Starting FHIR bundle ingestion from: {data_dir}")

        if not data_dir.exists():
            logger.warning(f"Data directory not found: {data_dir}")
            return self.results

        self._reset_results()

        try:
            bundle_files = self._get_bundle_files(data_dir)
            if not bundle_files:
                logger.warning(f"No FHIR bundle files found in {data_dir}")
                self._add_error(f"No FHIR bundle files found in {data_dir}")
                return self.results

            if max_bundles:
                bundle_files = bundle_files[:max_bundles]
                logger.info(f"Processing first {max_bundles} bundles")

            logger.info(f"Found {len(bundle_files)} FHIR bundle files to process")

            for bundle_file in bundle_files:
                try:
                    logger.info(
                        f"Starting ingestion of bundle file: {bundle_file.name}"
                    )
                    await self._ingest_bundle(bundle_file, self.ingestion_tag)
                except Exception as e:
                    error_msg = f"Error processing bundle {bundle_file.name}: {e}"
                    logger.error(error_msg)
                    self._add_error(error_msg)

            return self._finalize_results()

        except Exception as e:
            logger.error(f"FHIR bundle ingestion failed: {e}")
            self._add_error(str(e))
            return self.results

    async def _ingest_bundle(
        self, bundle_path: Path, ingestion_tag: str | None = None
    ) -> None:
        """Ingest a single FHIR bundle."""
        logger.info(f"Processing bundle: {bundle_path.name}")

        bundle = self._load_bundle(bundle_path)
        if not bundle:
            raise ValueError(f"Failed to load bundle: {bundle_path}")

        patient_resource = self._find_patient_in_bundle(bundle)
        if not patient_resource:
            raise ValueError(f"No Patient resource found in bundle: {bundle_path.name}")

        original_patient_id = patient_resource.get("id", "")
        patient_data = patient_resource.copy()
        patient_data.pop("id", None)

        # Add custom identifier to track ingested patients
        self._add_ingestion_identifier(patient_data, ingestion_tag)

        new_patient_id = await self.client.create_patient(patient_data)
        if not new_patient_id:
            raise ValueError(
                f"Failed to create patient from bundle: {bundle_path.name}"
            )

        logger.info(
            f"Created patient {new_patient_id} (original: {original_patient_id})"
        )

        patient_data_with_id = {**patient_data, "id": new_patient_id}
        patient_record = PatientHandler.to_patient_data(patient_data_with_id)
        self.results.patients_created.append(patient_record)

        resources_by_type = self._extract_resources_from_bundle(bundle)
        skipped_resources: dict[str, int] = {}

        for resource_type, resources in resources_by_type.items():
            if not resources:
                continue

            match resource_type:
                case ResourceType.PATIENT.value:
                    continue
                case _ if resource_type not in self.SUPPORTED_TYPES:
                    skipped_resources[resource_type] = len(resources)
                    logger.debug(
                        f"Skipping {len(resources)} {resource_type} resources (not yet supported)"
                    )
                    continue
                case _:
                    pass

            logger.debug(f"Processing {len(resources)} {resource_type} resources")

            for resource in resources:
                self.processor.prepare(resource, original_patient_id, new_patient_id)

                try:
                    await self._create_and_track_resource(
                        resource_type, resource, new_patient_id
                    )
                except Exception as e:
                    error_msg = f"Error creating {resource_type} resource for patient {new_patient_id}: {e!s}"
                    logger.error(error_msg)
                    self._add_error(error_msg)

        if skipped_resources:
            skipped_summary = ", ".join(
                f"{count} {rtype}" for rtype, count in skipped_resources.items()
            )
            logger.info(
                f"Bundle {bundle_path.name}: Skipped unsupported resource types: {skipped_summary}"
            )

    @staticmethod
    def _is_fhir_bundle(file_path: Path) -> bool:
        """Check if a file is a FHIR Bundle by reading its resourceType.

        Args:
            file_path: Path to the JSON file

        Returns:
            True if the file contains a FHIR Bundle
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("resourceType") == "Bundle"
        except Exception:
            return False

    @staticmethod
    def _load_bundle(file_path: Path) -> dict[str, Any] | None:
        """Load a FHIR bundle from a JSON file."""
        if not file_path.exists():
            logger.warning(f"Bundle file not found: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
            if bundle.get("resourceType") != "Bundle":
                logger.warning(f"File {file_path} is not a FHIR Bundle")
                return None
            return bundle
        except Exception as e:
            logger.error(f"Error loading bundle from {file_path}: {e}")
            return None

    @staticmethod
    def _extract_resources_from_bundle(
        bundle: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        """Extract resources from a FHIR bundle and group by resource type.

        Returns a dictionary mapping resource types to lists of resources.
        Resources have their 'id' field removed (server will assign new IDs),
        but the original ID is preserved in '_original_id' for reference mapping.
        """
        resources_by_type: dict[str, list[dict[str, Any]]] = {}

        if not bundle or bundle.get("resourceType") != "Bundle":
            logger.warning("Invalid bundle provided - not a FHIR Bundle")
            return resources_by_type

        entries = bundle.get("entry", [])
        if not entries:
            logger.warning("Bundle has no entries")
            return resources_by_type

        logger.info(f"Extracting resources from bundle with {len(entries)} entries")

        skipped_entries = 0
        for entry in entries:
            resource = entry.get("resource")
            if not resource:
                skipped_entries += 1
                continue

            resource_type = resource.get("resourceType")
            if not resource_type:
                skipped_entries += 1
                logger.debug("Entry missing resourceType, skipping")
                continue

            if resource_type not in resources_by_type:
                resources_by_type[resource_type] = []

            resource_copy = resource.copy()
            original_id = resource_copy.pop("id", None)
            if original_id:
                resource_copy["_original_id"] = original_id

            resources_by_type[resource_type].append(resource_copy)

        total_resources = sum(len(r) for r in resources_by_type.values())
        logger.info(
            f"Extracted {total_resources} resources from {len(entries)} entries"
        )

        if skipped_entries > 0:
            logger.debug(
                f"Skipped {skipped_entries} entries (missing resource or resourceType)"
            )

        for resource_type, resources in sorted(resources_by_type.items()):
            logger.debug(f"  - {resource_type}: {len(resources)}")

        return resources_by_type

    @staticmethod
    def _add_ingestion_identifier(
        patient_data: dict[str, Any], ingestion_tag: str | None = None
    ) -> None:
        """Add a custom identifier to patient data to track ingested patients.

        This identifier allows identifying patients ingested by this application,
        which is especially useful when using public FHIR servers like hapi.fhir.org.

        Args:
            patient_data: Patient resource data dictionary (modified in place)
            ingestion_tag: Tag value to use. If None, uses default production tag.
        """
        # Use provided tag or default to production tag
        tag_value = (
            ingestion_tag
            if ingestion_tag is not None
            else INGESTED_PATIENT_IDENTIFIER_VALUE
        )

        # Ensure identifier list exists
        if "identifier" not in patient_data:
            patient_data["identifier"] = []

        # Check if our custom identifier already exists
        existing_identifiers = patient_data.get("identifier", [])
        for identifier in existing_identifiers:
            if (
                isinstance(identifier, dict)
                and identifier.get("system") == INGESTED_PATIENT_IDENTIFIER_SYSTEM
            ):
                # Already has our identifier, no need to add again
                return

        # Add our custom identifier
        custom_identifier = {
            "system": INGESTED_PATIENT_IDENTIFIER_SYSTEM,
            "value": tag_value,
        }
        patient_data["identifier"].append(custom_identifier)
        logger.debug(
            f"Added ingestion identifier to patient: {INGESTED_PATIENT_IDENTIFIER_SYSTEM}={tag_value}"
        )

    @staticmethod
    def _find_patient_in_bundle(bundle: dict[str, Any]) -> dict[str, Any] | None:
        """Find the Patient resource in a FHIR bundle."""
        if not bundle or bundle.get("resourceType") != "Bundle":
            return None

        entries = bundle.get("entry", [])
        for entry in entries:
            resource = entry.get("resource")
            if resource and resource.get("resourceType") == "Patient":
                return resource

        return None

    @staticmethod
    def _get_bundle_files(data_dir: Path) -> list[Path]:
        """Get all FHIR Bundle JSON files from a directory.

        Filters out non-patient bundle files like:
        - hospitalInformation*.json
        - practitionerInformation*.json

        Returns sorted list of patient bundle file paths.
        """
        if not data_dir.exists():
            logger.warning(f"Data directory not found: {data_dir}")
            return []

        if not data_dir.is_dir():
            logger.warning(f"Data path is not a directory: {data_dir}")
            return []

        excluded_prefixes = ("hospitalInformation", "practitionerInformation")

        all_json_files = list(data_dir.glob("*.json"))
        patient_files = [
            f
            for f in all_json_files
            if not any(f.name.startswith(prefix) for prefix in excluded_prefixes)
        ]

        excluded_count = len(all_json_files) - len(patient_files)
        if excluded_count > 0:
            logger.debug(
                f"Filtered out {excluded_count} non-patient bundle file(s) "
                f"(hospitalInformation, practitionerInformation)"
            )

        logger.info(f"Found {len(patient_files)} FHIR Bundle files in {data_dir}")
        return sorted(patient_files)
