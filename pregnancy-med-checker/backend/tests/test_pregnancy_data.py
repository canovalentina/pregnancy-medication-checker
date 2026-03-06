#!/usr/bin/env python3
"""Test script to check pregnancy data for Maria Martinez."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.fhir_integration.application.api_handlers import FHIRAPIHandlers


async def main():
    handlers = FHIRAPIHandlers()
    summary_response = await handlers.get_patient_summary("53418889")

    # Check what we got
    print(f"Response type: {type(summary_response)}")
    print(f"Response attributes: {dir(summary_response)}")

    # Try to get the summary data with backwards compatibility
    summary_data = None
    if hasattr(summary_response, "resources") and summary_response.resources:
        # Expected format: ResourceResponse with resources list
        summary_data = summary_response.resources[0]

    elif hasattr(summary_response, "summary"):
        # Old format: direct summary attribute, keeping for backwards compatibility
        summary_data = summary_response.summary
    elif hasattr(summary_response, "model_dump"):
        # Pydantic model: dump to dict
        summary_data = summary_response.model_dump()
        # The summary might be in resources[0] after model_dump
        if isinstance(summary_data, dict) and summary_data.get("resources"):
            summary_data = summary_data["resources"][0]
    else:
        print("Could not extract summary data")
        return

    print(
        f"\nSummary keys: {summary_data.keys() if isinstance(summary_data, dict) else 'Not a dict'}"
    )

    # Access the summary data
    if isinstance(summary_data, dict):
        summary = summary_data
        pregnancy_history = summary.get("pregnancyHistory", {})
        print(
            f"\nPregnancy history keys: {pregnancy_history.keys() if isinstance(pregnancy_history, dict) else 'Not a dict'}"
        )
        pregnancies = (
            pregnancy_history.get("pregnancies", [])
            if isinstance(pregnancy_history, dict)
            else []
        )
        print(f"\nNumber of pregnancies: {len(pregnancies)}")
        for p in pregnancies:
            print(f"  ID: {p.get('id')}")
            print(f"    Outcome: {p.get('outcome')}")
            print(f"    Start: {p.get('startDate')}")
            print(f"    End: {p.get('endDate')}")
            print(f"    Preterm: {p.get('isPreterm')}")
            print(f"    Observations: {len(p.get('observations', []))}")
            print()

        # Also check conditions
        conditions = summary.get("conditions", [])
        print(f"\nConditions found: {len(conditions)}")
        for c in conditions:
            code = c.get("code", {})
            text = code.get("text", "N/A") if isinstance(code, dict) else "N/A"
            codings = code.get("coding", []) if isinstance(code, dict) else []
            print(f"  Condition: {text}")
            for coding in codings:
                print(f"    Code: {coding.get('code')}, System: {coding.get('system')}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
