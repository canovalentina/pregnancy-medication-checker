# Async calls to the OpenFDA API.
# Based on: Uses the OpenFDA API specification and examples from their documentation.
# Cache logic adapted from common TTL cache patterns in Python.

# Reads environment variables./cache time-to-live (TTL)./ Encode query strings safely./ hints for dictionaries and optional parameters./
import os
import time
import urllib.parse
from typing import Any

# modern async HTTP client to send requests./ Load .env file./
# URL: [https://www.python-httpx.org/], [https://pypi.org/project/python-dotenv/]
import httpx
from dotenv import load_dotenv

# loading variables from .env file into the runtime environment.
load_dotenv()
# root URL for all API requests
OPENFDA_BASE = "https://api.fda.gov"
# API key for higher rate limits. # "Add later if needed!""
OPENFDA_KEY = os.getenv("OPENFDA_API_KEY") or None
# cache keeps results for 5 min.
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# Simple in memory TTL cache --> creating a global dictionary. Helpful to avoid repeating identical API calls, for common queries.
_cache: dict[str, dict[str, Any]] = (
    {}
)  # key --> {"ts": float[timestamp when it was stored], "value": Any[cached JSON data]}


# if key exist and not expired --> return the cached response.
# if key expired --> delete it and return None.
def _cache_get(key: str):
    entry = _cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > CACHE_TTL:
        _cache.pop(key, None)
        return None
    return entry["value"]


# URL: [https://realpython.com/lru-cache-python/]
# add/update a cache entry
def _cache_set(key: str, value):
    _cache[key] = {"ts": time.time(), "value": value}


# for later: "to pass api key in headers --> openFDA uses query param 'api_key'!"
# User-Agent header: identifiying the app to the OpenFDA API
def _make_headers():
    return {"User-Agent": "pregnancy-med-checker/0.1 (#project contact)"}


# append the query string to FDA API key in .env./ FDA API key --> increase the request limit from 240 to 1200 requests per minute.
# for later! --> to get the key refer to URL: [https://open.fda.gov/apis/authentication/]
def _append_api_key(params: dict):
    # if OPENFDA_KEY set, append:
    if OPENFDA_KEY:
        params["api_key"] = OPENFDA_KEY
    return params


# async fetcher function. Building a unique cache key from the URL and query params.
# if the response exists in cache --> immediately return it
async def _get_json(
    url: str, params: dict | None = None, use_cache: bool = True
) -> dict:
    params = params or {}
    # cache key
    key = url + "?" + urllib.parse.urlencode(sorted(params.items()))
    if use_cache:
        cached = _cache_get(key)
        if cached is not None:
            return {"from_cache": True, "data": cached}

    # create asynchronous HTTP client.
    async with httpx.AsyncClient(timeout=20.0, headers=_make_headers()) as client:
        params = _append_api_key(params)
        # sends request to OpenFDA
        resp = await client.get(url, params=params)
        # raise for status will throw httpx.HTTPStatusError on non-2xx
        resp.raise_for_status()
        # convert the response body to a Python dictionary
        data = resp.json()

    # save the new response in cache
    if use_cache:
        _cache_set(key, data)
    # return a dictionary, indicate --> if it came from cache
    return {"from_cache": False, "data": data}


async def get_label_by_name(drug_name: str, limit: int = 1):

    url = f"{OPENFDA_BASE}/drug/label.json"
    # try searching harmonized fields first (safer): openfda.brand_name or openfda.generic_name
    # use quotes and exact match-ish query
    # queries the drug label endpoint
    q = f'openfda.brand_name:"{drug_name}"'
    params = {"search": q, "limit": limit}
    try:
        r = await _get_json(url, params)
        return r["data"]
    except httpx.HTTPStatusError:
        # fallback to medicinalproduct which appears in many entries
        params = {
            "search": f'pregnancy+OR+{urllib.parse.quote(f"medicinalproduct:{drug_name}")}',
            "limit": limit,
        }
        # simpler fallback: search medicinalproduct (non-harmonized)
        params = {"search": f'medicinalproduct:"{drug_name}"', "limit": limit}
        r = await _get_json(url, params)
        return r["data"]


# autocomplete/ search suggestions:
async def search_labels(term: str, limit: int = 10):

    url = f"{OPENFDA_BASE}/drug/label.json"
    # logical OR query: search both brand & generic name
    # q = f'openfda.brand_name:{term} +OR+openfda.generic_name:{term}' # noqa: ERA001
    # Handling OpenFDA case senditivity;
    q = f'openfda.brand_name:"{term}" +OR+ openfda.generic_name:"{term}"'
    # returning 10 results
    params = {"search": q, "limit": limit}
    r = await _get_json(url, params)
    return r["data"]


# calling the adverse event reports endpoint --> /drug/event.json
async def get_adverse_events_by_drug(drug_name: str, limit: int = 10):

    # Note! openFDA event records are --> noisy and may require normalization.

    url = f"{OPENFDA_BASE}/drug/event.json"
    # try using patient.drug.medicinalproduct exact-ish match to --> search for patient-reported reactions
    params = {"search": f'patient.drug.medicinalproduct:"{drug_name}"', "limit": limit}
    try:
        r = await _get_json(url, params)
        return r["data"]
    except httpx.HTTPStatusError:
        # if the first query fails --> fall back to a secondary field
        # fallback: try searching openfda.brand_name (pharm_class fields)
        params = {
            "search": f'patient.drug.openfda.brand_name:"{drug_name}"',
            "limit": limit,
        }
        r = await _get_json(url, params)
        return r["data"]


# fetch National Drug Code (NDC) data
# display dosage forms, manufacturers.
async def get_ndc_info(drug_name: str, limit: int = 10):
    url = f"{OPENFDA_BASE}/drug/ndc.json"
    params = {"search": f'proprietary_name:"{drug_name}"', "limit": limit}
    r = await _get_json(url, params)
    return r["data"]
