/**
 * Notes API client for provider notes
 */

import type { APIResponse } from '../types/api';
import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface Note {
  id: string;
  patient_id: string;
  content: string;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface NotesResponse {
  patient_id: string;
  notes: Note[];
  total: number;
}

export async function getPatientNotes(patientId: string): Promise<APIResponse<NotesResponse>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notes/patients/${patientId}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || response.statusText;
      } catch {
        // If response is not JSON, use statusText
      }
      return {
        data: { patient_id: patientId, notes: [], total: 0 },
        error: errorMessage,
        status: 'error',
      };
    }
    const data: NotesResponse = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { patient_id: patientId, notes: [], total: 0 },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function createNote(
  patientId: string,
  content: string
): Promise<APIResponse<{ message: string; note: Note }>> {
  try {
    const authHeaders = getAuthHeaders();
    const hasAuth = typeof authHeaders === 'object' && !Array.isArray(authHeaders) && 'Authorization' in authHeaders;
    console.log('Creating note - Auth header present:', hasAuth);
    
    const response = await fetch(`${API_BASE_URL}/api/notes/patients/${patientId}`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ patient_id: patientId, content }),
    });
    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || response.statusText;
      } catch {
        try {
          const errorText = await response.text();
          errorMessage = errorText || response.statusText;
        } catch {
          // Use statusText as fallback
        }
      }
      return {
        data: { message: '', note: {} as Note },
        error: errorMessage,
        status: 'error',
      };
    }
    const data = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { message: '', note: {} as Note },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function updateNote(
  patientId: string,
  noteId: string,
  content: string
): Promise<APIResponse<{ message: string; note: Note }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notes/patients/${patientId}/notes/${noteId}`, {
      method: 'PUT',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || response.statusText;
      } catch {
        try {
          const errorText = await response.text();
          errorMessage = errorText || response.statusText;
        } catch {
          // Use statusText as fallback
        }
      }
      return {
        data: { message: '', note: {} as Note },
        error: errorMessage,
        status: 'error',
      };
    }
    const data = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { message: '', note: {} as Note },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function deleteNote(
  patientId: string,
  noteId: string
): Promise<APIResponse<{ message: string }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/notes/patients/${patientId}/notes/${noteId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const errorText = await response.text();
      return {
        data: { message: '' },
        error: errorText || response.statusText,
        status: 'error',
      };
    }
    const data = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { message: '' },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

