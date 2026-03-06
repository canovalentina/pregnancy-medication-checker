"""In-memory store for demo patient IDs created at startup ingest.

Used so GET /ingested-patients can return IDs from the last ingest without
relying on identifier search (which may not work on all FHIR servers).
"""

from __future__ import annotations

_demo_patient_ids: list[str] = []


def set_demo_patient_ids(patient_ids: list[str]) -> None:
    """Store the list of patient IDs from the last startup demo ingest."""
    global _demo_patient_ids
    _demo_patient_ids = list(patient_ids)


def get_demo_patient_ids() -> list[str]:
    """Return the list of demo patient IDs from the last startup ingest, if any."""
    return list(_demo_patient_ids)
