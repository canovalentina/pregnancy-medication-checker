import os

from fastapi import APIRouter  # type: ignore[import-untyped]
from pydantic import BaseModel

from services.drug_interaction.interaction_service import (
    _get_cached_checker,
    get_interaction,
)

# API prefix from environment variable
API_PREFIX = os.getenv("API_PREFIX", "/api")

router = APIRouter(prefix=API_PREFIX, tags=["Drug Interactions"])


class DrugPair(BaseModel):
    """Drug pair for batch checking."""

    drug1: str
    drug2: str


class BatchInteractionRequest(BaseModel):
    """Request model for batch interaction checking."""

    pairs: list[DrugPair]


# To use this API endpoint --> http://127.0.0.1:8000/api/interaction?drug1=Acarbose&drug2=Digoxin
@router.get("/interaction")
def interaction(drug1: str, drug2: str):
    """Check interaction between two drugs."""
    # Call the function, and pass 2 drug names.
    result = get_interaction(drug1, drug2)
    # Handling no interaction found situation
    if result is None:
        return {
            "drug1": drug1,
            "drug2": drug2,
            "interaction": None,
            "message": "No interaction found in database",
        }
    # Returning JSON object, containing --> both drug names + interaction explanation
    return {"drug1": drug1, "drug2": drug2, "interaction": result}


@router.post("/interaction/batch")
def batch_interaction(request: BatchInteractionRequest):
    """Check interactions for multiple drug pairs at once.

    More efficient than calling /interaction multiple times.
    """
    checker = _get_cached_checker()
    if checker is None:
        return {
            "error": "Drug interaction service not available",
            "results": [],
        }

    # Convert request pairs to tuples
    drug_pairs = [(pair.drug1, pair.drug2) for pair in request.pairs]

    # Get batch results
    results = checker.get_interactions_batch(drug_pairs)

    # Format response
    formatted_results = [
        {
            "drug1": drug1,
            "drug2": drug2,
            "interaction": interaction,
            "message": (
                "No interaction found in database" if interaction is None else None
            ),
        }
        for (drug1, drug2), interaction in results.items()
    ]

    return {"results": formatted_results}
