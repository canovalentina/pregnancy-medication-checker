/**
 * Define the PubMed API client
 */

import type { APIResponse, PubMedSearchResponse, PubMedDetailsResponse } from '../types/api';
import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function searchPublications(
  query: string,
  resultStart: number = 0,
  resultMax: number = 10
): Promise<APIResponse<PubMedSearchResponse>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/publications`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query, result_start: resultStart, result_max: resultMax }),
    });
    if (!response.ok) {
      return {
        data: { ids: [] },
        error: `Failed to search publications: ${response.statusText}`,
        status: 'error',
      };
    }
    const data: PubMedSearchResponse = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { ids: [] },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function getPublicationDetails(
  ids: string[],
  fields: string = 'all'
): Promise<APIResponse<PubMedDetailsResponse>> {
  try {
    const idsParam = ids.join(',');
    const response = await fetch(
      `${API_BASE_URL}/api/publications/details?ids=${encodeURIComponent(idsParam)}&fields=${encodeURIComponent(fields)}`,
      { headers: getAuthHeaders() }
    );
    if (!response.ok) {
      return {
        data: { results: [], totalPages: 0, totalResults: 0 },
        error: `Failed to fetch publication details: ${response.statusText}`,
        status: 'error',
      };
    }
    const data: PubMedDetailsResponse = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { results: [], totalPages: 0, totalResults: 0 },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}