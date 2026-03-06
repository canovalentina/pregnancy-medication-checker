# Data cleaning and extraction- Extracts pregnancy/lactation information from the raw OpenFDA JSON form "/drug/label" endpoint.
# The code is inspired by openFDA label structure from /drug/label endpoint docs.
# raw API response data (JSON) --> search FDA labels --> return a dict. to send back to frontend.

# https://docs.python.org/3/library/typing.html
from typing import Any


# taking label_json ( raw API response) ,and return a dictionary with standardized keys.
def extract_pregnancy_info_from_label(label_json: dict[str, Any]) -> dict[str, Any]:
    # to return consistent keys,
    result_dict = {
        "has_pregnancy_section": False,
        "pregnancy": None,
        "lactation": None,
        "warnings": None,
        "openfda": label_json.get(
            "openfda", {}
        ),  # storing openfda metadata sub dict. brand_name/ generic_name.
    }

    """
    /drug/label
    {
        "meta": {...},
        "results": [ {...label_doc#...}, {...label_doc#...} ]
    }
    """

    # working with either full API response, or one record.
    document = None
    if isinstance(label_json, dict) and "results" in label_json:
        results = label_json["results"]
        document = results[0] if results else {}
    else:
        document = label_json

    # searching for keys in document.
    for key in (
        "pregnancy",
        "use_in_pregnancy",
        "lactation",
        "use_in_lactation",
        "warnings_and_cautions",
        "warnings",
    ):
        if key in document:
            result_dict["has_pregnancy_section"] = True
            if "preg" in key:
                result_dict["pregnancy"] = document.get(key)
            if "lact" in key:
                result_dict["lactation"] = document.get(key)
            if "warn" in key:
                result_dict["warnings"] = document.get(key)

    # making the code more robust, by searching relevant contents to pregnanacy, beside those with the label.
    # if not finding pregnancy section. looking into text fields for --> word "pregnancy".
    for text in ("description", "indications_and_usage", "warnings", "precautions"):
        if not result_dict["pregnancy"] and text in document:
            found_text = document.get(text)
            if isinstance(found_text, list):
                joined_text = " ".join(found_text)
            else:
                joined_text = found_text
            if "pregnancy" in str(joined_text).lower():
                result_dict["pregnancy"] = joined_text
                result_dict["has_pregnancy_section"] = True

    return result_dict
