"""PubMed service functions for interacting with PubMed API.

This service provides functions to search PubMed and retrieve publication details
using the NCBI E-utilities API.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

# PubMed E-utilities base URL
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_publications(
    query: str,
    result_start: int = 0,
    result_max: int = 10,
    sort: str = "relevance",
) -> list[str]:
    """Search PubMed and return list of publication IDs.

    Args:
        query: Search query string
        result_start: Starting index for pagination (default: 0)
        result_max: Maximum number of results to return (default: 10)
        sort: Sort order for results. Options: 'relevance' (default, best for impact),
              'pub_date' (most recent first), 'author', 'journal'

    Returns:
        List of PubMed IDs (PMIDs) matching the query

    Raises:
        ValueError: If the API request fails or invalid sort parameter
    """
    # Validate sort parameter
    valid_sorts = ["relevance", "pub_date", "author", "journal"]
    if sort not in valid_sorts:
        raise ValueError(
            f"Invalid sort parameter: {sort}. Must be one of {valid_sorts}"
        )

    url = (
        f"{PUBMED_BASE_URL}/esearch.fcgi"
        f"?db=pubmed&resultStart={result_start}&resultMax={result_max}"
        f"&term={query}&sort={sort}&retmode=json"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()

        # Extract IDs from response
        ids = result.get("esearchresult", {}).get("idlist", [])
        return ids
    except requests.RequestException as e:
        raise ValueError(f"PubMed API request failed: {e}")
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to parse PubMed API response: {e}")


def get_publication_details(
    ids: list[str],
    fields: list[str] | None = None,
) -> list[dict]:
    """Get detailed information for a list of publication IDs.

    Args:
        ids: List of PubMed IDs (PMIDs)
        fields: Optional list of fields to retrieve. If None or contains 'all',
                returns all available fields. Valid fields: PMID, Title, Abstract,
                AuthorList, Journal, PublicationYear, MeSHTerms

    Returns:
        List of dictionaries containing publication details

    Raises:
        ValueError: If the API request fails or XML parsing fails
    """
    if not ids:
        return []

    # Default to all fields if not specified
    if fields is None or "all" in fields:
        fields = ["all"]

    # Join IDs for API request
    id_string = ",".join(ids)
    url = f"{PUBMED_BASE_URL}/efetch.fcgi?db=pubmed&id={id_string}&retmode=xml"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        # Parse XML response
        root = ET.fromstring(response.content)  # noqa: S314
        details = []

        for article in root.findall(".//PubmedArticle"):
            pub_details = {}

            # Extract PMID
            if "PMID" in fields or "all" in fields:
                pmid_elem = article.find(".//PMID")
                pub_details["PMID"] = pmid_elem.text if pmid_elem is not None else None

            # Extract Title
            if "Title" in fields or "all" in fields:
                title_elem = article.find(".//ArticleTitle")
                pub_details["Title"] = (
                    title_elem.text if title_elem is not None else None
                )

            # Extract Abstract
            if "Abstract" in fields or "all" in fields:
                abstract_elem = article.find(".//AbstractText")
                pub_details["Abstract"] = (
                    abstract_elem.text if abstract_elem is not None else None
                )

            # Extract Author List
            if "AuthorList" in fields or "all" in fields:
                authors = []
                for author in article.findall(".//Author"):
                    last_name_elem = author.find(".//LastName")
                    fore_name_elem = author.find(".//ForeName")
                    last_name = (
                        last_name_elem.text if last_name_elem is not None else ""
                    )
                    fore_name = (
                        fore_name_elem.text if fore_name_elem is not None else ""
                    )
                    full_name = f"{fore_name} {last_name}".strip()
                    if full_name:
                        authors.append(full_name)
                pub_details["AuthorList"] = authors

            # Extract Journal
            if "Journal" in fields or "all" in fields:
                journal_elem = article.find(".//Journal//Title")
                pub_details["Journal"] = (
                    journal_elem.text if journal_elem is not None else None
                )

            # Extract Publication Year
            if "PublicationYear" in fields or "all" in fields:
                year_elem = article.find(".//PubDate//Year")
                pub_details["PublicationYear"] = (
                    year_elem.text if year_elem is not None else None
                )

            # Extract MeSH Terms
            if "MeSHTerms" in fields or "all" in fields:
                mesh_terms = []
                for mesh in article.findall(".//MeshHeading"):
                    descriptor_elem = mesh.find(".//DescriptorName")
                    if descriptor_elem is not None and descriptor_elem.text:
                        mesh_terms.append(descriptor_elem.text)
                pub_details["MeSHTerms"] = mesh_terms

            # Handle missing fields
            for field in fields:
                if field != "all" and field not in pub_details:
                    pub_details[field] = None

            details.append(pub_details)

        return details
    except requests.RequestException as e:
        raise ValueError(f"PubMed API request failed: {e}")
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse PubMed XML response: {e}")
