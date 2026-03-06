"""RxNorm service functions for interacting with RxNorm API.

Implementing 3 helper endpoints: autocomplete, map drug name to RxCUI, , and retrieve drug info by RxCUI

This code was adopted, after studying the below links:
URL: [https://github.com/EndurantDevs/drug-api/blob/main/api/endpoint/drug.py]
URL: [https://github.com/ricksuggs/similar-medication-search/blob/master/back-end/api/api.py]
and RxNorm documentations, including:
URL: [https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getDrugs.html]
URL: [https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiByString.html]
URL: [https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRxConceptProperties.html]
URL: [https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRxProperty.html]
"""

from __future__ import annotations

import requests
from cachetools import TTLCache, cached

# Endpoint: https://lhncbc.nlm.nih.gov/RxNav/APIs/
RXNORM_ENDPOINT = "https://rxnav.nlm.nih.gov/REST"

# Constants
HTTP_OK = 200
MIN_AUTOCOMPLETE_RESULTS = 3
REQUEST_TIMEOUT = 10

# Error messages
ERROR_CONNECTING_RXNORM = "Error connecting to RxNorm API"

# Caches for API responses
autocomplete_cache = TTLCache(maxsize=1024, ttl=300)
lookup_cache = TTLCache(maxsize=1024, ttl=300)
properties_cache = TTLCache(maxsize=1024, ttl=300)


@cached(autocomplete_cache)
def autocomplete_drugs(term: str) -> list[str]:
    """Get drug name autocomplete suggestions from RxNorm.

    Args:
        term: Incomplete drug name entry

    Returns:
        List of suggested drug names
    """
    address = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={term}"
    result = requests.get(address, timeout=REQUEST_TIMEOUT)

    if result.status_code != HTTP_OK:
        raise ValueError(ERROR_CONNECTING_RXNORM)

    info = result.json()

    # nested structure - drugGroup and conceptgroup extraction.
    """
    {
    "drugGroup": {
    "conceptGroup": [
      {
        "conceptProperties": [
          {"name": "Ibuprofen"},
          ...
        ]
      }
    ]
    }
    }
    """
    drug_group = info.get("drugGroup", {})
    concept_group = drug_group.get("conceptGroup", [])

    return_list = []
    for i in concept_group:
        concept_properties = i.get("conceptProperties", [])
        return_list.extend(j["name"] for j in concept_properties if "name" in j)

    # using approximateTerm to find fuzzy matches --> typo, partial.
    if len(return_list) < MIN_AUTOCOMPLETE_RESULTS:
        approximate = f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={term}&maxEntries=10"
        approximate_response = requests.get(approximate, timeout=REQUEST_TIMEOUT)
        if approximate_response.status_code == HTTP_OK:
            approximate_json = approximate_response.json()
            approximate_group = approximate_json.get("approximateGroup", {}).get(
                "candidate", []
            )
            for k in approximate_group:
                drug_name = k.get("inputTerm")
                if drug_name:
                    return_list.append(drug_name)

    # try limiting to 5/or 10 results
    suggestions = list(dict.fromkeys(return_list))[:10]

    return suggestions or [term]


@cached(lookup_cache)
def lookup_rxcui(name: str) -> dict:
    """Find RxCUI (RxNorm Concept Unique Identifier) for a drug name.

    Args:
        name: Drug name to look up

    Returns:
        Dictionary with query name and list of RxCUI IDs
    """
    # https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiByString.html
    url = f"{RXNORM_ENDPOINT}/rxcui.json"

    # exact or normalized- URL: [https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.findRxcuiByString.html]
    params = {"name": name, "search": 2}

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        error_msg = f"RxNav request failed: {e}"
        raise ValueError(error_msg)

    if resp.status_code != HTTP_OK:
        error_msg = f"RxNav returned {resp.status_code}"
        raise ValueError(error_msg)

    # JSON structure --> {"rxnormdata": {"idGroup": {"rxnormId": ["------"]}}}
    info = resp.json()
    id_no = []
    try:
        id_no = info.get("idGroup", {}).get("rxnormId") or info.get(
            "rxnormdata", {}
        ).get("idGroup", {}).get("rxnormId", [])
    except Exception:
        id_no = []

    id_no = id_no or []
    return {"query": name, "rxcui": id_no}


@cached(properties_cache)
def get_rxnorm_properties(rxcui: int, prop_name: str | None = None) -> dict:
    """Get properties for an RxCUI.

    Args:
        rxcui: RxNorm Concept Unique Identifier
        prop_name: Optional property name to retrieve specific property

    Returns:
        Dictionary with RxNorm properties
    """
    # getRxProperty: /REST/rxcui/{rxcui}/property.json?propName=propName
    # getRxConceptProperties: /REST/rxcui/{rxcui}/properties.json
    # https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRxProperty.html
    # https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getRxConceptProperties.html

    if prop_name:
        url = f"{RXNORM_ENDPOINT}/rxcui/{rxcui}/property.json"
        params = {"propName": prop_name}
    else:
        url = f"{RXNORM_ENDPOINT}/rxcui/{rxcui}/properties.json"
        params = {}

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except Exception as error:
        error_msg = f"Failed to connect to RxNav: {error}"
        raise ValueError(error_msg)

    if response.status_code != HTTP_OK:
        error_msg = f"RxNav API returned {response.status_code}"
        raise ValueError(error_msg)

    return response.json()
