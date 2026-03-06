/**
 * Define the FHIR API client
 */

import type { APIResponse, FHIRStatus, Patient, PatientSummary } from '../types/api';
import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function getFHIRStatus(): Promise<APIResponse<FHIRStatus>> {
  const response = await fetch(`${API_BASE_URL}/api/fhir/status`, { headers: getAuthHeaders() });
  if (!response.ok) {
    return { data: { status: 'error', server: API_BASE_URL }, error: response.statusText, status: 'error' };
  }
  const data: FHIRStatus = await response.json();
  return { data, error: null, status: 'success' };
}

export async function searchPatients(params: {
  name?: string;
  birth_date?: string;
  gender?: string;
  only_ingested_patients?: boolean;
}): Promise<APIResponse<Patient[]>> {
  try {
    const queryParams = new URLSearchParams();
    if (params.name) queryParams.append('name', params.name);
    if (params.birth_date) queryParams.append('birth_date', params.birth_date);
    if (params.gender) queryParams.append('gender', params.gender);
    if (params.only_ingested_patients !== undefined) {
      queryParams.append('only_ingested_patients', params.only_ingested_patients.toString());
    }

    const response = await fetch(`${API_BASE_URL}/api/fhir/patients?${queryParams.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return { data: [], error: response.statusText, status: 'error' };
    }
    const data = await response.json();
    // Handle both direct array and wrapped response
    const patients = Array.isArray(data) ? data : data.resources || [];
    return { data: patients, error: null, status: 'success' };
  } catch (error) {
    return { data: [], error: error instanceof Error ? error.message : 'Unknown error', status: 'error' };
  }
}

export async function getPatientMedications(patientId: string): Promise<APIResponse<any[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/fhir/patients/${patientId}/medications`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return { data: [], error: response.statusText, status: 'error' };
    }
    const data = await response.json();
    const medications = Array.isArray(data) ? data : data.resources || [];
    return { data: medications, error: null, status: 'success' };
  } catch (error) {
    return { data: [], error: error instanceof Error ? error.message : 'Unknown error', status: 'error' };
  }
}

export async function getPatientConditions(patientId: string): Promise<APIResponse<any[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/fhir/patients/${patientId}/conditions`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return { data: [], error: response.statusText, status: 'error' };
    }
    const data = await response.json();
    const conditions = Array.isArray(data) ? data : data.resources || [];
    return { data: conditions, error: null, status: 'success' };
  } catch (error) {
    return { data: [], error: error instanceof Error ? error.message : 'Unknown error', status: 'error' };
  }
}

export async function getPregnancyObservations(patientId: string): Promise<APIResponse<any[]>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/fhir/patients/${patientId}/pregnancy-observations`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return { data: [], error: response.statusText, status: 'error' };
    }
    const data = await response.json();
    const observations = Array.isArray(data) ? data : data.resources || [];
    return { data: observations, error: null, status: 'success' };
  } catch (error) {
    return { data: [], error: error instanceof Error ? error.message : 'Unknown error', status: 'error' };
  }
}

export async function getPatientSummary(patientId: string): Promise<APIResponse<PatientSummary>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/fhir/patients/${patientId}/summary`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return {
        data: { patient: null, medications: [], conditions: [], observations: [] },
        error: response.statusText,
        status: 'error',
      };
    }
    const data = await response.json();
    const summary = Array.isArray(data.resources) && data.resources.length > 0 ? data.resources[0] : data;
    return { data: summary, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { patient: null, medications: [], conditions: [], observations: [] },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}