"""Utility functions for processing and cleaning FHIR resources."""

from __future__ import annotations

from typing import Any

from ...domain.constants import SystemType


def _is_urn_uuid_reference(ref: Any) -> bool:
    """Check if a reference is a urn:uuid: reference (unresolvable in FHIR server).

    Args:
        ref: Reference value (string, dict, or other)

    Returns:
        True if the reference is a urn:uuid: reference
    """
    if isinstance(ref, dict):
        ref = ref.get("reference", "")
    if not isinstance(ref, str):
        return False
    return ref.startswith("urn:uuid:")


def _is_query_string_reference(ref: str) -> bool:
    """Check if a reference is a query string reference (not supported by FHIR servers).

    Examples: Practitioner?identifier=..., Organization?identifier=...

    Args:
        ref: Reference string

    Returns:
        True if the reference is a query string reference
    """
    if not isinstance(ref, str) or "?" not in ref:
        return False
    return ref.startswith(("Practitioner?", "Organization?", "Location?"))


def _extract_reference_string(value: Any) -> str:
    """Extract reference string from various reference formats.

    Args:
        value: Reference value (dict with "reference" key, string, or other)

    Returns:
        Reference string or empty string
    """
    if isinstance(value, dict):
        return value.get("reference", "")
    if isinstance(value, str):
        return value
    return ""


def matches_patient_reference(reference: str, old_patient_id: str) -> bool:
    """Check if a reference matches the old patient ID.

    Handles:
    - Patient/123 format
    - urn:uuid:uuid-value format (exact UUID match)
    - Direct UUID matches

    Args:
        reference: Reference string to check
        old_patient_id: Original patient ID from bundle

    Returns:
        True if the reference matches the old patient ID
    """
    if not reference or not old_patient_id:
        return False

    # Direct UUID match
    if reference == old_patient_id:
        return True

    # urn:uuid: format - extract UUID and match exactly
    if reference.startswith("urn:uuid:"):
        uuid_part = reference.replace("urn:uuid:", "")
        return uuid_part == old_patient_id

    # Patient/ format
    if reference.startswith("Patient/"):
        patient_id_part = reference.replace("Patient/", "")
        return patient_id_part == old_patient_id

    # Check if reference ends with old_patient_id
    return bool(reference.endswith(f"/{old_patient_id}"))


def update_resource_references(
    resource: dict[str, Any],
    old_patient_id: str,
    new_patient_id: str,
) -> None:
    """Update patient references in a resource to use the new patient ID.

    Handles various reference formats:
    - Patient/123
    - urn:uuid:uuid-value
    - Direct UUID matches
    """

    def _update_reference_field(field_path: str) -> None:
        """Update a reference field if it matches the old patient ID."""
        parts = field_path.split(".")
        current = resource
        for part in parts[:-1]:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return

        if not isinstance(current, dict):
            return

        field_name = parts[-1]
        reference_value = current.get(field_name)

        if not reference_value:
            return

        # Handle dict reference: {"reference": "..."}
        if isinstance(reference_value, dict):
            ref_str = reference_value.get("reference", "")
            if matches_patient_reference(ref_str, old_patient_id):
                reference_value["reference"] = f"Patient/{new_patient_id}"
        # Handle string reference
        elif isinstance(reference_value, str):
            if matches_patient_reference(reference_value, old_patient_id):
                current[field_name] = {"reference": f"Patient/{new_patient_id}"}
        # Handle list of references
        elif isinstance(reference_value, list):
            for item in reference_value:
                if isinstance(item, dict):
                    ref_str = item.get("reference", "")
                    if matches_patient_reference(ref_str, old_patient_id):
                        item["reference"] = f"Patient/{new_patient_id}"
                elif isinstance(item, str):
                    if matches_patient_reference(item, old_patient_id):
                        idx = reference_value.index(item)
                        reference_value[idx] = {
                            "reference": f"Patient/{new_patient_id}"
                        }

    # Update common reference fields
    _update_reference_field("subject")
    _update_reference_field("patient")


def remove_unresolvable_references(resource: dict[str, Any], field_path: str) -> None:
    """Remove unresolvable references (urn:uuid: or query strings) from a field.

    Args:
        resource: FHIR resource dictionary
        field_path: Dot-separated path to the field (e.g., "medication", "context")
    """
    parts = field_path.split(".")
    current = resource
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return

    if not isinstance(current, dict):
        return

    field_name = parts[-1]
    value = current.get(field_name)

    if not value:
        return

    should_remove = False

    # Check if value contains unresolvable references
    if isinstance(value, dict):
        ref = _extract_reference_string(value)
        if _is_urn_uuid_reference(ref) or _is_query_string_reference(ref):
            should_remove = True
    elif isinstance(value, str):
        if _is_urn_uuid_reference(value) or _is_query_string_reference(value):
            should_remove = True
    elif isinstance(value, list):
        # Check if any item in list has unresolvable reference
        for item in value:
            ref = _extract_reference_string(item)
            if _is_urn_uuid_reference(ref) or _is_query_string_reference(ref):
                should_remove = True
                break

    if should_remove:
        current.pop(field_name, None)


def clean_medication_references(resource: dict[str, Any]) -> None:
    """Remove invalid medication references in MedicationRequest resources.

    MedicationRequest can have medication as either:
    - medicationCodeableConcept (preferred, contains the actual medication info)
    - medication (Reference to Medication resource)

    Since Synthea bundles use urn:uuid: references that can't be resolved,
    we remove them. The resource should have medicationCodeableConcept instead.
    """
    if resource.get("resourceType") != "MedicationRequest":
        return

    remove_unresolvable_references(resource, "medication")


def clean_medication_administration_context(resource: dict[str, Any]) -> None:
    """Remove invalid context references in MedicationAdministration resources.

    MedicationAdministration.context can reference an Encounter, but if it's
    a urn:uuid: reference, we remove it since it can't be resolved.
    """
    if resource.get("resourceType") != "MedicationAdministration":
        return

    remove_unresolvable_references(resource, "context")


def clean_encounter_references(resource: dict[str, Any]) -> None:
    """Remove invalid encounter references from resources.

    Removes urn:uuid: encounter references that can't be resolved.
    Handles both direct encounter fields and nested encounter references.
    """
    # Handle direct encounter field
    remove_unresolvable_references(resource, "encounter")

    # Handle encounter references in nested structures (e.g., Claim.item[].encounter)
    if "item" in resource and isinstance(resource["item"], list):
        for item in resource["item"]:
            if isinstance(item, dict) and "encounter" in item:
                encounter_ref = item.get("encounter")
                if isinstance(encounter_ref, list):
                    # Filter out unresolvable references
                    filtered_refs = [
                        ref
                        for ref in encounter_ref
                        if not _is_urn_uuid_reference(ref)
                        and not _is_query_string_reference(
                            _extract_reference_string(ref)
                        )
                    ]
                    if filtered_refs:
                        item["encounter"] = filtered_refs
                    else:
                        item.pop("encounter", None)
                else:
                    # Check if single reference is unresolvable
                    ref_str = _extract_reference_string(encounter_ref)
                    if _is_urn_uuid_reference(ref_str) or _is_query_string_reference(
                        ref_str
                    ):
                        item.pop("encounter", None)


def clean_encounter_resource(resource: dict[str, Any]) -> None:
    """Clean Encounter resources to fix validation errors.

    Specifically handles:
    - location field: Must be an array, not null. Removes null/invalid entries.
      Each entry must be a dict (EncounterLocationComponent), not null.
    - Invalid location references (urn:uuid:)

    This fixes the validation error: "The property location must be an Array, not a Null"
    """
    if resource.get("resourceType") != "Encounter":
        return

    location = resource.get("location")
    if location is None:
        # Optional field, safe to remove
        resource.pop("location", None)
        return

    if not isinstance(location, list):
        # Invalid format, remove it
        resource.pop("location", None)
        return

    # Filter out invalid entries
    cleaned_locations = []
    for loc in location:
        # Skip null, empty, or non-dict values
        if not loc or not isinstance(loc, dict):
            continue

        # Check if location reference is valid
        location_ref = loc.get("location")
        if location_ref:
            ref_str = _extract_reference_string(location_ref)
            if _is_urn_uuid_reference(ref_str) or _is_query_string_reference(ref_str):
                continue  # Skip invalid references

        cleaned_locations.append(loc)

    # Update or remove location field
    if cleaned_locations:
        resource["location"] = cleaned_locations
    else:
        resource.pop("location", None)


def clean_query_string_references(resource: dict[str, Any]) -> None:
    """Remove invalid query string references recursively.

    FHIR servers don't support query string references like:
    - Practitioner?identifier=...
    - Organization?identifier=...
    - Location?identifier=...

    This function recursively finds and removes these references throughout
    the resource structure.
    """
    if not isinstance(resource, dict):
        return

    keys_to_remove = []
    for key, value in resource.items():
        if isinstance(value, dict):
            ref = _extract_reference_string(value)
            if _is_query_string_reference(ref):
                keys_to_remove.append(key)
            else:
                # Recursively clean nested structures
                clean_query_string_references(value)
        elif isinstance(value, list):
            # Clean list of references
            items_to_remove = []
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    ref = _extract_reference_string(item)
                    if _is_query_string_reference(ref):
                        items_to_remove.append(i)
                    else:
                        # Recursively clean nested structures
                        clean_query_string_references(item)
            # Remove items in reverse order to maintain indices
            for i in reversed(items_to_remove):
                value.pop(i)
            # If list becomes empty, remove the key
            if not value:
                keys_to_remove.append(key)
        elif isinstance(value, str) and key == "reference":
            # Direct reference string
            if _is_query_string_reference(value):
                keys_to_remove.append(key)

    # Remove keys that contain invalid references
    for key in keys_to_remove:
        resource.pop(key, None)


def extract_coding_info(
    coding_array: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """Extract code information from FHIR coding array.

    Returns a dict with code, system, display, and systemType (SystemType enum value).
    Prioritizes RxNorm codes for medications, then SNOMED codes for clinical terminology.
    """
    if not coding_array or not isinstance(coding_array, list):
        return None

    # First, try to find RxNorm code (for medications)
    for coding in coding_array:
        if not isinstance(coding, dict):
            continue
        system = coding.get("system", "")
        if "rxnorm" in system.lower():
            return {
                "code": coding.get("code"),
                "system": system,
                "display": coding.get("display"),
                "systemType": SystemType.RXNORM.value,
            }

    # Second, try to find SNOMED code (for clinical terminology like pregnancy, procedures, etc.)
    for coding in coding_array:
        if not isinstance(coding, dict):
            continue
        system = coding.get("system", "")
        if "snomed" in system.lower():
            return {
                "code": coding.get("code"),
                "system": system,
                "display": coding.get("display"),
                "systemType": SystemType.SNOMED.value,
            }

    # If no RxNorm or SNOMED, return the first coding
    if coding_array:
        coding = coding_array[0]
        if isinstance(coding, dict):
            system = coding.get("system", "")
            system_type = SystemType.UNKNOWN
            if "rxnorm" in system.lower():
                system_type = SystemType.RXNORM
            elif "snomed" in system.lower():
                system_type = SystemType.SNOMED
            elif "ndc" in system.lower():
                system_type = SystemType.NDC
            elif "loinc" in system.lower():
                system_type = SystemType.LOINC

            return {
                "code": coding.get("code"),
                "system": system,
                "display": coding.get("display"),
                "systemType": system_type.value,
            }

    return None
