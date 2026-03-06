/**
 * Define the RxNorm API client
 */

import type { APIResponse, RxNormLookupResult } from '../types/api';
import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function autocompleteDrugs(term: string): Promise<APIResponse<string[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/autocomplete?term=${encodeURIComponent(term)}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return {
        data: [],
        error: `Failed to fetch autocomplete: ${response.statusText}`,
        status: 'error',
      };
    }
    const data: string[] = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: [],
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function lookupRxCUI(name: string): Promise<APIResponse<RxNormLookupResult>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/rxnorm/lookup?name=${encodeURIComponent(name)}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return {
        data: { query: name, rxcui: [] },
        error: `Failed to lookup RxCUI: ${response.statusText}`,
        status: 'error',
      };
    }
    const data: RxNormLookupResult = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { query: name, rxcui: [] },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function getRxNormProperties(
  rxcui: number,
  propName?: string
): Promise<APIResponse<Record<string, unknown>>> {
  try {
    const url = propName
      ? `${API_BASE_URL}/api/rxnorm/properties/${rxcui}?prop_name=${encodeURIComponent(propName)}`
      : `${API_BASE_URL}/api/rxnorm/properties/${rxcui}`;
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) {
      return {
        data: {},
        error: `Failed to fetch properties: ${response.statusText}`,
        status: 'error',
      };
    }
    const data = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: {},
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

