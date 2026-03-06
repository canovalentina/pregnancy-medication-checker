"""RxNorm integration endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query  # type: ignore[import-untyped]

from services.rxnorm_integration.rxnorm_service import (
    autocomplete_drugs,
    get_rxnorm_properties,
    lookup_rxcui,
)

# API prefix from environment variable
API_PREFIX = os.getenv("API_PREFIX", "/api")

# Initialize router
router = APIRouter(prefix=API_PREFIX, tags=["RxNorm"])


@router.get("/autocomplete")
def autocomplete(term: str = Query(..., description="incomplete drug name entry")):
    """Get drug name autocomplete suggestions."""
    try:
        suggestions = autocomplete_drugs(term)
        return suggestions
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rxnorm/lookup", summary="Finding RxCUI")
def lookup_rxcui_endpoint(
    name: str = Query(..., min_length=1, example="ibuprofen"),
) -> dict:
    """Find RxCUI (RxNorm Concept Unique Identifier) for a drug name."""
    try:
        return lookup_rxcui(name)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/rxnorm/properties/{rxcui}", summary="Properties for RxCUI")
def get_rxnorm_properties_endpoint(
    rxcui: int,
    prop_name: str | None = Query(
        None, description="optional property name (propName)"
    ),
) -> dict:
    """Get properties for an RxCUI."""
    try:
        return get_rxnorm_properties(rxcui, prop_name)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
