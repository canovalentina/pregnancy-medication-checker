"""PubMed integration endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from services.pubmed_integration.pubmed_service import (
    get_publication_details,
    search_publications,
)

# API prefix from environment variable
API_PREFIX = os.getenv("API_PREFIX", "/api")

# Initialize router
router = APIRouter(prefix=API_PREFIX, tags=["PubMed"])


class PublicationSearchRequest(BaseModel):
    """Request model for publication search."""

    query: str = Field(..., description="Search query string")
    result_start: int = Field(0, ge=0, description="Starting index for pagination")
    result_max: int = Field(10, ge=1, le=100, description="Maximum number of results")
    sort: str = Field(
        "relevance",
        description="Sort order: 'relevance' (default, best for impact), 'pub_date' (most recent), 'author', 'journal'",
    )


@router.post("/publications")
def search_publications_endpoint(request: PublicationSearchRequest):
    """Search PubMed and return list of publication IDs.

    Args:
        request: Search request containing query and pagination parameters

    Returns:
        JSON response with list of PubMed IDs
    """
    try:
        ids = search_publications(
            query=request.query,
            result_start=request.result_start,
            result_max=request.result_max,
            sort=request.sort,
        )
        return {"ids": ids}
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/publications/details")
def get_publication_details_endpoint(
    ids: str = Query(..., description="Comma-separated list of PubMed IDs"),
    fields: str | None = Query(
        "all",
        description="Comma-separated list of fields to retrieve (PMID, Title, Abstract, AuthorList, Journal, PublicationYear, MeSHTerms, or 'all')",
    ),
):
    """Get detailed information for a list of publication IDs.

    Args:
        ids: Comma-separated string of PubMed IDs
        fields: Comma-separated string of field names, or 'all' for all fields

    Returns:
        JSON response with publication details and pagination info
    """
    try:
        # Parse IDs and fields
        id_list = [item_id.strip() for item_id in ids.split(",") if item_id.strip()]
        field_list = [f.strip() for f in (fields or "all").split(",") if f.strip()]

        if not id_list:
            raise HTTPException(status_code=400, detail="At least one ID is required")

        # Get publication details
        details = get_publication_details(ids=id_list, fields=field_list)

        # Calculate pagination (if needed)
        results_per_page = 20
        total_pages = (len(id_list) + results_per_page - 1) // results_per_page

        return {
            "results": details,
            "totalPages": total_pages,
            "totalResults": len(details),
        }
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
