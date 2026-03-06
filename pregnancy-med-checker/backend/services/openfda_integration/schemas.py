# defining data model, validation and structure, for openfda API responses. #
# rdefine the data contracts between:
# backend and-> frontend, documentation, and internal logic.
# https://docs.pydantic.dev/latest/

from typing import Any

from pydantic import BaseModel


# label based safety inf.. defining pydantic model (validates data type before sending).
class LabelResponse(BaseModel):
    source: str | None = (
        "openfda"  # /identifuing source of data in case of multiple API use.
    )
    raw: dict[
        str, Any
    ]  # /holding raw JSON file, from OpenFDA. /Any: maximize flex. for diff. drug structures.


""" # adding descriptions.
class LabelResponse(BaseModel):
    source: Optional[str] = Field("openfda", description="Data source identifier")
    raw: Dict[str, Any] = Field(..., description="Raw/Processed OpenFDA label data")
"""


# Reporting adverse event data, from /drug/event endpoint.
class EventResponse(BaseModel):
    source: str | None = "openfda"
    # query: Optional[str] = None # to store the term searched. # noqa: ERA001
    raw: dict[str, Any]


"""
# Nesting models tp --> return structured info.
class PregnancyData(BaseModel):
    pregnancy: Optional[str]
    lactation: Optional[str]
    warnings: Optional[str]
    has_pregnancy_section: bool

class LabelResponse(BaseModel):
    source: str = "openfda"
    data: PregnancyData
"""
