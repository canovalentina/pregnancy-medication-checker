/**
 * Drug Interactions API client
 * 
 * This client communicates with the backend API which uses the DrugBank database
 * to check for drug-drug interactions. The backend maintains a comprehensive
 * database of over 2.8 million drug interactions from DrugBank.
 */

import type { APIResponse } from '../types/api';
import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type DrugInteraction = {
  drug1: string;
  drug2: string;
  interaction: string | null;
  message?: string;
};

export async function checkDrugInteraction(
  drug1: string,
  drug2: string
): Promise<APIResponse<DrugInteraction>> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/interaction?drug1=${encodeURIComponent(drug1)}&drug2=${encodeURIComponent(drug2)}`,
      {
        headers: getAuthHeaders(),
      }
    );
    if (!response.ok) {
      return {
        data: { drug1, drug2, interaction: null, message: 'Failed to check interaction' },
        error: `Failed to check interaction: ${response.statusText}`,
        status: 'error',
      };
    }
    const data: DrugInteraction = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { drug1, drug2, interaction: null, message: 'Error checking interaction' },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export type BatchInteractionRequest = {
  pairs: Array<{ drug1: string; drug2: string }>;
};

export type BatchInteractionResponse = {
  results: DrugInteraction[];
  error?: string;
};

/**
 * Check multiple drug interactions in a single API call.
 * More efficient than calling checkDrugInteraction() multiple times.
 * 
 * @param pairs Array of drug pairs to check
 * @returns Promise with batch results
 */
export async function checkDrugInteractionsBatch(
  pairs: Array<{ drug1: string; drug2: string }>
): Promise<APIResponse<BatchInteractionResponse>> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/interaction/batch`,
      {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pairs }),
      }
    );
    
    if (!response.ok) {
      return {
        data: { results: [] },
        error: `Failed to check interactions: ${response.statusText}`,
        status: 'error',
      };
    }
    
    const data: BatchInteractionResponse = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { results: [] },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

