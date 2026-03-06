# Pregnancy Medication Checker - Makefile
# Task automation for development

# Load environment variables from root .env
ifneq (,$(wildcard ../.env))
    include ../.env
    export
endif

# Default values if .env doesn't exist
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173
HAPI_FHIR_PORT ?= 8080

.PHONY: help setup dev format lint lint-fix check test test-fhir-connection test-fhir-ingest test-fhir-ingest-synthea test-fhir-patient-search test-fhir-delete test-pregnancy-stage test-lactation-stage test-medications-list fhir-ingest-synthea-all-bundles fhir-ingest-test-data fhir-delete-all-ingested fhir-delete-test-data fhir-list-ingested fhir-add-pregnancy-observations drugbank-extract-interactions hapi-up hapi-down hapi-logs hapi-health clean

# Default target
help:
	@echo "Available targets:"
	@echo "  setup                      - Set up the development environment"
	@echo "  dev                        - Run the development server"
	@echo "  format                     - Format code with black"
	@echo "  lint                       - Lint code with ruff"
	@echo "  lint-fix                   - Auto-fix linting errors with ruff"
	@echo "  check                      - Format and lint code"
	@echo "  test                       - Run all tests with pytest"
	@echo "  test-fhir-connection       - Test FHIR server connection"
	@echo "  test-fhir-patient-search   - Test FHIR patient search"
	@echo "  test-fhir-ingest           - Test FHIR data ingestion"
	@echo "  test-fhir-ingest-synthea   - Test FHIR Synthea data ingestion (1 bundle)"
	@echo "  test-fhir-delete           - Test deleting an ingested test patient"
	@echo "  test-pregnancy-stage       - Test pregnancy stage extraction"
	@echo "  test-lactation-stage       - Test lactation stage extraction"
	@echo "  test-medications-list      - Test medications list extraction"
	@echo "  fhir-ingest-synthea-all-bundles - Ingest all Synthea bundles into FHIR server"
	@echo "  fhir-ingest-test-data      - Ingest test data from synthea/test directory (with test tag)"
	@echo "  fhir-delete-all-ingested   - Delete ALL patients with ingestion identifier"
	@echo "  fhir-delete-test-data      - Delete only test data (patients with test ingestion tag)"
	@echo "  fhir-list-ingested         - List count and IDs of all ingested patients"
	@echo "  fhir-add-pregnancy-observations - Add pregnancy observations to FHIR bundles (optional: FHIR_DIR=path/to/dir)"
	@echo "  drugbank-extract-interactions   - Extract all drug interactions from DrugBank XML"
	@echo "  hapi-up                    - Start local HAPI FHIR in Docker Compose"
	@echo "  hapi-down                  - Stop and remove local HAPI FHIR container"
	@echo "  hapi-logs                  - Tail logs for HAPI FHIR container"
	@echo "  hapi-health                - Check HAPI FHIR /metadata endpoint"
	@echo "  clean                      - Clean temporary files and caches"

# Setup
setup:
	@echo "Setting up development environment..."
	uv venv --python 3.12
	uv sync --extra dev
	mkdir -p logs
	@echo "Making scripts executable..."
	chmod +x scripts/*.py
	@echo "Setup complete!"

# Development
dev:
	@echo "Starting development server..."
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

# Code Quality
format:
	@echo "Formatting code with black..."
	uv run black .

lint:
	@echo "Linting code with ruff..."
	uv run ruff check .

lint-fix:
	@echo "Auto-fixing linting errors with ruff..."
	uv run ruff check --fix .

check: format lint
	@echo "Code formatting and linting complete!"

# Testing
test:
	@echo "Running all tests with pytest..."
	uv run pytest tests/ -v

test-fhir-connection:
	@echo "Testing FHIR server connection..."
	uv run pytest tests/test_fhir.py::test_fhir_connection -v

test-fhir-patient-search:
	@echo "Testing FHIR patient search..."
	uv run pytest tests/test_fhir.py::test_patient_search -v

test-fhir-ingest:
	@echo "Testing FHIR data ingestion..."
	uv run pytest tests/test_fhir.py::test_data_ingestion -v

test-fhir-ingest-synthea:
	@echo "Testing FHIR Synthea data ingestion (1 bundle)..."
	uv run pytest tests/test_fhir.py::test_data_ingestion_synthea -v

test-fhir-delete:
	@echo "Testing patient deletion..."
	uv run pytest tests/test_fhir.py::test_delete_patient -v

test-pregnancy-stage:
	@echo "Testing pregnancy stage extraction..."
	uv run pytest tests/test_fhir.py::test_pregnancy_stage_extraction -v

test-lactation-stage:
	@echo "Testing lactation stage extraction..."
	uv run pytest tests/test_fhir.py::test_lactation_stage_extraction -v

test-medications-list:
	@echo "Testing medications list extraction..."
	uv run pytest tests/test_fhir.py::test_medications_list_extraction -v

# FHIR Operations (using scripts)
fhir-ingest-synthea-all-bundles:
	@echo "Ingesting all Synthea bundles into FHIR server..."
	@chmod +x scripts/fhir-ingest-synthea-all-bundles.py
	uv run python scripts/fhir-ingest-synthea-all-bundles.py

fhir-ingest-test-data:
	@echo "Ingesting test data from synthea/test directory..."
	@chmod +x scripts/fhir-ingest-synthea-all-bundles.py
	uv run python scripts/fhir-ingest-synthea-all-bundles.py --test

fhir-delete-all-ingested:
	@echo "Deleting all ingested patients..."
	@chmod +x scripts/fhir-delete-all-ingested.py
	uv run python scripts/fhir-delete-all-ingested.py

fhir-delete-test-data:
	@echo "Deleting test ingested patients only..."
	@chmod +x scripts/fhir-delete-all-ingested.py
	uv run python scripts/fhir-delete-all-ingested.py --test-tag

fhir-list-ingested:
	@echo "Listing ingested patients..."
	@chmod +x scripts/fhir-list-ingested.py
	uv run python scripts/fhir-list-ingested.py

fhir-add-pregnancy-observations:
	@echo "Adding pregnancy observations to FHIR bundles..."
	@chmod +x services/synthea/scripts/add_pregnancy_observations.py
	@if [ -z "$(FHIR_DIR)" ]; then \
		echo "Using default FHIR directory..."; \
		uv run python services/synthea/scripts/add_pregnancy_observations.py; \
	else \
		echo "Using FHIR_DIR: $(FHIR_DIR)"; \
		uv run python services/synthea/scripts/add_pregnancy_observations.py --fhir-dir "$(FHIR_DIR)"; \
	fi

# DrugBank Integration
drugbank-extract-interactions:
	@echo "Extracting all drug interactions from DrugBank database..."
	@echo "Must store the DrugBank XML file in services/drugbank_integration/data/DrugBank/full_database.xml"
	uv run python services/drugbank_integration/scripts/extract_interactions.py

# HAPI FHIR (Docker Compose helpers)
hapi-up:
	@echo "Starting HAPI FHIR (port $(HAPI_FHIR_PORT))..."
	docker compose -f ../docker-compose.yml up -d hapi-fhir

hapi-down:
	@echo "Stopping and removing HAPI FHIR..."
	docker compose -f ../docker-compose.yml stop hapi-fhir
	docker compose -f ../docker-compose.yml rm -f hapi-fhir

hapi-logs:
	@echo "Tailing HAPI FHIR logs... (Ctrl+C to stop)"
	docker compose -f ../docker-compose.yml logs -f hapi-fhir

hapi-health:
	@echo "Checking HAPI FHIR health at http://localhost:$(HAPI_FHIR_PORT)/fhir/metadata ..."
	@curl -s -o /dev/null -w "%{http_code}\n" http://localhost:$(HAPI_FHIR_PORT)/fhir/metadata | grep -E "^(200|3..)" && echo "OK" || (echo "HAPI FHIR not healthy" && exit 1)


# Utilities
clean:
	@echo "Cleaning temporary files and caches..."
	rm -rf .uv/
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name '*.pyc' -delete
	find . -name '*.log' -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	@echo "Cleanup complete!"

