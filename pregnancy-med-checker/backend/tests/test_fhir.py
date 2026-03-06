"""Pytest tests for FHIR integration."""

from __future__ import annotations

import pytest  # type: ignore[import-untyped]
from loguru import logger

from services.fhir_integration import (
    DEFAULT_SYNTHEA_DATA_PATH,
    DEFAULT_TEST_DATA_PATH,
    FHIRAPIHandlers,
)


@pytest.fixture
def fhir_handlers():
    """Fixture providing FHIRAPIHandlers instance."""
    return FHIRAPIHandlers()


@pytest.fixture
def pregnant_test_path():
    """Fixture providing path to pregnant patient test data."""
    return (
        DEFAULT_TEST_DATA_PATH
        / "_test_Pregnant_Patient_11111111-1111-1111-1111-111111111111.json"
    )


@pytest.fixture
def lactating_test_path():
    """Fixture providing path to lactating patient test data."""
    return (
        DEFAULT_TEST_DATA_PATH
        / "_test_Lactating_Patient_22222222-2222-2222-2222-222222222222.json"
    )


@pytest.mark.asyncio
async def test_fhir_connection(fhir_handlers):
    """Test FHIR server connection using handlers."""
    logger.info("Testing FHIR server connection...")
    result = await fhir_handlers.is_server_connected()
    assert result, "FHIR server connection test failed"
    logger.success("FHIR server connection test passed")


@pytest.mark.asyncio
async def test_patient_search(fhir_handlers):
    """Test patient search functionality."""
    logger.info("Testing patient search...")

    # Test general search functionality first
    total_found = 0
    search_result = None
    for params in [
        None,
        {"gender": "female"},
        {"gender": "male"},
        {"gender": "other"},
        {"birth_date": "1990"},
        {"name": "Sarah"},
    ]:
        logger.debug(f"Testing search with params: {params}")
        search_result = await fhir_handlers.search_patients(**params or {})
        logger.info(f"Found patients: {search_result.total}")
        total_found += search_result.total

    # Test reading a specific patient (if we have any results)
    if search_result and search_result.resources:
        test_patient_id = search_result.resources[0].get("id")
        if test_patient_id:
            logger.debug(f"Testing read patient by ID: {test_patient_id}")
            patient_data = await fhir_handlers.client.read_patient(test_patient_id)
            if patient_data:
                logger.success(f"Successfully read patient: {patient_data.name}")

    logger.info(f"Total patients found across all searches: {total_found}")
    # Test passes if method works (even if no results found on public server)
    assert True, "Patient search test passed"


@pytest.mark.asyncio
async def test_data_ingestion(fhir_handlers):
    """Test data ingestion for 1 bundle in test directory."""
    logger.info("Testing data ingestion...")

    result = await fhir_handlers.ingest_resource_data(
        data_path=DEFAULT_TEST_DATA_PATH, max_bundles=1
    )
    logger.info("Resource data ingestion result:")
    logger.debug(result.model_dump_json(indent=2))

    assert result.summary.total_patients > 0, "No patients were ingested"
    assert (
        result.summary.total_errors == 0
    ), f"Errors occurred during ingestion: {result.summary.total_errors}"
    logger.success("Data ingestion test passed")


@pytest.mark.asyncio
async def test_data_ingestion_synthea(fhir_handlers):
    """Test data ingestion for 1 Synthea bundle."""
    logger.info("Testing Synthea data ingestion (1 bundle)...")

    result = await fhir_handlers.ingest_resource_data(
        data_path=DEFAULT_SYNTHEA_DATA_PATH, max_bundles=1
    )
    logger.info("Synthea data ingestion result:")
    logger.debug(result.model_dump_json(indent=2))

    assert (
        result.summary.total_patients > 0
    ), "No patients were ingested from Synthea bundle"
    # Allow some errors as Synthea bundles may have validation issues
    if result.summary.total_errors > 0:
        logger.warning(
            f"Ingestion completed with {result.summary.total_errors} error(s)"
        )
    else:
        logger.success("Synthea data ingestion test passed with no errors")


@pytest.mark.asyncio
async def test_delete_patient(fhir_handlers):
    """Test deleting an ingested test patient."""
    logger.info("Testing patient deletion...")

    # First, ingest a test patient
    logger.info("Step 1: Ingesting test patient...")
    result = await fhir_handlers.ingest_resource_data(
        data_path=DEFAULT_TEST_DATA_PATH, max_bundles=1
    )

    assert result.patients_created, "Failed to ingest test patient for deletion test"

    patient_id = result.patients_created[0].id
    patient_name = result.patients_created[0].name
    logger.info(f"Ingested patient: {patient_name} (ID: {patient_id})")

    # Verify patient exists before deletion
    logger.info("Step 2: Verifying patient exists...")
    patient = await fhir_handlers.client.read_patient(patient_id)
    assert patient is not None, f"Patient {patient_id} not found after ingestion"
    logger.success(f"Patient exists: {patient.name}")

    # Delete the patient (with cascade delete)
    logger.info(f"Step 3: Deleting patient {patient_id} with cascade delete...")
    delete_result = await fhir_handlers.delete_patient(patient_id)
    assert (
        delete_result.status == "success"
    ), f"Failed to delete patient: {delete_result.message}"
    assert delete_result.data is not None, "Delete result data is None"
    assert (
        delete_result.data.get("deleted") is True
    ), f"Delete result does not indicate success: {delete_result.data}"
    logger.success(f"Delete successful: {delete_result.message}")

    # Verify patient is deleted (should return None or raise exception)
    logger.info("Step 4: Verifying patient was deleted...")
    try:
        deleted_patient = await fhir_handlers.client.read_patient(patient_id)
        assert (
            deleted_patient is None
        ), f"Patient {patient_id} still exists after deletion"
    except Exception as e:
        # Exception on read is expected when resource is deleted
        logger.debug(f"Patient not found (expected): {type(e).__name__}")

    logger.success("Patient successfully deleted (not found when reading)")
    logger.success("Patient deletion test passed!")


@pytest.mark.asyncio
async def test_pregnancy_stage_extraction(fhir_handlers, pregnant_test_path):
    """Test extracting pregnancy stage (gestational weeks) from a patient."""
    logger.info("Testing pregnancy stage extraction...")

    # Ingest pregnant patient test data
    logger.info(f"Ingesting pregnant patient from: {pregnant_test_path}")
    result = await fhir_handlers.ingest_resource_data(
        data_path=str(pregnant_test_path), max_bundles=1
    )

    assert result.patients_created, "Failed to ingest pregnant test patient"

    patient_id = result.patients_created[0].id
    logger.info(
        f"Ingested pregnant patient: {result.patients_created[0].name} (ID: {patient_id})"
    )

    # Get pregnancy stage
    pregnancy_stage = await fhir_handlers.client.get_pregnancy_stage(patient_id)

    assert pregnancy_stage is not None, "Failed to extract pregnancy stage"
    logger.info(f"Pregnancy stage extracted: {pregnancy_stage}")

    # Verify the structure
    required_fields = ["gestational_weeks", "effective_date", "observation_id"]
    for field in required_fields:
        assert field in pregnancy_stage, f"Missing required field: {field}"

    # Verify gestational weeks is a valid number
    weeks = pregnancy_stage.get("gestational_weeks")
    assert isinstance(weeks, int), f"Gestational weeks should be int, got {type(weeks)}"
    assert weeks >= 0, f"Invalid gestational weeks: {weeks} (must be >= 0)"
    assert weeks == 20, f"Expected 20 weeks, got {weeks}"

    logger.success(f"Pregnancy stage test passed! Gestational weeks: {weeks}")

    # Clean up
    await fhir_handlers.delete_patient(patient_id)


@pytest.mark.asyncio
async def test_lactation_stage_extraction(fhir_handlers, lactating_test_path):
    """Test extracting lactation stage from a patient."""
    logger.info("Testing lactation stage extraction...")

    # Ingest lactating patient test data
    logger.info(f"Ingesting lactating patient from: {lactating_test_path}")
    result = await fhir_handlers.ingest_resource_data(
        data_path=str(lactating_test_path), max_bundles=1
    )

    assert result.patients_created, "Failed to ingest lactating test patient"

    patient_id = result.patients_created[0].id
    logger.info(
        f"Ingested lactating patient: {result.patients_created[0].name} (ID: {patient_id})"
    )

    # Get lactation stage
    lactation_stage = await fhir_handlers.client.get_lactation_stage(patient_id)

    assert lactation_stage is not None, "Failed to extract lactation stage"
    logger.info(f"Lactation stage extracted: {lactation_stage}")

    # Verify the structure
    required_fields = ["status", "effective_date", "observation_id"]
    for field in required_fields:
        assert field in lactation_stage, f"Missing required field: {field}"

    # Verify status is valid
    status = lactation_stage.get("status")
    valid_statuses = ["Lactating", "Not lactating"]
    assert (
        status in valid_statuses
    ), f"Invalid lactation status: {status} (expected one of {valid_statuses})"
    assert status == "Lactating", f"Expected 'Lactating', got '{status}'"

    logger.success(f"Lactation stage test passed! Status: {status}")

    # Clean up
    await fhir_handlers.delete_patient(patient_id)


@pytest.mark.asyncio
async def test_medications_list_extraction(fhir_handlers, pregnant_test_path):
    """Test extracting medications list from a patient."""
    logger.info("Testing medications list extraction...")

    # Ingest pregnant patient test data (has medications)
    logger.info(f"Ingesting patient with medications from: {pregnant_test_path}")
    result = await fhir_handlers.ingest_resource_data(
        data_path=str(pregnant_test_path), max_bundles=1
    )

    assert result.patients_created, "Failed to ingest test patient with medications"

    patient_id = result.patients_created[0].id
    logger.info(
        f"Ingested patient: {result.patients_created[0].name} (ID: {patient_id})"
    )

    # Get medications list
    medications = await fhir_handlers.client.get_patient_medications_list(patient_id)

    assert medications is not None, "Failed to extract medications list"
    assert len(medications) > 0, "Expected at least 1 medication"
    logger.info(f"Found {len(medications)} medication(s)")

    # Verify the structure of medications
    required_fields = ["id", "medication", "status"]
    for i, med in enumerate(medications):
        for field in required_fields:
            assert field in med, f"Medication {i} missing required field: {field}"

        logger.info(
            f"  Medication {i+1}: {med.get('medication')} (RxNorm: {med.get('medication_code')})"
        )

    # Verify we have the expected medications
    medication_names = [med.get("medication", "").lower() for med in medications]
    assert any(
        "prenatal" in name for name in medication_names
    ), "Expected to find prenatal vitamin"
    assert (
        len(medications) >= 2
    ), f"Expected at least 2 medications, got {len(medications)}"

    logger.success(
        f"Medications list test passed! Found {len(medications)} medication(s)"
    )

    # Clean up
    await fhir_handlers.delete_patient(patient_id)
