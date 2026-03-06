# Pregnancy Medication Checker Backend (still in development)

A FastAPI-based backend service for checking medication interactions during pregnancy using FHIR (Fast Healthcare Interoperability Resources) standards.

## Features

- FHIR R4 server integration
- Patient data management
- Medication interaction checking (placeholder)
- Pregnancy safety assessment (placeholder)
- Sample data ingestion
- API endpoints

## Pre-Requirements

### For Local Development
- Python 3.12+
- uv (for dependency management) (`brew install uv`)
- make (for running tasks) (usually pre-installed on macOS)

### For Docker Development
- Docker & Docker Compose
- make

## Quick Start

**Important:** All `make` commands must be run from the `pregnancy-med-checker/backend/` directory.

### Option 1: Local Development (Recommended for development)

1. Navigate to the backend directory:

   ```bash
   cd pregnancy-med-checker/backend
   ```

2. Set up the development environment:

   ```bash
   make setup
   ```

   Note: To rebuild dependencies run:
   ```bash
   rm -rf .venv uv.lock
   uv sync --extra dev
   ```

3. Set up environment variables:

   ```bash
   cd ..  # Go to root directory
   cp .env.example .env
   ```

   **Important:** The project uses a single `.env` file in the root directory for all services (backend, frontend, and Docker).

4. Activate the virtual environment (optional):

   ```bash
   source .venv/bin/activate
   ```

   **Note:** All `make` commands automatically use the virtual environment, so this step is optional.

5. Run the development server:
   ```bash
   make dev
   ```

### Option 2: Docker Development (Recommended for production-like testing)

Use the root level Makefile from `pregnancy-med-checker/` directory:

```bash
cd pregnancy-med-checker
make build  # Build Docker images
make up     # Start all services
```

All Docker commands are run from the root directory.

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests using:

```bash
make test
```

## Code Quality

**Important:** Always run `make check` before pushing code to ensure code quality and consistency:

```bash
make check
```

This command will:

- Format your code with `black`
- Lint your code with `ruff`
- Ensure all code follows project standards

## Docker Usage

Run the backend in Docker from the project root:

```bash
cd ..  # pregnancy-med-checker/
make build  # Build all Docker images
make up     # Start all services
```

See the root [README.md](../README.md) for full Docker documentation.

## Available Commands

All commands should be run from the `backend/` directory.

### Development Commands

- `make help` - Show all available commands
- `make setup` - Set up development environment (creates venv, installs dependencies)
- `make dev` - Run development server with hot reload
- `make test` - Run all tests
- `make format` - Format code with black
- `make lint` - Lint code with ruff
- `make check` - Format and lint code (run before pushing)

### FHIR Commands

- `make test-fhir-connection` - Test FHIR server connection
- `make test-fhir-ingest` - Ingest sample data into FHIR server
- `make test-fhir-patient-search` - Test patient search functionality

### Docker Commands

Docker commands are managed from the root directory:
```bash
cd pregnancy-med-checker
make build   # Build Docker images
make up      # Start all services
make down    # Stop all services
```

### Utility Commands

- `make clean` - Clean temporary files and caches

## Using the Makefile

The Makefile provides convenient shortcuts for common development tasks. Here are some common workflows:

### Daily Development Workflow

```bash
# Start coding
cd backend

# Run the development server (auto-reloads on changes)
make dev

# In another terminal, run tests
make test

# Before committing, check code quality
make check
```

### Docker Workflow

```bash
# From root directory
cd pregnancy-med-checker

# Build and run everything
make build
make up

# View logs if needed
make logs

# Stop when done
make down
```

### Testing Workflow

```bash
cd backend

# Test FHIR connection
make test-fhir-connection

# Ingest test data
make test-fhir-ingest

# Run all tests
make test
```
