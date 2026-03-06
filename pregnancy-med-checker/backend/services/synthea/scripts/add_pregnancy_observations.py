#!/usr/bin/env python3
"""
Script to add gestational age and lactation observations to FHIR bundles.
Adds observations based on pregnancy conditions found in the bundles.
"""

import argparse
import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

# Constants
GESTATIONAL_AGE_CODE = "11778-8"
GESTATIONAL_AGE_SYSTEM = "http://loinc.org"
GESTATIONAL_AGE_DISPLAY = "Gestational age"

LACTATION_STATUS_CODE = "225747004"
LACTATION_STATUS_SYSTEM = "http://snomed.info/sct"
LACTATION_STATUS_DISPLAY = "Lactation status"

PREGNANCY_CONDITION_CODE = "72892002"
PREGNANCY_CONDITION_SYSTEM = "http://snomed.info/sct"

DEFAULT_FHIR_DIR = Path(__file__).parent.parent / "output" / "fhir"
DEFAULT_FHIR_DIR = DEFAULT_FHIR_DIR.resolve()


def generate_uuid() -> str:
    """Generate a UUID for new resources."""
    return str(uuid.uuid4())


def parse_datetime(date_str: str) -> datetime:
    """Parse FHIR datetime string to datetime object."""
    # Handle various FHIR datetime formats
    formats = [
        ("%Y-%m-%dT%H:%M:%S%z", True),
        ("%Y-%m-%dT%H:%M:%S", False),
        ("%Y-%m-%d", False),
    ]
    for fmt, has_tz in formats:
        try:
            if has_tz:
                dt = datetime.strptime(date_str, fmt)  # noqa: DTZ007
            else:
                # For formats without timezone, parse and then add UTC
                dt = datetime.strptime(date_str, fmt).replace(tzinfo=UTC)
            return dt
        except ValueError:
            continue
    raise ValueError(f"Unable to parse datetime: {date_str}")


def format_datetime(dt: datetime) -> str:
    """Format datetime to FHIR datetime string."""
    return (
        dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        if dt.tzinfo
        else dt.strftime("%Y-%m-%dT%H:%M:%S")
    )


def create_gestational_age_observation(
    patient_ref: str,
    effective_date: datetime,
    gestational_weeks: int,
    encounter_ref: str | None = None,
) -> dict[str, Any]:
    """Create a gestational age observation."""
    obs_id = generate_uuid()
    obs = {
        "fullUrl": f"urn:uuid:{obs_id}",
        "resource": {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "procedure",
                            "display": "Procedure",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": GESTATIONAL_AGE_SYSTEM,
                        "code": GESTATIONAL_AGE_CODE,
                        "display": GESTATIONAL_AGE_DISPLAY,
                    }
                ],
                "text": GESTATIONAL_AGE_DISPLAY,
            },
            "subject": {"reference": patient_ref},
            "effectiveDateTime": format_datetime(effective_date),
            "issued": format_datetime(effective_date),
            "valueQuantity": {
                "value": gestational_weeks,
                "unit": "weeks",
                "system": "http://unitsofmeasure.org",
                "code": "wk",
            },
        },
        "request": {"method": "POST", "url": "Observation"},
    }

    if encounter_ref:
        obs["resource"]["encounter"] = {"reference": encounter_ref}

    return obs


def create_lactation_observation(
    patient_ref: str,
    effective_date: datetime,
    lactating: bool,
    encounter_ref: str | None = None,
) -> dict[str, Any]:
    """Create a lactation status observation."""
    obs_id = generate_uuid()
    status_value = "Lactating" if lactating else "Not lactating"

    obs = {
        "fullUrl": f"urn:uuid:{obs_id}",
        "resource": {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "procedure",
                            "display": "Procedure",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": LACTATION_STATUS_SYSTEM,
                        "code": LACTATION_STATUS_CODE,
                        "display": LACTATION_STATUS_DISPLAY,
                    }
                ],
                "text": LACTATION_STATUS_DISPLAY,
            },
            "subject": {"reference": patient_ref},
            "effectiveDateTime": format_datetime(effective_date),
            "issued": format_datetime(effective_date),
            "valueString": status_value,
        },
        "request": {"method": "POST", "url": "Observation"},
    }

    if encounter_ref:
        obs["resource"]["encounter"] = {"reference": encounter_ref}

    return obs


def find_pregnancy_conditions(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Find all pregnancy conditions in the bundle."""
    pregnancies = []
    entries = bundle.get("entry", [])

    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") != "Condition":
            continue

        code = resource.get("code", {})
        coding = code.get("coding", [])

        for c in coding:
            if (
                c.get("system", "").endswith("snomed.info/sct")
                and c.get("code") == PREGNANCY_CONDITION_CODE
            ):
                pregnancies.append(
                    {
                        "condition": resource,
                        "entry": entry,
                        "patient_ref": resource.get("subject", {}).get("reference", ""),
                        "encounter_ref": resource.get("encounter", {}).get(
                            "reference", ""
                        ),
                        "onset": resource.get("onsetDateTime"),
                        "abatement": resource.get("abatementDateTime"),
                    }
                )
                break

    return pregnancies


def find_encounter_by_reference(
    bundle: dict[str, Any], encounter_ref: str
) -> dict[str, Any] | None:
    """Find an encounter by its reference."""
    entries = bundle.get("entry", [])
    for entry in entries:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Encounter":
            full_url = entry.get("fullUrl", "")
            if encounter_ref in full_url or full_url.endswith(
                encounter_ref.split(":")[-1]
            ):
                return resource
    return None


def add_gestational_age_observations(
    pregnancy: dict[str, Any],
) -> list[dict[str, Any]]:
    """Add weekly gestational age observations during pregnancy."""
    observations = []

    if not pregnancy["onset"] or not pregnancy["abatement"]:
        return observations

    try:
        onset_date = parse_datetime(pregnancy["onset"])
        abatement_date = parse_datetime(pregnancy["abatement"])
    except ValueError:
        return observations

    # Calculate pregnancy duration
    duration = abatement_date - onset_date
    total_weeks = int(duration.days / 7)

    # Add observations weekly (up to 42 weeks max for safety)
    max_weeks = min(total_weeks, 42)
    patient_ref = pregnancy["patient_ref"]
    encounter_ref = pregnancy.get("encounter_ref")

    for week in range(max_weeks + 1):
        obs_date = onset_date + timedelta(weeks=week)
        if obs_date > abatement_date:
            break

        obs = create_gestational_age_observation(
            patient_ref=patient_ref,
            effective_date=obs_date,
            gestational_weeks=week,
            encounter_ref=(
                encounter_ref if week == 0 else None
            ),  # Only link first to encounter
        )
        observations.append(obs)

    return observations


def add_lactation_observations(
    pregnancy: dict[str, Any],
) -> list[dict[str, Any]]:
    """Add lactation observations after birth."""
    observations = []

    if not pregnancy["abatement"]:
        return observations

    try:
        birth_date = parse_datetime(pregnancy["abatement"])
    except ValueError:
        return observations

    patient_ref = pregnancy["patient_ref"]

    # Add "Lactating" observation shortly after birth (1-2 weeks)
    lactating_date = birth_date + timedelta(weeks=1)
    obs_lactating = create_lactation_observation(
        patient_ref=patient_ref,
        effective_date=lactating_date,
        lactating=True,
    )
    observations.append(obs_lactating)

    # Add "Not lactating" observation 24-40 weeks after birth (randomized)
    lactation_duration_weeks = random.randint(24, 40)  # noqa: S311
    not_lactating_date = birth_date + timedelta(weeks=lactation_duration_weeks)
    obs_not_lactating = create_lactation_observation(
        patient_ref=patient_ref,
        effective_date=not_lactating_date,
        lactating=False,
    )
    observations.append(obs_not_lactating)

    return observations


def process_fhir_bundle(file_path: Path) -> bool:
    """Process a single FHIR bundle file and add pregnancy observations."""
    print(f"Processing {file_path.name}...")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            bundle = json.load(f)
    except Exception as e:
        print(f"  Error reading file: {e}")
        return False

    # Find pregnancy conditions
    pregnancies = find_pregnancy_conditions(bundle)

    if not pregnancies:
        print(f"  No pregnancy conditions found")
        return False

    print(f"  Found {len(pregnancies)} pregnancy condition(s)")

    # Collect all new observations
    new_observations = []

    for pregnancy in pregnancies:
        # Add gestational age observations
        ga_obs = add_gestational_age_observations(pregnancy)
        new_observations.extend(ga_obs)
        print(f"    Added {len(ga_obs)} gestational age observations")

        # Add lactation observations (only if pregnancy ended with birth)
        # Check if abatement exists (pregnancy ended, not miscarriage/abortion)
        if pregnancy["abatement"]:
            lact_obs = add_lactation_observations(pregnancy)
            new_observations.extend(lact_obs)
            print(f"    Added {len(lact_obs)} lactation observations")

    if not new_observations:
        print(f"  No observations added")
        return False

    # Add new observations to bundle
    entries = bundle.get("entry", [])
    entries.extend(new_observations)
    bundle["entry"] = entries

    # Write back to file
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        print(f"  Successfully added {len(new_observations)} observations")
        return True
    except Exception as e:
        print(f"  Error writing file: {e}")
        return False


def process_all_fhir_bundles(fhir_dir: Path) -> None:
    """
    Process all FHIR bundle files in the given directory.

    Args:
        fhir_dir: Path to the directory containing the FHIR bundle files.
    """
    logger.info("Processing all FHIR bundle files...")

    if not fhir_dir.exists():
        logger.error(f"Error: Directory not found: {fhir_dir}")

    # Process all JSON files
    json_files = list(fhir_dir.glob("*.json"))

    # Filter out metadata files
    json_files = [
        f
        for f in json_files
        if not f.name.startswith("practitionerInformation")
        and not f.name.startswith("hospitalInformation")
    ]

    print(f"Found {len(json_files)} FHIR bundle files to process")
    print()

    processed = 0
    for json_file in json_files:
        if process_fhir_bundle(json_file):
            processed += 1
        print()

    logger.success(f"Processed {processed} files successfully")


def main() -> None:
    """Main function to process all FHIR bundle files."""
    parser = argparse.ArgumentParser(
        description="Add gestational age and lactation observations to FHIR bundles"
    )
    parser.add_argument(
        "--fhir-dir",
        type=str,
        default=str(DEFAULT_FHIR_DIR),
        help=f"Path to directory containing FHIR bundle files (default: {DEFAULT_FHIR_DIR})",
    )

    args = parser.parse_args()
    fhir_dir = Path(args.fhir_dir).resolve()

    process_all_fhir_bundles(fhir_dir=fhir_dir)


if __name__ == "__main__":
    main()
