"""Resource processor for cleaning and preparing FHIR resources for FHIR server."""

from __future__ import annotations

from typing import Any

from .utils import (
    clean_encounter_references,
    clean_encounter_resource,
    clean_medication_administration_context,
    clean_medication_references,
    clean_query_string_references,
    update_resource_references,
)


class FHIRResourceProcessor:
    """Processes and prepares FHIR resources for HAPI FHIR server ingestion.

    Note: Validation is performed via client $validate operation, not here.
    The validate flag is passed through to client methods.
    """

    def __init__(self, validate: bool = False):
        self.validate = validate

    def prepare(
        self,
        resource: dict[str, Any],
        old_patient_id: str,
        new_patient_id: str,
    ) -> None:
        """Prepare a resource for ingestion."""

        # 1. Update patient references (required for linking resources)
        update_resource_references(resource, old_patient_id, new_patient_id)

        # 2. Remove unresolvable medication references
        clean_medication_references(resource)

        # 3. Remove unresolvable context references in MedicationAdministration
        clean_medication_administration_context(resource)

        # 4. Remove unresolvable encounter references
        clean_encounter_references(resource)

        # 5. Fix Encounter validation errors (location field null/invalid)
        clean_encounter_resource(resource)

        # 6. Remove query string references (not supported by FHIR servers)
        clean_query_string_references(resource)

        # 7. Remove temporary fields (id is already removed during extraction)
        resource.pop("_original_id", None)
