"""Resource handlers for transforming FHIR resources."""

from __future__ import annotations

from typing import Any

from ...domain.constants import (
    UNKNOWN_VALUE,
    LactationStatus,
    ObservationCode,
    ResourceType,
)
from ...domain.models import PatientData
from .utils import extract_coding_info


class PatientHandler:
    """Handles Patient resource transformations."""

    @staticmethod
    def to_patient_data(resource: dict[str, Any]) -> PatientData:
        """Convert FHIR Patient resource to PatientData model."""
        name = PatientHandler._extract_name(resource.get("name", [])) or UNKNOWN_VALUE
        return PatientData(
            id=resource.get("id") or UNKNOWN_VALUE,
            name=name,
            birth_date=resource.get("birthDate"),
            gender=resource.get("gender"),
            resource_type=ResourceType.PATIENT,
        )

    @staticmethod
    def _extract_name(names: Any) -> str | None:
        """Extract best name from FHIR name array."""
        if not names or not isinstance(names, list):
            return None

        official = None
        for n in names:
            if isinstance(n, dict) and n.get("use") == "official":
                official = n
                break

        name = official or names[0]
        if not isinstance(name, dict):
            return None

        given = name.get("given", [])
        family = name.get("family", "")
        if isinstance(given, list):
            given_str = " ".join(given)
        else:
            given_str = str(given or "")
        formatted = f"{given_str} {family}".strip()
        return formatted or None


class MedicationRequestHandler:
    """Handles MedicationRequest resource transformations."""

    @staticmethod
    def extract_name(resource: dict[str, Any]) -> str:
        """Extract medication name from MedicationRequest."""
        concept = resource.get("medicationCodeableConcept", {}) or {}
        med_text = concept.get("text")
        if not med_text:
            coding = concept.get("coding", [])
            if coding:
                med_text = coding[0].get("display")
        return med_text or UNKNOWN_VALUE

    @staticmethod
    def extract_code_info(resource: dict[str, Any]) -> dict[str, Any] | None:
        """Extract code information from MedicationRequest.

        Handles both medicationCodeableConcept and medicationReference.
        """
        # Try medicationCodeableConcept first (preferred)
        concept = resource.get("medicationCodeableConcept", {}) or {}
        if concept:
            coding_array = concept.get("coding", [])
            if coding_array:
                return extract_coding_info(coding_array)

        # If medicationReference, we can't resolve it here, but return None
        # The reference would need to be resolved separately
        return None

    @staticmethod
    def to_dict(resource: dict[str, Any]) -> dict[str, Any]:
        """Convert MedicationRequest to simplified dict."""
        code_info = MedicationRequestHandler.extract_code_info(resource)
        result = {
            "id": resource.get("id"),
            "status": resource.get("status"),
            "intent": resource.get("intent"),
            "authoredOn": resource.get("authoredOn"),
            "medication": MedicationRequestHandler.extract_name(resource),
            "subject": resource.get("subject"),
            "dosageInstruction": resource.get("dosageInstruction", []),
        }

        # Add code information if available
        if code_info:
            result["medicationCode"] = code_info.get("code")
            result["medicationSystem"] = code_info.get("system")
            result["medicationSystemType"] = code_info.get("systemType")
            result["medicationDisplay"] = code_info.get("display")

        return result


class ConditionHandler:
    """Handles Condition resource transformations."""

    @staticmethod
    def extract_name(resource: dict[str, Any]) -> str:
        """Extract condition name from Condition."""
        code = resource.get("code", {}) or {}
        name = code.get("text")
        if not name:
            coding = code.get("coding", [])
            if coding:
                name = coding[0].get("display")
        return name or UNKNOWN_VALUE

    @staticmethod
    def extract_code_info(resource: dict[str, Any]) -> dict[str, Any] | None:
        """Extract code information from Condition."""
        code = resource.get("code", {}) or {}
        if code:
            coding_array = code.get("coding", [])
            if coding_array:
                return extract_coding_info(coding_array)
        return None

    @staticmethod
    def to_dict(resource: dict[str, Any]) -> dict[str, Any]:
        """Convert Condition to simplified dict."""
        code_info = ConditionHandler.extract_code_info(resource)
        result = {
            "id": resource.get("id"),
            "clinicalStatus": resource.get("clinicalStatus"),
            "verificationStatus": resource.get("verificationStatus"),
            "code": resource.get("code", {}),
            "condition": ConditionHandler.extract_name(resource),
            "subject": resource.get("subject"),
            "onsetDateTime": resource.get("onsetDateTime"),
            "abatementDateTime": resource.get("abatementDateTime"),
        }

        # Add code information if available
        if code_info:
            result["conditionCode"] = code_info.get("code")
            result["conditionSystem"] = code_info.get("system")
            result["conditionSystemType"] = code_info.get("systemType")
            result["conditionDisplay"] = code_info.get("display")

        return result


class ObservationHandler:
    """Handles Observation resource transformations."""

    @staticmethod
    def extract_name(resource: dict[str, Any]) -> str:
        """Extract observation name from Observation."""
        code = resource.get("code", {}) or {}
        obs_name = code.get("text")
        if not obs_name:
            coding = code.get("coding", [])
            if coding:
                obs_name = coding[0].get("display")
        return obs_name or UNKNOWN_VALUE

    @staticmethod
    def extract_code_info(resource: dict[str, Any]) -> dict[str, Any] | None:
        """Extract code information from Observation."""
        code = resource.get("code", {}) or {}
        if code:
            coding_array = code.get("coding", [])
            if coding_array:
                return extract_coding_info(coding_array)
        return None

    @staticmethod
    def to_dict(resource: dict[str, Any]) -> dict[str, Any]:
        """Convert Observation to simplified dict."""
        code_info = ObservationHandler.extract_code_info(resource)
        result = {
            "id": resource.get("id"),
            "status": resource.get("status"),
            "code": resource.get("code", {}),
            "observation": ObservationHandler.extract_name(resource),
            "effectiveDateTime": resource.get("effectiveDateTime"),
            "valueQuantity": resource.get("valueQuantity"),
            "valueString": resource.get("valueString"),
            "category": resource.get("category"),
            "subject": resource.get("subject"),
        }

        # Add code information if available
        if code_info:
            result["observationCode"] = code_info.get("code")
            result["observationSystem"] = code_info.get("system")
            result["observationSystemType"] = code_info.get("systemType")
            result["observationDisplay"] = code_info.get("display")

        return result

    @staticmethod
    def is_gestational_age_observation(observation: dict[str, Any]) -> bool:
        """Check if observation is a gestational age observation.

        Uses ObservationCode constant from domain layer.

        Args:
            observation: Observation dictionary (already processed by to_dict)

        Returns:
            True if observation is a gestational age observation
        """
        code_info = ObservationHandler.extract_code_info(observation)
        if not code_info:
            return False
        return code_info.get("code") == ObservationCode.GESTATIONAL_AGE.value

    @staticmethod
    def is_lactation_status_observation(observation: dict[str, Any]) -> bool:
        """Check if observation is a lactation status observation.

        Uses ObservationCode constant from domain layer.

        Args:
            observation: Observation dictionary (already processed by to_dict)

        Returns:
            True if observation is a lactation status observation
        """
        code_info = ObservationHandler.extract_code_info(observation)
        if not code_info:
            return False
        return code_info.get("code") == ObservationCode.LACTATION_STATUS.value

    @staticmethod
    def extract_gestational_weeks(observation: dict[str, Any]) -> int | None:
        """Extract gestational weeks from a gestational age observation.

        Extracts from valueQuantity.value field in the observation dictionary.

        Args:
            observation: Observation dictionary (already processed by to_dict)

        Returns:
            Gestational weeks as integer, or None if not available or invalid
        """
        value_quantity = observation.get("valueQuantity", {})
        if not isinstance(value_quantity, dict):
            return None

        weeks = value_quantity.get("value")

        if weeks is None:
            return None

        try:
            return int(float(weeks))  # Handle both int and float values
        except (ValueError, TypeError):
            return None

    @staticmethod
    def extract_lactation_status_value(
        observation: dict[str, Any],
    ) -> LactationStatus | None:
        """Extract and normalize lactation status from a lactation status observation.

        Uses LactationStatus enum from domain layer for normalization.

        Args:
            observation: Observation dictionary (already processed by to_dict)

        Returns:
            LactationStatus enum value, or None if not available
        """
        status = observation.get("valueString")

        if not status or not isinstance(status, str):
            return None

        # Normalize status value using enum
        status_lower = status.lower()
        if "lactating" in status_lower and "not" not in status_lower:
            return LactationStatus.LACTATING
        else:
            return LactationStatus.NOT_LACTATING


class MedicationAdministrationHandler:
    """Handles MedicationAdministration resource transformations."""

    @staticmethod
    def extract_name(resource: dict[str, Any]) -> str:
        """Extract medication name from MedicationAdministration."""
        medication = resource.get("medicationCodeableConcept", {}) or {}
        med_text = medication.get("text")
        if not med_text:
            coding = medication.get("coding", [])
            if coding:
                med_text = coding[0].get("display")
        if not med_text:
            med_ref = resource.get("medicationReference", {})
            if med_ref:
                med_text = med_ref.get("display")
        return med_text or UNKNOWN_VALUE

    @staticmethod
    def extract_code_info(resource: dict[str, Any]) -> dict[str, Any] | None:
        """Extract code information from MedicationAdministration.

        Handles both medicationCodeableConcept and medicationReference.
        """
        # Try medicationCodeableConcept first (preferred)
        concept = resource.get("medicationCodeableConcept", {}) or {}
        if concept:
            coding_array = concept.get("coding", [])
            if coding_array:
                return extract_coding_info(coding_array)

        # If medicationReference, we can't resolve it here, but return None
        # The reference would need to be resolved separately
        return None

    @staticmethod
    def to_dict(resource: dict[str, Any]) -> dict[str, Any]:
        """Convert MedicationAdministration to simplified dict."""
        code_info = MedicationAdministrationHandler.extract_code_info(resource)
        result = {
            "id": resource.get("id"),
            "status": resource.get("status"),
            "medication": MedicationAdministrationHandler.extract_name(resource),
            "subject": resource.get("subject"),
            "effectiveDateTime": resource.get("effectiveDateTime"),
            "dosage": resource.get("dosage", {}),
        }

        # Add code information if available
        if code_info:
            result["medicationCode"] = code_info.get("code")
            result["medicationSystem"] = code_info.get("system")
            result["medicationSystemType"] = code_info.get("systemType")
            result["medicationDisplay"] = code_info.get("display")

        return result


class EncounterHandler:
    """Handles Encounter resource transformations."""

    @staticmethod
    def extract_name(resource: dict[str, Any]) -> str:
        """Extract encounter name from Encounter."""
        encounter_type = resource.get("type", [{}])[0] if resource.get("type") else {}
        type_text = encounter_type.get("text")
        if not type_text:
            coding = encounter_type.get("coding", [])
            if coding:
                type_text = coding[0].get("display")
        return type_text or UNKNOWN_VALUE

    @staticmethod
    def extract_type_code_info(resource: dict[str, Any]) -> dict[str, Any] | None:
        """Extract code information from Encounter type."""
        encounter_types = resource.get("type", [])
        if not encounter_types or not isinstance(encounter_types, list):
            return None

        # Get the first type (usually there's only one)
        encounter_type = encounter_types[0] if encounter_types else {}
        if not isinstance(encounter_type, dict):
            return None

        coding_array = encounter_type.get("coding", [])
        if coding_array:
            return extract_coding_info(coding_array)
        return None

    @staticmethod
    def extract_reason_codes(resource: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract all reason codes with their code information."""
        reason_codes = resource.get("reasonCode", [])
        if not reason_codes or not isinstance(reason_codes, list):
            return []

        extracted_reasons = []
        for reason in reason_codes:
            if not isinstance(reason, dict):
                continue

            coding_array = reason.get("coding", [])
            if coding_array:
                code_info = extract_coding_info(coding_array)
                if code_info:
                    extracted_reasons.append(
                        {
                            "code": code_info.get("code"),
                            "system": code_info.get("system"),
                            "systemType": code_info.get("systemType"),
                            "display": code_info.get("display"),
                            "text": reason.get("text"),
                        }
                    )

        return extracted_reasons

    @staticmethod
    def to_dict(resource: dict[str, Any]) -> dict[str, Any]:
        """Convert Encounter to simplified dict."""
        type_code_info = EncounterHandler.extract_type_code_info(resource)
        reason_codes = EncounterHandler.extract_reason_codes(resource)

        result = {
            "id": resource.get("id"),
            "status": resource.get("status"),
            "class": resource.get("class", {}),
            "type": EncounterHandler.extract_name(resource),
            "subject": resource.get("subject"),
            "period": resource.get("period"),
            "reasonCode": resource.get("reasonCode", []),
        }

        # Add type code information if available
        if type_code_info:
            result["typeCode"] = type_code_info.get("code")
            result["typeSystem"] = type_code_info.get("system")
            result["typeSystemType"] = type_code_info.get("systemType")
            result["typeDisplay"] = type_code_info.get("display")

        # Add extracted reason codes
        if reason_codes:
            result["reasonCodes"] = reason_codes

        return result


class ProcedureHandler:
    """Handles Procedure resource transformations."""

    @staticmethod
    def extract_name(resource: dict[str, Any]) -> str:
        """Extract procedure name from Procedure."""
        code = resource.get("code", {}) or {}
        code_text = code.get("text")
        if not code_text:
            coding = code.get("coding", [])
            if coding:
                code_text = coding[0].get("display")
        return code_text or UNKNOWN_VALUE

    @staticmethod
    def extract_code_info(resource: dict[str, Any]) -> dict[str, Any] | None:
        """Extract code information from Procedure."""
        code = resource.get("code", {}) or {}
        if code:
            coding_array = code.get("coding", [])
            if coding_array:
                return extract_coding_info(coding_array)
        return None

    @staticmethod
    def to_dict(resource: dict[str, Any]) -> dict[str, Any]:
        """Convert Procedure to simplified dict."""
        code_info = ProcedureHandler.extract_code_info(resource)
        result = {
            "id": resource.get("id"),
            "status": resource.get("status"),
            "code": ProcedureHandler.extract_name(resource),
            "subject": resource.get("subject"),
            "performedDateTime": resource.get("performedDateTime"),
            "performedPeriod": resource.get("performedPeriod"),
        }

        # Add code information if available
        if code_info:
            result["procedureCode"] = code_info.get("code")
            result["procedureSystem"] = code_info.get("system")
            result["procedureSystemType"] = code_info.get("systemType")
            result["procedureDisplay"] = code_info.get("display")

        return result


class MedicationHandler:
    """Handles Medication resource transformations."""

    @staticmethod
    def extract_name(resource: dict[str, Any]) -> str:
        """Extract medication name from Medication resource."""
        code = resource.get("code", {})
        if code:
            text = code.get("text")
            if text:
                return text
            coding = code.get("coding", [{}])[0]
            display = coding.get("display")
            if display:
                return display
        name = resource.get("name")
        if name:
            return str(name)
        return UNKNOWN_VALUE

    @staticmethod
    def extract_code_info(resource: dict[str, Any]) -> dict[str, Any] | None:
        """Extract code information from Medication resource."""
        code = resource.get("code", {}) or {}
        if code:
            coding_array = code.get("coding", [])
            if coding_array:
                return extract_coding_info(coding_array)
        return None

    @staticmethod
    def to_dict(resource: dict[str, Any]) -> dict[str, Any]:
        """Convert Medication to simplified dict."""
        code_info = MedicationHandler.extract_code_info(resource)
        result = {
            "id": resource.get("id"),
            "status": resource.get("status"),
            "medication": MedicationHandler.extract_name(resource),
        }

        # Add code information if available
        if code_info:
            result["medicationCode"] = code_info.get("code")
            result["medicationSystem"] = code_info.get("system")
            result["medicationSystemType"] = code_info.get("systemType")
            result["medicationDisplay"] = code_info.get("display")

        return result


class PregnancyStageHandler:
    """Handles pregnancy stage extraction from observations."""

    @staticmethod
    def extract_from_observations(
        observations: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Extract pregnancy stage (gestational weeks) from a list of observations.

        Args:
            observations: List of observation dictionaries (already processed by ObservationHandler.to_dict)

        Returns:
            Dictionary with pregnancy stage information:
            {
                "gestational_weeks": int,  # Number of weeks (0-40+)
                "effective_date": str,     # ISO date string of the observation
                "observation_id": str      # FHIR observation ID
            }
            Returns None if no gestational age data found.
        """
        # Filter for gestational age observations using ObservationHandler
        gestational_obs = [
            obs
            for obs in observations
            if ObservationHandler.is_gestational_age_observation(obs)
        ]

        if not gestational_obs:
            return None

        # Get the most recent observation (by effectiveDateTime)
        latest_obs = max(
            gestational_obs,
            key=lambda x: x.get("effectiveDateTime") or "",
            default=None,
        )

        if not latest_obs:
            return None

        # Extract gestational weeks using ObservationHandler
        weeks = ObservationHandler.extract_gestational_weeks(latest_obs)

        if weeks is None:
            return None

        return {
            "gestational_weeks": weeks,
            "effective_date": latest_obs.get("effectiveDateTime"),
            "observation_id": latest_obs.get("id"),
        }


class LactationStageHandler:
    """Handles lactation stage extraction from observations."""

    @staticmethod
    def extract_from_observations(
        observations: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Extract lactation stage from a list of observations.

        Args:
            observations: List of observation dictionaries (already processed by ObservationHandler.to_dict)

        Returns:
            Dictionary with lactation status information:
            {
                "status": str,              # LactationStatus enum value
                "effective_date": str,      # ISO date string of the observation
                "observation_id": str       # FHIR observation ID
            }
            Returns None if no lactation status data found.
        """
        # Filter for lactation status observations using ObservationHandler
        lactation_obs = [
            obs
            for obs in observations
            if ObservationHandler.is_lactation_status_observation(obs)
        ]

        if not lactation_obs:
            return None

        # Get the most recent observation (by effectiveDateTime)
        latest_obs = max(
            lactation_obs, key=lambda x: x.get("effectiveDateTime") or "", default=None
        )

        if not latest_obs:
            return None

        # Extract lactation status using ObservationHandler
        status = ObservationHandler.extract_lactation_status_value(latest_obs)

        if status is None:
            return None

        return {
            "status": status.value,  # Convert enum to string value
            "effective_date": latest_obs.get("effectiveDateTime"),
            "observation_id": latest_obs.get("id"),
        }
