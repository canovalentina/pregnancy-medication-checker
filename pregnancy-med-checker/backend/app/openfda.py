# Implements the API endpoints (/label, /events, /ndc, /search).
# connect the app to OpenFDA via the client.
# https://fastapi.tiangolo.com/tutorial/bigger-applications/

# APIRouter to define routes separately and include them in main app./ Query for validation and documenting parameters./
# HTTPException to send error with specific HTTP status code./ Optional for type hints./

# openfda_clinet handles OpenFDA HTTP requests./
import os

from fastapi import APIRouter, HTTPException, Query  # type: ignore[import-untyped]

from services.openfda_integration import openfda_client as client
from services.openfda_integration.utils import extract_pregnancy_info_from_label

# API prefix from environment variable
API_PREFIX = os.getenv("API_PREFIX", "/api")

# initializing a router instance, all endpoints attached./
router = APIRouter(prefix=f"{API_PREFIX}/openfda", tags=["OpenFDA"])


# fetching label information./ displaying pregnancy warnings for searched drug.
# Endpoint --> /label
# path --> /api/openfda/label?drug=...
@router.get("/label", summary="Get drug label (pregnancy/lactation) information")
async def label(drug: str = Query(..., description="Brand or generic drug name")):
    # error handling logic --> try
    try:
        # call async. client func.
        raw = await client.get_label_by_name(drug, limit=1)
    except Exception as e:
        # external API error --> 502
        raise HTTPException(status_code=502, detail=str(e))
    # extract pregnancy sections from --> label JSON
    extract = extract_pregnancy_info_from_label(raw)
    # return for frontend use --> drug- raw file- filtered summary.
    return {"query": drug, "openfda_response": raw, "pregnancy_extracted": extract}


# fetching adverse drug reations.
# Endponit --> /events
# path --> /api/openfda/events?drug=...
@router.get("/events", summary="Get adverse events for a drug")
async def events(
    drug: str = Query(..., description="Drug name to search in FAERS records"),
    limit: int = Query(10, ge=1, le=100),
):
    try:
        # call Openfda adverse event endpoint
        raw = await client.get_adverse_events_by_drug(drug, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    # return --> drug- raw file.
    return {"query": drug, "openfda_response": raw}


# fetching national drug code (identifier to track drugs)- app may use ndc to display packaging and manufactering details.
# Endpoint --> /ndc
# path --> /api/openfda/ndc?drug=...
@router.get("/ndc", summary="Lookup NDC information for a drug")
async def ndc(drug: str = Query(...)):
    try:
        raw = await client.get_ndc_info(drug, limit=10)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    # return --> drug- raw file.
    return {"query": drug, "openfda_response": raw}


# search for matching labels for --> autocomplete./
# Endpoint --> /search
# path: /api/openfda/search?q=... ./
# try implementing: min. required string --> 2, up to 10 results.
# current 1<limit<50


# logic: build list of sugg. (brand/generic)
# for each hint --> get brand_name, generic_name, ndc
# as user type in search box, these hints may populate a drop down list
@router.get("/search", summary="Searching labels for autocomplete suggestions")
async def search(
    q: str = Query(..., description="Search term for brand or generic"),
    limit: int = Query(10, ge=1, le=50),
):
    try:
        raw = await client.search_labels(q, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    # build a lightweight hint list for UI
    hints = []
    results = raw.get("results", []) if isinstance(raw, dict) else []
    for item in results:
        of = item.get("openfda", {})
        brand = (
            of.get("brand_name") or of.get("generic_name") or item.get("product_ndc")
        )
        hints.append({"brand_or_generic": brand, "openfda": of})
    return {"query": q, "hints": hints}
