"""Pregnancy Medication Checker API - Main application module."""

from __future__ import annotations

import asyncio
import os
from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException  # type: ignore[import-untyped]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-untyped]
from loguru import logger

from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    LoginRequest,
    LoginResponse,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.fhir import fhir_handlers
from app.fhir import router as fhir_router
from app.interactions import router as interactions_router
from app.messaging import router as messaging_router
from app.notes import router as notes_router
from app.openfda import router as openfda_router
from app.pubmed import router as pubmed_router
from app.rxnorm import router as rxnorm_router
from services.fhir_integration import DEFAULT_TEST_DATA_PATH

# In-memory store for demo patient IDs from startup ingest (see app/demo_patients.py)
from app.demo_patients import set_demo_patient_ids

# Configuration
APP_NAME = os.getenv("APP_NAME", "Pregnancy Medication Checker API")
API_PREFIX = os.getenv("API_PREFIX", "/api")
# Default CORS origins - includes localhost for development and production domain
default_origins = "http://localhost:5173,https://www.pregsafe.org,https://pregsafe.org"
origins = [
    o.strip() for o in os.getenv("ENABLE_CORS_ORIGINS", default_origins).split(",")
]

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    description="API for checking medication interactions during pregnancy",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(fhir_router)
app.include_router(rxnorm_router)
app.include_router(pubmed_router)
app.include_router(interactions_router)
app.include_router(openfda_router)
app.include_router(notes_router)
app.include_router(messaging_router)

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logger.add(log_dir / "app.log", rotation="1 day", retention="7 days", level="INFO")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting {APP_NAME}")

    # Test FHIR connection in background (non-blocking)
    # This allows the app to respond to health checks immediately
    async def test_fhir_connection():
        try:
            connection_test = await fhir_handlers.get_fhir_status()
            if connection_test.status == "connected":
                logger.info(f"Connected to FHIR server: {connection_test.server}")
            else:
                logger.warning(f"FHIR server connection issue: {connection_test}")
        except Exception as e:
            logger.warning(f"FHIR connection test failed: {e}")

    # Don't await - let it run in background so health checks can respond immediately
    # Store task reference to prevent garbage collection
    fhir_test_task = asyncio.create_task(test_fhir_connection())
    # Keep task reference alive (task runs in background)
    logger.debug(f"Started background FHIR connection test task: {fhir_test_task}")

    # Optional: ingest demo (test) data at startup when INGEST_DEMO_AT_STARTUP is set
    if os.getenv("INGEST_DEMO_AT_STARTUP", "").lower() in ("true", "1", "yes"):

        async def ensure_demo_data():
            try:
                resp = await fhir_handlers.get_ingested_patient_ids()
                count = (resp.data or {}).get("count", 0)
                if count >= 3:
                    logger.info(
                        f"Demo patients already present ({count} ingested), skipping startup ingest"
                    )
                    return
                logger.info("Ingesting demo data at startup...")
                result = await fhir_handlers.ingest_resource_data(
                    data_path=str(DEFAULT_TEST_DATA_PATH),
                    max_bundles=None,
                    ingestion_tag=None,
                )
                ids = [p.id for p in (result.patients_created or []) if p.id]
                if ids:
                    set_demo_patient_ids(ids)
                    logger.info(f"Stored {len(ids)} demo patient IDs from startup ingest.")
                logger.info("Demo data ingestion at startup complete.")
            except Exception as e:
                logger.warning(f"Demo ingest at startup failed: {e}")

        asyncio.create_task(ensure_demo_data())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")


# Basic endpoints
@app.get("/")
def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Pregnancy Medication Checker API",
        "app": APP_NAME,
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{API_PREFIX}/health",
    }


@app.get(f"{API_PREFIX}/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "app": APP_NAME, "version": "0.1.0"}


@app.get(f"{API_PREFIX}/version")
def version():
    """Version information endpoint."""
    return {
        "version": "0.1.0",
        "name": APP_NAME,
        "description": "Pregnancy Medication Checker API",
    }


# Authentication endpoints
@app.post(f"{API_PREFIX}/auth/login", response_model=LoginResponse)
def login(login_request: LoginRequest):
    """Login endpoint for users."""
    user = authenticate_user(login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"].value},
        expires_delta=access_token_expires,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=User(
            username=user["username"],
            role=user["role"],
            full_name=user["full_name"],
            email=user["email"],
        ),
    )


@app.get(f"{API_PREFIX}/auth/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@app.get(f"{API_PREFIX}/auth/test-accounts")
def get_test_accounts():
    """Get test account information (for development)."""
    return {
        "provider": {
            "username": "provider",
            "password": "provider123",
            "role": "provider",
            "full_name": "Dr. Sarah Johnsonx",
        },
        "patient": {
            "username": "patient",
            "password": "patient123",
            "role": "patient",
            "full_name": "Jane Doex",
        },
    }
